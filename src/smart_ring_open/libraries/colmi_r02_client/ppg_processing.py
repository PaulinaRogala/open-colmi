import numpy as np
import pandas as pd
from scipy import signal
from dataclasses import dataclass
import matplotlib.pyplot as plt
from typing import Optional

@dataclass
class PPGPeaks:
    peaks: list[float] #peak values
    peak_times: list[float] #timestamps of peaks
    heart_rate: float #BPM
    peak_indices: list[int] #indices in the signal

@dataclass
class FilteredPPG:
    """Filtered PPG signal with processing metadata"""
    raw_signal: np.ndarray
    filtered_signal: np.ndarray
    sampling_rate:float
    peaks: PPGPeaks|None
    timestamp:list|None

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
        if len(ppg_signal)<50:
            return ppg_signal
        
        nyquist=0.5*self.sampling_rate
        low=lowcut/nyquist
        high=highcut/nyquist

        b,a=signal.butter(order,[low, high], btype='band' )
        filtered=signal.filtfilt(b,a,ppg_signal)

        return filtered

    def detect_peaks(self, filtered_signal: np.ndarray, height: Optional[float]=None, distance: Optional[float]=None)->PPGPeaks:
        """
        Detect PPG peaks using scipy's find_peaks
        Args:
            filtered_signal: Filtered PPG signal
            height: Minimum peak height (None=auto)
            distance: Minimum distance between peaks in samples (None=auto)
        Returns:
            PPGPeaks with detected peak information
        
        """
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
    
    def process(self, ppg_signal: np.ndarray, timestamps: Optional[list]=None)->FilteredPPG:
        """
        Complete PPG processing pipeline.
        Args:
            ppg_signal: Raw PPG signal
            timestamps: Optional list of timestamps for each sample
        Returns:
            FilteredPPG with all processing results
        """
        filtered=self.bandpass_filter(ppg_signal)
        peaks=self.detect_peaks(filtered)
        return FilteredPPG(
            raw_signal=ppg_signal, 
            filtered_signal=filtered,
            sampling_rate=self.sampling_rate,
            peaks=peaks, 
            timestamp=timestamps)
    
    def visualize(self, filtered_ppg: FilteredPPG, save_path: Optional[str]=None):
        """
        Visualize PPG processing results
        Args:
            filtered_ppg: FilteredPPG object from process()
            save_path: Optional file path to save the figure
        """
        plt.figure()
        time_axis=np.arange(len(filtered_ppg.raw_signal))/self.sampling_rate
        plt.plot(time_axis, filtered_ppg.raw_signal, alpha=0.3, label="Raw PPG signal")
        plt.plot(time_axis, filtered_ppg.filtered_signal, label="Filtered PPG signal")

        if filtered_ppg.peaks:
            peak_values=np.array(filtered_ppg.peaks.peaks)
            peak_times=np.array(filtered_ppg.peaks.peak_times)
            plt.scatter(peak_times,peak_values,color='red',label='Peaks')

            hr_text=f'HR: {filtered_ppg.peaks.heart_rate:.1f} BPM'
            plt.annotate(hr_text,xy=(0,1000))

        plt.xlabel("Time[s]")
        plt.ylabel("Amplitude")
        plt.title("PPG Signal Processing")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path)
            print(f"Figure is saved: {save_path}")
        plt.show()

        def calculate_snr(self, raw_signal: np.ndarray, filtered_signal: np.ndarray)->float:
            """
            Calculate SNR in dB
            Args:
                raw_signal: Raw PPG signal
                filtered_signal: Filtered PPG signal
            Returns:
                Signal to noise ratio as float

            """
            noise = raw_signal - filtered_signal
            signal_power= np.mean(filtered_signal**2)
            noise_power=np.mean(noise**2)
            if noise_power==0 or signal_power==0:
                return 0
            return 10*np.log10(signal_power/noise_power)

    

