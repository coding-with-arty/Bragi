import asyncio
import flet as ft
from components.header import Header
from components.note_display import NoteDisplay
from components.guitar_knob import GuitarKnob
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

        # Non-blocking Practice Timer
        self.timer = TrainerTimer(
            duration=3.0,
            mode=PracticeMode.SPEED_FLASHCARD,
            tick_interval=0.05,
            on_tick=self.on_timer_tick,
            on_timeout=self.on_timer_timeout,
        )

        self.note_display = NoteDisplay(on_next_click=self.generate_next_note)

        # 1. Preset Selector Dropdown
        self.preset_dropdown = ft.Dropdown(
            label="Instrument Preset",
            label_style=ft.TextStyle(color="#C4B5FD"),
            options=[ft.DropdownOption(key=p, text=p) for p in MusicTheory.get_presets()],
            value="Guitar (6-String Standard)",
            expand=True,
            bgcolor="#1E1A26",
            border_color="#4E4162",
            focused_border_color=ft.Colors.AMBER_400,
            color="#EDE7F6",
        )
        self.preset_dropdown.on_change = self.on_preset_change

        # 2. Guitar Knob Controls (String Count & Timer Duration)
        self.string_count_knob = GuitarKnob(
            label="Strings",
            min_val=1,
            max_val=8,
            initial_val=6,
            unit="",
            on_change=self.on_string_count_knob_change,
        )

        self.timer_knob = GuitarKnob(
            label="Timer",
            min_val=1,
            max_val=10,
            initial_val=3,
            unit="s",
            on_change=self.on_timer_duration_knob_change,
        )

        # 3. Auto-Advance Timer Switch
        self.auto_switch = ft.Switch(
            label="Auto-Advance Mode",
            label_text_style=ft.TextStyle(color="#EDE7F6", weight=ft.FontWeight.W_600),
            value=False,
            active_color=ft.Colors.AMBER_400,
            on_change=self.on_auto_switch_toggle,
        )

        # 4. Scrollable Strings & Tuning Column
        self.strings_column = ft.Column(
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            height=200,
        )

        # Darker Pastel Section Panels
        preset_panel = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("INSTRUMENT SETUP", size=13, weight=ft.FontWeight.BOLD, color="#C4B5FD"),
                    self.preset_dropdown,
                ],
                spacing=12,
            ),
            padding=16,
            bgcolor="#231F2D",
            border=ft.Border.all(1, "#3E354A"),
            border_radius=14,
        )

        knobs_panel = ft.Container(
            content=ft.Row(
                controls=[
                    self.string_count_knob,
                    ft.VerticalDivider(color="#3E354A", width=1),
                    self.timer_knob,
                ],
                alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=12, vertical=16),
            bgcolor="#231F2D",
            border=ft.Border.all(1, "#3E354A"),
            border_radius=14,
        )

        timer_toggle_panel = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.TIMER_OUTLINED, color=ft.Colors.AMBER_400, size=22),
                    self.auto_switch,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.Padding.symmetric(horizontal=16, vertical=12),
            bgcolor="#231F2D",
            border=ft.Border.all(1, "#3E354A"),
            border_radius=14,
        )

        tunings_panel = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("ACTIVE STRINGS & TUNING", size=13, weight=ft.FontWeight.BOLD, color="#C4B5FD"),
                    self.strings_column,
                ],
                spacing=12,
            ),
            padding=16,
            bgcolor="#231F2D",
            border=ft.Border.all(1, "#3E354A"),
            border_radius=14,
        )

        # Main Sidebar Wrapper with Spacious Vertical Spacing
        sidebar_container = ft.Container(
            content=ft.Column(
                controls=[
                    preset_panel,
                    knobs_panel,
                    timer_toggle_panel,
                    tunings_panel,
                ],
                spacing=18,  # Generous un-crowded spacing between options
            ),
            padding=18,
            bgcolor="#1A1721",  # Darker pastel background
            border_radius=18,
            border=ft.Border.all(1, "#3E354A"),
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.4, "#000000")),
        )

        self.controls = [
            Header(self.theme_manager),
            ft.ResponsiveRow(
                expand=True,
                controls=[
                    ft.Container(
                        content=sidebar_container,
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
        self.apply_preset("Guitar (6-String Standard)")

    def rebuild_string_controls(self, tunings: list[str] = None):
        self.string_configs.clear()
        self.strings_column.controls.clear()

        notes = MusicTheory.get_notes()
        for i in range(1, int(self.num_strings) + 1):
            default_tuning = tunings[i - 1] if tunings and (i - 1) < len(tunings) else "E"
            if default_tuning not in notes:
                default_tuning = "E"

            chk = ft.Checkbox(
                value=True,
                label=f"Str {i}",
                fill_color=ft.Colors.AMBER_400,
                label_style=ft.TextStyle(color="#EDE7F6"),
            )
            dd = ft.Dropdown(
                options=[ft.DropdownOption(key=n, text=n) for n in notes],
                value=default_tuning,
                width=80,
                dense=True,
                bgcolor="#1E1A26",
                border_color="#4E4162",
                color="#EDE7F6",
            )

            config = {"string_num": i, "checkbox": chk, "dropdown": dd}
            self.string_configs.append(config)

            # Styled String Tuning Pill Row
            self.strings_column.controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[chk, ft.Text("Tuning:", color="#B0A8C0"), dd],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                    bgcolor="#1A1721",
                    border_radius=8,
                    border=ft.Border.all(1, "#3E354A"),
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
            self.string_count_knob.set_value(self.num_strings)
            self.rebuild_string_controls(tunings)

    def on_string_count_knob_change(self, val: int):
        self.num_strings = val
        self.preset_dropdown.value = "Custom"
        self.rebuild_string_controls()

    def on_timer_duration_knob_change(self, val: int):
        self.timer.set_duration(val)

    def on_auto_switch_toggle(self, e):
        if self.auto_switch.value:
            self.note_display.update_progress(0.0, visible=True)
            if self.note_display.note_text.value != "?":
                asyncio.create_task(self.timer.start(self.timer_knob.value))
        else:
            asyncio.create_task(self.timer.reset())
            self.note_display.update_progress(0.0, visible=False)

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
            asyncio.create_task(self.timer.start(self.timer_knob.value))
