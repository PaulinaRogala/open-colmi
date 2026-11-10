import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "examples"))
import scan_colmi_ring  # noqa: E402

DEVICES = [SimpleNamespace(name="Phone", address="AA"), SimpleNamespace(name=None, address="BB"),
           SimpleNamespace(name="R02_1A2B", address="CC")]


async def fake_discover(timeout):
    return DEVICES


def test_scan_without_prompt(monkeypatch):
    monkeypatch.setattr(scan_colmi_ring.BleakScanner, "discover", fake_discover)
    monkeypatch.setattr("builtins.input", lambda _: (_ for _ in ()).throw(AssertionError("asked the user")))
    assert asyncio.run(scan_colmi_ring.scan(name_prefix="R02")) == "CC"
    assert asyncio.run(scan_colmi_ring.scan(address="bb")) == "BB"
    assert asyncio.run(scan_colmi_ring.scan(address="ZZ")) is None
