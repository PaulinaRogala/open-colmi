"""The Edge Impulse recorder's notification handler, without a ring."""
import asyncio
import csv
import io

from src.smart_ring_open.libraries.colmi_r02_edgeimpulse import ring as recorder

PPG = bytes.fromhex("a102066320281f5100d700000000009b")


def test_import_creates_no_folders(tmp_path, monkeypatch):
    import importlib
    monkeypatch.chdir(tmp_path)
    importlib.reload(recorder)
    assert list(tmp_path.iterdir()) == []


def test_corrupted_packets_are_skipped_and_rows_written_as_they_arrive(monkeypatch):
    out = io.StringIO()
    monkeypatch.setattr(recorder, "all_rows", [])
    monkeypatch.setattr(recorder, "packet_counter", 0)
    monkeypatch.setattr(recorder, "skipped_packets", 0)
    monkeypatch.setattr(recorder, "partial_writer", csv.writer(out))
    corrupted = bytearray(PPG)
    corrupted[3] ^= 0x01
    battery_reply = bytes.fromhex("03640000000000000000000000000067")
    for p in (PPG, bytes(corrupted), battery_reply):
        asyncio.run(recorder.handle_notification(0, bytearray(p)))
    assert recorder.packet_counter == 1 and recorder.skipped_packets == 1
    [row] = list(csv.reader(io.StringIO(out.getvalue())))
    assert row[1] == PPG.hex() and row[5] == str(0x0663)
