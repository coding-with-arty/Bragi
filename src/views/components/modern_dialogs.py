"""
src/views/components/modern_dialogs.py
======================================
Icon-driven modal dialogs for Instrument Profiles and Tuning Presets.
"""

from typing import Optional, Callable, List, Tuple
import flet as ft
from models.instrument import InstrumentProfile
from storage.instrument_store import InstrumentStore


class BaseModernDialog(ft.AlertDialog):
    """Base modal container matching the app's dark translucent dialog theme."""

    def __init__(self, title_text: str, icon_data: str, content_control: ft.Control):
        close_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CHECK_ROUNDED, size=16, color=ft.Colors.BLACK),
                    ft.Text("Done", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.BLACK),
                ],
                tight=True,
                spacing=4,
            ),
            bgcolor=ft.Colors.AMBER_400,
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=14, vertical=8),
            ink=True,
            on_click=self._close_dialog,
        )

        super().__init__(
            title=ft.Row(
                controls=[
                    ft.Icon(icon_data, color=ft.Colors.AMBER_400, size=22),
                    ft.Text(title_text, size=18, weight=ft.FontWeight.BOLD),
                ],
                spacing=10,
            ),
            content=ft.Container(width=460, content=content_control),
            actions=[close_btn],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _close_dialog(self, e=None) -> None:
        if self.page and hasattr(self.page, "close"):
            try:
                self.page.close(self)
                return
            except Exception:
                pass
        self.open = False
        if self.page:
            self.page.update()


class InstrumentSelectorDialog(BaseModernDialog):
    """Modal for single-click selection between built-in and custom instrument profiles."""

    def __init__(
        self,
        instrument_store: InstrumentStore,
        active_profile: InstrumentProfile,
        on_profile_selected: Callable[[InstrumentProfile], None],
        on_open_builder: Callable[[], None],
    ):
        self.store = instrument_store
        self.active_profile = active_profile
        self.on_profile_selected = on_profile_selected
        self.on_open_builder = on_open_builder

        profiles = self.store.get_all_profiles()
        profile_cards = []

        for p in profiles:
            is_active = p.name == self.active_profile.name
            card = ft.Container(
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(
                                    ft.Icons.RADIO_BUTTON_CHECKED_ROUNDED
                                    if is_active
                                    else ft.Icons.RADIO_BUTTON_UNCHECKED_ROUNDED,
                                    color=ft.Colors.AMBER_400 if is_active else ft.Colors.GREY_500,
                                    size=20,
                                ),
                                ft.Column(
                                    spacing=2,
                                    controls=[
                                        ft.Text(p.name, weight=ft.FontWeight.BOLD, size=13),
                                        ft.Text(f"{p.string_count} Strings • {p.category}", size=11, color=ft.Colors.GREY_400),
                                    ],
                                ),
                            ],
                            spacing=10,
                        ),
                        ft.Container(
                            content=ft.Text("CUSTOM" if p.is_custom else "PRESET", size=9, color=ft.Colors.BLACK, weight=ft.FontWeight.BOLD),
                            bgcolor=ft.Colors.AMBER_400 if p.is_custom else ft.Colors.GREY_700,
                            border_radius=4,
                            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                        ),
                    ],
                ),
                bgcolor=ft.Colors.with_opacity(0.18, ft.Colors.AMBER_400) if is_active else ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
                border=ft.Border.all(1, ft.Colors.AMBER_400 if is_active else ft.Colors.with_opacity(0.15, "#3E354A")),
                border_radius=8,
                padding=10,
                ink=True,
                data=p,
                on_click=self._handle_select,
            )
            profile_cards.append(card)

        add_builder_btn = ft.Container(
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINED, color=ft.Colors.AMBER_400, size=18),
                    ft.Text("Build Custom Instrument...", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.AMBER_400),
                ],
                spacing=8,
            ),
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.AMBER_400),
            border=ft.Border.all(1, ft.Colors.AMBER_400),
            border_radius=8,
            padding=10,
            ink=True,
            on_click=self._handle_open_builder,
        )

        column = ft.Column(
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            height=300,
            controls=[
                add_builder_btn,
                ft.Divider(height=1, color=ft.Colors.GREY_800),
                *profile_cards,
            ],
        )

        super().__init__(
            title_text="Instrument Setup",
            icon_data=ft.Icons.MUSIC_VIDEO_ROUNDED,
            content_control=column,
        )

    def _handle_select(self, e) -> None:
        profile = e.control.data
        self.on_profile_selected(profile)
        self._close_dialog()

    def _handle_open_builder(self, e) -> None:
        self._close_dialog()
        self.on_open_builder()


class TuningPresetDialog(BaseModernDialog):
    """Modal for switching tuning presets."""

    def __init__(self, on_selected: Callable[[str], None]):
        self.on_selected = on_selected
        tunings = ["Standard (E A D G B E)", "Drop D (D A D G B E)", "DADGAD", "Open G", "Half-Step Down"]

        controls = []
        for t in tunings:
            card = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.TUNE_ROUNDED, color=ft.Colors.AMBER_400, size=18),
                        ft.Text(t, weight=ft.FontWeight.BOLD, size=13),
                    ],
                    spacing=10,
                ),
                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                border_radius=8,
                padding=12,
                ink=True,
                data=t,
                on_click=self._handle_select,
            )
            controls.append(card)

        super().__init__(
            title_text="Tuning Preset",
            icon_data=ft.Icons.TUNE_ROUNDED,
            content_control=ft.Column(controls=controls, spacing=8, tight=True),
        )

    def _handle_select(self, e) -> None:
        self.on_selected(e.control.data)
        self._close_dialog()
