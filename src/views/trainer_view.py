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

        self.note_display = NoteDisplay(on_next_click=self.generate_next_note, theme_manager=self.theme_manager)

        # 1. Preset Title & Dropdown
        self.preset_title = ft.Text("INSTRUMENT SETUP", size=13, weight=ft.FontWeight.BOLD)
        self.preset_dropdown = ft.Dropdown(
            label="Instrument Preset",
            options=[ft.DropdownOption(key=p, text=p) for p in MusicTheory.get_presets()],
            value="Guitar (6-String Standard)",
            expand=True,
            focused_border_color=ft.Colors.AMBER_400,
        )
        # Bind event listeners post-instantiation
        self.preset_dropdown.on_change = self.on_preset_change
        self.preset_dropdown.on_select = self.on_preset_change

        # 2. Guitar Knob Controls
        self.string_count_knob = GuitarKnob(
            label="Strings",
            min_val=1,
            max_val=8,
            initial_val=6,
            unit="",
            theme_manager=self.theme_manager,
            on_change=self.on_string_count_knob_change,
        )

        self.timer_knob = GuitarKnob(
            label="Timer",
            min_val=1,
            max_val=10,
            initial_val=3,
            unit="s",
            theme_manager=self.theme_manager,
            on_change=self.on_timer_duration_knob_change,
        )

        # 3. Auto-Advance Timer Switch
        self.auto_switch = ft.Switch(
            label="Auto-Advance Mode",
            value=False,
            active_color=ft.Colors.AMBER_400,
            on_change=self.on_auto_switch_toggle,
        )

        # 4. Scrollable Strings Column
        self.tunings_title = ft.Text("ACTIVE STRINGS & TUNING", size=13, weight=ft.FontWeight.BOLD)
        self.strings_column = ft.Column(
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            height=200,
        )

        # Theme-aware Panels
        self.preset_panel = ft.Container(
            content=ft.Column(
                controls=[
                    self.preset_title,
                    self.preset_dropdown,
                ],
                spacing=12,
            ),
            padding=16,
            border_radius=14,
        )

        self.knobs_panel = ft.Container(
            content=ft.Row(
                controls=[
                    self.string_count_knob,
                    self.timer_knob,
                ],
                alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                wrap=True,
                run_spacing=12,
            ),
            padding=ft.Padding.symmetric(horizontal=12, vertical=16),
            border_radius=14,
        )

        self.timer_toggle_panel = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.TIMER_OUTLINED, color=ft.Colors.AMBER_400, size=22),
                    self.auto_switch,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.Padding.symmetric(horizontal=16, vertical=12),
            border_radius=14,
        )

        self.tunings_panel = ft.Container(
            content=ft.Column(
                controls=[
                    self.tunings_title,
                    self.strings_column,
                ],
                spacing=12,
            ),
            padding=16,
            border_radius=14,
        )

        self.sidebar_container = ft.Container(
            content=ft.Column(
                controls=[
                    self.preset_panel,
                    self.knobs_panel,
                    self.timer_toggle_panel,
                    self.tunings_panel,
                ],
                spacing=16,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=18,
            border_radius=18,
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.3, "#000000")),
            height=650,
        )

        self.controls = [
            Header(self.theme_manager),
            ft.ResponsiveRow(
                expand=True,
                controls=[
                    ft.Container(
                        content=self.sidebar_container,
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

        self.theme_manager.add_listener(self.apply_theme)
        self.apply_theme()

    def did_mount(self):
        self.apply_preset("Guitar (6-String Standard)")

    def apply_theme(self):
        is_dark = self.theme_manager.is_dark()

        bg_sidebar = "#1A1721" if is_dark else "#F3F0F8"
        bg_panel = "#231F2D" if is_dark else "#FFFFFF"
        bg_input = "#1E1A26" if is_dark else "#EFEBF5"
        border_col = "#3E354A" if is_dark else "#D0C8DF"
        text_primary = "#EDE7F6" if is_dark else "#1C1921"
        text_secondary = "#C4B5FD" if is_dark else "#5D4B75"

        self.preset_title.color = text_secondary
        self.tunings_title.color = text_secondary

        self.preset_dropdown.bgcolor = bg_input
        self.preset_dropdown.border_color = border_col
        self.preset_dropdown.color = text_primary
        self.preset_dropdown.label_style = ft.TextStyle(color=text_secondary)

        self.auto_switch.label_text_style = ft.TextStyle(color=text_primary, weight=ft.FontWeight.W_600)

        self.preset_panel.bgcolor = bg_panel
        self.preset_panel.border = ft.Border.all(1, border_col)

        self.knobs_panel.bgcolor = bg_panel
        self.knobs_panel.border = ft.Border.all(1, border_col)

        self.timer_toggle_panel.bgcolor = bg_panel
        self.timer_toggle_panel.border = ft.Border.all(1, border_col)

        self.tunings_panel.bgcolor = bg_panel
        self.tunings_panel.border = ft.Border.all(1, border_col)

        self.sidebar_container.bgcolor = bg_sidebar
        self.sidebar_container.border = ft.Border.all(1, border_col)

        for config in self.string_configs:
            config["checkbox"].label_style = ft.TextStyle(color=text_primary)
            config["dropdown"].bgcolor = bg_input
            config["dropdown"].border_color = border_col
            config["dropdown"].color = text_primary
            if "row_container" in config:
                config["row_container"].bgcolor = bg_sidebar
                config["row_container"].border = ft.Border.all(1, border_col)

    def rebuild_string_controls(self, tunings: list[str] = None):
        self.string_configs.clear()
        self.strings_column.controls.clear()

        is_dark = self.theme_manager.is_dark()
        bg_sidebar = "#1A1721" if is_dark else "#F3F0F8"
        bg_input = "#1E1A26" if is_dark else "#EFEBF5"
        border_col = "#3E354A" if is_dark else "#D0C8DF"
        text_primary = "#EDE7F6" if is_dark else "#1C1921"
        text_secondary = "#B0A8C0" if is_dark else "#6E6280"

        notes = MusicTheory.get_notes()
        for i in range(1, int(self.num_strings) + 1):
            default_tuning = tunings[i - 1] if tunings and (i - 1) < len(tunings) else "E"
            if default_tuning not in notes:
                default_tuning = "E"

            chk = ft.Checkbox(
                value=True,
                label=f"Str {i}",
                fill_color=ft.Colors.AMBER_400,
                label_style=ft.TextStyle(color=text_primary),
                on_change=self.on_string_config_change,
            )
            dd = ft.Dropdown(
                options=[ft.DropdownOption(key=n, text=n) for n in notes],
                value=default_tuning,
                width=80,
                dense=True,
                bgcolor=bg_input,
                border_color=border_col,
                color=text_primary,
            )
            dd.on_change = self.on_string_config_change

            row_cont = ft.Container(
                content=ft.Row(
                    controls=[chk, ft.Text("Tuning:", color=text_secondary), dd],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                bgcolor=bg_sidebar,
                border_radius=8,
                border=ft.Border.all(1, border_col),
            )

            config = {
                "string_num": i,
                "checkbox": chk,
                "dropdown": dd,
                "row_container": row_cont,
            }
            self.string_configs.append(config)
            self.strings_column.controls.append(row_cont)

    def on_preset_change(self, e):
        preset_name = e.control.value if (e and hasattr(e, "control") and e.control and e.control.value) else self.preset_dropdown.value
        if preset_name and preset_name != "Custom":
            self.apply_preset(preset_name)

    def apply_preset(self, preset_name: str):
        self.preset_dropdown.value = preset_name
        tunings = MusicTheory.get_preset_tuning(preset_name)
        if tunings:
            self.num_strings = len(tunings)
            self.string_count_knob.set_value(self.num_strings)
            self.rebuild_string_controls(tunings)
            self.generate_next_note()
            if self.page:
                self.page.update()

    def on_string_count_knob_change(self, val: int):
        self.num_strings = val
        self.preset_dropdown.value = "Custom"
        self.rebuild_string_controls()
        self.generate_next_note()
        if self.page:
            self.page.update()

    def on_string_config_change(self, e):
        self.preset_dropdown.value = "Custom"
        self.generate_next_note()
        if self.page:
            self.page.update()

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
