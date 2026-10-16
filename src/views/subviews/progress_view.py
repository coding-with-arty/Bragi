"""
src/views/subviews/progress_view.py
====================================
Gamified Progress & Analytics View featuring interactive chromatic note mastery cards,
rank progression, daily practice quest tracking, and achievement badge unlock gallery.
"""

from typing import Optional, Dict, List
import flet as ft
from storage.progress_repository import ProgressRepository
from utils.theme_manager import ThemeManager
from utils.music_theory import CHROMATIC_SHARPS

ElevatedBtn = getattr(ft, "ElevatedButton", None) or getattr(ft, "FilledButton", None) or getattr(ft, "Button", ft.TextButton)
TextBtn = getattr(ft, "TextButton", None) or getattr(ft, "Button", ft.Container)


class NoteDetailDialog(ft.AlertDialog):
    """Modal displaying deep analytics and response speed metrics for a single pitch class."""

    def __init__(self, note_name: str, mastery_info: dict, theme_manager: Optional[ThemeManager] = None):
        self.note_name = note_name
        self.theme_manager = theme_manager

        attempts = mastery_info.get("attempts_count", 0)
        successes = mastery_info.get("success_count", 0)
        accuracy = mastery_info.get("accuracy_percentage", 0.0)
        avg_speed = mastery_info.get("avg_response_time_sec", 0.0)
        tier = mastery_info.get("tier", "UNRANKED")

        tier_colors = {
            "PLATINUM": ft.Colors.CYAN_300,
            "GOLD": ft.Colors.AMBER_400,
            "SILVER": ft.Colors.GREY_300,
            "BRONZE": ft.Colors.ORANGE_400,
            "UNRANKED": ft.Colors.GREY_600,
        }
        color = tier_colors.get(str(tier).upper(), ft.Colors.GREY_500)

        title = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text(note_name, size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                    bgcolor=color,
                    shape=ft.BoxShape.CIRCLE,
                    width=42,
                    height=42,
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Column(
                    spacing=2,
                    controls=[
                        ft.Text(f"{note_name} Note Mastery", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Tier Status: {tier}", size=12, color=color, weight=ft.FontWeight.BOLD),
                    ],
                ),
            ],
            spacing=12,
        )

        content = ft.Container(
            width=360,
            content=ft.Column(
                tight=True,
                spacing=12,
                controls=[
                    ft.Divider(height=1, color=ft.Colors.GREY_800),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_AROUND,
                        controls=[
                            self._build_metric_box("Accuracy", f"{accuracy:.1f}%", ft.Icons.SPEED_ROUNDED, ft.Colors.CYAN_400),
                            self._build_metric_box("Avg Speed", f"{avg_speed:.2f}s" if avg_speed > 0 else "--", ft.Icons.TIMER_ROUNDED, ft.Colors.AMBER_400),
                        ],
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_AROUND,
                        controls=[
                            self._build_metric_box("Total Attempts", str(attempts), ft.Icons.REPEAT_ROUNDED, ft.Colors.PURPLE_300),
                            self._build_metric_box("Correct Plays", str(successes), ft.Icons.CHECK_CIRCLE_ROUNDED, ft.Colors.GREEN_400),
                        ],
                    ),
                    ft.Container(
                        content=ft.Text(
                            "Tier Requirements: Platinum requires >90% accuracy and <1.2s avg speed over 3+ attempts.",
                            size=11,
                            color=ft.Colors.GREY_400,
                            italic=True,
                        ),
                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                        border_radius=8,
                        padding=10,
                    ),
                ],
            ),
        )

        close_btn = TextBtn("Close", on_click=self._close)

        super().__init__(
            title=title,
            content=content,
            actions=[close_btn],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _build_metric_box(self, label: str, val: str, icon_data: str, icon_color: str) -> ft.Control:
        return ft.Container(
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
                controls=[
                    ft.Icon(icon_data, color=icon_color, size=18),
                    ft.Text(val, size=16, weight=ft.FontWeight.BOLD),
                    ft.Text(label, size=10, color=ft.Colors.GREY_400),
                ],
            ),
            bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
            border_radius=8,
            padding=10,
            width=150,
        )

    def _close(self, e=None) -> None:
        if self.page and hasattr(self.page, "close"):
            try:
                self.page.close(self)
                return
            except Exception:
                pass
        self.open = False
        if self.page:
            self.page.update()


