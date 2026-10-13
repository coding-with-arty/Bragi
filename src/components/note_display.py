import flet as ft
from utils.theme_manager import ThemeManager

class NoteDisplay(ft.Container):
    def __init__(self, on_next_click, theme_manager: ThemeManager = None):
        super().__init__()
        self.on_next_click = on_next_click
        self.theme_manager = theme_manager
        self.alignment = ft.Alignment.CENTER
        self.padding = 20

        self.note_text = ft.Text("?", size=88, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400)
        self.string_text = ft.Text(
            "Press Next to Start",
            size=20,
            weight=ft.FontWeight.W_500
        )
        self.progress_bar = ft.ProgressBar(
            value=0.0,
            width=260,
            color=ft.Colors.AMBER_500,
            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.GREY),
            visible=False,
        )

        self.target_circle = ft.Container(
            width=300,
            height=300,
            shape=ft.BoxShape.CIRCLE,
            border=ft.Border.all(3, ft.Colors.AMBER_400),
            shadow=ft.BoxShadow(
                blur_radius=25,
                color=ft.Colors.with_opacity(0.35, ft.Colors.AMBER_400),
            ),
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
                controls=[
                    self.string_text,
                    self.note_text,
                ]
            )
        )

        self.content = ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self.target_circle,
                ft.Container(height=16),
                self.progress_bar,
                ft.Container(height=16),
                ft.Button(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED, size=24),
                            ft.Text("Next Note", size=18, weight=ft.FontWeight.BOLD)
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        tight=True,
                    ),
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=30),
                        padding=ft.Padding.symmetric(horizontal=36, vertical=20),
                        color=ft.Colors.BLACK,
                        bgcolor=ft.Colors.AMBER_400,
                    ),
                    on_click=lambda e: self.on_next_click(),
                )
            ]
        )

        if self.theme_manager:
            self.theme_manager.add_listener(self.apply_theme)
            self.apply_theme()

    def apply_theme(self):
        if not self.theme_manager:
            return
        is_dark = self.theme_manager.is_dark()
        self.target_circle.bgcolor = ft.Colors.with_opacity(0.35, ft.Colors.BLACK) if is_dark else ft.Colors.with_opacity(0.85, ft.Colors.WHITE)
        self.string_text.color = ft.Colors.with_opacity(0.8, ft.Colors.WHITE) if is_dark else ft.Colors.with_opacity(0.8, ft.Colors.BLACK)

    def set_target(self, string_num: int, tuning: str, note: str):
        self.note_text.value = note
        self.string_text.value = f"String {string_num} ({tuning})"
        if self.page:
            self.page.update()

    def update_progress(self, progress: float, visible: bool = True):
        self.progress_bar.visible = visible
        self.progress_bar.value = progress
        if self.page:
            self.page.update()
