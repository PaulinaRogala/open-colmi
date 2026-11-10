import asyncio
import numpy as np
import traceback
import pandas as pd
from smart_ring_open.libraries.colmi_r02_client.ppg_processing import PPGProcessor, sampling_rate_from_timestamps
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
    # seconds from the first sample (independent of pandas' datetime resolution)
    timestamps = (ppg_df['timestamp'] - ppg_df['timestamp'].iloc[0]).dt.total_seconds()
    # the rate of this file, measured from its timestamps (not assumed). A file resampled to a
    # finer grid has that grid's rate but no more information than the ~1 Hz stock stream.
    processor=PPGProcessor(sampling_rate=sampling_rate_from_timestamps(timestamps))
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

    ppg_list=[]
    window_size=100

    async with Client(ring_address) as client:
        print("Starting...")
        await client.send_packet(ENABLE_RAW_SENSOR_CMD)
        print("Raw PPG sensor enabled! Waiting for data...")

        try:
            while True:
                data=await client.queues[RAW_SENSOR_CMD_TYPE].get()             
                if isinstance(data,PPGRawData):
                    ppg_list.append(data)
                    print(f"ppg_list: {len(ppg_list)}/{window_size}")

                    if len(ppg_list)>=window_size:
                        ppg_values, raw_timestamps = ppg_to_numpy(ppg_list[-window_size:])
                        print(f"Processing {len(ppg_values)} samples...")
                        timestamps=raw_timestamps-raw_timestamps[0]
                        # measured rate of this window (stock firmware: ~1 Hz, too slow for HR)
                        processor=PPGProcessor(sampling_rate=sampling_rate_from_timestamps(timestamps))
                        filtered_ppg=processor.process(ppg_values,list(timestamps))
                    
                        if filtered_ppg.peaks:
                            print(f"HR: {filtered_ppg.peaks.heart_rate:.1f} BPM")
                        else:
                            print("No peaks detected!")
                        ppg_list = ppg_list[-window_size//2:]
        except KeyboardInterrupt:
            await client.send_packet(DISABLE_RAW_SENSOR_CMD)
            print("Raw PPG sensor disabled !")
                    

    
if __name__=="__main__":
    try:
        process_from_csv("resampled/test.ring_data_20261028_165313.csv")
        #asyncio.run(process_real_time())
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc() 