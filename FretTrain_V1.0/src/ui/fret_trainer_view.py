"""
fret_trainer_view.py
====================
Interactive Note Training Control using pitch verification and animated feedback.
"""

import time
import flet as ft

from src.audio.pitch_detector import PitchDetector, list_input_devices
from src.audio.audio_worker import AudioWorker, AudioWorkerConfig, ToneMatchStatement, PitchData
from src.engine.trainer_engine import TrainerEngine, NotePrompt


class FretTrainerControl(ft.Container):
    """Reusable Flet note recognition training container."""

    def __init__(self, **kwargs):
        super().__init__(
            padding=30,
            border_radius=16,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            **kwargs
        )

        self.engine = TrainerEngine()
        self.detector = PitchDetector()
        self.worker = AudioWorker(
            pitch_detector=self.detector,
            config=AudioWorkerConfig(
                tolerance_cents=20.0,
                min_volume_db=-40.0,
                hold_duration_sec=0.30,
                lockout_duration_sec=0.60,
            ),
            on_pitch_update=self._on_pitch_update,
            on_note_matched=self._on_note_matched,
        )

        self._is_transitioning = False

        self.mic_dropdown = ft.Dropdown(
            label="Microphone",
            width=300,
            on_select=self._on_mic_selected,
        )

        self.prompt_title = ft.Text(
            value="",
            size=22,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.ON_SURFACE,
        )

        self.circle_label = ft.Text("?", size=42, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
        self.status_subtext = ft.Text("Play note...", size=14, color=ft.Colors.GREY_400)

        self.tone_circle = ft.Container(
            content=ft.Column(
                [self.circle_label, self.status_subtext],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=180,
            height=180,
            border_radius=90,
            bgcolor=ft.Colors.GREY_800,
            border=ft.Border.all(4, ft.Colors.GREY_600),
            alignment=ft.Alignment.CENTER,
            animate=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
        )

        self.progress_text = ft.Text("Completed: 0", size=14, color=ft.Colors.PRIMARY)

        self.content = ft.Column([
            ft.Row([self.mic_dropdown], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            self.prompt_title,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            self.tone_circle,
            ft.Divider(height=15, color=ft.Colors.TRANSPARENT),
            self.progress_text,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def did_mount(self):
        self._populate_microphones()
        self._load_current_prompt()
        self.detector.start()
        self.worker.start()

    def will_unmount(self):
        self.worker.stop()
        self.detector.stop()

    def _populate_microphones(self):
        devices = list_input_devices()
        options = [
            ft.DropdownOption(key=str(d["index"]), text=f"{d['name']}")
            for d in devices
        ]
        self.mic_dropdown.options = options
        if devices:
            first_id = str(devices[0]["index"])
            self.mic_dropdown.value = first_id
            self.worker.set_input_device(int(first_id))
        self.update()

    def _on_mic_selected(self, e):
        if self.mic_dropdown.value:
            self.worker.set_input_device(int(self.mic_dropdown.value))

    def _load_current_prompt(self):
        prompt = self.engine.current_prompt
        if not prompt:
            return

        self.worker.set_target_note_by_string_fret(prompt.string_num, prompt.fret_num)

        self.prompt_title.value = prompt.display_label
        self.circle_label.value = prompt.note_name
        self.circle_label.color = ft.Colors.WHITE
        self.status_subtext.value = "Listening..."
        self.status_subtext.color = ft.Colors.GREY_400

        self.tone_circle.bgcolor = ft.Colors.GREY_800
        self.tone_circle.border = ft.Border.all(4, ft.Colors.GREY_600)
        self.progress_text.value = f"Notes Mastered: {self.engine.completed_count}"

        self._is_transitioning = False
        self.update()

    def _on_pitch_update(self, data: PitchData):
        if self._is_transitioning:
            return

        if not data.is_in_tune and data.detected_note != "N/A":
            self.tone_circle.border = ft.Border.all(4, ft.Colors.AMBER)
            self.status_subtext.value = f"{data.raw_pitch_str} ({data.cents:+.0f}c)"
            self.status_subtext.color = ft.Colors.AMBER
            self.update()

    def _on_note_matched(self, statement: ToneMatchStatement):
        if self._is_transitioning or not statement.is_correct:
            return

        self._is_transitioning = True

        self.tone_circle.bgcolor = ft.Colors.GREEN_700
        self.tone_circle.border = ft.Border.all(6, ft.Colors.GREEN_ACCENT)
        self.circle_label.color = ft.Colors.WHITE
        self.status_subtext.value = "CORRECT!"
        self.status_subtext.color = ft.Colors.WHITE
        self.update()

        def delayed_advance():
            time.sleep(0.5)
            self.engine.advance()
            self._load_current_prompt()

        if self.page:
            self.page.run_thread(delayed_advance)
