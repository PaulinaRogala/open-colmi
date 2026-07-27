import pandas as pd
import numpy as np
from typing import Literal

def calculate_stability_metrics(intervals: pd.Series):
     """
     The sampling rate stability analysis now includes:
    - np.std ; measures how much the time intervals between consecutive samples differ from the average interval. 
    - cv_percent ; describes the relative variability of sampling intervals compared to the average interval. 
    - np.min, np.max ; show the shortest and longest time intervals between consecutive samples. 
    - np.median ; represents the middle value of all sampling intervals. 
    - iqr ; measures the spread of the middle 50% of sampling intervals.
    Args:
        intervals: Pandas Series containing time intervals between consecutive samples in seconds
    Returns:
        Prints calculated sampling rates stability metrics
     """
     avg_interval=np.mean(intervals)
     sampling_rate=1/avg_interval if avg_interval>0 else 0
     std_interval=np.std(intervals)
     cv_percent=(std_interval/avg_interval)*100 if avg_interval>0 else 0
     min_interval=np.min(intervals)
     max_interval=np.max(intervals)
     median_interval=np.median(intervals)
     q1, q3= np.percentile(intervals,[25,75])
     iqr=q3-q1
     return print (f'sampling_rate:  {sampling_rate:.2f} Hz,\navg_interval: {avg_interval:.4f} s,\nmedian_interval: {median_interval:.4f} s,\nstd_interval: {std_interval:.4f} s,\ncv_percent: {cv_percent:.2f} %,\nmin_interval: {min_interval:.4f} s,\nmax_interval: {max_interval:.4f} s,\niqr_interval: {iqr:.4f} s')

def get_sensor_type_from_payload(payload_hex: str)->str|None:
    """
    Determine the sensor type based on the payload header.
    The sensor type is identified from the first two bytes of the hex payload:
    - a101 -> spo2
    - a102 -> ppg
    - a103 -> acc
    Args:
        payload_hex: Hexadecimal payload string (e.g. "a103de72fde6fb460000000000000018").
    Returns:
        Sensor type ('spo2', 'ppg', 'acc') if recognized, otherwise None.
    """
    payload_hex=payload_hex.lower()

    if payload_hex.startswith('a101'):
            return 'spo2'
    if payload_hex.startswith('a102'):
            return 'ppg'
    if payload_hex.startswith('a103'):
            return 'acc'
    return None
    

def calculate_sampling_rate(csv_file_path: str, sensor_type: Literal['ppg','acc','spo2','all'] ,window_size: int, details: bool|None=True)->float|dict[str,float]:
    """
    Calculate the average sampling rate of the choosen sensor data from CSV file.
    Args: 
    csv_file_path: Path to CSV file with 'timestamp' and for eg. 'ppg' column.
    sensor_type: type of sensor; 'acc'-accelerometer, 'ppg'-PPG, 'spo2'-SpO2, 'all'-all sensors
    window_size: Number of samples used for calculation
    details: if True or None displays sampling stability metrics
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
            if details is True:
                 print(f"metrics for {sensor}")
                 calculate_stability_metrics(intervals)
                 print("####")
            if avg_interval>0:
                sampling_rate=1/avg_interval 
                results[sensor]=sampling_rate
            else:
                sampling_rate=0
        return results
                    

    else:
        if sensor_type not in known_sensors:
             raise ValueError(f"Unknown sensor type: {sensor_type}. Available: {known_sensors}")
        sensor_df = df[df['sensor_type']==sensor_type]
        
        intervals=sensor_df['timestamp'].diff().dt.total_seconds().dropna()
        avg_interval=np.mean(intervals)
        if details is True:
            print(f"metrics for {sensor_type}")
            calculate_stability_metrics(intervals)
            print("####")

        if avg_interval>0:
            sampling_rate=1/avg_interval 
        else:
            sampling_rate=0
        return sampling_rate
         

if __name__=="__main__":
    file_path="raw_data/ring_data_20260727_094818.csv"
    calculate_sampling_rate(file_path,"all",100)

   


