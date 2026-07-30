import asyncio
import traceback
import pandas as pd
from smart_ring_open.libraries.colmi_r02_client.ppg_processing import PPGProcessor
from smart_ring_open.libraries.colmi_r02_client.client import Client
from smart_ring_open.libraries.colmi_r02_client.raw_sensor_decoder import RAW_SENSOR_CMD_TYPE, decode_raw_sensor_packet,ENABLE_RAW_SENSOR_CMD, DISABLE_RAW_SENSOR_CMD, ppg_to_numpy,PPGRawData
from calculate_sampling_rate import calculate_sampling_rate
from scan_colmi_ring import scan

def process_from_csv(csv_path:str):
    df=pd.read_csv(csv_path, parse_dates=['timestamp'],comment='#')
    ppg_df=df[df['ppg'].notna() & (df['ppg']!='')]

    if len(ppg_df)==0:
        print(f"No PPG data found in {csv_path}")
        return
    ppg_values=ppg_df['ppg'].astype(float).values
    timestamps = ppg_df['timestamp'].astype('int64') // 10**9  #Convert ns to s
    timestamps = timestamps - timestamps.iloc[0]  #Start from 0
    #processor=PPGProcessor(sampling_rate=calculate_sampling_rate(csv_path,'ppg'))
    processor=PPGProcessor(sampling_rate=25)
    filtered_ppg=processor.process(ppg_values, timestamps=timestamps)

    if filtered_ppg.peaks:
        print(f"Detected {len(filtered_ppg.peaks.peaks)} peaks")
        print(f"Estimated HR: {filtered_ppg.peaks.heart_rate} BPM")
        processor.visualize(filtered_ppg,"graphs/ppg_processed.png")
    return filtered_ppg

async def process_real_time():
    ring_address= await scan()
    if not ring_address:
        return

    processor=PPGProcessor(sampling_rate=25)
    ppg_list=[]

    async with Client(ring_address) as client:
        print("Starting...")
        await client.send_packet(ENABLE_RAW_SENSOR_CMD)
        print("Raw PPG sensor enabled! Waiting for data...")

        try:
            while True:
                data=await client.queues[RAW_SENSOR_CMD_TYPE].get()                
                if isinstance(data,PPGRawData):
                    ppg_list.append(data)
                    ppg_values, raw_timestamps = ppg_to_numpy(ppg_list)
                    timestamps=raw_timestamps-raw_timestamps[0]
                    filtered_ppg=processor.process(ppg_values,list(timestamps))
                    if filtered_ppg.peaks:
                        print(f"HR: {filtered_ppg.peaks.heart_rate:.1f} BPM")
        except KeyboardInterrupt:
            await client.send_packet(DISABLE_RAW_SENSOR_CMD)
            print("Raw PPG sensor disabled !")
                    

    
if __name__=="__main__":
    try:
        #process_from_csv("raw_data/ring_data_20260729_130215.csv")
        asyncio.run(process_real_time())
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc() 