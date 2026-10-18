# tests/test_session_controller.py
from controllers.session_controller import SessionController
from engine.note_evaluator import EvaluatedPitchPayload

def test_session_controller_match():
    controller = SessionController()
    controller.start_session(initial_target="C")

    # Create a matching payload for C4 (Pitch class C, in-tune)
    payload = EvaluatedPitchPayload(
        frequency_hz=261.63,
        pitch_class=0,
        octave=4,
        cents_deviation=0.0,
        confidence=0.95,
        is_in_tune=True,
    )

    # First payload starts the hold timer
    matched_1 = controller.process_audio_payload(payload)
    assert matched_1 is False

    # Simulate waiting 0.6 seconds
    import time
    time.sleep(0.55)

    # Second payload satisfies hold time requirement
    matched_2 = controller.process_audio_payload(payload)
    assert matched_2 is True
    assert controller.stats.successful_matches == 1
    assert controller.stats.total_xp_gained > 0
