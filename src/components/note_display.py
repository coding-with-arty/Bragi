import flet as ft

class NoteDisplay(ft.Container):
    def __init__(self, on_next_click):
        super().__init__()
        self.on_next_click = on_next_click
        self.alignment = ft.Alignment.CENTER
        self.padding = 20

        self.note_text = ft.Text("?", size=88, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_300)
        self.string_text = ft.Text(
            "Press Next to Start",
            size=20,
            color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
            weight=ft.FontWeight.W_500
        )

        self.content = ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=300,
                    height=300,
                    shape=ft.BoxShape.CIRCLE,
                    bgcolor=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
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
                ),
                ft.Container(height=24),
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

    def set_target(self, string_num: int, tuning: str, note: str):
        self.note_text.value = note
        self.string_text.value = f"String {string_num} ({tuning})"
        if self.page:
            self.page.update()
