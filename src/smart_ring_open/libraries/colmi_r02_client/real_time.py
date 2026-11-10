"""
Stream real time data from the ring.

Currently heart rate and SPO2 seem reasonable.

HRV, ECG, blood pressure and blood sugar seem unlikely to be something you
can correct
"""

import time
from dataclasses import dataclass
from enum import IntEnum

from .packet import make_packet


class Action(IntEnum):
    START = 1
    PAUSE = 2
    CONTINUE = 3
    STOP = 4


class RealTimeReading(IntEnum):
    """
    Taken from https://colmi.puxtril.com/commands/#data-request
    """

    HEART_RATE = 1
    BLOOD_PRESSURE = 2
    SPO2 = 3
    FATIGUE = 4
    HEALTH_CHECK = 5
    # leaving this out as it's redundant
    # REAL_TIME_HEART_RATE = 6
    ECG = 7
    PRESSURE = 8
    BLOOD_SUGAR = 9
    HRV = 10


REAL_TIME_MAPPING: dict[str, RealTimeReading] = {
    "heart-rate": RealTimeReading.HEART_RATE,
    "blood-pressure": RealTimeReading.BLOOD_PRESSURE,
    "spo2": RealTimeReading.SPO2,
    "fatigue": RealTimeReading.FATIGUE,
    "health-check": RealTimeReading.HEALTH_CHECK,
    "ecg": RealTimeReading.ECG,
    "pressure": RealTimeReading.PRESSURE,
    "blood-sugar": RealTimeReading.BLOOD_SUGAR,
    "hrv": RealTimeReading.HRV,
}

CMD_START_REAL_TIME = 105
CMD_STOP_REAL_TIME = 106

CMD_REAL_TIME_HEART_RATE = 30
# UNVERIFIED (inherited from colmi_r02_client): b"3" is the byte 0x33 (ASCII '3'), not 3.
# Nothing here uses this packet; stream_real_time() uses get_continue_packet() instead.
CONTINUE_HEART_RATE_PACKET = make_packet(CMD_REAL_TIME_HEART_RATE, bytearray(b"3"))


@dataclass
class Reading:
    kind: RealTimeReading
    value: int
    timestamp: float = 0.0
    """Unix time (s) when the packet was received; 0.0 if not set."""


@dataclass
class ReadingError:
    kind: RealTimeReading
    code: int
    timestamp: float = 0.0
    """Unix time (s) when the packet was received; 0.0 if not set."""


def get_start_packet(reading_type: RealTimeReading) -> bytearray:
    return make_packet(CMD_START_REAL_TIME, bytearray([reading_type, Action.START]))


def get_continue_packet(reading_type: RealTimeReading) -> bytearray:
    return make_packet(CMD_START_REAL_TIME, bytearray([reading_type, Action.CONTINUE]))


def get_stop_packet(reading_type: RealTimeReading) -> bytearray:
    return make_packet(CMD_STOP_REAL_TIME, bytearray([reading_type, 0, 0]))


def parse_real_time_reading(packet: bytearray) -> Reading | ReadingError:
    assert packet[0] == CMD_START_REAL_TIME

    kind = RealTimeReading(packet[1])
    error_code = packet[2]
    timestamp = time.time()
    if error_code != 0:
        return ReadingError(kind=kind, code=error_code, timestamp=timestamp)

    return Reading(kind=kind, value=packet[3], timestamp=timestamp)
