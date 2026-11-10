import asyncio
from bleak import BleakScanner

async def scan(address: str | None = None, name_prefix: str | None = None):
    """
    Scan for Colmi R02 and return its MAC address (on macOS: a CoreBluetooth UUID).
    Args:
        address: use this ring without asking (e.g. in scripts); returned if it is advertising
        name_prefix: use the first ring whose name starts with this (e.g. "R02") without asking
    Without either, the user picks a device from the list.
    """
    print("Scanning for BLE devices... ")
    devices = await BleakScanner.discover(timeout=10)
    if not devices:
        print("No devices found!")
        return None
    if address is not None or name_prefix is not None:
        for device in devices:
            if (address is not None and device.address.lower() == address.lower()) or (
                    name_prefix is not None and (device.name or "").startswith(name_prefix)):
                print(f"Found {device}!")
                return device.address
        print(f"Ring not found (address={address}, name_prefix={name_prefix})")
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
