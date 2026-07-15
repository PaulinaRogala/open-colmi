import asyncio
from smart_ring_open.libraries.colmi_r02_client.client import Client
from smart_ring_open.libraries.colmi_r02_client import steps
from datetime import datetime

async def get_data():
    """Get data from Colmi R02 by MAC address"""
    ring_address="30:36:42:33:86:02"
    print("Loading data...")
    async with Client(ring_address) as client:
        print("Connected!")
        await client.blink_twice()
        battery=await client.get_battery()
        print(f"Battery level: {battery.battery_level}%")
        steps_data=await client.get_steps(datetime.now())
        if isinstance(steps_data, steps.NoData):
            print("No steps data found")
        else: 
            print(f"Steps: {steps}")
        print("Disconnected!")
        
if __name__=="__main__":
    try:
        asyncio.run(get_data())
    except Exception as e:
        print(f"Error: {e}")

