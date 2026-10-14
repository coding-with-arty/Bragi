"""
src/views/subviews/progress_view.py
===================================
Analytics dashboard displaying practice stats, accuracy metrics, and recent activity history.
"""

from typing import Optional
import flet as ft
from storage.progress_repository import ProgressRepository
from utils.theme_manager import ThemeManager


class ProgressView(ft.Column):
    """Analytics dashboard presenting user practice statistics."""

    def __init__(self, repository: ProgressRepository, theme_manager: Optional[ThemeManager] = None):
        super().__init__()
        self.repository = repository
        self.theme_manager = theme_manager
        self.expand = True

        self.title_text = ft.Text("PRACTICE ANALYTICS & HISTORY", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400)

        # Summary Metric Cards
        self.total_attempts_card = self._create_metric_card("Total Attempts", "0")
        self.accuracy_card = self._create_metric_card("Overall Accuracy", "0.0%")
        self.latency_card = self._create_metric_card("Avg Latency", "0.0s")

        self.metrics_row = ft.Row(
            controls=[self.total_attempts_card, self.accuracy_card, self.latency_card],
            alignment=ft.MainAxisAlignment.SPACE_EVENLY
        )

        self.history_listview = ft.ListView(
            expand=True,
            spacing=8,
            padding=10
        )

        self.controls = [
            ft.Container(content=self.title_text, padding=16),
            self.metrics_row,
            ft.Container(height=16),
            ft.Text("RECENT ATTEMPTS", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_300),
            ft.Container(
                content=self.history_listview,
                expand=True,
                padding=10,
                border=ft.Border.all(1, "#3E354A"),
                border_radius=12,
                bgcolor="#231F2D"
            )
        ]

    def did_mount(self):
        self.refresh_stats()

    def refresh_stats(self):
        """Queries repository and updates analytics visual widgets."""
        attempts = self.repository.get_recent_attempts(limit=50)

        total = len(attempts)
        successful = sum(1 for a in attempts if a.is_success)
        accuracy = (successful / total * 100.0) if total > 0 else 0.0

        latencies = [a.response_time_sec for a in attempts if a.is_success]
        avg_latency = (sum(latencies) / len(latencies)) if latencies else 0.0

        self.total_attempts_card.content.controls[1].value = str(total)
        self.accuracy_card.content.controls[1].value = f"{accuracy:.1f}%"
        self.latency_card.content.controls[1].value = f"{avg_latency:.2f}s"

        history_controls = []
        for att in attempts:
            status_icon = ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_400) if att.is_success else ft.Icon(ft.Icons.CANCEL, color=ft.Colors.RED_400)
            item = ft.ListTile(
                leading=status_icon,
                title=ft.Text(f"{att.target_name} ({att.target_type.upper()})", weight=ft.FontWeight.BOLD),
                subtitle=ft.Text(f"Response Time: {att.response_time_sec:.2f}s | Error: {att.cents_error:.1f}c"),
            )
            history_controls.append(item)

        self.history_listview.controls = history_controls
        if self.page:
            self.page.update()

    def _create_metric_card(self, title: str, initial_val: str) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(title, size=12, color=ft.Colors.GREY_400),
                    ft.Text(initial_val, size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=16,
            border_radius=12,
            bgcolor="#231F2D",
            border=ft.Border.all(1, "#3E354A"),
            width=180
        )
