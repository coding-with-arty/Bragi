"""
src/views/subviews/progress_view.py
====================================
Analytics and Gamification View for tracking user progress, note mastery,
daily practice streaks, challenges, and achievement badges.
"""

from typing import Optional, Dict, List
import flet as ft
from storage.progress_repository import ProgressRepository
from utils.theme_manager import ThemeManager
from utils.music_theory import CHROMATIC_SHARPS


class ProgressView(ft.Container):
    """Analytics & Gamification View featuring mastery tiers, daily challenges, and achievement badges."""

    def __init__(
        self,
        repository: Optional[ProgressRepository] = None,
        theme_manager: Optional[ThemeManager] = None,
    ):
        super().__init__()
        self.repository = repository or ProgressRepository()
        self.theme_manager = theme_manager
        self.expand = True
        self.padding = ft.Padding.all(16)

        # Main Layout Column
        self.scroll_column = ft.Column(
            spacing=20,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.content = self.scroll_column

        # Active Category Filter for Badges
        self.selected_badge_filter = "All"

        self.refresh_stats()

    def refresh_stats(self) -> None:
        """Fetches latest data from repository with safe fallback method checks."""
        # 1. Fetch User Overall Stats
        stats = {}
        for method_name in ("get_user_stats", "get_stats", "get_user_progress", "get_summary"):
            if hasattr(self.repository, method_name):
                stats = getattr(self.repository, method_name)() or {}
                break

        # 2. Fetch Chromatic Note Mastery
        mastery = {}
        for method_name in ("get_note_mastery", "get_mastery", "get_note_accuracy"):
            if hasattr(self.repository, method_name):
                mastery = getattr(self.repository, method_name)() or {}
                break

        # 3. Fetch Daily Practice Challenges
        challenges = []
        for method_name in ("get_daily_challenges", "get_challenges", "get_daily_quests"):
            if hasattr(self.repository, method_name):
                challenges = getattr(self.repository, method_name)() or []
                break

        # 4. Fetch Achievements / Badges
        badges = []
        if hasattr(self.repository, "get_achievements"):
            try:
                badges = self.repository.get_achievements(category=self.selected_badge_filter) or []
            except TypeError:
                badges = self.repository.get_achievements() or []
        elif hasattr(self.repository, "get_badges"):
            badges = self.repository.get_badges() or []

        self.scroll_column.controls = [
            self._build_header_overview(stats),
            self._build_note_mastery_section(mastery),
            self._build_daily_challenges_section(challenges),
            self._build_achievements_section(badges),
        ]

        try:
            self.update()
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # 1. OVERVIEW STATS CARDS (XP, Level, Streak)
    # -------------------------------------------------------------------------
    def _build_header_overview(self, stats: Dict) -> ft.Control:
        total_xp = stats.get("total_xp", 0)
        streak = stats.get("current_streak", 0)
        best_streak = stats.get("best_streak", 0)

        level = (total_xp // 500) + 1
        xp_in_level = total_xp % 500
        progress_pct = xp_in_level / 500.0

        # Level Card
        level_card = self._create_stat_card(
            title=f"LEVEL {level}",
            value=f"{total_xp} Total XP",
            icon=ft.Icons.AUTO_AWESOME_ROUNDED,
            icon_color=ft.Colors.AMBER_400,
            subtitle_control=ft.Column(
                spacing=4,
                controls=[
                    ft.ProgressBar(value=progress_pct, color=ft.Colors.AMBER_400, height=6),
                    ft.Text(f"{xp_in_level} / 500 XP to Level {level + 1}", size=11, color=ft.Colors.GREY_400),
                ],
            ),
        )

        # Streak Card
        streak_card = self._create_stat_card(
            title="PRACTICE STREAK",
            value=f"{streak} Day{'s' if streak != 1 else ''}",
            icon=ft.Icons.LOCAL_FIRE_DEPARTMENT_ROUNDED,
            icon_color=ft.Colors.ORANGE_400,
            subtitle_control=ft.Text(f"Personal Best: {best_streak} Days", size=11, color=ft.Colors.GREY_400),
        )

        # Accuracy Card
        attempts = stats.get("total_attempts", 0)
        accuracy = stats.get("accuracy_rate", 0.0)
        acc_card = self._create_stat_card(
            title="PITCH ACCURACY",
            value=f"{accuracy:.1f}%",
            icon=ft.Icons.SPEED_ROUNDED,
            icon_color=ft.Colors.CYAN_400,
            subtitle_control=ft.Text(f"{attempts} Total Attempts", size=11, color=ft.Colors.GREY_400),
        )

        return ft.ResponsiveRow(
            controls=[
                ft.Container(level_card, col={"sm": 12, "md": 4}),
                ft.Container(streak_card, col={"sm": 12, "md": 4}),
                ft.Container(acc_card, col={"sm": 12, "md": 4}),
            ],
            spacing=12,
        )

    # -------------------------------------------------------------------------
    # 2. CHROMATIC NOTE MASTERY TIERS
    # -------------------------------------------------------------------------
    def _build_note_mastery_section(self, mastery: Dict[str, float]) -> ft.Control:
        items = []
        for note in CHROMATIC_SHARPS:
            acc = mastery.get(note, 0.0)
            tier_name, tier_color = self._get_mastery_tier(acc)

            badge = ft.Container(
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=4,
                    controls=[
                        ft.Text(note, size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Container(
                            content=ft.Text(tier_name, size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                            bgcolor=tier_color,
                            border_radius=4,
                            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                        ),
                        ft.Text(f"{acc:.0f}%", size=11, color=ft.Colors.GREY_300),
                    ],
                ),
                bgcolor=ft.Colors.with_opacity(0.18, "#1A1523"),
                border=ft.Border.all(1, ft.Colors.with_opacity(0.3, tier_color)),
                border_radius=10,
                padding=10,
            )
            items.append(ft.Container(badge, col={"xs": 4, "sm": 3, "md": 2}))

        return ft.Container(
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.START,
                spacing=10,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.GOLF_COURSE_ROUNDED, color=ft.Colors.AMBER_400, size=20),
                            ft.Text("Chromatic Note Mastery", size=16, weight=ft.FontWeight.BOLD),
                        ],
                        spacing=8,
                    ),
                    ft.ResponsiveRow(controls=items, spacing=8, run_spacing=8),
                ],
            ),
            bgcolor=ft.Colors.with_opacity(0.25, "#130F1C"),
            border_radius=12,
            padding=14,
        )

    # -------------------------------------------------------------------------
    # 3. DAILY PRACTICE CHALLENGES
    # -------------------------------------------------------------------------
    def _build_daily_challenges_section(self, challenges: List[Dict]) -> ft.Control:
        cards = []
        for c in challenges:
            is_done = c.get("completed", False)
            prog = c.get("progress", 0)
            target = c.get("target", 10)
            pct = min(1.0, prog / max(1, target))

            card = ft.Container(
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(
                                    ft.Icons.CHECK_CIRCLE_ROUNDED if is_done else ft.Icons.RADIO_BUTTON_UNCHECKED_ROUNDED,
                                    color=ft.Colors.GREEN_400 if is_done else ft.Colors.GREY_500,
                                    size=22,
                                ),
                                ft.Column(
                                    spacing=2,
                                    controls=[
                                        ft.Text(
                                            c.get("title", "Daily Quest"),
                                            weight=ft.FontWeight.BOLD,
                                            size=13,
                                            style=ft.TextStyle(
                                                decoration=ft.TextDecoration.LINE_THROUGH if is_done else None
                                            ),
                                        ),
                                        ft.Text(c.get("description", ""), size=11, color=ft.Colors.GREY_400),
                                    ],
                                ),
                            ],
                            spacing=10,
                        ),
                        ft.Row(
                            controls=[
                                ft.Container(
                                    width=80,
                                    content=ft.ProgressBar(value=pct, color=ft.Colors.AMBER_400, height=6),
                                ),
                                ft.Text(f"+{c.get('xp_reward', 50)} XP", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400),
                            ],
                            spacing=10,
                        ),
                    ],
                ),
                bgcolor=ft.Colors.with_opacity(0.12, "#1A1523"),
                border_radius=8,
                padding=10,
            )
            cards.append(card)

        return ft.Container(
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.START,
                spacing=10,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.TASK_ALT_ROUNDED, color=ft.Colors.AMBER_400, size=20),
                            ft.Text("Daily Challenges", size=16, weight=ft.FontWeight.BOLD),
                        ],
                        spacing=8,
                    ),
                    ft.Column(controls=cards, spacing=8),
                ],
            ),
            bgcolor=ft.Colors.with_opacity(0.25, "#130F1C"),
            border_radius=12,
            padding=14,
        )

    # -------------------------------------------------------------------------
    # 4. ACHIEVEMENT BADGES
    # -------------------------------------------------------------------------
    def _build_achievements_section(self, badges: List[Dict]) -> ft.Control:
        badge_cards = []
        for b in badges:
            unlocked = b.get("unlocked", False)
            icon_color = ft.Colors.AMBER_400 if unlocked else ft.Colors.GREY_600

            card = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Icon(ft.Icons.EMOJI_EVENTS_ROUNDED, color=icon_color, size=28),
                            padding=8,
                            bgcolor=ft.Colors.with_opacity(0.1, icon_color),
                            border_radius=20,
                        ),
                        ft.Column(
                            spacing=2,
                            expand=True,
                            controls=[
                                ft.Text(b.get("title", "Achievement"), weight=ft.FontWeight.BOLD, size=13),
                                ft.Text(b.get("description", ""), size=11, color=ft.Colors.GREY_400),
                            ],
                        ),
                    ],
                    spacing=10,
                ),
                bgcolor=ft.Colors.with_opacity(0.15 if unlocked else 0.05, "#1A1523"),
                border=ft.Border.all(1, ft.Colors.AMBER_400 if unlocked else ft.Colors.with_opacity(0.2, "#3E354A")),
                border_radius=10,
                padding=10,
            )
            badge_cards.append(ft.Container(card, col={"sm": 12, "md": 6}))

        categories = ["All", "Trainer", "Ear Training", "Streaks"]
        filter_pills = []
        for cat in categories:
            active = cat == self.selected_badge_filter
            pill = ft.Container(
                content=ft.Text(
                    cat,
                    size=11,
                    weight=ft.FontWeight.BOLD if active else ft.FontWeight.NORMAL,
                    color=ft.Colors.BLACK if active else ft.Colors.WHITE,
                ),
                bgcolor=ft.Colors.AMBER_400 if active else ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
                border_radius=6,
                padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                ink=True,
                data=cat,
                on_click=self._on_filter_changed,
            )
            filter_pills.append(pill)

        return ft.Container(
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.START,
                spacing=12,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.MILITARY_TECH_ROUNDED, color=ft.Colors.AMBER_400, size=20),
                                    ft.Text("Achievement Badges", size=16, weight=ft.FontWeight.BOLD),
                                ],
                                spacing=8,
                            ),
                            ft.Row(controls=filter_pills, spacing=6),
                        ],
                    ),
                    ft.ResponsiveRow(controls=badge_cards, spacing=10, run_spacing=10),
                ],
            ),
            bgcolor=ft.Colors.with_opacity(0.25, "#130F1C"),
            border_radius=12,
            padding=14,
        )

    # -------------------------------------------------------------------------
    # UTILITIES
    # -------------------------------------------------------------------------
    def _create_stat_card(
        self, title: str, value: str, icon: str, icon_color: str, subtitle_control: ft.Control
    ) -> ft.Control:
        return ft.Container(
            content=ft.Column(
                spacing=6,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(title, size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_400),
                            ft.Icon(icon, color=icon_color, size=20),
                        ],
                    ),
                    ft.Text(value, size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    subtitle_control,
                ],
            ),
            bgcolor=ft.Colors.with_opacity(0.30, "#130F1C"),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.2, "#3E354A")),
            border_radius=12,
            padding=14,
        )

    def _get_mastery_tier(self, accuracy: float) -> tuple[str, str]:
        if accuracy >= 90:
            return "PLATINUM", "#E5E4E2"
        elif accuracy >= 75:
            return "GOLD", "#FFD700"
        elif accuracy >= 50:
            return "SILVER", "#C0C0C0"
        elif accuracy > 0:
            return "BRONZE", "#CD7F32"
        return "UNRANKED", "#4A4255"

    def _on_filter_changed(self, e) -> None:
        self.selected_badge_filter = e.control.data
        self.refresh_stats()
