import asyncio
import traceback
import pandas as pd
from smart_ring_open.libraries.colmi_r02_client.ppg_processing import PPGProcessor
from calculate_sampling_rate import calculate_sampling_rate


async def process_from_csv(csv_path:str):
    df=pd.read_csv(csv_path, parse_dates=['timestamp'],comment='#')
    ppg_df=df[df['ppg'].notna() & (df['ppg']!='')]

    if len(ppg_df)==0:
        print(f"No PPG data found in {csv_path}")
        return
    ppg_values=ppg_df['ppg'].astype(float).values
    timestamps = ppg_df['timestamp'].astype('int64') // 10**9  #Convert ns to s
    timestamps = timestamps - timestamps.iloc[0]  #Start from 0
    processor=PPGProcessor(sampling_rate=calculate_sampling_rate(csv_path,'ppg'))
    filtered_ppg=processor.process(ppg_values, timestamps=timestamps)

    if filtered_ppg.peaks:
        print(f"Detected {len(filtered_ppg.peaks.peaks)} peaks")
        print(f"Estimated HR: {filtered_ppg.peaks.heart_rate} BPM")

    return filtered_ppg

if __name__=="__main__":
    try:
        asyncio.run(process_from_csv("raw_data/ring_data_20260729_130215.csv"))
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc() 