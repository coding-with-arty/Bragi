"""
tuner_app.py - Standalone Tuner Control and Embeddable UI
"""

import json
import flet as ft

from src.audio.pitch_detector import PitchDetector, list_input_devices
from src.audio.audio_worker import AudioWorker, AudioWorkerConfig, ToneMatchStatement, PitchData


class TunerControl(ft.Container):
    """Embeddable tuner widget component."""

    def __init__(self, on_tone_evaluated=None, **kwargs):
        super().__init__(padding=20, border_radius=12, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, **kwargs)
        self.on_tone_evaluated = on_tone_evaluated

        self.detector = PitchDetector()
        self.worker = AudioWorker(
            pitch_detector=self.detector,
            config=AudioWorkerConfig(tolerance_cents=20.0, hold_duration_sec=0.25),
            on_pitch_update=self._handle_pitch_update,
            on_note_matched=self._handle_note_matched,
        )

        self.mic_dropdown = ft.Dropdown(
            label="Select Microphone",
            options=[],
            on_select=self._on_mic_selected,
            expand=True,
        )

        self.note_display = ft.Text("--", size=48, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE)
        self.cents_text = ft.Text("0 cents", size=18, color=ft.Colors.GREY_400)
        self.cents_progress = ft.ProgressBar(value=0.5, color=ft.Colors.AMBER, height=12)
        self.target_text = ft.Text("Target Note: A2", size=20, weight=ft.FontWeight.W_500)
        self.match_badge = ft.Text("Listening...", size=16, color=ft.Colors.GREY)
        self.output_log = ft.Text("Output JSON Statement will appear here...", size=12, selectable=True)

        # Updated ft.ElevatedButton -> ft.Button
        self.string_buttons = ft.Row([
            ft.Button("E2 (6)", on_click=lambda e: self.set_string_target(6, 0)),
            ft.Button("A2 (5)", on_click=lambda e: self.set_string_target(5, 0)),
            ft.Button("D3 (4)", on_click=lambda e: self.set_string_target(4, 0)),
            ft.Button("G3 (3)", on_click=lambda e: self.set_string_target(3, 0)),
            ft.Button("B3 (2)", on_click=lambda e: self.set_string_target(2, 0)),
            ft.Button("E4 (1)", on_click=lambda e: self.set_string_target(1, 0)),
        ], alignment=ft.MainAxisAlignment.CENTER, wrap=True)

        self.content = ft.Column([
            ft.Row([self.mic_dropdown], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(),
            ft.Column([
                self.target_text,
                self.note_display,
                self.cents_text,
                self.cents_progress,
                self.match_badge,
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Divider(),
            ft.Text("Select Target String:"),
            self.string_buttons,
            ft.Divider(),
            ft.Text("App Match Output Payload:"),
            ft.Container(
                content=self.output_log,
                bgcolor=ft.Colors.BLACK,
                padding=10,
                border_radius=6,
            )
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def did_mount(self):
        self.refresh_microphones()
        self.worker.set_target_note("A", 2)
        self.detector.start()
        self.worker.start()

    def will_unmount(self):
        self.worker.stop()
        self.detector.stop()

    def refresh_microphones(self):
        mics = list_input_devices()
        options = [
            ft.DropdownOption(key=str(m["index"]), text=f"{m['name']} (ID: {m['index']})")
            for m in mics
        ]
        self.mic_dropdown.options = options
        if mics:
            default_id = str(mics[0]["index"])
            self.mic_dropdown.value = default_id
            self.worker.set_input_device(int(default_id))
        self.update()

    def _on_mic_selected(self, e):
        if self.mic_dropdown.value:
            dev_id = int(self.mic_dropdown.value)
            self.worker.set_input_device(dev_id)

    def set_string_target(self, string_num: int, fret_num: int):
        self.worker.set_target_note_by_string_fret(string_num, fret_num)
        target = self.worker._target_note
        self.target_text.value = f"Target Note: {target.display_name}" if target else "Target Note: --"
        self.match_badge.value = "Listening..."
        self.match_badge.color = ft.Colors.GREY
        self.update()

    def _handle_pitch_update(self, data: PitchData):
        cents_normalized = max(0.0, min(1.0, (data.cents + 50.0) / 100.0))
        self.cents_progress.value = cents_normalized
        self.note_display.value = data.raw_pitch_str if not data.is_in_tune else f"{data.raw_pitch_str} ✓"
        self.cents_text.value = f"{data.cents:+.1f} cents | {data.frequency:.1f} Hz"

        if data.is_in_tune:
            self.note_display.color = ft.Colors.GREEN
            self.cents_progress.color = ft.Colors.GREEN
        else:
            self.note_display.color = ft.Colors.WHITE
            self.cents_progress.color = ft.Colors.AMBER

        self.update()

    def _handle_note_matched(self, statement: ToneMatchStatement):
        payload_dict = statement.to_dict()
        json_output = json.dumps(payload_dict, indent=2)

        self.match_badge.value = "MATCH CONFIRMED!"
        self.match_badge.color = ft.Colors.GREEN_ACCENT
        self.output_log.value = json_output
        self.update()

        if self.on_tone_evaluated:
            self.on_tone_evaluated(payload_dict)


def main(page: ft.Page):
    page.title = "Standalone Guitar Tuner"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 500
    page.window.height = 700

    tuner_component = TunerControl()
    page.add(tuner_component)


if __name__ == "__main__":
    ft.run(main)
