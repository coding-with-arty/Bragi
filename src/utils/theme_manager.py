import flet as ft


class ThemeManager:
    def __init__(self, page: ft.Page):
        self.page = page
        self._listeners = []

    def toggle_theme(self):
        if self.page.theme_mode == ft.ThemeMode.DARK:
            self.page.theme_mode = ft.ThemeMode.LIGHT
        else:
            self.page.theme_mode = ft.ThemeMode.DARK

        for listener in self._listeners:
            try:
                listener()
            except Exception:
                pass

        self.page.update()

    def is_dark(self) -> bool:
        return self.page.theme_mode == ft.ThemeMode.DARK

    def add_listener(self, callback):
        if callback not in self._listeners:
            self._listeners.append(callback)
