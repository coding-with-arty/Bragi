"""
src/views/components/audio_device_dialog.py
============================================
Audio Device Selector Modal ensuring background capture stays active when closed.
"""

from typing import Optional
import flet as ft
from services.audio_manager import AudioManager
from utils.theme_manager import ThemeManager


class AudioDeviceDialog(ft.AlertDialog):
    """Modal dialog for selecting hardware microphones without interrupting background capture."""

    def __init__(self, theme_manager: Optional[ThemeManager] = None):
        self.theme_manager = theme_manager
        self.audio_manager = AudioManager.get_instance()

        # Enumerate hardware devices
        devices = self.audio_manager.get_available_devices()
        options = [
            ft.DropdownOption(key=str(d["id"]), text=d["name"])
            for d in devices
        ]

        self.device_dropdown = ft.Dropdown(
            label="Hardware Microphone Input",
            options=options,
            value=str(self.audio_manager.current_device_id),
            expand=True,
            on_select=self._on_device_changed,
        )

        self.mic_toggle = ft.Switch(
            label="Enable Microphone Stream",
            value=self.audio_manager.is_listening,
            on_change=self._on_toggle_mic,
        )

        super().__init__(
            title=ft.Text("Audio Device Settings", weight=ft.FontWeight.BOLD),
            content=ft.Column(
                controls=[
                    self.mic_toggle,
                    self.device_dropdown,
                ],
                tight=True,
                spacing=16,
            ),
            actions=[
                ft.TextButton("Close", on_click=self._close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _on_device_changed(self, e):
        selected_id = e.control.value
        self.audio_manager.set_input_device(selected_id)
        self.audio_manager.start_listening()

    def _on_toggle_mic(self, e):
        if e.control.value:
            self.audio_manager.start_listening()
        else:
            self.audio_manager.stop_listening()

    def _close_dialog(self, e):
        self.open = False
        if self.page:
            self.page.update()
