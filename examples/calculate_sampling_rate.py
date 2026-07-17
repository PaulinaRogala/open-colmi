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
    timestamps=df['timestamp']//10**9 #convert from nanoseconds to seconds
    timestamps=timestamps[:window_size]
    intervals=np.diff(timestamps)
    avg_interval=np.mean(intervals)
    sampling_rate=1/avg_interval
    print(f"sampling_rate:{sampling_rate}")
    return sampling_rate
if __name__=="__main__":
    file_path="file path to your csv file"
    calculate_sampling_rate(file_path, 1000)

   


