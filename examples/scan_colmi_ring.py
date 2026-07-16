import asyncio
from bleak import BleakScanner
from smart_ring_open.libraries.colmi_r02_edgeimpulse.ring import select_device

async def scan():
    """Scan Colmi R02-to find MAC address"""
    print("Scanning BLE... press Ctrl+C to interrupt")
    device=await select_device()
    if select_device:
        print(f"Connected to {device}!")
        return device.address
    else:
        print("Choose a device to connect!")
        return None
   
if __name__=="__main__":
    asyncio.run(scan())
