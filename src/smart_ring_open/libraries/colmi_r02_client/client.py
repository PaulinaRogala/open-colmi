import asyncio
from collections.abc import AsyncIterator, Callable
from datetime import datetime, timezone
from dataclasses import dataclass
import logging
from pathlib import Path
from types import TracebackType
from typing import Any
import time
import statistics

from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic

from . import battery
from . import blink_twice, date_utils, hr, hr_settings, packet, real_time, reboot, set_time, steps
from . import raw_sensor_decoder
from .packet import has_error_flag, is_valid

UART_SERVICE_UUID = "6E40FFF0-B5A3-F393-E0A9-E50E24DCCA9E"
UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

DEVICE_INFO_UUID = "0000180A-0000-1000-8000-00805F9B34FB"
DEVICE_HW_UUID = "00002A27-0000-1000-8000-00805F9B34FB"
DEVICE_FW_UUID = "00002A26-0000-1000-8000-00805F9B34FB"

logger = logging.getLogger(__name__)


def empty_parse(_packet: bytearray) -> None:
    """Used for commands that we expect a response, but there's nothing in the response"""
    return None


def log_packet(packet: bytearray) -> None:
    print("received: ", packet)


# TODO move this maybe?
@dataclass
class FullData:
    address: str
    heart_rates: list[hr.HeartRateLog | hr.NoData]
    sport_details: list[list[steps.SportDetail] | steps.NoData]


COMMAND_HANDLERS: dict[int, Callable[[bytearray], Any]] = {
    battery.CMD_BATTERY: battery.parse_battery,
    real_time.CMD_START_REAL_TIME: real_time.parse_real_time_reading,
    real_time.CMD_STOP_REAL_TIME: empty_parse,
    real_time.CMD_REAL_TIME_HEART_RATE: real_time.parse_realtime_heart_rate,
    steps.CMD_GET_STEP_SOMEDAY: steps.SportDetailParser().parse,
    hr.CMD_READ_HEART_RATE: hr.HeartRateLogParser().parse,
    set_time.CMD_SET_TIME: empty_parse,
    hr_settings.CMD_HEART_RATE_LOG_SETTINGS: hr_settings.parse_heart_rate_log_settings,
    blink_twice.CMD_BLINK_TWICE: empty_parse,
    raw_sensor_decoder.RAW_SENSOR_CMD_TYPE: raw_sensor_decoder.decode_raw_sensor_packet
}
"""
TODO put these somewhere nice

These are commands that we expect to have a response returned for
they must accept a packet as bytearray and then return a value to be put
in the queue for that command type
NOTE: if the value returned is None, it is not added to the queue, this is to support
multi packet messages where the parser has state
"""


