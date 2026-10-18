# src/views/subviews/ear_training_view.py
from typing import Optional
import flet as ft
from utils.audio_synth import AudioSynth
from utils.theme_manager import ThemeManager
from models.ear_training import (
    EarTrainingCategory,
    EarTrainingDifficulty,
    EarTrainingQuestion,
)
from engine.ear_training_generator import EarTrainingGenerator


class EarTrainingView(ft.Column):
    """Ear Training Subview for note, interval, and chord recognition practice."""

    def __init__(self, theme_manager: Optional[ThemeManager] = None):
        super().__init__()
        self.theme_manager = theme_manager
        self.expand = True
        self.audio_synth = AudioSynth()

        self.current_question: Optional[EarTrainingQuestion] = None
        self.streak_count: int = 0
        self.total_answered: int = 0
        self.correct_answered: int = 0

        # UI Header Elements
        self.title_text = ft.Text("EAR TRAINING MODULE", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400)
        self.score_text = ft.Text("Score: 0/0 | Streak: 0 🔥", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_300)

        # Controls Header Row
        self.category_dropdown = ft.Dropdown(
            label="Category",
            options=[ft.DropdownOption(key=cat.value, text=cat.value) for cat in EarTrainingCategory],
            value=EarTrainingCategory.CHORD_QUALITY.value,
            width=240,
            dense=True,
            on_select=self._on_category_or_difficulty_changed,
        )

        self.difficulty_dropdown = ft.Dropdown(
            label="Difficulty",
            options=[ft.DropdownOption(key=d.value, text=d.value) for d in EarTrainingDifficulty],
            value=EarTrainingDifficulty.BEGINNER.value,
            width=160,
            dense=True,
            on_select=self._on_category_or_difficulty_changed,
        )

        # Question & Feedback Labels
        self.prompt_text = ft.Text("Listen and choose your answer", size=16, weight=ft.FontWeight.BOLD)
        self.feedback_text = ft.Text("", size=15, weight=ft.FontWeight.W_500)

        # Audio Replay Button
        self.play_button = ft.Button(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.VOLUME_UP_ROUNDED, size=24),
                    ft.Text("Replay Audio", size=16, weight=ft.FontWeight.BOLD)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                tight=True,
            ),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=20),
                padding=ft.Padding.symmetric(horizontal=24, vertical=16),
                color=ft.Colors.BLACK,
                bgcolor=ft.Colors.AMBER_400,
            ),
            on_click=self._replay_audio,
        )

        self.next_button = ft.Button(
            content=ft.Text("Next Question", size=15, weight=ft.FontWeight.BOLD),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=20),
                padding=ft.Padding.symmetric(horizontal=20, vertical=14),
            ),
            on_click=lambda e: self.generate_new_question(),
        )

        self.options_row = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=12,
            wrap=True,
            controls=[]
        )

        self.controls = [
            # Header Container with right=260 padding offset to avoid overlapping floating action bar
            ft.Container(
                content=ft.Row(
                    controls=[self.title_text, self.score_text],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    wrap=True,
                ),
                padding=ft.Padding.only(left=16, top=12, right=260, bottom=8),
            ),
            ft.Container(
                content=ft.Row(
                    controls=[self.category_dropdown, self.difficulty_dropdown],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=12,
                    wrap=True,
                ),
                padding=ft.Padding.symmetric(horizontal=16, vertical=8),
            ),
            ft.Container(
                content=ft.Column(
                    controls=[
                        self.prompt_text,
                        ft.Container(height=12),
                        self.play_button,
                        ft.Container(height=12),
                        self.feedback_text,
                        ft.Container(height=16),
                        self.options_row,
                        ft.Container(height=24),
                        self.next_button,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                padding=20,
                alignment=ft.Alignment.CENTER,
            )
        ]

    def did_mount(self):
        self.generate_new_question()

    def _on_category_or_difficulty_changed(self, e) -> None:
        self.generate_new_question()

    def generate_new_question(self) -> None:
        """Generates a question payload and triggers audio playback."""
        cat = EarTrainingCategory(self.category_dropdown.value)
        diff = EarTrainingDifficulty(self.difficulty_dropdown.value)

        q = EarTrainingGenerator.generate_question(cat, diff)
        self.current_question = q

        self.prompt_text.value = q.prompt_text
        self.feedback_text.value = ""

        # Construct answer option buttons
        self.options_row.controls = [
            ft.Button(
                content=ft.Text(choice, size=15, weight=ft.FontWeight.BOLD),
                style=ft.ButtonStyle(
                    padding=ft.Padding.symmetric(horizontal=20, vertical=14),
                ),
                on_click=lambda e, name=choice: self._check_answer(name),
            )
            for choice in q.options
        ]

        self._replay_audio()
        if self.page:
            self.page.update()

    def _replay_audio(self, e=None) -> None:
        """Triggers audio synth output for the active question payload."""
        q = self.current_question
        if not q:
            return

        # Safely extract pitch classes
        pcs_raw = getattr(q, "pitch_classes", None) or getattr(q, "target_pcs", None) or set()
        pcs = set(pcs_raw) if isinstance(pcs_raw, (set, list, tuple)) else set()

        if q.category == EarTrainingCategory.SINGLE_NOTE:
            pc = list(pcs)[0] if pcs else 0
            self.audio_synth.play_note_async(pc, getattr(q, "octave", 4))
        elif q.category == EarTrainingCategory.INTERVAL:
            sorted_pcs = sorted(list(pcs))
            if len(sorted_pcs) >= 2:
                pc1, pc2 = sorted_pcs[0], sorted_pcs[1]
                oct1 = getattr(q, "octave", 4)
                oct2 = getattr(q, "second_note_octave", None) or oct1
                mode_val = getattr(q.interval_mode, "value", "Harmonic (Simultaneous)") if hasattr(q, "interval_mode") else "Harmonic (Simultaneous)"
                self.audio_synth.play_interval_async(pc1, oct1, pc2, oct2, mode_val)
            elif len(sorted_pcs) == 1:
                self.audio_synth.play_note_async(sorted_pcs[0], getattr(q, "octave", 4))
        else:
            self.audio_synth.play_chord_async(pcs, getattr(q, "octave", 4))

    def _check_answer(self, selected_name: str) -> None:
        q = self.current_question
        if not q:
            return

        self.total_answered += 1

        if selected_name == q.correct_answer:
            self.correct_answered += 1
            self.streak_count += 1
            self.feedback_text.value = f"CORRECT! 🎉 {q.explanation}"
            self.feedback_text.color = ft.Colors.GREEN_400
        else:
            self.streak_count = 0
            self.feedback_text.value = f"INCORRECT. Correct Answer: {q.correct_answer}. {q.explanation}"
            self.feedback_text.color = ft.Colors.RED_400

        self.score_text.value = f"Score: {self.correct_answered}/{self.total_answered} | Streak: {self.streak_count} 🔥"

        if self.page:
            self.page.update()
