"""Stream the ring's real-time heart rate with arrival times, zeros and errors included."""
import asyncio
import sys
from datetime import datetime

from scan_colmi_ring import scan
from smart_ring_open.libraries.colmi_r02_client import real_time
from smart_ring_open.libraries.colmi_r02_client.client import Client


async def stream_hr(duration_s: float) -> None:
    ring_address = await scan()
    if ring_address is None:
        return
    async with Client(ring_address) as client:
        async for r in client.stream_real_time(real_time.RealTimeReading.HEART_RATE, duration_s):
            t = datetime.fromtimestamp(r.timestamp).strftime("%H:%M:%S.%f")[:-3]
            if isinstance(r, real_time.ReadingError):
                print(f"{t}  error {r.code}")
            else:
                print(f"{t}  {r.value} bpm" if r.value else f"{t}  0 (no lock yet)")
        print(f"invalid packets: {client.invalid_packets}, error replies: {client.error_packets}")


if __name__ == "__main__":
    asyncio.run(stream_hr(float(sys.argv[1]) if len(sys.argv) > 1 else 60))
