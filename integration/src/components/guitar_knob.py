"""
guitar_knob.py - Custom rotary guitar knob control[cite: 8].
"""

import flet as ft
from utils.theme_manager import ThemeManager


class GuitarKnob(ft.Container):
    def __init__(
        self,
        label: str,
        min_val: int = 1,
        max_val: int = 10,
        initial_val: int = 3,
        unit: str = "",
        theme_manager: ThemeManager = None,
        on_change = None,
    ):
        super().__init__()
        self.label_str = label
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.unit = unit
        self.theme_manager = theme_manager
        self.on_change = on_change

        self.label_text = ft.Text(
            self.label_str.upper(),
            size=11,
            weight=ft.FontWeight.W_700,
        )

        self.value_text = ft.Text(
            f"{self.value}{self.unit}",
            size=18,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.AMBER_500,
        )

        self.dial_marker = ft.Container(
            width=3,
            height=6,
            border_radius=2,
            bgcolor=ft.Colors.AMBER_400,
        )

        self.knob_face = ft.Container(
            width=76,
            height=76,
            shape=ft.BoxShape.CIRCLE,
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2,
                controls=[
                    self.dial_marker,
                    self.value_text,
                ],
            ),
        )

        self.dec_icon = ft.Icon(ft.Icons.REMOVE_ROUNDED, size=18)
        self.dec_button = ft.Container(
            content=self.dec_icon,
            width=32,
            height=32,
            shape=ft.BoxShape.CIRCLE,
            alignment=ft.Alignment.CENTER,
            on_click=self._decrement,
            ink=True,
            tooltip=f"Decrease {label}",
        )

        self.inc_icon = ft.Icon(ft.Icons.ADD_ROUNDED, size=18)
        self.inc_button = ft.Container(
            content=self.inc_icon,
            width=32,
            height=32,
            shape=ft.BoxShape.CIRCLE,
            alignment=ft.Alignment.CENTER,
            on_click=self._increment,
            ink=True,
            tooltip=f"Increase {label}",
        )

        self.content = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
            controls=[
                self.label_text,
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                    tight=True,
                    controls=[
                        self.dec_button,
                        self.knob_face,
                        self.inc_button,
                    ],
                ),
            ],
        )

        if self.theme_manager:
            self.theme_manager.add_listener(self.apply_theme)
            self.apply_theme()

    def apply_theme(self):
        if not self.theme_manager:
            return
        is_dark = self.theme_manager.is_dark()

        self.label_text.color = "#C4B5FD" if is_dark else "#5D4B75"
        self.knob_face.bgcolor = "#1A1721" if is_dark else "#EFEBF5"
        self.knob_face.border = ft.Border.all(3, "#4E4162" if is_dark else "#B8ADCE")

        button_bg = "#2E2838" if is_dark else "#DDD5E8"
        button_border = "#5C4E72" if is_dark else "#A393BD"
        icon_color = "#E2D8EE" if is_dark else "#3A2E4C"

        self.dec_button.bgcolor = button_bg
        self.dec_button.border = ft.Border.all(1.5, button_border)
        self.dec_icon.color = icon_color

        self.inc_button.bgcolor = button_bg
        self.inc_button.border = ft.Border.all(1.5, button_border)
        self.inc_icon.color = icon_color

    def _decrement(self, e):
        if self.value > self.min_val:
            self.value -= 1
            self.value_text.value = f"{self.value}{self.unit}"
            if self.page:
                self.page.update()
            if self.on_change:
                self.on_change(self.value)

    def _increment(self, e):
        if self.value < self.max_val:
            self.value += 1
            self.value_text.value = f"{self.value}{self.unit}"
            if self.page:
                self.page.update()
            if self.on_change:
                self.on_change(self.value)

    def set_value(self, new_val: int):
        self.value = max(self.min_val, min(self.max_val, int(new_val)))
        self.value_text.value = f"{self.value}{self.unit}"
        if self.page:
            self.page.update()
