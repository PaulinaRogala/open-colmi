import asyncio
from bleak import BleakScanner

async def scan():
    """Scan for Colmi R02 and return its MAC address."""
    print("Scanning for BLE devices... ")
    devices = await BleakScanner.discover(timeout=10)
    if not devices:
        print("No devices found!")
        return None
    device= await select_device(devices)
    if device:
        print(f"Selected {device}!")
        return device.address
    return None

async def select_device(devices):
    """
    Scan for available Bluetooth devices and allow the user to select one.
    Args: devices- available devices to connect by BLE 
    Return: selected device or None.
    """
    for i, device in enumerate(devices):
        print(f"{i+1}: {device.name} [{device.address}]")
    try:
        choice = int(input("Select a device by entering its number: "))
        if choice>len(devices) or choice<1:
            print("Invalid choice. Select an available device.")
            return None
        return devices[choice-1]
    except ValueError:
        print("Error: enter a valid number!")
        return None
        
   
if __name__=="__main__":
    asyncio.run(scan())
