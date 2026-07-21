import asyncio
from scan_colmi_ring import scan
from smart_ring_open.libraries.colmi_r02_client.client import Client

async def connect_to_ring():
    """
    Connect to a Colmi Ring via BLE, blink twice, and wait for Ctrl+C to disconnect. 
    Automatic reconnection on failure
    """
    retry_count=0
    retry_delay=5
    while retry_count < 3:
        try: 
            device_address=await scan()
            if not device_address:
                print("No device found. Retrying...")
                retry_count += 1
                await asyncio.sleep(retry_delay)
                continue

            ring_client=Client(device_address)

            print(f"Connecting to {device_address}... (Attempt: {retry_count+1})")
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
                print("Disconnected by user.") 
            except Exception as e:
                print(f"Error during disconnection: {e}")
            return
        except Exception as e:
            retry_count+=1
            print(f"Connection error: {e}. Retrying in {retry_delay} seconds...")
            await asyncio.sleep(retry_delay)
            
            if retry_count>=3:
                print("Max retries reached. Giving up.")
                return
        retry_count=0
    

if __name__=="__main__":
    try:
        asyncio.run(connect_to_ring())
    except KeyboardInterrupt:
        pass