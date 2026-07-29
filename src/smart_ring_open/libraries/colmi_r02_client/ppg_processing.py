import numpy as np
import pandas as pd
from scipy import signal

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

