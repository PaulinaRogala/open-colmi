import math

from src.smart_ring_open.libraries.colmi_r02_client import real_time
from src.smart_ring_open.libraries.colmi_r02_client.client import Client
from src.smart_ring_open.libraries.colmi_r02_client.packet import make_packet

HR = real_time.CMD_START_REAL_TIME


def client_with(arrivals: list[tuple[float, int]]) -> Client:
    c = Client("00:00:00:00:00:00")
    for i, (t, cmd) in enumerate(arrivals, start=1):
        c._received_sequence[i], c._received_types[i] = t, cmd
    return c


def test_delays_per_packet_type():
    c = client_with([(0.0, HR), (0.5, 0x03), (1.0, HR), (2.0, HR)])  # a battery reply in between
    assert c.get_delays() == [0.5, 0.5, 1.0]
    assert c.get_delays(HR) == [1.0, 1.0]
    assert c.get_jitter(HR) == 0.0
    assert c.get_transmission_continuity(4, HR) == 0.75


def test_jitter_with_too_few_packets_is_nan_not_an_error():
    assert math.isnan(client_with([(0.0, HR), (1.0, HR)]).get_jitter())
    assert math.isnan(Client("00:00:00:00:00:00").get_jitter())


def test_handler_records_packet_type():
    c = Client("00:00:00:00:00:00")
    c._handle_tx(None, make_packet(HR, bytearray([1, 0, 70])))
    assert c.get_transmission_continuity(1, HR) == 1.0
