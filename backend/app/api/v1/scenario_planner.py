"""API endpoints for Scenario Planner."""

import structlog
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.scenario_planner import (
    RegionGroup,
    ScenarioPlannerService,
    ScenarioType,
)


logger = structlog.get_logger()
router = APIRouter()


class ScenarioPlanRequest(BaseModel):
    title: str = Field(...)
    scenario_type: str = Field(...)
    description: str = Field(...)
    target_regions: list[str] = Field(...)
    data_types: list[str] = Field(default_factory=list)
    ai_features: bool = Field(default=False)
    health_data: bool = Field(default=False)
    payment_data: bool = Field(default=False)


@router.post("/plan", status_code=status.HTTP_201_CREATED, summary="Plan a scenario")
async def plan_scenario(request: ScenarioPlanRequest, db: DB) -> dict:
    """Plan a compliance scenario and generate a report."""
    service = ScenarioPlannerService(db=db)
    result = await service.plan_scenario(
        title=request.title,
        scenario_type=ScenarioType(request.scenario_type),
        description=request.description,
        target_regions=[RegionGroup(r) for r in request.target_regions],
        data_types=request.data_types,
        ai_features=request.ai_features,
        health_data=request.health_data,
        payment_data=request.payment_data,
    )
    return {
        "id": str(result.id),
        "scenario": {
            "id": str(result.scenario.id),
            "title": result.scenario.title,
            "scenario_type": result.scenario.scenario_type.value,
            "description": result.scenario.description,
            "target_regions": [r.value for r in result.scenario.target_regions],
            "data_types": result.scenario.data_types,
        },
        "requirements": {
            "applicable_frameworks": result.requirements.applicable_frameworks,
            "total_requirements": result.requirements.total_requirements,
            "estimated_effort_hours": result.requirements.estimated_effort_hours,
            "estimated_cost_usd": result.requirements.estimated_cost_usd,
            "priority_actions": result.requirements.priority_actions,
            "timeline_months": result.requirements.timeline_months,
        },
        "risk_assessment": result.risk_assessment,
        "recommendations": result.recommendations,
        "generated_at": result.generated_at.isoformat() if result.generated_at else None,
    }


@router.get("/scenarios", summary="List all scenarios")
async def list_scenarios(db: DB) -> list[dict]:
    """List all planning reports."""
    service = ScenarioPlannerService(db=db)
    reports = await service.list_scenarios()
    return [
        {
            "id": str(r.id),
            "title": r.scenario.title,
            "scenario_type": r.scenario.scenario_type.value,
            "target_regions": [rg.value for rg in r.scenario.target_regions],
            "frameworks": r.requirements.applicable_frameworks,
            "generated_at": r.generated_at.isoformat() if r.generated_at else None,
        }
        for r in reports
    ]


@router.get("/stats", summary="Get scenario planner stats")
async def get_stats(db: DB) -> dict:
    """Get aggregate planner statistics."""
    service = ScenarioPlannerService(db=db)
    stats = await service.get_stats()
    return {
        "total_scenarios": stats.total_scenarios,
        "by_type": stats.by_type,
        "by_region": stats.by_region,
        "avg_frameworks_per_scenario": stats.avg_frameworks_per_scenario,
    }
