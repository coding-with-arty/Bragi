# src/views/trainer_view.py
import asyncio
import time
from typing import Optional, Set, List, Tuple
import flet as ft

from views.components.header import Header
from views.components.note_display import NoteDisplay
from views.components.chord_display import ChordDisplay
from views.components.filter_panel import FilterPanel
from views.components.fretboard_view import FretboardView
from views.components.custom_instrument_dialog import CustomInstrumentDialog

from models.settings import TrainerSettings, DetectionMode, PracticeMode
from models.chord import TargetChord, ChordMatchStatement
from models.instrument import InstrumentProfile
from models.progress import AttemptRecord
from storage.instrument_store import InstrumentStore, BUILTIN_PROFILES
from storage.progress_repository import ProgressRepository
from engine.note_evaluator import SingleNoteMatchStatement, EvaluatedPitchPayload
from engine.chord_generator import ChordGenerator

from utils.music_theory import MusicTheory
from utils.theme_manager import ThemeManager
from utils.timer_manager import TrainerTimer

from audio.audio_worker import AudioWorker
from services.audio_manager import AudioManager


class TrainerView(ft.Column):
    """Trainer view featuring flashcard display, toggleable fretboard map help, and analytics persistence."""

    def __init__(self, theme_manager: ThemeManager, repository: Optional[ProgressRepository] = None):
        super().__init__()
        self.theme_manager = theme_manager
        self.repository = repository or ProgressRepository()
        self.expand = True
        self._is_transitioning = False

        self.settings = TrainerSettings()
        self.instrument_store = InstrumentStore()
        self.active_profile: InstrumentProfile = BUILTIN_PROFILES[0]

        # Base Tuning State
        self.current_tuning: List[Tuple[str, int]] = self.active_profile.to_tuning_tuples()
        self.num_strings: int = len(self.current_tuning)

        # Practice Metrics & Timing State
        self.timer_duration_sec = 3
        self.auto_advance_enabled = False
        self.target_start_time = time.time()
        self.current_target_note = "E"
        self.current_target_octave = 2

        # Audio Engine Setup - Share singleton PitchDetector from AudioManager
        self.detector = AudioManager.get_instance().detector
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

        # Interactive Fretboard Map (Hidden by default)
        self.fretboard_view = FretboardView(
            profile=self.active_profile,
            visible_frets=15,
            on_fret_clicked=self._on_fret_clicked,
            theme_manager=self.theme_manager,
        )
        self.fretboard_view.visible = False

        # Help / Hint Toggle Button
        self.fretboard_help_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.LIGHTBULB_OUTLINED, size=18, color=ft.Colors.AMBER_400),
                    ft.Text("Show Fretboard Hint", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.AMBER_400),
                ],
                tight=True,
                spacing=6,
            ),
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.AMBER_400),
            border=ft.Border.all(1, ft.Colors.AMBER_400),
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=14, vertical=8),
            ink=True,
            on_click=self._toggle_fretboard_help,
        )

        # Sidebar Filter Panel
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

        # Scrollable Display Column for handling dynamic expansion
        self.display_column = ft.Column(
            controls=[
                self.note_display,
                self.chord_display,
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[self.fretboard_help_btn],
                ),
                self.fretboard_view,
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
        )

        self.display_container = ft.Container(
            content=self.display_column,
            alignment=ft.Alignment.TOP_CENTER,
            padding=10,
            expand=True,
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
                        alignment=ft.Alignment.TOP_CENTER,
                        padding=10,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.START,
            )
        ]

        self.theme_manager.add_listener(self.apply_theme)
        self.apply_theme()

    def did_mount(self):
        self._is_mounted = True
        self.apply_instrument_profile(self.active_profile)
        AudioManager.get_instance().subscribe(self._on_audio_manager_update)
        self._sync_audio_device()
        AudioManager.get_instance().start_listening()
        self.worker.start()
        asyncio.create_task(self._live_trainer_ui_loop())

    def will_unmount(self):
        self._is_mounted = False
        AudioManager.get_instance().unsubscribe(self._on_audio_manager_update)
        self.worker.stop()

    async def _live_trainer_ui_loop(self):
        """Main-thread UI loop pushing pitch feedback to Trainer controls (~25 FPS)."""
        while self._is_mounted:
            if self.page:
                try:
                    self.update()
                except Exception:
                    pass
            await asyncio.sleep(0.04)

    def _sync_audio_device(self):
        dev_id = AudioManager.get_instance().current_device_id
        target_id = int(dev_id) if (dev_id is not None and str(dev_id) != "default") else None
        self.worker.set_input_device(target_id)

    def _on_audio_manager_update(self, data: dict):
        if data.get("event") == "device_changed":
            self._sync_audio_device()

    def _toggle_fretboard_help(self, e=None):
        """Toggles visibility of the interactive fretboard hint map."""
        self.fretboard_view.visible = not self.fretboard_view.visible

        if self.fretboard_view.visible:
            self.fretboard_help_btn.content.controls[0].icon = ft.Icons.LIGHTBULB_ROUNDED
            self.fretboard_help_btn.content.controls[0].color = ft.Colors.BLACK
            self.fretboard_help_btn.content.controls[1].value = "Hide Fretboard Hint"
            self.fretboard_help_btn.content.controls[1].color = ft.Colors.BLACK
            self.fretboard_help_btn.bgcolor = ft.Colors.AMBER_400
        else:
            self.fretboard_help_btn.content.controls[0].icon = ft.Icons.LIGHTBULB_OUTLINED
            self.fretboard_help_btn.content.controls[0].color = ft.Colors.AMBER_400
            self.fretboard_help_btn.content.controls[1].value = "Show Fretboard Hint"
            self.fretboard_help_btn.content.controls[1].color = ft.Colors.AMBER_400
            self.fretboard_help_btn.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.AMBER_400)

        self.update()
        if self.page:
            self.page.update()

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
        self.active_profile = profile
        self.num_strings = profile.string_count
        self.current_tuning = profile.to_tuning_tuples()
        self.fretboard_view.set_instrument_profile(profile)

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
        self._log_attempt_to_repository(is_success=False)
        self.generate_next_target()

    def generate_next_target(self, update_page: bool = True):
        self._is_transitioning = False
        self.target_start_time = time.time()

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
            self.current_target_note = target_note
            self.current_target_octave = target_octave

            self.note_display.set_target(string_num, base_tuning, target_note)
            self.worker.set_target_note(target_note, octave=target_octave)

            locs = self.fretboard_view.univ_instrument.get_note_coordinates(target_note, target_octave)
            self.fretboard_view.highlight_locations(locs, color=ft.Colors.AMBER_400, label=target_note)
        else:
            target_chord = ChordGenerator.generate_target(self.settings.chord_filters)
            self.chord_display.set_target_chord(target_chord)
            self.worker.set_target_chord(target_chord)
            self.fretboard_view.clear_markers()

        if self.auto_advance_enabled:
            asyncio.create_task(self.timer.start(self.timer_duration_sec))

        if update_page and self.page:
            self.page.update()

    def _on_fret_clicked(self, string_num: int, fret: int, note_name: str, octave: int) -> None:
        """Handles manual user touch interactions on the fretboard map."""
        if self.settings.detection_mode == DetectionMode.NOTE_DETECTION:
            is_match = (note_name.upper() == self.current_target_note.upper())
            self._log_attempt_to_repository(is_success=is_match)
            if is_match:
                self.note_display.update_pitch_feedback(f"{note_name}{octave}", 0.0, True)
                def delayed_advance():
                    time.sleep(0.5)
                    self.generate_next_target()
                if self.page:
                    self.page.run_thread(delayed_advance)

    def _log_attempt_to_repository(self, is_success: bool) -> None:
        """Persists exercise attempt data into SQLite for analytics & XP progression."""
        response_time = max(0.1, time.time() - self.target_start_time)
        record = AttemptRecord(
            target_name=self.current_target_note,
            target_type="note" if self.settings.detection_mode == DetectionMode.NOTE_DETECTION else "chord",
            is_success=is_success,
            response_time_sec=round(response_time, 2),
            cents_error=0.0,
            timestamp=time.time(),
        )
        self.repository.log_attempt(record)

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
        self._log_attempt_to_repository(is_success=True)

        def delayed_advance():
            time.sleep(0.5)
            self.generate_next_target()

        if self.page:
            self.page.run_thread(delayed_advance)

    def _on_chord_matched(self, statement: ChordMatchStatement):
        if self._is_transitioning or not statement.is_correct:
            return

        self._is_transitioning = True
        self._log_attempt_to_repository(is_success=True)
        self.chord_display.update_pitch_feedback(statement.detected_pitch_classes, is_correct=True)

        def delayed_advance():
            time.sleep(0.6)
            self.generate_next_target()

        if self.page:
            self.page.run_thread(delayed_advance)