class ProgressView(ft.Container):
    """Analytics & Gamification Hub featuring chromatic mastery matrix and badge gallery."""

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

        self.scroll_column = ft.Column(
            spacing=20,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.content = self.scroll_column

        self.selected_badge_filter = "All"
        self.refresh_stats()

    def refresh_stats(self) -> None:
        """Fetches live statistics and refreshes dashboard controls."""
        stats = self.repository.get_user_stats()

        if hasattr(self.repository, "get_detailed_note_mastery"):
            detailed_mastery = self.repository.get_detailed_note_mastery()
        else:
            detailed_mastery = {}

        challenges = self.repository.get_daily_challenges()
        badges = self.repository.get_achievements(category=self.selected_badge_filter)

        self.scroll_column.controls = [
            self._build_header_overview(stats),
            self._build_note_mastery_section(detailed_mastery),
            self._build_daily_challenges_section(challenges),
            self._build_achievements_section(badges),
        ]

        try:
            self.update()
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # 1. OVERVIEW STATS CARDS (Rank, Level Progress, Streaks)
    # -------------------------------------------------------------------------
    def _build_header_overview(self, stats: Dict) -> ft.Control:
        total_xp = stats.get("total_xp", 0)
        level = stats.get("current_level", 1)
        rank_title = stats.get("rank_title", "Fret Novice")
        streak = stats.get("current_streak", 0)
        best_streak = stats.get("best_streak", 0)
        accuracy = stats.get("accuracy_rate", 0.0)
        attempts = stats.get("total_attempts", 0)

        xp_in_level = total_xp % 500
        progress_pct = xp_in_level / 500.0

        level_card = self._create_stat_card(
            title=f"LEVEL {level} • {rank_title.upper()}",
            value=f"{total_xp} XP",
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

        streak_card = self._create_stat_card(
            title="PRACTICE STREAK",
            value=f"{streak} Day{'s' if streak != 1 else ''}",
            icon=ft.Icons.LOCAL_FIRE_DEPARTMENT_ROUNDED,
            icon_color=ft.Colors.ORANGE_400,
            subtitle_control=ft.Text(f"Personal Record: {best_streak} Days", size=11, color=ft.Colors.GREY_400),
        )

        acc_card = self._create_stat_card(
            title="PITCH ACCURACY",
            value=f"{accuracy:.1f}%",
            icon=ft.Icons.SPEED_ROUNDED,
            icon_color=ft.Colors.CYAN_400,
            subtitle_control=ft.Text(f"{attempts} Total Attempts Logged", size=11, color=ft.Colors.GREY_400),
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
    # 2. CHROMATIC NOTE MASTERY INTERACTIVE MATRIX
    # -------------------------------------------------------------------------
    def _build_note_mastery_section(self, detailed_mastery: Dict) -> ft.Control:
        items = []
        for note in CHROMATIC_SHARPS:
            m_info = detailed_mastery.get(note)
            if hasattr(m_info, "accuracy_percentage"):
                acc = m_info.accuracy_percentage
                tier_name = m_info.tier.value if hasattr(m_info.tier, "value") else str(m_info.tier)
                m_dict = {
                    "attempts_count": m_info.attempts_count,
                    "success_count": m_info.success_count,
                    "accuracy_percentage": m_info.accuracy_percentage,
                    "avg_response_time_sec": m_info.avg_response_time_sec,
                    "tier": tier_name,
                }
            else:
                acc = detailed_mastery.get(note, 0.0) if isinstance(detailed_mastery.get(note), float) else 0.0
                tier_name, _ = self._get_mastery_tier_legacy(acc)
                m_dict = {"accuracy_percentage": acc, "tier": tier_name}

            tier_str, tier_color = self._get_mastery_tier_legacy(acc)

            badge = ft.Container(
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=4,
                    controls=[
                        ft.Text(note, size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Container(
                            content=ft.Text(tier_str, size=9, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                            bgcolor=tier_color,
                            border_radius=4,
                            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                        ),
                        ft.Text(f"{acc:.0f}%", size=11, color=ft.Colors.GREY_300),
                    ],
                ),
                bgcolor=ft.Colors.with_opacity(0.18, "#1A1523"),
                border=ft.Border.all(1, ft.Colors.with_opacity(0.4, tier_color)),
                border_radius=10,
                padding=10,
                ink=True,
                data={"note": note, "info": m_dict},
                on_click=self._on_note_card_clicked,
            )
            items.append(ft.Container(badge, col={"xs": 4, "sm": 3, "md": 2}))

        return ft.Container(
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.START,
                spacing=10,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.GRID_VIEW_ROUNDED, color=ft.Colors.AMBER_400, size=20),
                                    ft.Text("Chromatic Note Mastery Matrix", size=16, weight=ft.FontWeight.BOLD),
                                ],
                                spacing=8,
                            ),
                            ft.Text("Click note card for details", size=11, color=ft.Colors.GREY_400),
                        ],
                    ),
                    ft.ResponsiveRow(controls=items, spacing=8, run_spacing=8),
                ],
            ),
            bgcolor=ft.Colors.with_opacity(0.25, "#130F1C"),
            border_radius=12,
            padding=14,
        )

    def _on_note_card_clicked(self, e) -> None:
        data = e.control.data
        note = data["note"]
        info = data["info"]

        dialog = NoteDetailDialog(note_name=note, mastery_info=info, theme_manager=self.theme_manager)
        if self.page:
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()

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
                            ft.Text("Daily Quests & Practice Challenges", size=16, weight=ft.FontWeight.BOLD),
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
                            content=ft.Icon(
                                ft.Icons.EMOJI_EVENTS_ROUNDED if unlocked else ft.Icons.LOCK_ROUNDED,
                                color=icon_color,
                                size=26,
                            ),
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

    def _get_mastery_tier_legacy(self, accuracy: float) -> tuple[str, str]:
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
