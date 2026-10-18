# src/views/main_view.py
"""
Main Application Shell
======================
Primary application layout connecting navigation, subviews (ScaleView,
ChordView, MetronomeWidget), and global educational guidance modals.
"""

from typing import Optional
import flet as ft

from views.subviews.scale_view import ScaleView
from views.subviews.chord_view import ChordView
from views.components.metronome_widget import MetronomeWidget
from storage.instrument_store import InstrumentStore
from models.instrument import InstrumentProfile
from utils.theme_manager import ThemeManager


class MainView(ft.Row):
    """Main application shell container with navigation rail and subview views."""

    def __init__(
        self,
        instrument_profile: Optional[InstrumentProfile] = None,
        theme_manager: Optional[ThemeManager] = None,
    ):
        super().__init__()
        self.expand = True
        self.spacing = 0
        self.theme_manager = theme_manager

        # Instrument Profile Resolution
        store = InstrumentStore()
        if hasattr(store, "get_default_profile"):
            default_prof = store.get_default_profile()
        elif hasattr(store, "get_all_profiles"):
            profiles = store.get_all_profiles()
            default_prof = profiles[0] if profiles else InstrumentProfile()
        else:
            default_prof = InstrumentProfile()

        self.profile = instrument_profile or default_prof

        # Instantiate Subviews
        self.scale_view = ScaleView(instrument_profile=self.profile, theme_manager=self.theme_manager)
        self.chord_view = ChordView(instrument_profile=self.profile, theme_manager=self.theme_manager)
        self.metronome_view = MetronomeWidget(theme_manager=self.theme_manager)

        self.subviews = [
            self.scale_view,
            self.chord_view,
            self.metronome_view,
        ]

        # Content Display Area
        self.content_area = ft.Container(
            content=self.subviews[0],
            expand=True,
            padding=20,
        )

        # Navigation Rail
        self.nav_rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,
            group_alignment=-0.9,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icons.MUSIC_NOTE_ROUNDED,
                    selected_icon=ft.Icons.MUSIC_NOTE,
                    label="Scales",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.GRID_VIEW_ROUNDED,
                    selected_icon=ft.Icons.GRID_VIEW,
                    label="Chords",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.SPEED_ROUNDED,
                    selected_icon=ft.Icons.SPEED,
                    label="Metronome",
                ),
            ],
            on_change=self._on_navigation_change,
        )

        # Educational Guidance Modal Trigger
        self.help_button = ft.IconButton(
            icon=ft.Icons.HELP_OUTLINE_ROUNDED,
            icon_color=ft.Colors.AMBER_400,
            tooltip="Why Learn Bragi?",
            on_click=self._show_pedagogy_modal,
        )

        # Main Layout Structure
        self.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        self.nav_rail,
                        ft.Container(expand=True),
                        ft.Container(content=self.help_button, alignment=ft.Alignment.CENTER, padding=10),
                    ],
                ),
                border=ft.Border(right=ft.BorderSide(1, ft.Colors.with_opacity(0.2, "#3E354A"))),
            ),
            self.content_area,
        ]

    def _safe_update(self) -> None:
        """Safely triggers page update if attached to an active Page."""
        try:
            if self.page:
                self.page.update()
        except RuntimeError:
            pass

    def _on_navigation_change(self, e) -> None:
        """Switches displayed subview based on selected navigation index."""
        selected_idx = e.control.selected_index
        if 0 <= selected_idx < len(self.subviews):
            self.content_area.content = self.subviews[selected_idx]
            self._safe_update()

    def _show_pedagogy_modal(self, e=None) -> None:
        """Displays the 'Why Learn Bragi?' pedagogical guidance dialog."""
        dialog = ft.AlertDialog(
            title=ft.Text("Why Learn with Bragi?", weight=ft.FontWeight.BOLD),
            content=ft.Column(
                tight=True,
                spacing=12,
                controls=[
                    ft.Text(
                        "Bragi combines real-time pitch detection with visual fretboard mapping to help you build true spatial mastery of the neck.",
                        size=14,
                    ),
                    ft.Text(
                        "• Octave-Agnostic Single Notes: Train your muscle memory to locate notes anywhere on the neck.",
                        size=13,
                    ),
                    ft.Text(
                        "• Polyphonic Chord Trainer: Instant acoustic verification of complex chord voicings.",
                        size=13,
                    ),
                    ft.Text(
                        "• Rhythm Engine: Practice with tight timing using the built-in metronome subsystem.",
                        size=13,
                    ),
                ],
            ),
            actions=[
                ft.Button(
                    "Got it!",
                    on_click=lambda evt: self._close_dialog(dialog),
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        try:
            if self.page:
                self.page.open(dialog)
        except (RuntimeError, AttributeError):
            pass

    def _close_dialog(self, dialog: ft.AlertDialog) -> None:
        """Closes the open dialog."""
        try:
            if self.page:
                self.page.close(dialog)
        except (RuntimeError, AttributeError):
            pass
