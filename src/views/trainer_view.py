import asyncio
import flet as ft
from components.header import Header
from components.note_display import NoteDisplay
from utils.music_theory import MusicTheory
from utils.theme_manager import ThemeManager
from utils.timer_manager import TrainerTimer, PracticeMode

class TrainerView(ft.Column):
    def __init__(self, theme_manager: ThemeManager):
        super().__init__()
        self.theme_manager = theme_manager
        self.expand = True
        self.num_strings = 6
        self.string_configs = []

        # Instantiate Non-blocking Practice Timer
        self.timer = TrainerTimer(
            duration=3.0,
            mode=PracticeMode.SPEED_FLASHCARD,
            tick_interval=0.05,
            on_tick=self.on_timer_tick,
            on_timeout=self.on_timer_timeout,
        )

        self.note_display = NoteDisplay(on_next_click=self.generate_next_note)

        # Preset Dropdown
        self.preset_dropdown = ft.Dropdown(
            label="Instrument Preset",
            options=[ft.DropdownOption(key=p, text=p) for p in MusicTheory.get_presets()],
            value="Guitar (6-String Standard)",
            expand=True,
        )
        self.preset_dropdown.on_change = self.on_preset_change
        self.preset_dropdown.on_select = self.on_preset_change

        self.string_count_slider = ft.Slider(
            min=1,
            max=8,
            divisions=7,
            value=6,
            label="{value} Strings",
            on_change=self.on_string_count_change,
        )

        # Timer Controls (1s to 10s range)
        self.auto_switch = ft.Switch(
            label="Auto-Advance Timer",
            value=False,
            on_change=self.on_auto_switch_toggle,
        )

        self.timer_duration_slider = ft.Slider(
            min=1,
            max=10,
            divisions=9,
            value=3,
            label="{value}s",
            on_change=self.on_timer_duration_change,
        )

        self.strings_column = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, height=180)

        config_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Instrument Setup", size=18, weight=ft.FontWeight.BOLD),
                        self.preset_dropdown,
                        ft.Row(
                            [
                                ft.Text("Strings Count:"),
                                ft.Container(content=self.string_count_slider, expand=True)
                            ]
                        ),
                        ft.Divider(),
                        ft.Text("Practice Timer", size=16, weight=ft.FontWeight.BOLD),
                        self.auto_switch,
                        ft.Row(
                            [
                                ft.Text("Interval:"),
                                ft.Container(content=self.timer_duration_slider, expand=True)
                            ]
                        ),
                        ft.Divider(),
                        ft.Text("Active Strings & Tuning", size=14, weight=ft.FontWeight.W_500),
                        self.strings_column,
                    ],
                    spacing=12,
                ),
                padding=16,
                bgcolor=ft.Colors.with_opacity(0.65, ft.Colors.SURFACE),
                border_radius=12,
            ),
            elevation=4,
        )

        self.controls = [
            Header(self.theme_manager),
            ft.ResponsiveRow(
                expand=True,
                controls=[
                    ft.Container(
                        content=config_card,
                        col={"sm": 12, "md": 5, "lg": 4},
                        padding=10,
                    ),
                    ft.Container(
                        content=self.note_display,
                        col={"sm": 12, "md": 7, "lg": 8},
                        alignment=ft.Alignment.CENTER,
                        padding=10,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        ]

    def did_mount(self):
        """Flet automatically invokes did_mount after TrainerView is attached to the page DOM."""
        self.apply_preset("Guitar (6-String Standard)")

    def rebuild_string_controls(self, tunings: list[str] = None):
        self.string_configs.clear()
        self.strings_column.controls.clear()

        notes = MusicTheory.get_notes()
        for i in range(1, int(self.num_strings) + 1):
            default_tuning = tunings[i - 1] if tunings and (i - 1) < len(tunings) else "E"
            if default_tuning not in notes:
                default_tuning = "E"

            chk = ft.Checkbox(value=True, label=f"Str {i}")
            dd = ft.Dropdown(
                options=[ft.DropdownOption(key=n, text=n) for n in notes],
                value=default_tuning,
                width=80,
                dense=True,
            )

            config = {"string_num": i, "checkbox": chk, "dropdown": dd}
            self.string_configs.append(config)

            self.strings_column.controls.append(
                ft.Row(
                    controls=[chk, ft.Text("Tuning:"), dd],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            )

        if self.page:
            self.page.update()

    def on_preset_change(self, e):
        preset = self.preset_dropdown.value
        if preset != "Custom":
            self.apply_preset(preset)

    def apply_preset(self, preset_name: str):
        tunings = MusicTheory.get_preset_tuning(preset_name)
        if tunings:
            self.num_strings = len(tunings)
            self.string_count_slider.value = self.num_strings
            self.rebuild_string_controls(tunings)

    def on_string_count_change(self, e):
        self.num_strings = int(self.string_count_slider.value)
        self.preset_dropdown.value = "Custom"
        self.rebuild_string_controls()

    def on_auto_switch_toggle(self, e):
        if self.auto_switch.value:
            self.note_display.update_progress(0.0, visible=True)
            if self.note_display.note_text.value != "?":
                asyncio.create_task(self.timer.start(self.timer_duration_slider.value))
        else:
            asyncio.create_task(self.timer.reset())
            self.note_display.update_progress(0.0, visible=False)

    def on_timer_duration_change(self, e):
        self.timer.set_duration(self.timer_duration_slider.value)

    def on_timer_tick(self, elapsed: float, remaining: float, progress: float):
        if self.auto_switch.value:
            self.note_display.update_progress(progress, visible=True)

    def on_timer_timeout(self):
        self.generate_next_note()

    def generate_next_note(self):
        active_strings = [
            {
                "string_num": c["string_num"],
                "tuning": c["dropdown"].value,
                "active": c["checkbox"].value,
            }
            for c in self.string_configs
        ]
        string_num, tuning, note = MusicTheory.generate_random_note(active_strings)
        self.note_display.set_target(string_num, tuning, note)

        if self.auto_switch.value:
            asyncio.create_task(self.timer.start(self.timer_duration_slider.value))
