import asyncio
from bleak import BleakScanner

async def scan():
    """Scan Colmi R02-to find MAC address"""
    print("Scanning BLE... press Ctrl+C to interrupt")
    devices = await BleakScanner.discover()
    colmi_devices=[]
    for device in devices:
        print(f"Found: {device.address}")
        name=device.name or ""
        if "Colmi" in name or "R02" in name:
            colmi_devices.append((device.address, name))
            print(f"Found Colmi: {device.name} - {device.address}")
            return device.address
    if not colmi_devices:
        return None
   
if __name__=="__main__":
    asyncio.run(scan())
