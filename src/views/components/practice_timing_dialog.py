"""
src/views/components/practice_timing_dialog.py
================================================
Modal dialog for configuring practice timer duration and auto-advance modes,
launched via the stopwatch header action button.
"""

from typing import Callable, Optional
import flet as ft
from views.components.guitar_knob import GuitarKnob
from utils.theme_manager import ThemeManager

ElevatedBtn = getattr(ft, "ElevatedButton", None) or getattr(ft, "FilledButton", None) or getattr(ft, "Button", ft.TextButton)
TextBtn = getattr(ft, "TextButton", None) or getattr(ft, "Button", ft.Container)


class PracticeTimingDialog(ft.AlertDialog):
    """Modal dialog for controlling practice timer speed and auto-advance settings."""

    def __init__(
        self,
        current_duration_sec: int,
        auto_advance_enabled: bool,
        on_duration_changed: Callable[[int], None],
        on_auto_advance_toggled: Callable[[bool], None],
        theme_manager: Optional[ThemeManager] = None,
    ):
        self.theme_manager = theme_manager
        self.on_duration_changed = on_duration_changed
        self.on_auto_advance_toggled = on_auto_advance_toggled

        self.timer_knob = GuitarKnob(
            label="Timer Speed",
            min_val=1,
            max_val=10,
            initial_val=current_duration_sec,
            unit="s",
            theme_manager=self.theme_manager,
            on_change=self._handle_duration_change,
        )

        self.auto_switch = ft.Switch(
            label="Auto-Advance Mode",
            value=auto_advance_enabled,
            active_color=ft.Colors.AMBER_400,
            on_change=self._handle_auto_switch_toggle,
        )

        title = ft.Row(
            controls=[
                ft.Icon(ft.Icons.TIMER_ROUNDED, color=ft.Colors.AMBER_400, size=24),
                ft.Text("Practice Speed & Timing", size=18, weight=ft.FontWeight.BOLD),
            ],
            spacing=10,
        )

        content = ft.Container(
            width=380,
            content=ft.Column(
                tight=True,
                spacing=16,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        "Set target duration per flashcard and toggle auto-advance:",
                        size=12,
                        color=ft.Colors.GREY_400,
                    ),
                    ft.Divider(height=1, color=ft.Colors.GREY_800),
                    ft.Container(
                        content=ft.Row(
                            controls=[self.timer_knob],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        padding=ft.Padding.symmetric(vertical=8),
                    ),
                    ft.Container(
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.AUTORENEW_ROUNDED, color=ft.Colors.AMBER_400, size=20),
                                        ft.Text("Auto-Advance", weight=ft.FontWeight.BOLD, size=13),
                                    ],
                                    spacing=8,
                                ),
                                self.auto_switch,
                            ],
                        ),
                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                        border_radius=8,
                        padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                    ),
                ],
            ),
        )

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
            title=title,
            content=content,
            actions=[close_btn],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _handle_duration_change(self, val: int) -> None:
        self.on_duration_changed(val)

    def _handle_auto_switch_toggle(self, e) -> None:
        self.on_auto_advance_toggled(self.auto_switch.value)

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
