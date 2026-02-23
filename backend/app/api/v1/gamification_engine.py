"""API endpoints for Gamification Engine."""

import structlog
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.gamification_engine import GamificationEngineService


logger = structlog.get_logger()
router = APIRouter()


# --- Request / Response Schemas ---


class RecordActivityRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    activity_type: str = Field(..., description="Type of compliance activity")
    details: dict = Field(default_factory=dict, description="Activity details")


# --- Endpoints ---


@router.post("/activity")
async def record_activity(request: RecordActivityRequest, db: DB) -> dict:
    """Record a user compliance activity."""
    svc = GamificationEngineService()
    return await svc.record_activity(
        db,
        user_id=request.user_id,
        activity_type=request.activity_type,
        details=request.details,
    )


@router.get("/profile/{user_id}")
async def get_profile(user_id: str, db: DB) -> dict:
    """Get a user's gamification profile."""
    svc = GamificationEngineService()
    return await svc.get_profile(db, user_id=user_id)


@router.get("/leaderboard")
async def get_leaderboard(
    db: DB,
    limit: int = Query(10, ge=1, le=100, description="Number of entries to return"),
) -> list[dict]:
    """Get the compliance leaderboard."""
    svc = GamificationEngineService()
    return await svc.get_leaderboard(db, limit=limit)


@router.get("/achievements")
async def list_achievements(db: DB) -> list[dict]:
    """List all available achievements."""
    svc = GamificationEngineService()
    return await svc.list_achievements(db)


@router.get("/stats")
async def get_stats(db: DB) -> dict:
    """Get gamification engine statistics."""
    svc = GamificationEngineService()
    return await svc.get_stats(db)
