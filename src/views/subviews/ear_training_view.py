"""
src/views/subviews/ear_training_view.py
========================================
Ear training subview for chord and interval pitch recognition.
"""

from typing import Optional, Set
import flet as ft
from utils.audio_synth import AudioSynth
from utils.theme_manager import ThemeManager
from engine.chord_generator import ChordGenerator
from models.settings import ChordFilterSettings, ChordQuality


class EarTrainingView(ft.Column):
    """Ear training view for audio pitch and chord recognition practice."""

    def __init__(self, theme_manager: Optional[ThemeManager] = None):
        super().__init__()
        self.theme_manager = theme_manager
        self.expand = True
        self.audio_synth = AudioSynth()

        self.current_pitch_classes: Set[int] = set()
        self.current_chord_name: str = ""

        # UI Components
        self.title_text = ft.Text("EAR TRAINING PRACTICE", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400)
        self.feedback_text = ft.Text("Listen to the chord and select your answer", size=16, color=ft.Colors.GREY_400)

        self.play_button = ft.Button(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.VOLUME_UP_ROUNDED, size=24),
                    ft.Text("Play Audio Chord", size=16, weight=ft.FontWeight.BOLD)
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
            on_click=self._play_current_chord,
        )

        self.next_button = ft.Button(
            content=ft.Text("Next Question", size=16, weight=ft.FontWeight.BOLD),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=20),
                padding=ft.Padding.symmetric(horizontal=24, vertical=16),
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
            ft.Container(content=self.title_text, padding=16),
            ft.Container(
                content=ft.Column(
                    controls=[
                        self.play_button,
                        ft.Container(height=16),
                        self.feedback_text,
                        ft.Container(height=16),
                        self.options_row,
                        ft.Container(height=24),
                        self.next_button,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                padding=24,
                alignment=ft.Alignment.CENTER,
            )
        ]

    def did_mount(self):
        self.generate_new_question()

    def generate_new_question(self) -> None:
        """Generates a new chord question and updates option choices."""
        filters = ChordFilterSettings(qualities={ChordQuality.MAJOR, ChordQuality.MINOR})
        target = ChordGenerator.generate_target(filters)

        self.current_pitch_classes = target.chord_definition.pitch_classes
        self.current_chord_name = target.chord_definition.name
        self.feedback_text.value = "Listen and select the chord name"
        self.feedback_text.color = ft.Colors.GREY_400

        # Extract root note directly from chord name (e.g., "C Major" -> "C")
        root_note = self.current_chord_name.split()[0] if self.current_chord_name else "C"

        # Create multiple choice distractors
        qualities = ["Major", "Minor", "7th", "Maj7"]
        choices = {self.current_chord_name}

        for q in qualities:
            candidate = f"{root_note} {q}"
            choices.add(candidate)
            if len(choices) >= 4:
                break

        choice_list = sorted(list(choices))

        self.options_row.controls = [
            ft.Button(
                content=ft.Text(choice, size=16, weight=ft.FontWeight.BOLD),
                style=ft.ButtonStyle(
                    padding=ft.Padding.symmetric(horizontal=20, vertical=14),
                ),
                on_click=lambda e, name=choice: self._check_answer(name),
            )
            for choice in choice_list
        ]

        self.audio_synth.play_chord_async(self.current_pitch_classes)
        if self.page:
            self.page.update()

    def _play_current_chord(self, e) -> None:
        if self.current_pitch_classes:
            self.audio_synth.play_chord_async(self.current_pitch_classes)

    def _check_answer(self, selected_name: str) -> None:
        if selected_name == self.current_chord_name:
            self.feedback_text.value = f"CORRECT! It's {self.current_chord_name}"
            self.feedback_text.color = ft.Colors.GREEN_400
        else:
            self.feedback_text.value = f"INCORRECT. Expected: {self.current_chord_name}"
            self.feedback_text.color = ft.Colors.RED_400

        if self.page:
            self.page.update()
