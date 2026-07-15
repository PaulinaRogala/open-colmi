import asyncio
from bleak import BleakScanner

async def scan():
    """Scan Colmi R02-to find MAC address"""
    print("Scanning BLE... press Ctrl+C to interrupt")
    devices = await BleakScanner.discover()
    colmi_devices=[]
    for device in devices:
        print(f"Found device: {device.address}")
        name=device.name or ""
        if "Colmi" in name or "R02" in name:
            colmi_devices.append((device.address, name))
            print(f"Colmi address: {device.address}\n")
            return device.address
    if not colmi_devices:
        return None
   
if __name__=="__main__":
    asyncio.run(scan())
