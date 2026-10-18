# src/views/subviews/tuner_view.py
"""
Tuner View Subview
==================
Real-time chromatic instrument tuner component reading DSP audio frames
from AudioManager via a thread-safe main-loop polling task.
"""

import asyncio
from typing import Optional
import flet as ft
from services.audio_manager import AudioManager
from utils.theme_manager import ThemeManager


class TunerView(ft.Column):
    """Chromatic Tuner view with real-time pitch detection and needle gauge."""

    def __init__(self, theme_manager: Optional[ThemeManager] = None):
        super().__init__()
        self.theme_manager = theme_manager
        self.expand = True
        self.alignment = ft.MainAxisAlignment.CENTER
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        self._is_mounted = False

        # 1. Typography Controls
        self.note_text = ft.Text("--", size=72, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400)
        self.cents_text = ft.Text("Play a string...", size=20, color=ft.Colors.GREY_400)
        self.freq_text = ft.Text("0.0 Hz", size=14, color=ft.Colors.GREY_500)

        # 2. Visual Needle Gauge (0.5 represents pitch center / 0 cents)
        self.needle_progress = ft.ProgressBar(
            value=0.5,
            width=360,
            color=ft.Colors.AMBER_400,
            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.GREY),
        )

        # 3. In-Tune Status Badge
        self.status_badge = ft.Container(
            content=ft.Text("IN TUNE", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
            bgcolor=ft.Colors.GREEN_400,
            border_radius=12,
            padding=ft.Padding.symmetric(horizontal=12, vertical=4),
            visible=False,
        )

        # 4. Outer Gauge Frame Container
        self.gauge_container = ft.Container(
            width=420,
            height=300,
            border_radius=20,
            border=ft.Border.all(2, ft.Colors.AMBER_400),
            padding=24,
            alignment=ft.Alignment.CENTER,
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.2, "#000000")),
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
                controls=[
                    self.note_text,
                    self.status_badge,
                    self.needle_progress,
                    self.cents_text,
                    self.freq_text,
                ],
            ),
        )

        self.controls = [
            ft.Text("CHROMATIC INSTRUMENT TUNER", size=18, weight=ft.FontWeight.BOLD),
            ft.Container(height=20),
            self.gauge_container,
        ]

        if self.theme_manager:
            self.theme_manager.add_listener(self.apply_theme)
            self.apply_theme()

    def did_mount(self):
        """Starts thread-safe asyncio polling loop when mounted."""
        self._is_mounted = True
        asyncio.create_task(self._update_loop())

    def will_unmount(self):
        """Stops polling loop when navigating away."""
        self._is_mounted = False

    def apply_theme(self):
        """Updates background colors according to theme mode."""
        if not self.theme_manager:
            return
        is_dark = self.theme_manager.is_dark()
        bg_card = "#231F2D" if is_dark else "#FFFFFF"
        self.gauge_container.bgcolor = bg_card

    async def _update_loop(self):
        """Thread-safe main event loop polling task (~25 FPS)."""
        am = AudioManager.get_instance()

        while self._is_mounted:
            state = am.current_state
            pdata = state.get("pitch_data", {})

            is_silent = pdata.get("is_silent", True)
            freq = pdata.get("frequency", pdata.get("pitch", 0.0))
            cents = pdata.get("cents", 0.0)
            note_name = pdata.get("note_name", "--")

            if is_silent or freq <= 0:
                self.note_text.value = "--"
                self.freq_text.value = "0.0 Hz"
                self.cents_text.value = "Listening for string..."
                self.cents_text.color = ft.Colors.GREY_400
                self.needle_progress.value = 0.5
                self.needle_progress.color = ft.Colors.AMBER_400
                self.status_badge.visible = False
                self.gauge_container.border = ft.Border.all(2, ft.Colors.AMBER_400)
            else:
                self.note_text.value = note_name
                self.freq_text.value = f"{freq:.1f} Hz"

                # Map cents (-50 to +50) to progress position (0.0 to 1.0)
                clamped_cents = max(-50.0, min(50.0, cents))
                norm_pos = (clamped_cents + 50.0) / 100.0
                self.needle_progress.value = norm_pos

                # Accuracy feedback thresholds
                if abs(cents) <= 5.0:
                    self.needle_progress.color = ft.Colors.GREEN_400
                    self.cents_text.value = f"IN TUNE ({cents:+.1f} cents)"
                    self.cents_text.color = ft.Colors.GREEN_400
                    self.status_badge.visible = True
                    self.gauge_container.border = ft.Border.all(3, ft.Colors.GREEN_400)
                else:
                    self.status_badge.visible = False
                    self.gauge_container.border = ft.Border.all(2, ft.Colors.AMBER_400)
                    if cents < 0:
                        self.needle_progress.color = ft.Colors.RED_400
                        self.cents_text.value = f"FLAT ({cents:+.1f} cents)"
                        self.cents_text.color = ft.Colors.RED_400
                    else:
                        self.needle_progress.color = ft.Colors.AMBER_400
                        self.cents_text.value = f"SHARP ({cents:+.1f} cents)"
                        self.cents_text.color = ft.Colors.AMBER_400

            if self.page:
                try:
                    self.update()
                except Exception:
                    pass

            await asyncio.sleep(0.04)
