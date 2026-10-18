# tests/test_metronome_controller.py
import time
from controllers.metronome_controller import MetronomeController


def test_metronome_controller_pulse_and_accent():
    beats_recorded = []

    def handle_beat(beat_num: int, is_accent: bool):
        beats_recorded.append((beat_num, is_accent))

    controller = MetronomeController(
        bpm=240,  # Fast BPM for short test runtime
        time_signature_beats=4,
        on_beat=handle_beat,
    )

    assert controller.is_running is False
    controller.start()
    assert controller.is_running is True

    time.sleep(0.35)
    controller.stop()

    assert controller.is_running is False
    assert len(beats_recorded) > 0

    # First beat must be Beat 1 and flagged as accent
    assert beats_recorded[0] == (1, True)
    if len(beats_recorded) > 1:
        assert beats_recorded[1] == (2, False)
