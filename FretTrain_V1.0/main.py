"""
main.py
=======
Main application entry point for Frettrain.
"""

import flet as ft
from src.ui.fret_trainer_view import FretTrainerControl
from src.ui.tuner_app import TunerControl


def main(page: ft.Page):
    page.title = "Frettrain - Guitar Ear & Fretboard Trainer"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 500
    page.window.height = 700
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.START

    tabs = ft.Tabs(
        length=2,
        selected_index=0,
        animation_duration=300,
        tab_bar=ft.TabBar(
            tabs=[
                ft.Tab(
                    label="Trainer",
                    icon=ft.Icons.SCHOOL,
                ),
                ft.Tab(
                    label="Standalone Tuner",
                    icon=ft.Icons.TUNE,
                ),
            ]
        ),
        content=ft.TabBarView(
            controls=[
                ft.Container(
                    content=FretTrainerControl(),
                    padding=20,
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Container(
                    content=TunerControl(),
                    padding=20,
                    alignment=ft.Alignment.CENTER,
                ),
            ]
        ),
        expand=True,
    )

    page.add(tabs)


if __name__ == "__main__":
    ft.run(main)
