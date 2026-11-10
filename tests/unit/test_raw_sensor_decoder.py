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

#test for accelerometer
def test_decode_acc_packet():
    raw_hex="a103deb4fdc8fb3e0000000000000034"
    payload=bytes.fromhex(raw_hex)

    decoded=decode_raw_sensor_packet(payload)
    assert isinstance(decoded, AccelerometerRawData)
    # 12-bit two's complement: 0xFBE, 0xDE4, 0xFD8 are negative
    assert decoded.accX==-66
    assert decoded.accY==-540
    assert decoded.accZ==-40

#full signed range: sign bit is bit 7 of the high byte
def test_decode_acc_sign_and_range():
    for hi, lo, expected in [(0x00, 0x01, 1), (0x7F, 0x0F, 2047), (0x80, 0x00, -2048), (0xFF, 0x0F, -1)]:
        payload = bytes([0xA1, 0x03, hi, lo, 0, 0, 0, 0]) + bytes(8)
        assert decode_raw_sensor_packet(payload).accY == expected

#test for invalid packet
def test_decode_invalid_packet():
    raw_hex="a105066320281f5100d700000000009b"
    payload=bytes.fromhex(raw_hex)
    
    decoded=decode_raw_sensor_packet(payload)
    assert decoded is None 