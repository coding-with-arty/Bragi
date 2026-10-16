"""
src/views/components/audio_device_dialog.py
============================================
Global Audio Input Management Dialog launched via the G-Clef header action button.
Includes top Microphone On/Off verification switch and system device picker.
"""

from typing import Optional
import flet as ft
from services.audio_manager import AudioManager
from utils.theme_manager import ThemeManager


class AudioDeviceDialog(ft.AlertDialog):
    """Modal dialog for toggling microphone input and switching active input devices."""

    def __init__(self, theme_manager: Optional[ThemeManager] = None):
        self.theme_manager = theme_manager
        self.audio_manager = AudioManager.get_instance()

        title = ft.Row(
            controls=[
                ft.Icon(ft.Icons.MUSIC_NOTE_ROUNDED, color=ft.Colors.AMBER_400, size=24),
                ft.Text("Audio Source & Microphone", size=18, weight=ft.FontWeight.BOLD),
            ],
            spacing=10,
        )

        # Top Master Microphone Toggle Switch
        self.mic_switch = ft.Switch(
            label="Microphone Processing Enabled",
            value=self.audio_manager.is_listening,
            active_color=ft.Colors.GREEN_400,
            on_change=self._on_mic_switch_changed,
        )

        self.device_list_column = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO)
        self._render_devices()

        content = ft.Container(
            width=480,
            height=320,
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.MIC_ROUNDED, color=ft.Colors.AMBER_400, size=20),
                                        ft.Text("Audio Verification", weight=ft.FontWeight.BOLD, size=13),
                                    ],
                                    spacing=8,
                                ),
                                self.mic_switch,
                            ],
                        ),
                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                        border_radius=8,
                        padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                    ),
                    ft.Divider(height=1, color=ft.Colors.GREY_800),
                    ft.Text(
                        "Select an active input interface for real-time pitch & tuner detection:",
                        size=12,
                        color=ft.Colors.GREY_400,
                    ),
                    self.device_list_column,
                ],
                spacing=10,
            ),
        )

        close_button = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CLOSE_ROUNDED, size=16, color=ft.Colors.WHITE),
                    ft.Text("Cancel", size=12, color=ft.Colors.WHITE),
                ],
                tight=True,
                spacing=4,
            ),
            bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=14, vertical=8),
            ink=True,
            on_click=self._close_dialog,
        )

        super().__init__(
            title=title,
            content=content,
            actions=[close_button],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _on_mic_switch_changed(self, e) -> None:
        if self.mic_switch.value:
            self.audio_manager.start_listening()
        else:
            self.audio_manager.stop_listening()

    def _render_devices(self) -> None:
        devices = self.audio_manager.get_available_devices()
        current_id = self.audio_manager.current_device_id

        controls = []
        for dev in devices:
            is_selected = str(dev["id"]) == str(current_id) or (
                current_id == "default" and dev.get("is_default")
            )

            card = ft.Container(
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(
                                    ft.Icons.RADIO_BUTTON_CHECKED_ROUNDED
                                    if is_selected
                                    else ft.Icons.RADIO_BUTTON_UNCHECKED_ROUNDED,
                                    color=ft.Colors.AMBER_400 if is_selected else ft.Colors.GREY_500,
                                    size=20,
                                ),
                                ft.Column(
                                    spacing=2,
                                    controls=[
                                        ft.Text(
                                            dev["name"],
                                            weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.NORMAL,
                                            size=13,
                                        ),
                                        ft.Text(f"{dev['type']} • {dev['status']}", size=11, color=ft.Colors.GREY_400),
                                    ],
                                ),
                            ],
                            spacing=12,
                        ),
                        ft.Container(
                            content=ft.Text(
                                "DEFAULT" if dev.get("is_default") else "READY",
                                size=9,
                                color=ft.Colors.BLACK,
                                weight=ft.FontWeight.BOLD,
                            ),
                            bgcolor=ft.Colors.AMBER_400 if dev.get("is_default") else ft.Colors.GREY_700,
                            border_radius=4,
                            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                        ),
                    ],
                ),
                bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.AMBER_400)
                if is_selected
                else ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
                border=ft.Border.all(
                    1, ft.Colors.AMBER_400 if is_selected else ft.Colors.with_opacity(0.15, "#3E354A")
                ),
                border_radius=8,
                padding=10,
                ink=True,
                data=dev["id"],
                on_click=self._select_device,
            )
            controls.append(card)

        self.device_list_column.controls = controls

    def _select_device(self, e) -> None:
        dev_id = e.control.data
        self.audio_manager.set_input_device(dev_id)
        self._close_dialog()

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
