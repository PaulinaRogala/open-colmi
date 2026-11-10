import numpy as np
import pytest

from src.smart_ring_open.libraries.colmi_r02_client.ppg_processing import PPGProcessor, sampling_rate_from_timestamps


def test_sampling_rate_is_measured_from_timestamps():
    t = np.arange(100) * 0.04 + np.random.default_rng(0).normal(0, 0.002, 100)  # 25 Hz with jitter
    assert sampling_rate_from_timestamps(t) == pytest.approx(25, rel=0.05)


def test_heart_rate_from_a_25_hz_signal():
    fs, bpm = 25.0, 72.0
    t = np.arange(0, 30, 1 / fs)
    ppg = 1000 + 50 * np.sin(2 * np.pi * bpm / 60 * t)
    result = PPGProcessor(sampling_rate=sampling_rate_from_timestamps(t)).process(ppg)
    assert result.peaks.heart_rate == pytest.approx(bpm, abs=2)


def test_too_slow_stream_is_refused_not_misread():
    # stock firmware: ~1 sample/s. Before the check, an assumed rate gave a confident wrong HR.
    t = np.arange(0, 120, 1.0)
    ppg = 1000 + 50 * np.sin(2 * np.pi * 1.2 * t)
    with pytest.raises(ValueError, match="too low"):
        PPGProcessor(sampling_rate=sampling_rate_from_timestamps(t)).process(ppg)


def test_heart_rate_from_a_pulse_with_a_dicrotic_notch():
    # systolic peak + smaller diastolic wave: must count one beat per pulse, not two
    fs, bpm = 25.0, 90.0
    t = np.arange(0, 30, 1 / fs)
    phase = (t * bpm / 60) % 1.0
    ppg = 1000 + 60 * np.exp(-0.5 * ((phase - 0.25) / 0.07) ** 2) + 27 * np.exp(-0.5 * ((phase - 0.55) / 0.10) ** 2)
    result = PPGProcessor(sampling_rate=fs).process(ppg)
    assert result.peaks.heart_rate == pytest.approx(bpm, abs=2)
