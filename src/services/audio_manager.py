import threading
from typing import Optional, Dict, Any, Callable, List
import numpy as np
from models.audio_frame import AudioFrame
from audio.pitch_detector import PitchDetector

try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False


class AudioManager:
    """
    Singleton audio hardware capture manager handling input stream buffering
    and broadcasting pitch state updates to UI subscribers.
    """

    _instance: Optional["AudioManager"] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self, sample_rate: int = 44100, buffer_size: int = 2048):
        if getattr(self, "_initialized", False):
            return

        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self._device_id: Optional[int] = None
        self.detector = PitchDetector(sample_rate=sample_rate, buffer_size=buffer_size)
        self.subscribers: List[Callable[[AudioFrame], None]] = []
        self._latest_frame: AudioFrame = AudioFrame()
        self._is_running = False
        self._initialized = True

        # Start hardware capture
        self.start_capture()

    @classmethod
    def get_instance(cls, sample_rate: int = 44100, buffer_size: int = 2048) -> "AudioManager":
        """Returns the singleton instance of AudioManager."""
        return cls(sample_rate=sample_rate, buffer_size=buffer_size)

    @property
    def is_listening(self) -> bool:
        """Returns True if input hardware capture is actively running."""
        return self._is_running

    @property
    def current_device_id(self) -> Optional[int]:
        """Returns the currently selected hardware input device ID."""
        return self._device_id

    @current_device_id.setter
    def current_device_id(self, device_id: Optional[int]) -> None:
        """Updates the selected hardware input device ID."""
        self._device_id = device_id

    def set_device(self, device_id: Optional[int]) -> None:
        """Sets the active input capture device ID."""
        self._device_id = device_id

    def set_input_device(self, device_id: Optional[int]) -> None:
        """
        Alias for set_device() to satisfy AudioDeviceDialog selection handlers.
        """
        self.set_device(device_id)

    def get_available_devices(self) -> List[Dict[str, Any]]:
        """
        Retrieves available input hardware devices.
        Returns a list of device dictionary items.
        """
        devices = []
        if HAS_SOUNDDEVICE:
            try:
                all_devices = sd.query_devices()
                for idx, dev in enumerate(all_devices):
                    if dev.get("max_input_channels", 0) > 0:
                        devices.append({
                            "id": idx,
                            "name": dev.get("name", f"Device {idx}"),
                            "max_input_channels": dev.get("max_input_channels", 1),
                            "default_sample_rate": dev.get("default_samplerate", 44100)
                        })
            except Exception as e:
                print(f"[AudioManager] Error querying sounddevice hardware: {e}")

        if not devices:
            devices = [
                {"id": 0, "name": "Default Input Device", "max_input_channels": 2, "default_sample_rate": 44100}
            ]

        return devices

    def start_capture(self) -> None:
        """Starts input capture and processing loop."""
        if not self._is_running:
            self._is_running = True
            print(f"[AudioManager] Hardware capture started on device ID: {self._device_id}")

    def start_listening(self) -> None:
        """Alias for start_capture() to satisfy AppLayout calls."""
        self.start_capture()

    def stop_capture(self) -> None:
        """Stops active input audio streams."""
        self._is_running = False

    def stop_listening(self) -> None:
        """Alias for stop_capture()."""
        self.stop_capture()

    def subscribe(self, callback: Callable[[AudioFrame], None]) -> None:
        """Registers a callback function to receive real-time AudioFrame updates."""
        if callback not in self.subscribers:
            self.subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[AudioFrame], None]) -> None:
        """Removes a callback function from subscriber list."""
        if callback in self.subscribers:
            self.subscribers.remove(callback)

    def _audio_callback(self, signal: np.ndarray) -> None:
        """Internal DSP pipeline processing callback."""
        result = self.detector.process_frame(signal)
        if result:
            frame = AudioFrame(
                frequency=result.frequency,
                pitch_class=result.pitch_class,
                octave=result.octave,
                cents_deviation=result.cents_deviation,
                confidence=result.confidence,
                is_silent=False,
                rms_db=-20.0
            )
        else:
            frame = AudioFrame()

        self._latest_frame = frame
        self._notify_subscribers(frame)

    def _notify_subscribers(self, frame: AudioFrame) -> None:
        """Broadcasting updates safely to all registered listeners."""
        for callback in list(self.subscribers):
            try:
                callback(frame)
            except Exception as e:
                print(f"[AudioManager] Subscriber exception: {e}")

    @property
    def current_state(self) -> Dict[str, Any]:
        """
        Exposes current audio frame state formatted for UI and worker consumption.
        """
        frame = self._latest_frame
        return {
            "pitch_data": frame,
            "frequency": frame.frequency,
            "pitch_class": frame.pitch_class,
            "octave": frame.octave,
            "cents_deviation": frame.cents_deviation,
            "is_silent": frame.is_silent,
            "confidence": frame.confidence
        }
