"""The client's notification handler, fed packets directly (no ring, no BLE connection)."""
from src.smart_ring_open.libraries.colmi_r02_client import real_time
from src.smart_ring_open.libraries.colmi_r02_client.client import Client
from src.smart_ring_open.libraries.colmi_r02_client.packet import make_packet


def hr_packet(value: int, error_code: int = 0) -> bytearray:
    return make_packet(real_time.CMD_START_REAL_TIME, bytearray([real_time.RealTimeReading.HEART_RATE, error_code, value]))


def queued(client: Client) -> list:
    q = client.queues[real_time.CMD_START_REAL_TIME]
    return [q.get_nowait() for _ in range(q.qsize())]


def test_valid_heart_rate_packet_is_queued():
    client = Client("00:00:00:00:00:00")
    client._handle_tx(None, hr_packet(72))
    [reading] = queued(client)
    assert isinstance(reading, real_time.Reading)
    assert reading.value == 72


def test_bad_checksum_is_dropped_and_counted():
    client = Client("00:00:00:00:00:00")
    p = hr_packet(72)
    p[3] = 85  # corrupted HR byte: must not reach the caller as 85 BPM
    client._handle_tx(None, p)
    assert queued(client) == []
    assert client.invalid_packets == 1


def test_short_packet_does_not_raise():
    client = Client("00:00:00:00:00:00")
    client._handle_tx(None, bytearray(hr_packet(72)[:10]))
    assert client.invalid_packets == 1


def test_error_flag_packet_is_counted_not_parsed():
    client = Client("00:00:00:00:00:00")
    client._handle_tx(None, make_packet(real_time.CMD_START_REAL_TIME | 0x80, bytearray([1, 0, 72])))
    assert queued(client) == []
    assert client.error_packets == 1


def test_unknown_reading_kind_does_not_raise():
    client = Client("00:00:00:00:00:00")
    client._handle_tx(None, make_packet(real_time.CMD_START_REAL_TIME, bytearray([6, 0, 72])))  # kind 6 not in the enum
    assert queued(client) == []


def test_raw_sensor_packets_are_not_error_replies():
    # 0xA1 has its top bit set but is a command of its own, not 0x21 with the error flag
    from src.smart_ring_open.libraries.colmi_r02_client import raw_sensor_decoder
    client = Client("00:00:00:00:00:00")
    client._handle_tx(None, bytearray(bytes.fromhex("a102066320281f5100d700000000009b")))
    assert client.error_packets == 0
    q = client.queues[raw_sensor_decoder.RAW_SENSOR_CMD_TYPE]
    assert isinstance(q.get_nowait(), raw_sensor_decoder.PPGRawData)