class Client:
    def __init__(self, address: str, record_to: Path | None = None):
        self.address = address
        self.bleak_client = BleakClient(self.address)
        self.queues: dict[int, asyncio.Queue] = {cmd: asyncio.Queue() for cmd in COMMAND_HANDLERS}
        self.record_to = record_to
        self._packet_counter = 0
        self._received_sequence = {}
        self._received_types: dict[int, int] = {}
        self.invalid_packets = 0
        """Packets dropped because of a wrong length or checksum."""
        self.error_packets = 0
        """Packets the ring sent with the error flag set (command rejected)."""

    async def __aenter__(self) -> "Client":
        logger.info(f"Connecting to {self.address}")
        await self.connect()
        logger.info("Connected!")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        logger.info("Disconnecting")
        if exc_val is not None:
            logger.error("had an error")
        await self.disconnect()

    async def connect(self):
        await self.bleak_client.connect()

        nrf_uart_service = self.bleak_client.services.get_service(UART_SERVICE_UUID)
        assert nrf_uart_service
        rx_char = nrf_uart_service.get_characteristic(UART_RX_CHAR_UUID)
        assert rx_char
        self.rx_char = rx_char

        await self.bleak_client.start_notify(UART_TX_CHAR_UUID, self._handle_tx)

    async def disconnect(self):
        await self.bleak_client.disconnect()

    def _handle_tx(self, _: BleakGATTCharacteristic, packet: bytearray) -> None:
        """Bleak callback that handles new packets from the ring."""
        self._packet_counter+=1
        self._received_sequence[self._packet_counter]=time.time()
        self._received_types[self._packet_counter] = packet[0] if len(packet) else -1

        logger.info(f"Received packet {packet}")

        # Record every packet as received, before any check, so a recording can be decoded again.
        if self.record_to is not None:
            with self.record_to.open("ab") as f:
                f.write(packet)
                f.write(b"\n")

        # An exception raised here is swallowed by bleak and the packet is lost silently, so
        # bad packets are logged and counted instead of asserted.
        if not is_valid(packet):
            self.invalid_packets += 1
            logger.warning(f"Dropped packet with wrong length or checksum: {bytes(packet).hex()}")
            return
        if has_error_flag(packet, COMMAND_HANDLERS):
            self.error_packets += 1
            logger.warning(f"Ring answered command {packet[0] & 0x7F:#04x} with an error: {bytes(packet).hex()}")
            return

        packet_type = packet[0]
        if packet_type in COMMAND_HANDLERS:
            try:
                result = COMMAND_HANDLERS[packet_type](packet)
            except (AssertionError, ValueError) as e:
                logger.warning(f"Could not parse packet {bytes(packet).hex()}: {e!r}")
                return
            if result is not None:
                self.queues[packet_type].put_nowait(result)
            else:
                logger.debug(f"No result returned from parser for {packet_type}")
        else:
            logger.warning(f"Did not expect this packet: {packet}")

    def get_delays(self, command: int | None = None)->list[float]:
        """Return time intervals between consecutive received packets.
    Args:
        command: only packets of this command (e.g. real_time.CMD_START_REAL_TIME); None = all.
            Mixing packet types (battery, HR, raw data) mixes their intervals.
    Returns:
        A list of delays in seconds between each pair of consecutive packets."""
        sequences = sorted(k for k in self._received_sequence
                           if command is None or self._received_types.get(k) == command)
        delays=[]
        for i in range(1, len(sequences)):
            curr_time=self._received_sequence[sequences[i]]
            prev_time=self._received_sequence[sequences[i-1]]
            delays.append(curr_time-prev_time)
        return delays

    def get_jitter(self, command: int | None = None)->float:
        """Calculate the jitter of received packets.
        Args:
            command: only packets of this command; None = all.
        Returns:
            standard deviation of packet arrival intervals in second;
            nan with fewer than 3 packets (fewer than 2 intervals)."""     
        delays=self.get_delays(command)
        if len(delays) < 2:
            return float("nan")
        return statistics.stdev(delays)

    def get_transmission_continuity(self, expected_packets: int, command: int | None = None)->float:
        """Calculate transmission continuity as the ratio of received packets 
        to the expected number of packets.
    Args:
        expected_packets:
            The expected number of packets during the transmission period.
        command: count only packets of this command; None = all.
    Returns:
        A value between 0.0 and 1.0 representing transmission continuity.
        Returns 1.0 if no packets were expected."""
        
        if expected_packets==0:
            return 1
        received = sum(1 for k in self._received_sequence
                       if command is None or self._received_types.get(k) == command)
        return received/expected_packets
    
    async def send_packet(self, packet: bytearray) -> None:
        logger.debug(f"Sending packet: {packet}")
        await self.bleak_client.write_gatt_char(self.rx_char, packet, response=False)

    async def get_battery(self) -> battery.BatteryInfo:
        await self.send_packet(battery.BATTERY_PACKET)
        result = await self.queues[battery.CMD_BATTERY].get()
        assert isinstance(result, battery.BatteryInfo)
        return result

    def _drain(self, command: int) -> None:
        """Throw away queued results, e.g. readings left over from an earlier measurement."""
        queue = self.queues[command]
        while not queue.empty():
            queue.get_nowait()

    async def _poll_real_time_reading(self, reading_type: real_time.RealTimeReading) -> list[int] | None:
        start_packet = real_time.get_start_packet(reading_type)
        stop_packet = real_time.get_stop_packet(reading_type)

        self._drain(real_time.CMD_START_REAL_TIME)
        await self.send_packet(start_packet)

        valid_readings: list[int] = []
        error = False
        tries = 0
        while len(valid_readings) < 6 and tries < 20:
            try:
                data: real_time.Reading | real_time.ReadingError = await asyncio.wait_for(
                    self.queues[real_time.CMD_START_REAL_TIME].get(),
                    timeout=2,
                )
                if data.kind != reading_type:
                    continue
                if isinstance(data, real_time.ReadingError):
                    error = True
                    break
                if data.value != 0:
                    valid_readings.append(data.value)
            except TimeoutError:
                tries += 1

        await self.send_packet(stop_packet)
        if error:
            return None
        return valid_readings

    async def get_realtime_reading(self, reading_type: real_time.RealTimeReading) -> list[int] | None:
        return await self._poll_real_time_reading(reading_type)

    async def stream_real_time(
        self, reading_type: real_time.RealTimeReading, duration_s: float, keepalive_s: float = 10.0
    ) -> AsyncIterator[real_time.Reading | real_time.ReadingError]:
        """
        Stream every real-time reading for `duration_s` seconds.

        Each reading carries its arrival time (`timestamp`, Unix seconds). Zeros (no lock yet)
        and errors are yielded too, so the caller can tell "no reading" from a value and skip
        the ring's settling period itself. A continue packet is sent every `keepalive_s`
        seconds to keep the measurement running; the stop packet is sent at the end, also
        when the caller leaves the loop early.

            async for r in client.stream_real_time(RealTimeReading.HEART_RATE, 60):
                print(r.timestamp, r.value if isinstance(r, Reading) else f"error {r.code}")
        """
        queue = self.queues[real_time.CMD_START_REAL_TIME]
        self._drain(real_time.CMD_START_REAL_TIME)
        loop = asyncio.get_running_loop()
        await self.send_packet(real_time.get_start_packet(reading_type))
        end = loop.time() + duration_s
        next_keepalive = loop.time() + keepalive_s
        try:
            while (now := loop.time()) < end:
                if now >= next_keepalive:
                    await self.send_packet(real_time.get_continue_packet(reading_type))
                    next_keepalive = now + keepalive_s
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=max(min(end, next_keepalive) - now, 0.01))
                except TimeoutError:
                    continue
                if data.kind == reading_type:
                    yield data
        finally:
            await self.send_packet(real_time.get_stop_packet(reading_type))

    async def set_time(self, ts: datetime) -> None:
        await self.send_packet(set_time.set_time_packet(ts))

    async def blink_twice(self) -> None:
        await self.send_packet(blink_twice.BLINK_TWICE_PACKET)

    async def get_device_info(self) -> dict[str, str]:
        client = self.bleak_client
        data = {}
        device_info_service = client.services.get_service(DEVICE_INFO_UUID)
        assert device_info_service

        hw_info_char = device_info_service.get_characteristic(DEVICE_HW_UUID)
        assert hw_info_char
        hw_version = await client.read_gatt_char(hw_info_char)
        data["hw_version"] = hw_version.decode("utf-8")

        fw_info_char = device_info_service.get_characteristic(DEVICE_FW_UUID)
        assert fw_info_char
        fw_version = await client.read_gatt_char(fw_info_char)
        data["fw_version"] = fw_version.decode("utf-8")

        return data

    async def get_heart_rate_log(self, target: datetime | None = None) -> hr.HeartRateLog | hr.NoData:
        if target is None:
            target = date_utils.start_of_day(date_utils.now())
        await self.send_packet(hr.read_heart_rate_packet(target))
        return await asyncio.wait_for(
            self.queues[hr.CMD_READ_HEART_RATE].get(),
            timeout=2,
        )

    async def get_heart_rate_log_settings(self) -> hr_settings.HeartRateLogSettings:
        await self.send_packet(hr_settings.READ_HEART_RATE_LOG_SETTINGS_PACKET)
        return await asyncio.wait_for(
            self.queues[hr_settings.CMD_HEART_RATE_LOG_SETTINGS].get(),
            timeout=2,
        )

    async def set_heart_rate_log_settings(self, enabled: bool, interval: int) -> None:
        await self.send_packet(hr_settings.hr_log_settings_packet(hr_settings.HeartRateLogSettings(enabled, interval)))

        # clear response from queue as it's unused and wrong
        await asyncio.wait_for(
            self.queues[hr_settings.CMD_HEART_RATE_LOG_SETTINGS].get(),
            timeout=2,
        )

    async def get_steps(self, target: datetime, today: datetime | None = None) -> list[steps.SportDetail] | steps.NoData:
        if today is None:
            today = datetime.now(timezone.utc)

        if target.tzinfo != timezone.utc:
            logger.info("Converting target time to utc")
            target = target.astimezone(tz=timezone.utc)

        days = (today.date() - target.date()).days
        logger.debug(f"Looking back {days} days")

        await self.send_packet(steps.read_steps_packet(days))
        return await asyncio.wait_for(
            self.queues[steps.CMD_GET_STEP_SOMEDAY].get(),
            timeout=2,
        )

    async def reboot(self) -> None:
        await self.send_packet(reboot.REBOOT_PACKET)

    async def raw(self, command: int, subdata: bytearray, replies: int = 0) -> list[bytearray]:
        p = packet.make_packet(command, subdata)
        await self.send_packet(p)

        results = []
        while replies > 0:
            data: bytearray = await asyncio.wait_for(
                self.queues[command].get(),
                timeout=2,
            )
            results.append(data)
            replies -= 1

        return results

    async def get_full_data(self, start: datetime, end: datetime) -> FullData:
        """
        Fetches all data from the ring between start and end. Useful for syncing.
        """
        heart_rate_logs = []
        sport_detail_logs = []
        for d in date_utils.dates_between(start, end):
            heart_rate_logs.append(await self.get_heart_rate_log(d))
            sport_detail_logs.append(await self.get_steps(d))

        return FullData(self.address, heart_rates=heart_rate_logs, sport_details=sport_detail_logs)
