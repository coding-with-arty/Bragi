# src/views/components/audio_device_dialog.py
"""
Audio Device Selector Dialog
============================
Modal dialog providing clean microphone input selection and a live volume testing meter.
"""

import asyncio
import flet as ft
from typing import Optional, Callable
from services.audio_manager import AudioManager


class AudioDeviceDialog(ft.AlertDialog):
    """Modal dialog allowing users to pick an input device and test microphone levels."""

    def __init__(
        self,
        on_device_selected: Optional[Callable[[Optional[int]], None]] = None,
        theme_manager: Optional[Any] = None,
        **kwargs,
    ):
        self.audio_manager = AudioManager.get_instance()
        self.on_device_selected = on_device_selected
        self.theme_manager = theme_manager
        self._is_monitoring = False

        # Query filtered input devices
        self.devices = self.audio_manager.get_filtered_input_devices()

        options = [
            ft.DropdownOption(
                key=str(dev["id"]),
                text=f"{'★ ' if dev['is_default'] else ''}{dev['name']}"
            )
            for dev in self.devices
        ]

        current_id = (
            str(self.audio_manager.current_device_id)
            if self.audio_manager.current_device_id is not None
            else (options[0].key if options else "")
        )

        self.device_dropdown = ft.Dropdown(
            label="Select Microphone Input",
            options=options,
            value=current_id,
            width=360,
            on_select=self._on_device_changed,
        )

        self.volume_bar = ft.ProgressBar(
            value=0.0,
            color=ft.Colors.GREEN_400,
            bgcolor=ft.Colors.GREY_800,
            height=12,
        )

        self.volume_label = ft.Text(
            "Input Volume Level: Below Threshold",
            size=12,
            color=ft.Colors.GREY_400,
        )

        content = ft.Column(
            tight=True,
            spacing=16,
            controls=[
                ft.Text("Select your primary audio capture device below:", size=13),
                self.device_dropdown,
                ft.Divider(height=1, color=ft.Colors.GREY_800),
                ft.Text("Live Microphone Test", weight=ft.FontWeight.BOLD, size=14),
                self.volume_bar,
                self.volume_label,
            ],
        )

        close_btn = ft.Button(
            "Done",
            style=ft.ButtonStyle(
                color=ft.Colors.BLACK,
                bgcolor=ft.Colors.AMBER_400,
            ),
            on_click=self._close_dialog,
        )

        super().__init__(
            title=ft.Row([
                ft.Icon(ft.Icons.MIC_ROUNDED, color=ft.Colors.AMBER_400),
                ft.Text("Audio Input Settings", weight=ft.FontWeight.BOLD),
            ], spacing=10),
            content=ft.Container(content=content, width=400, padding=10),
            actions=[close_btn],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _on_device_changed(self, e) -> None:
        selected_key = self.device_dropdown.value
        if selected_key is not None:
            dev_id = int(selected_key)
            success = self.audio_manager.start_listening(dev_id)
            if success and self.on_device_selected:
                self.on_device_selected(dev_id)

    def did_mount(self):
        self._is_monitoring = True
        if not self.audio_manager.is_listening:
            self.audio_manager.start_listening()
        asyncio.create_task(self._update_volume_loop())

    def will_unmount(self):
        self._is_monitoring = False

    async def _update_volume_loop(self):
        while self._is_monitoring:
            db = self.audio_manager.latest_volume_db
            norm_val = max(0.0, min(1.0, (db + 60.0) / 60.0))
            self.volume_bar.value = norm_val

            if db > -40.0:
                self.volume_bar.color = ft.Colors.GREEN_400
                self.volume_label.value = f"Input Volume Level: Active ({int(db)} dB) 🎵"
                self.volume_label.color = ft.Colors.GREEN_400
            else:
                self.volume_bar.color = ft.Colors.AMBER_400
                self.volume_label.value = "Input Volume Level: Speak or play a note..."
                self.volume_label.color = ft.Colors.GREY_400

            if self.page:
                try:
                    self.page.update()
                except Exception:
                    pass
            await asyncio.sleep(0.05)

    def _close_dialog(self, e=None) -> None:
        self._is_monitoring = False
        if self.page and hasattr(self.page, "close"):
            try:
                self.page.close(self)
                return
            except Exception:
                pass
        self.open = False
        if self.page:
            self.page.update()
