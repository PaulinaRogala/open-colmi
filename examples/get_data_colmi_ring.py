import asyncio
from smart_ring_open.libraries.colmi_r02_client import Client

async def get_data():
    """Get data from Colmi R02 by MAC address"""
    ring_address="30:36:42:33:86:02"
    async with Client(ring_address) as client:
        print("Connected! Loading battery level...")
        battery=await client.get_battery()
        print(f"Battery level: {battery}")
if __name__=="__main__":
    try:
        asyncio.run(get_data())
    except Exception as e:
        print(f"Error: {e}")

#problem; blad o braku modulu smart_ring_open 
# i prawdopodobnie dlatego ze nie ma w pyproject build-system,
#ale usunelam bo byl problem z `uv sync`(nie dalo sie zrobic uv sync)
# bo byl (błąd: `AttributeError: Using uv.build_editable is not allowed`)