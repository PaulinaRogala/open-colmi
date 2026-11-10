"""Real-time HR without a ring: send_packet is replaced by a fake ring that answers through _handle_tx."""
import asyncio
import time

from src.smart_ring_open.libraries.colmi_r02_client import real_time
from src.smart_ring_open.libraries.colmi_r02_client.client import Client
from src.smart_ring_open.libraries.colmi_r02_client.packet import make_packet

HR = real_time.RealTimeReading.HEART_RATE


def hr_packet(value: int, error_code: int = 0) -> bytearray:
    return make_packet(real_time.CMD_START_REAL_TIME, bytearray([HR, error_code, value]))


class FakeRingClient(Client):
    """Answers a start packet with `values`, one every `period_s` seconds."""

    def __init__(self, values: list[int], period_s: float = 0.01):
        super().__init__("00:00:00:00:00:00")
        self.values, self.period_s, self.sent = values, period_s, []

    async def send_packet(self, packet: bytearray) -> None:
        self.sent.append(bytes(packet))
        if packet == real_time.get_start_packet(HR):
            asyncio.get_running_loop().create_task(self._answer())

    async def _answer(self) -> None:
        for v in self.values:
            await asyncio.sleep(self.period_s)
            self._handle_tx(None, hr_packet(v))


def test_parsed_reading_carries_arrival_time():
    before = time.time()
    reading = real_time.parse_real_time_reading(hr_packet(61))
    assert reading.value == 61 and before <= reading.timestamp <= time.time()


def test_stale_readings_are_not_returned_by_the_next_measurement():
    async def run():
        client = FakeRingClient([60] * 6)
        client._handle_tx(None, hr_packet(85))  # left over from an earlier measurement
        return await client.get_realtime_reading(HR)

    assert asyncio.run(run()) == [60] * 6


def test_stream_yields_zeros_and_values_with_times_then_stops():
    async def run():
        client = FakeRingClient([0, 0, 59, 60, 61])
        got = [r async for r in client.stream_real_time(HR, duration_s=0.3, keepalive_s=0.1)]
        return client, got

    client, got = asyncio.run(run())
    assert [r.value for r in got] == [0, 0, 59, 60, 61]
    assert all(r.timestamp > 0 for r in got)
    assert [r.timestamp for r in got] == sorted(r.timestamp for r in got)
    assert client.sent[0] == real_time.get_start_packet(HR)
    assert real_time.get_continue_packet(HR) in client.sent
    assert client.sent[-1] == real_time.get_stop_packet(HR)


def test_stream_sends_stop_when_the_caller_leaves_early():
    async def run():
        client = FakeRingClient([60] * 50)
        stream = client.stream_real_time(HR, duration_s=5)
        async for _ in stream:
            break
        await stream.aclose()
        return client

    assert asyncio.run(run()).sent[-1] == real_time.get_stop_packet(HR)


def test_continue_packet_carries_the_number_3_not_ascii():
    assert real_time.CONTINUE_HEART_RATE_PACKET[:2] == bytearray([0x1E, 0x03])


def test_command_30_heart_rate_is_parsed_and_queued():
    client = Client("00:00:00:00:00:00")
    client._handle_tx(None, make_packet(real_time.CMD_REAL_TIME_HEART_RATE, bytearray([64])))
    r = client.queues[real_time.CMD_REAL_TIME_HEART_RATE].get_nowait()
    assert isinstance(r, real_time.RealtimeHeartRate) and r.value == 64 and r.timestamp > 0
