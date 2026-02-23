"""Compliance Gamification Engine models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class BadgeType(str, Enum):
    COMPLIANCE_CHAMPION = "compliance_champion"
    FIRST_FIX = "first_fix"
    STREAK_7 = "streak_7"
    STREAK_30 = "streak_30"
    FRAMEWORK_MASTER = "framework_master"
    ZERO_VIOLATIONS = "zero_violations"
    TEAM_LEADER = "team_leader"
    EARLY_ADOPTER = "early_adopter"


class AchievementTier(str, Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


@dataclass
class UserProfile:
    id: UUID = field(default_factory=uuid4)
    user_id: str = ""
    display_name: str = ""
    points: int = 0
    level: int = 1
    badges: list[str] = field(default_factory=list)
    current_streak: int = 0
    longest_streak: int = 0
    fixes_count: int = 0
    violations_resolved: int = 0
    joined_at: datetime | None = None


@dataclass
class Achievement:
    badge_type: BadgeType = BadgeType.FIRST_FIX
    tier: AchievementTier = AchievementTier.BRONZE
    name: str = ""
    description: str = ""
    icon: str = ""
    points_required: int = 0
    criteria: str = ""


@dataclass
class LeaderboardEntry:
    rank: int = 0
    user_id: str = ""
    display_name: str = ""
    points: int = 0
    level: int = 1
    badges_count: int = 0


@dataclass
class GamificationStats:
    total_users: int = 0
    total_points_awarded: int = 0
    total_badges_awarded: int = 0
    by_level: dict[int, int] = field(default_factory=dict)
    by_badge: dict[str, int] = field(default_factory=dict)
    avg_points: float = 0.0
