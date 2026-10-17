from enum import Enum
from dataclasses import dataclass
from typing import Tuple


class MasteryTier(Enum):
    PLATINUM = "Platinum"
    GOLD = "Gold"
    SILVER = "Silver"
    BRONZE = "Bronze"
    UNRANKED = "Unranked"


@dataclass(frozen=True)
class RewardResult:
    xp_earned: int
    new_total_xp: int
    current_level: int
    leveled_up: bool
    streak_count: int


class GamificationPolicy:
    """
    Central policy engine governing XP reward rules, level progression,
    and chromatic pitch mastery tier rankings.
    """

    XP_PER_LEVEL: int = 500
    BASE_CORRECT_XP: int = 20
    SPEED_BONUS_THRESHOLD_SEC: float = 2.0
    SPEED_BONUS_XP: int = 10

    @classmethod
    def calculate_level(cls, total_xp: int) -> int:
        """Calculates current user level from total XP using Level = floor(XP / 500) + 1."""
        return max(1, (total_xp // cls.XP_PER_LEVEL) + 1)

    @classmethod
    def calculate_reward(
        cls,
        is_correct: bool,
        response_time_sec: float,
        current_streak: int,
        current_total_xp: int
    ) -> RewardResult:
        """
        Calculates XP earned for an exercise attempt accounting for correctness,
        response speed, and active streak multipliers.
        """
        if not is_correct:
            return RewardResult(
                xp_earned=0,
                new_total_xp=current_total_xp,
                current_level=cls.calculate_level(current_total_xp),
                leveled_up=False,
                streak_count=0
            )

        # Base XP calculation
        xp = cls.BASE_CORRECT_XP

        # Speed bonus for rapid identification (< 2.0 seconds)
        if 0.0 < response_time_sec <= cls.SPEED_BONUS_THRESHOLD_SEC:
            xp += cls.SPEED_BONUS_XP

        # Streak multiplier bonus
        new_streak = current_streak + 1
        streak_bonus = min(20, (new_streak // 3) * 5)
        xp += streak_bonus

        new_total_xp = current_total_xp + xp
        old_level = cls.calculate_level(current_total_xp)
        new_level = cls.calculate_level(new_total_xp)

        return RewardResult(
            xp_earned=xp,
            new_total_xp=new_total_xp,
            current_level=new_level,
            leveled_up=(new_level > old_level),
            streak_count=new_streak
        )

    @classmethod
    def get_mastery_tier(cls, accuracy_pct: float, attempts_count: int) -> Tuple[MasteryTier, str]:
        """
        Determines chromatic note mastery tier from accuracy percentage and sample size.
        Returns tuple of (MasteryTier, HexColorCode).
        """
        if attempts_count < 3:
            return MasteryTier.UNRANKED, "#4A4255"

        if accuracy_pct >= 90.0:
            return MasteryTier.PLATINUM, "#E5E4E2"
        elif accuracy_pct >= 75.0:
            return MasteryTier.GOLD, "#FFD700"
        elif accuracy_pct >= 50.0:
            return MasteryTier.SILVER, "#C0C0C0"
        elif accuracy_pct > 0.0:
            return MasteryTier.BRONZE, "#CD7F32"

        return MasteryTier.UNRANKED, "#4A4255"
