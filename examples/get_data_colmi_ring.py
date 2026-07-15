import asyncio
from smart_ring_open.libraries.colmi_r02_client.client import Client
from smart_ring_open.libraries.colmi_r02_client import steps, real_time
from datetime import datetime
from scan_colmi_ring import scan

async def get_data():
    """Get data from Colmi R02 by MAC address"""
    ring_address=await scan()
    if ring_address is None:
        print("No Colmi device found")
    else:
        print("Loading data from Colmi...")
        async with Client(ring_address) as client:
            print("Connected!")
            await client.blink_twice()
            battery=await client.get_battery()
            print(f"Battery level: {battery.battery_level}%")
            steps_data=await client.get_steps(datetime.now())
            if isinstance(steps_data, steps.NoData):
                print("No steps data found")
            else: 
                print(f"Steps data: {steps_data}")
            real_time_reading_hr=await client.get_realtime_reading(real_time.RealTimeReading.HEART_RATE)
            if real_time_reading_hr:
                i=1
                for hr in real_time_reading_hr:
                    print(f"Real time reading HR{i}: {hr} bpm")
                    i+=1
            real_time_reading_pressure=await client.get_realtime_reading(real_time.RealTimeReading.BLOOD_PRESSURE)
            if real_time_reading_pressure:
                i=1
                for p in real_time_reading_pressure:
                    print(f"Real time reading pressure {i}: {p}")
                    i+=1
            print("Disconnected!")
        
if __name__=="__main__":
    try:
        asyncio.run(get_data())
    except Exception as e:
        print(f"Error: {e}")

