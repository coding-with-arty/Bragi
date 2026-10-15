# src/views/subviews/progress_view.py
from typing import Optional, List
import flet as ft
from storage.progress_repository import ProgressRepository
from engine.gamification import GamificationEngine
from models.progress import MasteryTier, Achievement
from utils.theme_manager import ThemeManager


class ProgressView(ft.Column):
    """Achievement-driven Analytics and Gamification Hub."""

    TIER_COLORS = {
        MasteryTier.UNRANKED: ft.Colors.GREY_700,
        MasteryTier.BRONZE: "#CD7F32",
        MasteryTier.SILVER: "#C0C0C0",
        MasteryTier.GOLD: "#FFD700",
        MasteryTier.PLATINUM: "#E5E4E2",
    }

    def __init__(self, repository: ProgressRepository, theme_manager: Optional[ThemeManager] = None):
        super().__init__()
        self.repository = repository
        self.gamification = GamificationEngine(self.repository)
        self.theme_manager = theme_manager
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO
        self.active_category_filter = "All"

        # Header Title
        self.title_text = ft.Text("ACHIEVEMENTS & MASTERY HUB", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400)

        # Profile Summary Header Card
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

        # Dynamic Challenges Section
        self.challenges_column = ft.Column(spacing=10)

        # 12 Chromatic Pitch Class Mastery Matrix
        self.mastery_grid = ft.Row(wrap=True, spacing=10, alignment=ft.MainAxisAlignment.START)

        # Achievement Filter Tabs / Chips
        self.category_chips = ft.Row(
            spacing=8,
            controls=[
                ft.Chip(
                    label=ft.Text(cat),
                    selected=(cat == self.active_category_filter),
                    on_select=lambda e, c=cat: self._filter_achievements(c)
                )
                for cat in ["All", "Memorization", "Accuracy", "Speed", "Ear Training"]
            ]
        )

        # Achievement Cards Grid
        self.achievements_grid = ft.Row(wrap=True, spacing=10)

        self.controls = [
            ft.Container(content=self.title_text, padding=16),
            self.profile_card,
            ft.Container(height=12),
            ft.Text("ACTIVE PRACTICE CHALLENGES", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_300),
            self.challenges_column,
            ft.Container(height=16),
            ft.Text("FRETBOARD CHROMATIC MEMORIZATION MATRIX", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_300),
            ft.Text("Rank up notes by maintaining >85% accuracy and fast response speed.", size=12, color=ft.Colors.GREY_400),
            ft.Container(height=6),
            self.mastery_grid,
            ft.Container(height=16),
            ft.Text("MILESTONE BADGES & ACHIEVEMENTS", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_300),
            self.category_chips,
            ft.Container(height=8),
            self.achievements_grid,
            ft.Container(height=24),
        ]

    def did_mount(self):
        self.refresh_stats()

    def _filter_achievements(self, category: str):
        self.active_category_filter = category
        for chip in self.category_chips.controls:
            chip.selected = (chip.label.value == category)
        self.refresh_stats()

    def refresh_stats(self):
        """Refreshes XP level, active challenges, memorization tiers, and badge grids."""
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

        # 1. Active Challenges Render
        challenges = self.gamification.get_active_challenges()
        ch_controls = []
        for ch in challenges:
            ch_card = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(
                            ft.Icons.CHECK_CIRCLE if ch.is_completed else ft.Icons.DRAG_HANDLE,
                            color=ft.Colors.GREEN_400 if ch.is_completed else ft.Colors.AMBER_400,
                            size=26
                        ),
                        ft.Column(
                            controls=[
                                ft.Text(ch.title, weight=ft.FontWeight.BOLD, size=13),
                                ft.Text(ch.description, size=11, color=ft.Colors.GREY_400),
                                ft.ProgressBar(value=ch.current_count / float(ch.target_count), width=200, color=ft.Colors.AMBER_400),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ft.Text(f"+{ch.xp_reward} XP", weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_300)
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                padding=12,
                border_radius=10,
                bgcolor="#231F2D",
                border=ft.Border.all(1, "#3E354A"),
            )
            ch_controls.append(ch_card)
        self.challenges_column.controls = ch_controls

        # 2. Chromatic Memorization Matrix Render
        mastery_map = self.repository.get_chromatic_mastery()
        m_controls = []
        for note, stats in mastery_map.items():
            tier_color = self.TIER_COLORS[stats.tier]
            card = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(note, size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Text(f"{stats.tier.value.upper()}", size=10, weight=ft.FontWeight.BOLD, color=tier_color),
                        ft.Text(f"{stats.accuracy_percentage}% | {stats.avg_response_time_sec}s", size=10, color=ft.Colors.GREY_400),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=2,
                ),
                padding=10,
                border_radius=10,
                bgcolor="#231F2D",
                border=ft.Border.all(2, tier_color),
                width=100,
                alignment=ft.Alignment.CENTER,
            )
            m_controls.append(card)
        self.mastery_grid.controls = m_controls

        # 3. Filtered Achievement Badges Render
        achievements = self.repository.get_achievements()
        filtered = [
            a for a in achievements
            if self.active_category_filter == "All" or a.category == self.active_category_filter
        ]

        badge_controls = []
        for ach in filtered:
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
            badge_controls.append(card)

        self.achievements_grid.controls = badge_controls

        try:
            self.update()
        except RuntimeError:
            pass
