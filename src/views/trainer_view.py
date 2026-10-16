# src/views/trainer_view.py
import asyncio
import time
from typing import Optional, Set, List, Tuple
import flet as ft

from views.components.header import Header
from views.components.note_display import NoteDisplay
from views.components.chord_display import ChordDisplay
from views.components.filter_panel import FilterPanel
from views.components.custom_instrument_dialog import CustomInstrumentDialog

from models.settings import TrainerSettings, DetectionMode, PracticeMode
from models.chord import TargetChord, ChordMatchStatement
from models.instrument import InstrumentProfile
from storage.instrument_store import InstrumentStore, BUILTIN_PROFILES
from engine.note_evaluator import SingleNoteMatchStatement, EvaluatedPitchPayload
from engine.chord_generator import ChordGenerator

from utils.music_theory import MusicTheory
from utils.theme_manager import ThemeManager
from utils.timer_manager import TrainerTimer

from audio.pitch_detector import PitchDetector
from audio.audio_worker import AudioWorker
from services.audio_manager import AudioManager


class TrainerView(ft.Column):
    """Trainer view focusing strictly on practice visualizer and chord/note filter controls."""

    def __init__(self, theme_manager: ThemeManager):
        super().__init__()
        self.theme_manager = theme_manager
        self.expand = True
        self._is_transitioning = False

        self.settings = TrainerSettings()
        self.instrument_store = InstrumentStore()
        self.active_profile: InstrumentProfile = BUILTIN_PROFILES[0]

        # Base Tuning State
        self.current_tuning: List[Tuple[str, int]] = self.active_profile.to_tuning_tuples()
        self.num_strings: int = len(self.current_tuning)

        # Timing State
        self.timer_duration_sec = 3
        self.auto_advance_enabled = False

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
            duration=self.timer_duration_sec,
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

        # Sidebar Filter Panel (Dedicated practice filters)
        self.filter_panel = FilterPanel(
            settings=self.settings,
            on_settings_changed=self.on_settings_changed,
            theme_manager=self.theme_manager
        )

        self.sidebar_container = ft.Container(
            content=ft.Column(
                controls=[
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
        self.apply_instrument_profile(self.active_profile)
        AudioManager.get_instance().subscribe(self._on_audio_manager_update)
        self._sync_audio_device()
        self.detector.start()
        self.worker.start()

    def will_unmount(self):
        AudioManager.get_instance().unsubscribe(self._on_audio_manager_update)
        self.worker.stop()
        self.detector.stop()

    def _sync_audio_device(self):
        dev_id = AudioManager.get_instance().current_device_id
        target_id = int(dev_id) if (dev_id is not None and str(dev_id) != "default") else None
        self.worker.set_input_device(target_id)

    def _on_audio_manager_update(self, data: dict):
        if data.get("event") == "device_changed":
            self._sync_audio_device()

    # Handlers for Practice Timing Modal
    def set_timer_duration(self, duration_sec: int) -> None:
        self.timer_duration_sec = duration_sec
        self.timer.set_duration(duration_sec)

    def set_auto_advance(self, enabled: bool) -> None:
        self.auto_advance_enabled = enabled
        if self.auto_advance_enabled:
            if self.settings.detection_mode == DetectionMode.NOTE_DETECTION:
                self.note_display.update_progress(0.0, visible=True)
            else:
                self.chord_display.update_progress(0.0, visible=True)
            asyncio.create_task(self.timer.start(self.timer_duration_sec))
        else:
            asyncio.create_task(self.timer.reset())
            self.note_display.update_progress(0.0, visible=False)
            self.chord_display.update_progress(0.0, visible=False)

    def open_custom_builder(self, e=None):
        """Opens custom instrument builder dialog."""
        dialog = CustomInstrumentDialog(
            instrument_store=self.instrument_store,
            on_instrument_saved=self.on_custom_instrument_saved,
            existing_profile=self.active_profile if self.active_profile.is_custom else None,
            theme_manager=self.theme_manager
        )
        if self.page:
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()

    def on_custom_instrument_saved(self, profile: InstrumentProfile):
        self.apply_instrument_profile(profile)

    def apply_instrument_profile(self, profile: InstrumentProfile):
        """Applies InstrumentProfile model to trainer state."""
        self.active_profile = profile
        self.num_strings = profile.string_count
        self.current_tuning = profile.to_tuning_tuples()

        self.generate_next_target()
        if self.page:
            self.page.update()

    def apply_theme(self):
        is_dark = self.theme_manager.is_dark()

        bg_sidebar = "#1A1721" if is_dark else "#F3F0F8"
        border_col = "#3E354A" if is_dark else "#D0C8DF"

        self.sidebar_container.bgcolor = bg_sidebar
        self.sidebar_container.border = ft.Border.all(1, border_col)

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

    def on_timer_tick(self, elapsed: float, remaining: float, progress: float):
        if self.auto_advance_enabled:
            if self.settings.detection_mode == DetectionMode.NOTE_DETECTION:
                self.note_display.update_progress(progress, visible=True)
            else:
                self.chord_display.update_progress(progress, visible=True)

    def on_timer_timeout(self):
        self.generate_next_target()

    def generate_next_target(self, update_page: bool = True):
        self._is_transitioning = False

        if self.settings.detection_mode == DetectionMode.NOTE_DETECTION:
            active_strings = []
            for i in range(self.num_strings):
                if i < len(self.current_tuning):
                    note, oct = self.current_tuning[i]
                else:
                    note, oct = ("E", 2)

                active_strings.append({
                    "string_num": i + 1,
                    "tuning": note,
                    "octave": oct,
                    "active": True
                })

            string_num, base_tuning, base_octave, target_note, target_octave = MusicTheory.generate_random_note(active_strings)
            self.note_display.set_target(string_num, base_tuning, target_note)
            self.worker.set_target_note(target_note, octave=target_octave)
        else:
            target_chord = ChordGenerator.generate_target(self.settings.chord_filters)
            self.chord_display.set_target_chord(target_chord)
            self.worker.set_target_chord(target_chord)

        if self.auto_advance_enabled:
            asyncio.create_task(self.timer.start(self.timer_duration_sec))

        if update_page and self.page:
            self.page.update()

    def _on_note_pitch_update(self, data: EvaluatedPitchPayload):
        if not self._is_transitioning and self.settings.detection_mode == DetectionMode.NOTE_DETECTION:
            self.note_display.update_pitch_feedback(data.raw_pitch_str, data.cents, data.is_in_tune)

    def _on_chord_pitch_update(self, detected_pcs: Set[int], volume_db: float):
        if not self._is_transitioning and self.settings.detection_mode == DetectionMode.CHORD_DETECTION:
            self.chord_display.render_pitch_badges(detected_pcs)

    def _on_note_matched(self, statement: SingleNoteMatchStatement):
        if self._is_transitioning or not statement.is_correct:
            return

        self._is_transitioning = True

        def delayed_advance():
            time.sleep(0.5)
            self.generate_next_target()

        if self.page:
            self.page.run_thread(delayed_advance)

    def _on_chord_matched(self, statement: ChordMatchStatement):
        if self._is_transitioning or not statement.is_correct:
            return

        self._is_transitioning = True
        self.chord_display.update_pitch_feedback(statement.detected_pitch_classes, is_correct=True)

        def delayed_advance():
            time.sleep(0.6)
            self.generate_next_target()

        if self.page:
            self.page.run_thread(delayed_advance)
