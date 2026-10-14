"""
src/views/components/guitar_knob.py
====================================
Custom circular knob/slider control component for instrument strings and timer settings.
"""

from typing import Optional, Callable
import flet as ft
from utils.theme_manager import ThemeManager


class GuitarKnob(ft.Container):
    """Custom rotary knob / numeric control widget for strings and timer values."""

    def __init__(
        self,
        label: str,
        min_val: int = 1,
        max_val: int = 12,
        initial_val: int = 6,
        unit: str = "",
        theme_manager: Optional[ThemeManager] = None,
        on_change: Optional[Callable[[int], None]] = None,
    ):
        super().__init__()
        self.label_text = label
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.unit = unit
        self.theme_manager = theme_manager
        self.on_change = on_change

        self.val_display = ft.Text(
            f"{self.value}{self.unit}",
            size=18,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.AMBER_400,
        )

        self.title_display = ft.Text(
            self.label_text,
            size=11,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.GREY_400,
        )

        self.minus_btn = ft.IconButton(
            icon=ft.Icons.REMOVE_ROUNDED,
            icon_size=16,
            on_click=self._decrement,
        )

        self.plus_btn = ft.IconButton(
            icon=ft.Icons.ADD_ROUNDED,
            icon_size=16,
            on_click=self._increment,
        )

        self.content = ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
            controls=[
                self.title_display,
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=2,
                    controls=[
                        self.minus_btn,
                        self.val_display,
                        self.plus_btn,
                    ],
                ),
            ],
        )

        self.padding = 8
        self.border_radius = 10

        if self.theme_manager:
            self.theme_manager.add_listener(self.apply_theme)
            self.apply_theme()

    def set_value(self, new_val: int, update_page: bool = True) -> None:
        """Updates internal knob value and optionally triggers a control update."""
        clamped = max(self.min_val, min(self.max_val, new_val))
        if clamped != self.value:
            self.value = clamped
            self.val_display.value = f"{self.value}{self.unit}"
            if update_page and self.page:
                self.update()

    def _decrement(self, e) -> None:
        if self.value > self.min_val:
            self.set_value(self.value - 1)
            if self.on_change:
                self.on_change(self.value)

    def _increment(self, e) -> None:
        if self.value < self.max_val:
            self.set_value(self.value + 1)
            if self.on_change:
                self.on_change(self.value)

    def apply_theme(self) -> None:
        """Applies light/dark theme styling without triggering premature page updates."""
        if not self.theme_manager:
            return
        is_dark = self.theme_manager.is_dark()
        self.title_display.color = "#C4B5FD" if is_dark else "#5D4B75"
