from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Set
from models.audio_frame import AudioFrame
from utils.music_theory import CHROMATIC_SHARPS, MusicTheory


class ScaleType(Enum):
    MAJOR = "Major"
    NATURAL_MINOR = "Natural Minor"
    MAJOR_PENTATONIC = "Major Pentatonic"
    MINOR_PENTATONIC = "Minor Pentatonic"


# Interval semitone formulas relative to the root note
SCALE_FORMULAS = {
    ScaleType.MAJOR: [0, 2, 4, 5, 7, 9, 11],
    ScaleType.NATURAL_MINOR: [0, 2, 3, 5, 7, 8, 10],
    ScaleType.MAJOR_PENTATONIC: [0, 2, 4, 7, 9],
    ScaleType.MINOR_PENTATONIC: [0, 3, 5, 7, 10],
}


@dataclass(frozen=True)
class ScaleStep:
    """Represents a single note step within an active scale practice sequence."""
    step_index: int
    note_name: str
    pitch_class: int
    octave: int
    is_completed: bool = False


@dataclass
class ScaleSequenceState:
    """Active state of a scale exercise run."""
    root_note: str
    scale_type: ScaleType
    steps: List[ScaleStep]
    current_step_index: int = 0
    is_completed: bool = False


class ScaleEngine:
    """
    Generates scale step sequences and evaluates live audio pitch frames
    against the active target scale step.
    """

    @staticmethod
    def generate_scale_sequence(
        root_note: str,
        scale_type: ScaleType,
        start_octave: int = 3,
        num_octaves: int = 1
    ) -> ScaleSequenceState:
        """Constructs an ascending and descending scale step sequence."""
        root_pc = MusicTheory.note_to_pitch_class(root_note)
        semitones = SCALE_FORMULAS[scale_type]

        steps: List[ScaleStep] = []
        step_idx = 0

        # Build ascending scale notes
        for oct_offset in range(num_octaves):
            for semi in semitones:
                abs_pc = (root_pc + semi) % 12
                octave_shift = (root_pc + semi) // 12
                note_name = CHROMATIC_SHARPS[abs_pc]
                octave = start_octave + oct_offset + octave_shift

                steps.append(
                    ScaleStep(
                        step_index=step_idx,
                        note_name=note_name,
                        pitch_class=abs_pc,
                        octave=octave,
                    )
                )
                step_idx += 1

        # Add top root note octave anchor
        top_root_pc = root_pc
        top_octave = start_octave + num_octaves
        steps.append(
            ScaleStep(
                step_index=step_idx,
                note_name=CHROMATIC_SHARPS[top_root_pc],
                pitch_class=top_root_pc,
                octave=top_octave,
            )
        )

        return ScaleSequenceState(
            root_note=root_note,
            scale_type=scale_type,
            steps=steps,
            current_step_index=0,
            is_completed=False,
        )

    @staticmethod
    def evaluate_frame(
        state: ScaleSequenceState,
        frame: AudioFrame,
        require_octave_match: bool = False
    ) -> bool:
        """
        Evaluates current audio frame against active scale step index.
        Advances to the next step index if the note is correctly matched.
        """
        if state.is_completed or frame.is_silent or frame.pitch_class == "--":
            return False

        target_step = state.steps[state.current_step_index]
        detected_pc = MusicTheory.note_to_pitch_class(frame.pitch_class)

        pc_match = (target_step.pitch_class == detected_pc)
        oct_match = (target_step.octave == frame.octave) if require_octave_match else True

        if pc_match and oct_match:
            # Mark current step completed and advance cursor
            updated_step = ScaleStep(
                step_index=target_step.step_index,
                note_name=target_step.note_name,
                pitch_class=target_step.pitch_class,
                octave=target_step.octave,
                is_completed=True,
            )
            state.steps[state.current_step_index] = updated_step
            state.current_step_index += 1

            if state.current_step_index >= len(state.steps):
                state.is_completed = True

            return True

        return False
