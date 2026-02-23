"""Compliance Gamification Engine Service."""

from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.gamification_engine.models import (
    Achievement,
    AchievementTier,
    BadgeType,
    GamificationStats,
    LeaderboardEntry,
    UserProfile,
)


logger = structlog.get_logger()

_ACHIEVEMENTS: list[Achievement] = [
    Achievement(
        badge_type=BadgeType.FIRST_FIX,
        tier=AchievementTier.BRONZE,
        name="First Fix",
        description="Resolved your first compliance violation",
        icon="🔧",
        points_required=10,
        criteria="fixes_count >= 1",
    ),
    Achievement(
        badge_type=BadgeType.STREAK_7,
        tier=AchievementTier.SILVER,
        name="Week Warrior",
        description="Maintained a 7-day compliance activity streak",
        icon="🔥",
        points_required=100,
        criteria="current_streak >= 7",
    ),
    Achievement(
        badge_type=BadgeType.STREAK_30,
        tier=AchievementTier.GOLD,
        name="Monthly Master",
        description="Maintained a 30-day compliance activity streak",
        icon="⚡",
        points_required=500,
        criteria="current_streak >= 30",
    ),
    Achievement(
        badge_type=BadgeType.COMPLIANCE_CHAMPION,
        tier=AchievementTier.PLATINUM,
        name="Compliance Champion",
        description="Resolved 50+ violations and maintained exemplary compliance",
        icon="🏆",
        points_required=1000,
        criteria="violations_resolved >= 50",
    ),
    Achievement(
        badge_type=BadgeType.FRAMEWORK_MASTER,
        tier=AchievementTier.GOLD,
        name="Framework Master",
        description="Demonstrated expertise across multiple compliance frameworks",
        icon="📚",
        points_required=750,
        criteria="fixes_count >= 25",
    ),
    Achievement(
        badge_type=BadgeType.ZERO_VIOLATIONS,
        tier=AchievementTier.SILVER,
        name="Clean Slate",
        description="Achieved zero active violations in a managed repository",
        icon="✨",
        points_required=200,
        criteria="violations_resolved >= 10",
    ),
    Achievement(
        badge_type=BadgeType.TEAM_LEADER,
        tier=AchievementTier.GOLD,
        name="Team Leader",
        description="Top contributor on the compliance leaderboard",
        icon="👑",
        points_required=800,
        criteria="points >= 800",
    ),
    Achievement(
        badge_type=BadgeType.EARLY_ADOPTER,
        tier=AchievementTier.BRONZE,
        name="Early Adopter",
        description="Among the first to use the compliance platform",
        icon="🌟",
        points_required=0,
        criteria="joined early",
    ),
]

_SEED_PROFILES: list[dict] = [
    {
        "user_id": "alice",
        "display_name": "Alice Chen",
        "points": 850,
        "level": 8,
        "badges": ["first_fix", "streak_7", "framework_master", "team_leader"],
        "current_streak": 12,
        "longest_streak": 34,
        "fixes_count": 42,
        "violations_resolved": 38,
    },
    {
        "user_id": "bob",
        "display_name": "Bob Martinez",
        "points": 520,
        "level": 5,
        "badges": ["first_fix", "streak_7", "zero_violations"],
        "current_streak": 8,
        "longest_streak": 15,
        "fixes_count": 23,
        "violations_resolved": 19,
    },
    {
        "user_id": "carol",
        "display_name": "Carol Williams",
        "points": 1200,
        "level": 12,
        "badges": ["first_fix", "streak_7", "streak_30", "compliance_champion", "framework_master", "team_leader"],
        "current_streak": 31,
        "longest_streak": 45,
        "fixes_count": 67,
        "violations_resolved": 55,
    },
    {
        "user_id": "dave",
        "display_name": "Dave Kim",
        "points": 180,
        "level": 2,
        "badges": ["first_fix", "early_adopter"],
        "current_streak": 3,
        "longest_streak": 7,
        "fixes_count": 8,
        "violations_resolved": 6,
    },
    {
        "user_id": "eve",
        "display_name": "Eve Johnson",
        "points": 340,
        "level": 4,
        "badges": ["first_fix", "streak_7"],
        "current_streak": 0,
        "longest_streak": 10,
        "fixes_count": 15,
        "violations_resolved": 12,
    },
]


