"""API endpoints for Gamification Engine."""

from typing import Any

import structlog
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CurrentOrganization
from app.services.gamification_engine import (
    Achievement,
    GamificationEngineService,
    GamificationStats,
    LeaderboardEntry,
    UserProfile,
)


logger = structlog.get_logger()
router = APIRouter()


# --- Request / Response Schemas ---


class RecordActivityRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    activity_type: str = Field(..., description="Type of compliance activity")
    details: dict[str, Any] = Field(default_factory=dict, description="Activity details")


# --- Endpoints ---


@router.post("/activity")
async def record_activity(
    request: RecordActivityRequest, db: DB, org: CurrentOrganization
) -> UserProfile:
    """Record a user compliance activity."""
    svc = GamificationEngineService(db=db, organization_id=org.id, user_id=None)
    return await svc.record_activity(
        user_id=request.user_id,
        activity_type=request.activity_type,
    )


@router.get("/profile/{user_id}")
async def get_profile(user_id: str, db: DB, org: CurrentOrganization) -> UserProfile:
    """Get a user's gamification profile."""
    svc = GamificationEngineService(db=db, organization_id=org.id, user_id=None)
    return await svc.get_profile(user_id=user_id)


@router.get("/leaderboard")
async def get_leaderboard(
    db: DB,
    org: CurrentOrganization,
    limit: int = Query(10, ge=1, le=100, description="Number of entries to return"),
) -> list[LeaderboardEntry]:
    """Get the compliance leaderboard."""
    svc = GamificationEngineService(db=db, organization_id=org.id, user_id=None)
    return await svc.get_leaderboard(top_n=limit)


@router.get("/achievements")
async def list_achievements(db: DB) -> list[Achievement]:
    """List all available achievements."""
    svc = GamificationEngineService(db=db)
    return svc.list_achievements()


@router.get("/stats")
async def get_stats(db: DB, org: CurrentOrganization) -> GamificationStats:
    """Get gamification engine statistics."""
    svc = GamificationEngineService(db=db, organization_id=org.id, user_id=None)
    return await svc.get_stats()
