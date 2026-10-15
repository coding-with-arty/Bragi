# src/views/subviews/progress_view.py
from typing import Optional
import flet as ft
from storage.progress_repository import ProgressRepository
from engine.gamification import GamificationEngine
from utils.theme_manager import ThemeManager


class ProgressView(ft.Column):
    """Analytics and gamification dashboard presenting user level, streak, weak notes, and achievements."""

    def __init__(self, repository: ProgressRepository, theme_manager: Optional[ThemeManager] = None):
        super().__init__()
        self.repository = repository
        self.gamification = GamificationEngine(self.repository)
        self.theme_manager = theme_manager
        self.expand = True

        self.title_text = ft.Text("PROGRESS & GAMIFICATION DASHBOARD", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400)

        # Profile Summary Card
        self.level_text = ft.Text("Level 1", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400)
        self.xp_text = ft.Text("0 / 50 XP", size=13, color=ft.Colors.GREY_400)
        self.streak_text = ft.Text("0 🔥", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_300)

        self.xp_progress_bar = ft.ProgressBar(
            value=0.0,
            width=320,
            color=ft.Colors.AMBER_500,
            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.GREY),
        )

        self.profile_card = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            self.level_text,
                            self.xp_progress_bar,
                            self.xp_text,
                        ],
                        spacing=6,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text("DAILY STREAK", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_400),
                            self.streak_text,
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=20,
            border_radius=14,
            bgcolor="#231F2D",
            border=ft.Border.all(1, "#3E354A"),
        )

        # Metric Cards
        self.total_attempts_card = self._create_metric_card("Total Attempts", "0")
        self.accuracy_card = self._create_metric_card("Overall Accuracy", "0.0%")
        self.latency_card = self._create_metric_card("Avg Response Time", "0.0s")

        self.metrics_row = ft.Row(
            controls=[self.total_attempts_card, self.accuracy_card, self.latency_card],
            alignment=ft.MainAxisAlignment.SPACE_EVENLY
        )

        # Strongest and Weakest Note Breakdown Chips
        self.strong_weak_row = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
            controls=[]
        )

        # Achievements Grid
        self.achievements_row = ft.Row(
            spacing=10,
            wrap=True,
            controls=[]
        )

        # History List
        self.history_listview = ft.ListView(
            expand=True,
            spacing=8,
            padding=10
        )

        self.controls = [
            ft.Container(content=self.title_text, padding=16),
            self.profile_card,
            ft.Container(height=12),
            self.metrics_row,
            ft.Container(height=16),
            ft.Text("STRONG & WEAK NOTE MASTERY", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_300),
            self.strong_weak_row,
            ft.Container(height=16),
            ft.Text("UNLOCKED BADGES & ACHIEVEMENTS", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_300),
            self.achievements_row,
            ft.Container(height=16),
            ft.Text("RECENT PRACTICE HISTORY", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_300),
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
        profile = self.repository.get_profile()
        curr_lvl = profile.current_level
        min_xp = self.gamification.xp_for_level(curr_lvl)
        next_xp = self.gamification.xp_for_level(curr_lvl + 1)
        needed = max(1, next_xp - min_xp)
        gained = profile.current_xp - min_xp
        progress = max(0.0, min(1.0, gained / float(needed)))

        self.level_text.value = f"Level {curr_lvl}"
        self.xp_text.value = f"{profile.current_xp} / {next_xp} XP"
        self.xp_progress_bar.value = progress
        self.streak_text.value = f"{profile.current_streak} Days 🔥"

        # Attempt statistics calculation
        attempts = self.repository.get_recent_attempts(limit=100)
        total = len(attempts)
        successful = sum(1 for a in attempts if a.is_success)
        accuracy = (successful / total * 100.0) if total > 0 else 0.0

        latencies = [a.response_time_sec for a in attempts if a.is_success]
        avg_latency = (sum(latencies) / len(latencies)) if latencies else 0.0

        self.total_attempts_card.content.controls[1].value = str(total)
        self.accuracy_card.content.controls[1].value = f"{accuracy:.1f}%"
        self.latency_card.content.controls[1].value = f"{avg_latency:.2f}s"

        # Strongest and Weakest Note Breakdown Chips
        strongest, weakest = self.repository.get_pitch_accuracies()

        strong_chips = [
            ft.Chip(label=ft.Text(f"💪 {s.note_name}: {s.accuracy_percentage}%"), bgcolor=ft.Colors.GREEN_900)
            for s in strongest
        ]
        weak_chips = [
            ft.Chip(label=ft.Text(f"🎯 {w.note_name}: {w.accuracy_percentage}%"), bgcolor=ft.Colors.RED_900)
            for w in weakest
        ]

        self.strong_weak_row.controls = [
            ft.Column(controls=[ft.Text("Strongest Notes", size=12, color=ft.Colors.GREY_400)] + strong_chips),
            ft.Column(controls=[ft.Text("Weakest Notes to Practice", size=12, color=ft.Colors.GREY_400)] + weak_chips),
        ]

        # Render Achievements
        achievements = self.repository.get_achievements()
        ach_controls = []
        for ach in achievements:
            col = ft.Colors.AMBER_400 if ach.unlocked else ft.Colors.GREY_700
            bg = "#312B3D" if ach.unlocked else "#1E1A26"
            card = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.EMOJI_EVENTS, color=col, size=24),
                        ft.Column(
                            controls=[
                                ft.Text(ach.title, size=13, weight=ft.FontWeight.BOLD, color=col),
                                ft.Text(ach.description, size=11, color=ft.Colors.GREY_400),
                            ],
                            spacing=2,
                        ),
                    ],
                    spacing=10,
                ),
                padding=10,
                border_radius=10,
                bgcolor=bg,
                border=ft.Border.all(1, col if ach.unlocked else "#3E354A"),
                width=240,
            )
            ach_controls.append(card)

        self.achievements_row.controls = ach_controls

        # Render Recent History
        history_controls = []
        for att in attempts[:20]:
            status_icon = ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_400) if att.is_success else ft.Icon(ft.Icons.CANCEL, color=ft.Colors.RED_400)
            item = ft.ListTile(
                leading=status_icon,
                title=ft.Text(f"{att.target_name} ({att.target_type.upper()})", weight=ft.FontWeight.BOLD),
                subtitle=ft.Text(f"Response Time: {att.response_time_sec:.2f}s | Cents Error: {att.cents_error:.1f}c"),
            )
            history_controls.append(item)

        self.history_listview.controls = history_controls

        try:
            self.update()
        except RuntimeError:
            pass

    def _create_metric_card(self, title: str, initial_val: str) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(title, size=12, color=ft.Colors.GREY_400),
                    ft.Text(initial_val, size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=14,
            border_radius=12,
            bgcolor="#231F2D",
            border=ft.Border.all(1, "#3E354A"),
            width=180
        )