def _level_from_points(points: int) -> int:
    """Calculate level from points (100 points per level)."""
    return max(1, points // 100)


class GamificationEngineService:
    """Gamify compliance activities with points, badges, and leaderboards."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._profiles: dict[str, UserProfile] = {}
        self._seed_data()

    def _seed_data(self) -> None:
        now = datetime.now(UTC)
        for profile_def in _SEED_PROFILES:
            profile = UserProfile(
                user_id=profile_def["user_id"],
                display_name=profile_def["display_name"],
                points=profile_def["points"],
                level=profile_def["level"],
                badges=profile_def["badges"],
                current_streak=profile_def["current_streak"],
                longest_streak=profile_def["longest_streak"],
                fixes_count=profile_def["fixes_count"],
                violations_resolved=profile_def["violations_resolved"],
                joined_at=now,
            )
            self._profiles[profile.user_id] = profile

    async def award_points(self, user_id: str, points: int, reason: str = "") -> UserProfile:
        profile = self._profiles.get(user_id)
        if not profile:
            raise ValueError(f"User not found: {user_id}")

        profile.points += points
        profile.level = _level_from_points(profile.points)
        logger.info("Points awarded", user_id=user_id, points=points, total=profile.points, reason=reason)
        return profile

    async def check_and_award_badges(self, user_id: str) -> list[str]:
        profile = self._profiles.get(user_id)
        if not profile:
            raise ValueError(f"User not found: {user_id}")

        newly_awarded: list[str] = []
        for achievement in _ACHIEVEMENTS:
            badge_key = achievement.badge_type.value
            if badge_key in profile.badges:
                continue

            earned = False
            if achievement.badge_type == BadgeType.FIRST_FIX:
                earned = profile.fixes_count >= 1
            elif achievement.badge_type == BadgeType.STREAK_7:
                earned = profile.current_streak >= 7
            elif achievement.badge_type == BadgeType.STREAK_30:
                earned = profile.current_streak >= 30
            elif achievement.badge_type == BadgeType.COMPLIANCE_CHAMPION:
                earned = profile.violations_resolved >= 50
            elif achievement.badge_type == BadgeType.FRAMEWORK_MASTER:
                earned = profile.fixes_count >= 25
            elif achievement.badge_type == BadgeType.ZERO_VIOLATIONS:
                earned = profile.violations_resolved >= 10
            elif achievement.badge_type == BadgeType.TEAM_LEADER:
                earned = profile.points >= 800

            if earned:
                profile.badges.append(badge_key)
                newly_awarded.append(badge_key)
                logger.info("Badge awarded", user_id=user_id, badge=badge_key)

        return newly_awarded

    async def get_profile(self, user_id: str) -> UserProfile:
        profile = self._profiles.get(user_id)
        if not profile:
            raise ValueError(f"User not found: {user_id}")
        return profile

    async def get_leaderboard(self, top_n: int = 10) -> list[LeaderboardEntry]:
        sorted_profiles = sorted(self._profiles.values(), key=lambda p: p.points, reverse=True)
        entries: list[LeaderboardEntry] = []
        for rank, profile in enumerate(sorted_profiles[:top_n], start=1):
            entries.append(
                LeaderboardEntry(
                    rank=rank,
                    user_id=profile.user_id,
                    display_name=profile.display_name,
                    points=profile.points,
                    level=profile.level,
                    badges_count=len(profile.badges),
                )
            )
        return entries

    def list_achievements(self) -> list[Achievement]:
        return list(_ACHIEVEMENTS)

    async def record_activity(self, user_id: str, activity_type: str) -> UserProfile:
        profile = self._profiles.get(user_id)
        if not profile:
            raise ValueError(f"User not found: {user_id}")

        if activity_type == "fix":
            profile.fixes_count += 1
            profile.points += 10
        elif activity_type == "resolve":
            profile.violations_resolved += 1
            profile.points += 25
        elif activity_type == "scan":
            profile.points += 5
        else:
            profile.points += 1

        profile.current_streak += 1
        profile.longest_streak = max(profile.longest_streak, profile.current_streak)
        profile.level = _level_from_points(profile.points)

        await self.check_and_award_badges(user_id)
        logger.info("Activity recorded", user_id=user_id, activity=activity_type, points=profile.points)
        return profile

    def get_stats(self) -> GamificationStats:
        profiles = list(self._profiles.values())
        by_level: dict[int, int] = {}
        by_badge: dict[str, int] = {}
        total_points = 0
        total_badges = 0

        for p in profiles:
            by_level[p.level] = by_level.get(p.level, 0) + 1
            total_points += p.points
            total_badges += len(p.badges)
            for badge in p.badges:
                by_badge[badge] = by_badge.get(badge, 0) + 1

        return GamificationStats(
            total_users=len(profiles),
            total_points_awarded=total_points,
            total_badges_awarded=total_badges,
            by_level=by_level,
            by_badge=by_badge,
            avg_points=round(total_points / len(profiles), 1) if profiles else 0.0,
        )
