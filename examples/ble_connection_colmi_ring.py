import asyncio
from scan_colmi_ring import scan
from smart_ring_open.libraries.colmi_r02_client.client import Client

async def connect_to_ring():
    device_address=await scan()
    if not device_address:
        return 
    ring_client=Client(device_address)
    
    try:
        print(f"Connecting to {device_address}...")
        await ring_client.connect()
        print(f"Connected to {device_address}!\n Press Ctrl+C to disconnect.")
        
        await ring_client.blink_twice()
        while True:
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                raise KeyboardInterrupt
           
    
    except (KeyboardInterrupt, asyncio.CancelledError):
        try: 
            await ring_client.blink_twice()
            await ring_client.disconnect()
            print("Disconnected!") 
        except Exception as e:
            print(f"Error during disconnection: {e}")
        return
    

if __name__=="__main__":
    try:
        asyncio.run(connect_to_ring())
    except KeyboardInterrupt:
        pass