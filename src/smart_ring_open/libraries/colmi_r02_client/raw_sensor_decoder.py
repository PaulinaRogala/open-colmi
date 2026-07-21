"""
Raw sensor decoder for Colmi R02.
Handles PPG, accelerometer and Sp02 raw packets.
"""
from smart_ring_open.libraries.colmi_r02_edgeimpulse.ring import create_command
from dataclasses import dataclass
from datetime import datetime

RAW_SENSOR_CMD_TYPE = 0xA1
ENABLE_RAW_SENSOR_CMD = create_command("a104")
DISABLE_RAW_SENSOR_CMD = create_command("a102")

@dataclass
class SpO2RawData:
    """Raw SpO2 data from Colmi R02"""
    spo2: int
    spo2_max: int
    spo2_min: int
    spo2_diff: int
    timestamp: float

@dataclass
class AccelerometerRawData:
    """Raw accelerometer data from Colmi R02"""
    accX: float
    accY: float
    accZ: float
    timestamp: float

@dataclass
class PPGRawData:
    """Raw PPG data from Colmi R02"""
    ppg: int
    ppg_max: int
    ppg_min: int
    ppg_diff: int
    timestamp: float

def decode_raw_sensor_packet(data: bytearray)->SpO2RawData|PPGRawData|AccelerometerRawData|None:
    """
    Decode a raw sensor packet from Colmi R02.
    Args:
        data: Raw packet from BLE notification.
    Returns:
        SpO2RawData, PPGRawData, or AccelerometerRawData if valid, else None.
    """
    if len(data)<10 or data[0]!= RAW_SENSOR_CMD_TYPE:
        return None
    
    subtype = data[1]
    timestamp=datetime.now().timestamp()

    if subtype == 0x01:
        spO2 = (data[2] << 8) | data[3]
        spO2_max = data[5]
        spO2_min = data[7]
        spO2_diff = data[9]
        return SpO2RawData(
            spo2=spO2,
            spo2_max=spO2_max,
            spo2_min=spO2_min,
            spo2_diff=spO2_diff,
            timestamp=timestamp
        )
    
    elif subtype == 0x02:
        ppg = (data[2] << 8) | data[3]
        ppg_max = (data[4] << 8) | data[5]
        ppg_min = (data[6] << 8) | data[7]
        ppg_diff = (data[8] << 8) | data[9]
        return PPGRawData(
            ppg=ppg,
            ppg_max=ppg_max,
            ppg_min=ppg_min,
            ppg_diff=ppg_diff,
            timestamp=timestamp
        )
    
    elif subtype == 0x03:
        accX = ((data[6] << 4) | (data[7] & 0xF)) - (1 << 11) if data[6] & 0x8 else ((data[6] << 4) | (data[7] & 0xF))
        accY = ((data[2] << 4) | (data[3] & 0xF)) - (1 << 11) if data[2] & 0x8 else ((data[2] << 4) | (data[3] & 0xF))
        accZ = ((data[4] << 4) | (data[5] & 0xF)) - (1 << 11) if data[4] & 0x8 else ((data[4] << 4) | (data[5] & 0xF))
        return AccelerometerRawData(
            accX=accX,
            accY=accY,
            accZ=accZ,
            timestamp=timestamp
        )
    return None
        

    



