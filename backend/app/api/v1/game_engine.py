"""API endpoints for Compliance Simulation Game Engine."""

from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.game_engine import (
    GameEngineService,
    ScenarioCategory,
    ScenarioDifficulty,
)

logger = structlog.get_logger()
router = APIRouter()


# --- Response Models ---

class GameDecisionSchema(BaseModel):
    id: str
    prompt: str
    options: list[str]
    points: int
    time_limit_seconds: int
    regulation_reference: str


class GameScenarioSchema(BaseModel):
    id: str
    title: str
    description: str
    category: str
    difficulty: str
    estimated_minutes: int
    max_score: int
    decisions: list[GameDecisionSchema]
    learning_objectives: list[str]
    frameworks: list[str]


class GameScenarioSummarySchema(BaseModel):
    id: str
    title: str
    description: str
    category: str
    difficulty: str
    estimated_minutes: int
    max_score: int
    decisions_count: int
    frameworks: list[str]


class SubmitDecisionRequest(BaseModel):
    decision_id: str = Field(..., description="ID of the decision")
    selected_option: int = Field(..., description="Index of the selected option")


class DecisionResultSchema(BaseModel):
    correct: bool
    points_earned: int
    explanation: str
    regulation_reference: str
    correct_option: int


class LeaderboardEntrySchema(BaseModel):
    display_name: str
    organization: str
    total_xp: int
    level: int
    scenarios_completed: int
    achievements_count: int
    accuracy_rate: float
    rank: int


class AchievementSchema(BaseModel):
    id: str
    name: str
    description: str
    tier: str
    icon: str
    xp_reward: int


# --- Endpoints ---

@router.get("/scenarios", response_model=list[GameScenarioSummarySchema])
async def list_scenarios(
    category: str | None = Query(None),
    difficulty: str | None = Query(None),
) -> list[dict]:
    svc = GameEngineService()
    try:
        cat = ScenarioCategory(category) if category else None
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid category: {category}")
    try:
        diff = ScenarioDifficulty(difficulty) if difficulty else None
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid difficulty: {difficulty}")
    scenarios = await svc.list_scenarios(category=cat, difficulty=diff)
    return [
        {"id": s.id, "title": s.title, "description": s.description,
         "category": s.category.value, "difficulty": s.difficulty.value,
         "estimated_minutes": s.estimated_minutes, "max_score": s.max_score,
         "decisions_count": len(s.decisions), "frameworks": s.frameworks}
        for s in scenarios
    ]


@router.get("/scenarios/{scenario_id}", response_model=GameScenarioSchema)
async def get_scenario(scenario_id: str) -> dict:
    svc = GameEngineService()
    s = await svc.get_scenario(scenario_id)
    if not s:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return {
        "id": s.id, "title": s.title, "description": s.description,
        "category": s.category.value, "difficulty": s.difficulty.value,
        "estimated_minutes": s.estimated_minutes, "max_score": s.max_score,
        "decisions": [
            {"id": d.id, "prompt": d.prompt, "options": d.options,
             "points": d.points, "time_limit_seconds": d.time_limit_seconds,
             "regulation_reference": d.regulation_reference}
            for d in s.decisions
        ],
        "learning_objectives": s.learning_objectives, "frameworks": s.frameworks,
    }


@router.post("/scenarios/{scenario_id}/submit", response_model=DecisionResultSchema)
async def submit_decision(scenario_id: str, req: SubmitDecisionRequest) -> dict:
    svc = GameEngineService()
    try:
        result = await svc.submit_decision(scenario_id, req.decision_id, req.selected_option)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


@router.get("/leaderboard", response_model=list[LeaderboardEntrySchema])
async def get_leaderboard(limit: int = Query(10, ge=1, le=100)) -> list[dict]:
    svc = GameEngineService()
    entries = await svc.get_leaderboard(limit=limit)
    return [
        {"display_name": e.display_name, "organization": e.organization,
         "total_xp": e.total_xp, "level": e.level,
         "scenarios_completed": e.scenarios_completed,
         "achievements_count": e.achievements_count,
         "accuracy_rate": e.accuracy_rate, "rank": e.rank}
        for e in entries
    ]


@router.get("/achievements", response_model=list[AchievementSchema])
async def get_achievements() -> list[dict]:
    svc = GameEngineService()
    achievements = await svc.get_achievements()
    return [
        {"id": a.id, "name": a.name, "description": a.description,
         "tier": a.tier.value, "icon": a.icon, "xp_reward": a.xp_reward}
        for a in achievements
    ]
