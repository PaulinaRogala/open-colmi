import pandas as pd
import numpy as np
from typing import Literal

def get_sensor_type_from_payload(payload_hex: str)->str|None:
    payload_hex=payload_hex.lower()

    if payload_hex.startswith('a101'):
            return 'spo2'
    if payload_hex.startswith('a102'):
            return 'ppg'
    if payload_hex.startswith('a103'):
            return 'acc'
    return None
    

def calculate_sampling_rate(csv_file_path: str, sensor_type: Literal['ppg','acc','spo2','all'] ,window_size: int)->float|dict[str,float]:
    """
    Calculate the average sampling rate of the choosen sensor data from CSV file.
    Args: 
    csv_file_path: Path to CSV file with 'timestamp' and for eg. 'ppg' column.
    sensor_type: type of sensor; 'acc'-accelerometer, 'ppg'-PPG, 'spo2'-SpO2, 'all'-all sensors
    window_size: Number of samples used for calculation
    Return:
    Average sampling rate in Hz for choosen sensor
    
    """
    df=pd.read_csv(csv_file_path, parse_dates=['timestamp'], comment='#')
    df=df.iloc[:window_size]
    df['sensor_type']=df['payload'].apply(get_sensor_type_from_payload)

    known_sensors=['ppg','acc','spo2']
    if sensor_type=='all':
        results={}
        for sensor in known_sensors:
            sensor_df = df[df['sensor_type']==sensor]
            intervals=sensor_df['timestamp'].diff().dt.total_seconds().dropna()
            avg_interval=np.mean(intervals)
            print(f"average interval for {sensor}: {f"{avg_interval:.4f}"} s")
    
            if avg_interval>0:
                sampling_rate=1/avg_interval 
                results[sensor]=sampling_rate
            else:
                sampling_rate=0

            print(f"Sampling rate for {sensor}: {f"{sampling_rate:.2f}"} Hz")
        return results
                    

    else:
        if sensor_type not in known_sensors:
             raise ValueError(f"Unknown sensor type: {sensor_type}. Available: {known_sensors}")
        sensor_df = df[df['sensor_type']==sensor_type]
        
        intervals=sensor_df['timestamp'].diff().dt.total_seconds().dropna()
        avg_interval=np.mean(intervals)
        print(f"average interval for {sensor_type}: {f"{avg_interval:.4f}"} s")

        if avg_interval>0:
            sampling_rate=1/avg_interval 
        else:
            sampling_rate=0

        print(f"Sampling rate: {f"{sampling_rate:.2f}"} Hz")
        return sampling_rate
         

if __name__=="__main__":
    file_path="raw_data/ring_data_20260727_094818.csv"
    calculate_sampling_rate(file_path,"all",100)

   


