# src/views/components/education_dialog.py
"""
Education Dialog Modal
======================
Contextual pedagogical modal dialog explaining 'Why Learn This?' and
real-world application for every active view module.
"""

from typing import Optional
import flet as ft
from utils.theme_manager import ThemeManager


PEDAGOGY_CONTENT = {
    "scale_trainer": {
        "title": "Why Learn Scales?",
        "icon": ft.Icons.AUTO_AWESOME_ROUNDED,
        "summary": "Scales are the fundamental building blocks of solos, melodies, and riffs.",
        "points": [
            "Fretboard Navigation: Memorizing scale shapes allows you to instantly locate key center notes anywhere on the neck.",
            "Improvisation: Knowing Major, Minor, and Pentatonic scales lets you jam over chord progressions naturally without hitting sour notes.",
            "Technique & Dexterity: Scale runs build speed, finger independence, and synchronized picking.",
        ],
        "real_world": "In Rock, Blues, and Pop, over 80% of classic guitar solos rely directly on Minor Pentatonic and Major Scale patterns.",
    },
    "chord_trainer": {
        "title": "Why Learn Chords & Extensions?",
        "icon": ft.Icons.GRID_VIEW_ROUNDED,
        "summary": "Chords provide the harmonic foundation for all songwriting and accompaniment.",
        "points": [
            "Harmonic Foundation: Master Major, Minor, Dom7, Maj7, and Sus4 voicings across the fretboard.",
            "Voice Leading: Smoothly connect chord shapes up and down the neck without large hand jumps.",
            "Real-time Verification: Train your ear and fingers to press clean frets so all chord notes ring cleanly.",
        ],
        "real_world": "Dominant 7th and Sus4 chords create harmonic tension and resolution that drive Funk, Jazz, Blues, and Acoustic rhythm guitar.",
    },
    "tuner": {
        "title": "Why Use a Precision Tuner?",
        "icon": ft.Icons.GRAPHIC_EQ_ROUNDED,
        "summary": "Accurate tuning ensures pitch harmony, correct ear training, and proper instrument resonance.",
        "points": [
            "Ear Training Calibration: Practicing on an in-tune instrument trains your brain to internalize true pitch centers.",
            "Pitch Accuracy: Clean cents error feedback ensures string harmonics resonate cleanly.",
        ],
        "real_world": "Even minor pitch drift (5–10 cents) causes multi-string chords to sound out of tune.",
    },
    "ear_training": {
        "title": "Why Train Your Ear?",
        "icon": ft.Icons.HEARING_ROUNDED,
        "summary": "Ear training bridges the gap between the music you hear in your head and your instrument.",
        "points": [
            "Transcribing Songs: Identify intervals and chord qualities by ear without needing sheet music or tabs.",
            "Musical Intuition: Hear pitch jumps and immediately translate them to fretboard positions.",
        ],
        "real_world": "Professional musicians use ear training to learn songs on the fly during rehearsals and live performances.",
    },
}


class EducationDialog(ft.AlertDialog):
    """Reusable modal dialog presenting contextual pedagogy for any exercise module."""

    def __init__(self, module_key: str = "scale_trainer", theme_manager: Optional[ThemeManager] = None):
        data = PEDAGOGY_CONTENT.get(module_key, PEDAGOGY_CONTENT["scale_trainer"])

        title = ft.Row(
            controls=[
                ft.Icon(data["icon"], color=ft.Colors.AMBER_400, size=24),
                ft.Text(data["title"], size=18, weight=ft.FontWeight.BOLD),
            ],
            spacing=10,
        )

        content_controls = [
            ft.Text(data["summary"], size=13, weight=ft.FontWeight.W_500, color=ft.Colors.AMBER_300),
            ft.Divider(height=1, color=ft.Colors.GREY_800),
        ]

        for pt in data["points"]:
            content_controls.append(
                ft.Row(
                    cross_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Text("•", size=14, color=ft.Colors.AMBER_400, weight=ft.FontWeight.BOLD),
                        ft.Container(
                            content=ft.Text(pt, size=12, color=ft.Colors.GREY_300),
                            expand=True,
                        ),
                    ],
                    spacing=6,
                )
            )

        content_controls.extend([
            ft.Container(height=6),
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Real-World Application:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_400),
                        ft.Text(data["real_world"], size=11, color=ft.Colors.GREY_400, italic=True),
                    ],
                    spacing=2,
                ),
                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.CYAN_400),
                border_radius=8,
                padding=10,
            ),
        ])

        close_btn = ft.Container(
            content=ft.Text("Got it!", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.BLACK),
            bgcolor=ft.Colors.AMBER_400,
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=16, vertical=8),
            ink=True,
            on_click=self._close_dialog,
        )

        super().__init__(
            title=title,
            content=ft.Container(
                width=400,
                content=ft.Column(controls=content_controls, tight=True, spacing=10),
            ),
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
