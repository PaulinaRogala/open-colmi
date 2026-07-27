import pandas as pd
import numpy as np

def get_sensor_type_from_payload(payload_hex: str)->str|None:
    payload_hex=payload_hex.lower()

    if payload_hex.startswith('a101'):
            return 'spo2'
    if payload_hex.startswith('a102'):
            return 'ppg'
    if payload_hex.startswith('a103'):
            return 'acc'
    

def calculate_sampling_rate(csv_file_path: str, window_size: int)->float:
    """
    Calculate the average sampling rate of the PPG data from CSV file.
    Args: 
    csv_file_path: Path to CSV file with 'timestamp' and for eg. 'ppg' column.
    window_size: Number of samples used for calculation
    Return:
    Average sampling rate in Hz
    
    """
    df=pd.read_csv(csv_file_path, parse_dates=['timestamp'], comment='#')
    df=df.iloc[:window_size]

    intervals=df['timestamp'].diff().dt.total_seconds().dropna()
    #print(intervals)
    avg_interval=np.mean(intervals)
    print(f"average interval: {f"{avg_interval:.4f}"} s")

    if avg_interval>0:
        sampling_rate=1/avg_interval 
    else:
        sampling_rate=0

    print(f"sampling_rate: {f"{sampling_rate:.2f}"} Hz")
    return sampling_rate

if __name__=="__main__":
    file_path="resampled/test.ring_data_20260723_093033.csv"
    calculate_sampling_rate(file_path, 100)

   


