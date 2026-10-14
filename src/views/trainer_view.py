"""
src/views/trainer_view.py
=========================
Primary trainer view integrating instrument controls, microphone setup, timer engine,
filter panel, and dual note/chord target visualizers.
"""

import asyncio
import time
from typing import Optional, Set
import flet as ft

from views.components.header import Header
from views.components.note_display import NoteDisplay
from views.components.chord_display import ChordDisplay
from views.components.filter_panel import FilterPanel
from views.components.guitar_knob import GuitarKnob

from models.settings import TrainerSettings, DetectionMode, PracticeMode
from models.chord import TargetChord, ChordMatchStatement
from engine.note_evaluator import SingleNoteMatchStatement, EvaluatedPitchPayload
from engine.chord_generator import ChordGenerator

from utils.music_theory import MusicTheory
from utils.theme_manager import ThemeManager
from utils.timer_manager import TrainerTimer

from audio.pitch_detector import PitchDetector, list_input_devices
from audio.audio_worker import AudioWorker


class TrainerView(ft.Column):
    """Main application trainer view supporting single note and chord modes."""

    def __init__(self, theme_manager: ThemeManager):
        super().__init__()
        self.theme_manager = theme_manager
        self.expand = True
        self.num_strings = 6
        self.string_configs = []
        self._is_transitioning = False

        self.settings = TrainerSettings()

        # Audio Engine Setup
        self.detector = PitchDetector()
        self.worker = AudioWorker(
            pitch_detector=self.detector,
            settings=self.settings,
            on_pitch_update=self._on_note_pitch_update,
            on_note_matched=self._on_note_matched,
            on_chord_matched=self._on_chord_matched,
            on_chord_pitch_update=self._on_chord_pitch_update,
        )

        # Timer Setup
        self.timer = TrainerTimer(
            duration=self.settings.timer_duration_sec,
            mode=PracticeMode.SPEED_FLASHCARD,
            tick_interval=0.05,
            on_tick=self.on_timer_tick,
            on_timeout=self.on_timer_timeout,
        )

        # Visualizers
        self.note_display = NoteDisplay(
            on_next_click=self.generate_next_target,
            theme_manager=self.theme_manager
        )
        self.chord_display = ChordDisplay(
            on_next_click=self.generate_next_target,
            theme_manager=self.theme_manager
        )
        self.chord_display.visible = False

        # Sidebar Controls
        self.preset_title = ft.Text("INSTRUMENT & MIC SETUP", size=13, weight=ft.FontWeight.BOLD)
        self.preset_dropdown = ft.Dropdown(
            label="Instrument Preset",
            options=[ft.DropdownOption(key=p, text=p) for p in MusicTheory.get_presets()],
            value="Guitar (6-String Standard)",
            expand=True,
            on_select=self.on_preset_change,
        )

        self.mic_dropdown = ft.Dropdown(
            label="Microphone",
            options=[],
            expand=True,
            on_select=self.on_mic_selected,
        )

        self.string_count_knob = GuitarKnob(
            label="Strings",
            min_val=1,
            max_val=8,
            initial_val=6,
            unit="",
            theme_manager=self.theme_manager,
            on_change=self.on_string_count_knob_change,
        )

        self.timer_knob = GuitarKnob(
            label="Timer",
            min_val=1,
            max_val=10,
            initial_val=3,
            unit="s",
            theme_manager=self.theme_manager,
            on_change=self.on_timer_duration_knob_change,
        )

        self.audio_switch = ft.Switch(
            label="Microphone Audio Verification",
            value=True,
            active_color=ft.Colors.GREEN_ACCENT,
            on_change=self.on_audio_switch_toggle,
        )

        self.auto_switch = ft.Switch(
            label="Auto-Advance Mode",
            value=False,
            active_color=ft.Colors.AMBER_400,
            on_change=self.on_auto_switch_toggle,
        )

        self.filter_panel = FilterPanel(
            settings=self.settings,
            on_settings_changed=self.on_settings_changed,
            theme_manager=self.theme_manager
        )

        self.preset_panel = ft.Container(
            content=ft.Column(
                controls=[
                    self.preset_title,
                    self.preset_dropdown,
                    self.mic_dropdown,
                ],
                spacing=12,
            ),
            padding=16,
            border_radius=14,
        )

        self.knobs_panel = ft.Container(
            content=ft.Row(
                controls=[
                    self.string_count_knob,
                    self.timer_knob,
                ],
                alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                wrap=True,
                run_spacing=12,
            ),
            padding=ft.Padding.symmetric(horizontal=12, vertical=16),
            border_radius=14,
        )

        self.timer_toggle_panel = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row([ft.Icon(ft.Icons.MIC, color=ft.Colors.GREEN_ACCENT, size=20), self.audio_switch], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([ft.Icon(ft.Icons.TIMER_OUTLINED, color=ft.Colors.AMBER_400, size=20), self.auto_switch], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ],
                spacing=8,
            ),
            padding=ft.Padding.symmetric(horizontal=16, vertical=12),
            border_radius=14,
        )

        self.sidebar_container = ft.Container(
            content=ft.Column(
                controls=[
                    self.preset_panel,
                    self.knobs_panel,
                    self.timer_toggle_panel,
                    self.filter_panel,
                ],
                spacing=16,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=18,
            border_radius=18,
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.3, "#000000")),
            height=650,
        )

        self.display_container = ft.Container(
            content=ft.Column(
                controls=[
                    self.note_display,
                    self.chord_display,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            alignment=ft.Alignment.CENTER,
            padding=10,
        )

        self.controls = [
            Header(self.theme_manager),
            ft.ResponsiveRow(
                expand=True,
                controls=[
                    ft.Container(
                        content=self.sidebar_container,
                        col={"sm": 12, "md": 5, "lg": 4},
                        padding=10,
                    ),
                    ft.Container(
                        content=self.display_container,
                        col={"sm": 12, "md": 7, "lg": 8},
                        alignment=ft.Alignment.CENTER,
                        padding=10,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        ]

        self.theme_manager.add_listener(self.apply_theme)
        self.apply_theme()

    def did_mount(self):
        self.populate_microphones(update_page=False)
        self.apply_preset("Guitar (6-String Standard)", update_page=False)
        if self.audio_switch.value:
            self.detector.start()
            self.worker.start()

    def will_unmount(self):
        self.worker.stop()
        self.detector.stop()

    def populate_microphones(self, update_page: bool = True):
        """Populates microphone device dropdown."""
        mics = list_input_devices()
        options = [
            ft.DropdownOption(
                key=str(m["index"]) if m["index"] is not None else "default",
                text=m["name"],
            )
            for m in mics
        ]
        self.mic_dropdown.options = options
        if mics:
            self.mic_dropdown.value = "default"
            self.worker.set_input_device(None)
        if update_page and self.page:
            self.page.update()

    def on_mic_selected(self, e):
        val = self.mic_dropdown.value
        device_id = int(val) if val and val != "default" else None
        self.worker.set_input_device(device_id)

    def apply_theme(self):
        """Applies color scheme styles across UI containers."""
        is_dark = self.theme_manager.is_dark()

        bg_sidebar = "#1A1721" if is_dark else "#F3F0F8"
        bg_panel = "#231F2D" if is_dark else "#FFFFFF"
        bg_input = "#1E1A26" if is_dark else "#EFEBF5"
        border_col = "#3E354A" if is_dark else "#D0C8DF"
        text_primary = "#EDE7F6" if is_dark else "#1C1921"
        text_secondary = "#C4B5FD" if is_dark else "#5D4B75"

        self.preset_title.color = text_secondary

        self.preset_dropdown.bgcolor = bg_input
        self.preset_dropdown.color = text_primary

        self.mic_dropdown.bgcolor = bg_input
        self.mic_dropdown.color = text_primary

        self.preset_panel.bgcolor = bg_panel
        self.preset_panel.border = ft.Border.all(1, border_col)

        self.knobs_panel.bgcolor = bg_panel
        self.knobs_panel.border = ft.Border.all(1, border_col)

        self.timer_toggle_panel.bgcolor = bg_panel
        self.timer_toggle_panel.border = ft.Border.all(1, border_col)

        self.sidebar_container.bgcolor = bg_sidebar
        self.sidebar_container.border = ft.Border.all(1, border_col)

    def on_preset_change(self, e):
        preset_name = self.preset_dropdown.value
        if preset_name and preset_name != "Custom":
            self.apply_preset(preset_name)

    def apply_preset(self, preset_name: str, update_page: bool = True):
        self.preset_dropdown.value = preset_name
        tunings = MusicTheory.get_preset_tuning(preset_name)
        if tunings:
            self.num_strings = len(tunings)
            self.string_count_knob.set_value(self.num_strings, update_page=False)
            self.generate_next_target(update_page=False)
            if update_page and self.page:
                self.page.update()

    def on_settings_changed(self, new_settings: TrainerSettings):
        self.settings = new_settings
        self.worker.update_settings(self.settings)

        if self.settings.detection_mode == DetectionMode.NOTE_DETECTION:
            self.note_display.visible = True
            self.chord_display.visible = False
        else:
            self.note_display.visible = False
            self.chord_display.visible = True

        self.generate_next_target()
        if self.page:
            self.page.update()

    def on_string_count_knob_change(self, val: int):
        self.num_strings = val
        self.preset_dropdown.value = "Custom"
        self.generate_next_target()
        if self.page:
            self.page.update()

    def on_timer_duration_knob_change(self, val: int):
        self.timer.set_duration(val)

    def on_audio_switch_toggle(self, e):
        if self.audio_switch.value:
            self.detector.start()
            self.worker.start()
        else:
            self.worker.stop()
            self.detector.stop()

    def on_auto_switch_toggle(self, e):
        if self.auto_switch.value:
            if self.settings.detection_mode == DetectionMode.NOTE_DETECTION:
                self.note_display.update_progress(0.0, visible=True)
            else:
                self.chord_display.update_progress(0.0, visible=True)
            asyncio.create_task(self.timer.start(self.timer_knob.value))
        else:
            asyncio.create_task(self.timer.reset())
            self.note_display.update_progress(0.0, visible=False)
            self.chord_display.update_progress(0.0, visible=False)

    def on_timer_tick(self, elapsed: float, remaining: float, progress: float):
        if self.auto_switch.value:
            if self.settings.detection_mode == DetectionMode.NOTE_DETECTION:
                self.note_display.update_progress(progress, visible=True)
            else:
                self.chord_display.update_progress(progress, visible=True)

    def on_timer_timeout(self):
        self.generate_next_target()

    def generate_next_target(self, update_page: bool = True):
        self._is_transitioning = False

        if self.settings.detection_mode == DetectionMode.NOTE_DETECTION:
            active_strings = [
                {"string_num": i, "tuning": "E", "octave": 2, "active": True}
                for i in range(1, int(self.num_strings) + 1)
            ]
            string_num, base_tuning, base_octave, target_note, target_octave = MusicTheory.generate_random_note(active_strings)
            self.note_display.set_target(string_num, base_tuning, target_note)
            self.worker.set_target_note(target_note, octave=target_octave)
        else:
            target_chord = ChordGenerator.generate_target(self.settings.chord_filters)
            self.chord_display.set_target_chord(target_chord)
            self.worker.set_target_chord(target_chord)

        if self.auto_switch.value:
            asyncio.create_task(self.timer.start(self.timer_knob.value))

        if update_page and self.page:
            self.page.update()

    def _on_note_pitch_update(self, data: EvaluatedPitchPayload):
        if not self._is_transitioning and self.audio_switch.value and self.settings.detection_mode == DetectionMode.NOTE_DETECTION:
            self.note_display.update_pitch_feedback(data.raw_pitch_str, data.cents, data.is_in_tune)

    def _on_chord_pitch_update(self, detected_pcs: Set[int], volume_db: float):
        if not self._is_transitioning and self.audio_switch.value and self.settings.detection_mode == DetectionMode.CHORD_DETECTION:
            self.chord_display.render_pitch_badges(detected_pcs)

    def _on_note_matched(self, statement: SingleNoteMatchStatement):
        if self._is_transitioning or not statement.is_correct or not self.audio_switch.value:
            return

        self._is_transitioning = True

        def delayed_advance():
            time.sleep(0.5)
            self.generate_next_target()

        if self.page:
            self.page.run_thread(delayed_advance)

    def _on_chord_matched(self, statement: ChordMatchStatement):
        if self._is_transitioning or not statement.is_correct or not self.audio_switch.value:
            return

        self._is_transitioning = True
        self.chord_display.update_pitch_feedback(statement.detected_pitch_classes, is_correct=True)

        def delayed_advance():
            time.sleep(0.6)
            self.generate_next_target()

        if self.page:
            self.page.run_thread(delayed_advance)
