import asyncio
from smart_ring_open.libraries.colmi_r02_edgeimpulse.ring import main as ring_main

async def run_saving_data_function():
    await ring_main(duration=10, label="test", columns=["ppg"], resample_ms=20, plot=True, ei_upload=False)
if __name__=="__main__":
    asyncio.run(run_saving_data_function())