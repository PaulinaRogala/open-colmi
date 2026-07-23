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

#test for SpO2
def test_decode_spo2_packet():
    raw_hex="a101007d007d0042003b01000000001a"
    payload=bytes.fromhex(raw_hex)

    decoded=decode_raw_sensor_packet(payload)
    assert isinstance(decoded, SpO2RawData)
    assert decoded.spo2== 0x007d
    assert decoded.spo2_max==0x007d
    assert decoded.spo2_min==0x0042
    assert decoded.spo2_diff==0x003b


#test for invalid packet
def test_decode_invalid_packet():
    raw_hex="a105066320281f5100d700000000009b"
    payload=bytes.fromhex(raw_hex)
    
    decoded=decode_raw_sensor_packet(payload)
    assert decoded is None 