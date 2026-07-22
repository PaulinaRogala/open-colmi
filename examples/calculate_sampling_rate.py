import pandas as pd
import numpy as np

def calculate_sampling_rate(csv_file_path: str, window_size: int)->float:
    """
    Calculate the average sampling rate of the PPG data from CSV file.
    Args: 
    csv_file_path: Path to CSV file with 'timestamp' and for eg. 'ppg' column.
    window_size: Number of samples used for calculation
    Return:
    Average sampling rate in Hz
    
    """
    df=pd.read_csv(csv_file_path, parse_dates=['timestamp'])

    timestamps=pd.to_numeric(df['timestamp'])/10**9 #convert from nanoseconds to seconds
    timestamps=timestamps[:window_size]
    print(f"timestamps: {timestamps}")
    
    intervals=np.diff(timestamps)
    print(intervals)
    avg_interval=np.mean(intervals)
    print(f"average interval: {avg_interval} s")

    if avg_interval>0:
        sampling_rate=1/avg_interval 
    else:
        sampling_rate=0

    print(f"sampling_rate: {sampling_rate} Hz")
    return sampling_rate

if __name__=="__main__":
    file_path="raw_data/ring_data_20260722_092848.csv"
    calculate_sampling_rate(file_path, 100)

   


