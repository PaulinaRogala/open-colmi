"""
Raw sensor decoder for Colmi R02.
Handles PPG, accelerometer and Sp02 raw packets.
"""
from smart_ring_open.libraries.colmi_r02_edgeimpulse.ring import create_command
from dataclasses import dataclass
from datetime import datetime

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





