import flet as ft

class GuitarKnob(ft.Container):
    """
    A custom Flet control modeled after a vintage guitar volume/tone knob.
    Features a dark pastel metallic dome aesthetic with - and + increment buttons.
    """
    def __init__(
        self,
        label: str,
        min_val: int = 1,
        max_val: int = 10,
        initial_val: int = 3,
        unit: str = "",
        on_change = None,
    ):
        super().__init__()
        self.label_str = label
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.unit = unit
        self.on_change = on_change

        # Central value readout
        self.value_text = ft.Text(
            f"{self.value}{self.unit}",
            size=22,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.AMBER_300,
        )

        # Top dial marker notch
        self.dial_marker = ft.Container(
            width=4,
            height=8,
            border_radius=2,
            bgcolor=ft.Colors.AMBER_400,
        )

        # Knob Dome Face
        self.knob_face = ft.Container(
            width=92,
            height=92,
            shape=ft.BoxShape.CIRCLE,
            bgcolor="#1A1721",
            border=ft.Border.all(3.5, "#4E4162"),
            shadow=ft.BoxShadow(
                blur_radius=14,
                spread_radius=1,
                color=ft.Colors.with_opacity(0.5, "#000000"),
            ),
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2,
                controls=[
                    self.dial_marker,
                    self.value_text,
                ],
            ),
        )

        # Decrement Button (- Stomp / Pickup style button)
        self.dec_button = ft.Container(
            content=ft.Icon(ft.Icons.REMOVE_ROUNDED, size=20, color="#E2D8EE"),
            width=38,
            height=38,
            shape=ft.BoxShape.CIRCLE,
            bgcolor="#2E2838",
            border=ft.Border.all(1.5, "#5C4E72"),
            alignment=ft.Alignment.CENTER,
            on_click=self._decrement,
            ink=True,
            tooltip=f"Decrease {label}",
        )

        # Increment Button (+ Stomp / Pickup style button)
        self.inc_button = ft.Container(
            content=ft.Icon(ft.Icons.ADD_ROUNDED, size=20, color="#E2D8EE"),
            width=38,
            height=38,
            shape=ft.BoxShape.CIRCLE,
            bgcolor="#2E2838",
            border=ft.Border.all(1.5, "#5C4E72"),
            alignment=ft.Alignment.CENTER,
            on_click=self._increment,
            ink=True,
            tooltip=f"Increase {label}",
        )

        # Overall Knob Layout
        self.content = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            controls=[
                ft.Text(
                    self.label_str.upper(),
                    size=12,
                    weight=ft.FontWeight.W_700,
                    color="#C4B5FD",
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12,
                    controls=[
                        self.dec_button,
                        self.knob_face,
                        self.inc_button,
                    ],
                ),
            ],
        )

    def _decrement(self, e):
        if self.value > self.min_val:
            self.value -= 1
            self.value_text.value = f"{self.value}{self.unit}"
            self.update()
            if self.on_change:
                self.on_change(self.value)

    def _increment(self, e):
        if self.value < self.max_val:
            self.value += 1
            self.value_text.value = f"{self.value}{self.unit}"
            self.update()
            if self.on_change:
                self.on_change(self.value)

    def set_value(self, new_val: int):
        self.value = max(self.min_val, min(self.max_val, int(new_val)))
        self.value_text.value = f"{self.value}{self.unit}"
        if self.page:
            self.update()
