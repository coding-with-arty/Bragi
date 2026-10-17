import numpy as np


class SignalQualityAnalyzer:
    """
    Analyzes raw PCM audio buffers for decibel levels, signal clipping,
    and dynamic room noise floors.
    """

    def __init__(self, silence_threshold_db: float = -50.0, clipping_threshold: float = 0.98):
        self.silence_threshold_db = silence_threshold_db
        self.clipping_threshold = clipping_threshold
        self.noise_floor_db = -60.0

    @staticmethod
    def calculate_rms_db(signal: np.ndarray) -> float:
        """Calculates Root Mean Square (RMS) volume level converted to dBFS."""
        if signal is None or len(signal) == 0:
            return -100.0

        rms = np.sqrt(np.mean(np.square(signal), dtype=np.float64))
        if rms <= 1e-9:
            return -100.0

        db = 20.0 * np.log10(rms)
        return float(np.clip(db, -100.0, 0.0))

    def check_clipping(self, signal: np.ndarray) -> bool:
        """Determines if any sample in the buffer exceeds the clipping threshold."""
        if signal is None or len(signal) == 0:
            return False
        return bool(np.max(np.abs(signal)) >= self.clipping_threshold)

    def is_signal_silent(self, rms_db: float) -> bool:
        """Checks whether the current RMS level falls below the silence threshold."""
        return rms_db < self.silence_threshold_db

    def update_noise_floor(self, rms_db: float, alpha: float = 0.05) -> None:
        """Updates exponential moving average of room background noise during silent frames."""
        if rms_db < self.silence_threshold_db:
            self.noise_floor_db = (1.0 - alpha) * self.noise_floor_db + alpha * rms_db
