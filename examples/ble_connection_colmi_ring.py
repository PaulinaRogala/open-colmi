from bleak import BleakClient
import asyncio
from scan_colmi_ring import scan

async def connect():
    device_address=await scan()
    if not device_address:
        return 
    client=BleakClient(device_address, timeout=10)
    await client.connect()
    print(f"Connected to {device_address}!")
    try:
         while True:
              await asyncio.sleep(1)
    except KeyboardInterrupt:
         await client.disconnect()
    

if __name__=="__main__":
    asyncio.run(connect())