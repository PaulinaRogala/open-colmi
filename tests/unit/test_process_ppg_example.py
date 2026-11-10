import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "examples"))
import process_ppg_data  # noqa: E402


def test_resampled_file_is_refused():
    with pytest.raises(ValueError, match="resampled"):
        process_ppg_data.process_from_csv(str(ROOT / "resampled/test.ring_data_20261028_165313.csv"))


def test_stock_firmware_recording_is_refused_as_too_slow():
    # the raw file holds ~1 PPG sample per second: no heart rate can come out of it
    with pytest.raises(ValueError, match="too low"):
        process_ppg_data.process_from_csv(str(ROOT / "raw_data/ring_data_20261028_165313.csv"))
