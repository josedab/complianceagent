"""Compliance Gamification Engine Service."""

from typing import TypedDict
from uuid import UUID

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_state import GamificationEventRecord, GamificationProfileRecord
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


class _SeedProfile(TypedDict):
    """Static seed data shape for demo gamification profiles."""

    user_id: str
    display_name: str
    points: int
    level: int
    badges: list[str]
    current_streak: int
    longest_streak: int
    fixes_count: int
    violations_resolved: int


_SEED_PROFILES: list[_SeedProfile] = [
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
        "badges": [
            "first_fix",
            "streak_7",
            "streak_30",
            "compliance_champion",
            "framework_master",
            "team_leader",
        ],
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
    return max(1, points // 100)


def _coerce_user_uuid(user_id: str, fallback: UUID | None = None) -> UUID:
    if user_id:
        return UUID(user_id)
    if fallback is None:
        raise ValueError("user_id is required")
    return fallback


def _profile_record_to_domain(record: GamificationProfileRecord) -> UserProfile:
    meta = record.profile_metadata or {}
    return UserProfile(
        id=record.id,
        user_id=str(record.user_id),
        display_name=meta.get("display_name", str(record.user_id)),
        points=record.xp_total,
        level=record.level,
        badges=list(record.badges or []),
        current_streak=record.streak_days,
        longest_streak=meta.get("longest_streak", record.streak_days),
        fixes_count=meta.get("fixes_count", 0),
        violations_resolved=meta.get("violations_resolved", 0),
        joined_at=record.created_at,
    )


class GamificationEngineService:
    """Gamify compliance activities with points, badges, and leaderboards."""

    def __init__(
        self,
        db: AsyncSession,
        organization_id: UUID | None = None,
        user_id: UUID | None = None,
    ):
        self.db = db
        self.organization_id = organization_id
        self.user_id = user_id

    async def award_points(self, user_id: str, points: int, reason: str = "") -> UserProfile:
        record = await self._get_or_create_profile_record(user_id)
        await self.db.execute(
            update(GamificationProfileRecord)
            .where(
                GamificationProfileRecord.id == record.id,
                GamificationProfileRecord.organization_id == self.organization_id,
            )
            .values(xp_total=GamificationProfileRecord.xp_total + points)
        )
        refreshed = await self._get_profile_record(user_id)
        if refreshed is None:
            raise ValueError(f"User not found: {user_id}")
        refreshed.level = _level_from_points(refreshed.xp_total)
        meta = dict(refreshed.profile_metadata or {})
        if reason:
            meta["last_award_reason"] = reason
        refreshed.profile_metadata = meta
        await self.db.flush()
        logger.info(
            "Points awarded",
            user_id=user_id,
            points=points,
            total=refreshed.xp_total,
            reason=reason,
        )
        return _profile_record_to_domain(refreshed)

    async def check_and_award_badges(self, user_id: str) -> list[str]:
        record = await self._get_profile_record(user_id)
        if not record:
            raise ValueError(f"User not found: {user_id}")

        profile = _profile_record_to_domain(record)
        newly_awarded: list[str] = []
        badges = list(record.badges or [])
        for achievement in _ACHIEVEMENTS:
            badge_key = achievement.badge_type.value
            if badge_key in badges:
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
                badges.append(badge_key)
                newly_awarded.append(badge_key)
                self.db.add(
                    GamificationEventRecord(
                        organization_id=self.organization_id,
                        user_id=record.user_id,
                        event_type="badge_awarded",
                        badge_awarded=badge_key,
                        event_metadata={"achievement": achievement.name},
                    )
                )
                logger.info("Badge awarded", user_id=user_id, badge=badge_key)

        record.badges = badges
        await self.db.flush()
        return newly_awarded

    async def get_profile(self, user_id: str) -> UserProfile:
        record = await self._get_profile_record(user_id)
        if not record:
            raise ValueError(f"User not found: {user_id}")
        return _profile_record_to_domain(record)

    async def get_leaderboard(self, top_n: int = 10) -> list[LeaderboardEntry]:
        stmt = (
            select(GamificationProfileRecord)
            .where(GamificationProfileRecord.organization_id == self.organization_id)
            .order_by(
                GamificationProfileRecord.xp_total.desc(),
                GamificationProfileRecord.created_at.asc(),
            )
            .limit(top_n)
        )
        result = await self.db.execute(stmt)
        entries: list[LeaderboardEntry] = []
        for rank, record in enumerate(result.scalars().all(), start=1):
            profile = _profile_record_to_domain(record)
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
        record = await self._get_or_create_profile_record(user_id)
        meta = dict(record.profile_metadata or {})
        points_delta = 1
        if activity_type == "fix":
            meta["fixes_count"] = meta.get("fixes_count", 0) + 1
            points_delta = 10
        elif activity_type == "resolve":
            meta["violations_resolved"] = meta.get("violations_resolved", 0) + 1
            points_delta = 25
        elif activity_type == "scan":
            points_delta = 5

        record.xp_total += points_delta
        record.streak_days += 1
        record.level = _level_from_points(record.xp_total)
        meta["longest_streak"] = max(meta.get("longest_streak", 0), record.streak_days)
        record.profile_metadata = meta
        self.db.add(
            GamificationEventRecord(
                organization_id=self.organization_id,
                user_id=record.user_id,
                event_type=activity_type,
                xp_awarded=points_delta,
                event_metadata={"xp_total": record.xp_total},
            )
        )
        await self.check_and_award_badges(user_id)
        await self.db.flush()
        logger.info(
            "Activity recorded", user_id=user_id, activity=activity_type, points=record.xp_total
        )
        return _profile_record_to_domain(record)

    async def get_stats(self) -> GamificationStats:
        stmt = select(GamificationProfileRecord).where(
            GamificationProfileRecord.organization_id == self.organization_id
        )
        result = await self.db.execute(stmt)
        profiles = [_profile_record_to_domain(record) for record in result.scalars().all()]
        by_level: dict[int, int] = {}
        by_badge: dict[str, int] = {}
        total_points = 0
        total_badges = 0
        for profile in profiles:
            by_level[profile.level] = by_level.get(profile.level, 0) + 1
            total_points += profile.points
            total_badges += len(profile.badges)
            for badge in profile.badges:
                by_badge[badge] = by_badge.get(badge, 0) + 1
        return GamificationStats(
            total_users=len(profiles),
            total_points_awarded=total_points,
            total_badges_awarded=total_badges,
            by_level=by_level,
            by_badge=by_badge,
            avg_points=round(total_points / len(profiles), 1) if profiles else 0.0,
        )

    async def _get_profile_record(self, user_id: str) -> GamificationProfileRecord | None:
        db_user_id = _coerce_user_uuid(user_id, self.user_id)
        stmt = select(GamificationProfileRecord).where(
            GamificationProfileRecord.organization_id == self.organization_id,
            GamificationProfileRecord.user_id == db_user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_or_create_profile_record(self, user_id: str) -> GamificationProfileRecord:
        record = await self._get_profile_record(user_id)
        if record:
            return record
        db_user_id = _coerce_user_uuid(user_id, self.user_id)
        record = GamificationProfileRecord(
            organization_id=self.organization_id,
            user_id=db_user_id,
            level=1,
            xp_total=0,
            badges=[],
            streak_days=0,
            profile_metadata={
                "display_name": user_id or str(db_user_id),
                "longest_streak": 0,
                "fixes_count": 0,
                "violations_resolved": 0,
            },
        )
        self.db.add(record)
        await self.db.flush()
        return record
