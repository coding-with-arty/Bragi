import flet as ft

class ThemeManager:
    def __init__(self, page: ft.Page):
        self.page = page

    def toggle_theme(self):
        if self.page.theme_mode == ft.ThemeMode.DARK:
            self.page.theme_mode = ft.ThemeMode.LIGHT
        else:
            self.page.theme_mode = ft.ThemeMode.DARK
        self.page.update()

    def is_dark(self) -> bool:
        return self.page.theme_mode == ft.ThemeMode.DARK
