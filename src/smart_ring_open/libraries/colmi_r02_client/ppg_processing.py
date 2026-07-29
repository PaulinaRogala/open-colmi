import numpy as np
import pandas as pd
from scipy import signal
from dataclasses import dataclass

@dataclass
class PPGPeaks:
    peaks: list[float] #peak values
    peak_times: list[float] #timestamps of peaks
    heart_rate: float #BPM
    peak_indices: list[int] #indices in the signal

class PPGProcessor:
    def __init__(self, sampling_rate: float):
        self.sampling_rate = sampling_rate

    def bandpass_filter(self, ppg_signal: np.ndarray, lowcut: float=0.75, highcut: float=8.0, order=3)->np.ndarray:
        """
        Apply bandpass filter to remove motion artifacts and high-frequency noise.
        Args:
            ppg_signal: Raw PPG signal
            lowcut: Low cutoff frequency[Hz]-removes slow baseline drift
            highcut: High cutoff frequency[Hz]-removes high-frequency noise
            order: Filter order

        Returns:
            Filtered PPG signal
        """
        nyquist=0.5*self.sampling_rate
        low=lowcut/nyquist
        high=highcut/nyquist

        b,a=signal.butter(order,[low, high], btype='band' )
        filtered=signal.filtfilt(b,a,ppg_signal)

        return filtered

    def detect_peaks(self, filtered_signal: np.ndarray, height: float|None, distance: float|None):
        if distance is None:
            #based on max HR ~220 BPM = ~3.67 Hz
            min_distance=int(self.sampling_rate/3.67)
            distance=max(min_distance,1)

        if height is None:
            #height as 50% of signal range
            height=(np.max(filtered_signal)-np.min(filtered_signal))*0.5

        peaks, properties=signal.find_peaks(filtered_signal, height=height,distance=distance,prominence=height*0.3 )
        peak_values=filtered_signal[peaks]
        peak_times=peaks/self.sampling_rate

        if len(peaks)>=2:
            intervals=np.diff(peaks)/self.sampling_rate
            hr=60/np.median(intervals) #60 seconds / median interval
        else: 
            hr=0

        return PPGPeaks(
            peaks=list(peak_values),
            peak_times=list(peak_times),
            heart_rate=float(hr),
            peak_indices=list(peaks))

