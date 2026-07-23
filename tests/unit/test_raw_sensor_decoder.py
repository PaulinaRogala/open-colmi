import pytest
from src.smart_ring_open.libraries.colmi_r02_client.raw_sensor_decoder import decode_raw_sensor_packet, PPGRawData, AccelerometerRawData, SpO2RawData

#test for PPG 
def test_decode_ppg_packet():
    raw_hex="a102066320281f5100d700000000009b"
    payload=bytes.fromhex(raw_hex)

    decoded=decode_raw_sensor_packet(payload)
    assert isinstance(decoded, PPGRawData)
    assert decoded.ppg == 0x0663
    assert decoded.ppg_max == 0x2028
    assert decoded.ppg_min == 0x1F51
    assert decoded.ppg_diff == 0x00D7