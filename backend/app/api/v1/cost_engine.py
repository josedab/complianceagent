"""API endpoints for Compliance Cost Engine."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB


logger = structlog.get_logger()
router = APIRouter()


def _serialize(obj):
    """Convert a dataclass to a JSON-serializable dict."""
    from dataclasses import fields, is_dataclass

    if not is_dataclass(obj):
        return obj

    result = {}
    for f in fields(obj):
        v = getattr(obj, f.name)
        result[f.name] = _ser_val(v)
    return result


def _ser_val(v):
    from dataclasses import is_dataclass
    from datetime import datetime
    from enum import Enum
    from uuid import UUID

    if v is None:
        return None
    if isinstance(v, Enum):
        return v.value
    if isinstance(v, UUID):
        return str(v)
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, list):
        return [_ser_val(item) for item in v]
    if isinstance(v, dict):
        return {k: _ser_val(val) for k, val in v.items()}
    if is_dataclass(v):
        return _serialize(v)
    return v


# --- Schemas ---


class AttributeCostRequest(BaseModel):
    team: str = Field(..., description="Team responsible for the cost")
    repository: str = Field(..., description="Repository associated with the cost")
    framework: str = Field(..., description="Compliance framework")
    category: str = Field(..., description="Cost category (e.g. 'engineering', 'audit', 'tooling')")
    hours: float = Field(..., description="Hours spent", gt=0)


class CostAttributionResponse(BaseModel):
    model_config = {"extra": "ignore"}
    id: UUID
    team: str
    repository: str
    framework: str
    category: str
    hours: float
    estimated_cost: float
    created_at: str


class CostAttributionListResponse(BaseModel):
    model_config = {"extra": "ignore"}
    attributions: list[CostAttributionResponse]
    total: int
    total_hours: float
    total_cost: float


class TeamCostSummaryResponse(BaseModel):
    model_config = {"extra": "ignore"}
    team: str
    total_hours: float
    total_cost: float
    by_framework: dict[str, float] = Field(default_factory=dict)
    by_category: dict[str, float] = Field(default_factory=dict)
    trend: str


class FrameworkCostResponse(BaseModel):
    model_config = {"extra": "ignore"}
    framework: str
    total_hours: float
    total_cost: float
    by_team: dict[str, float] = Field(default_factory=dict)
    by_category: dict[str, float] = Field(default_factory=dict)


class ForecastRequest(BaseModel):
    months_ahead: int = Field(..., description="Number of months to forecast", ge=1, le=24)


class ForecastResponse(BaseModel):
    model_config = {"extra": "ignore"}
    months_ahead: int
    projected_total_cost: float
    monthly_projections: list[dict[str, Any]] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class RoiReportResponse(BaseModel):
    model_config = {"extra": "ignore"}
    total_investment: float
    total_savings: float
    roi_percentage: float
    payback_months: float
    breakdown: dict[str, Any] = Field(default_factory=dict)


# --- Endpoints ---


@router.post(
    "/attribute",
    response_model=CostAttributionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Attribute compliance costs",
)
async def attribute_cost(request: AttributeCostRequest, db: DB) -> CostAttributionResponse:
    """Attribute compliance costs to a team, repository, and framework."""
    from app.services.cost_engine import CostAttributionEngine as CostEngineService

    service = CostEngineService(db=db)
    attribution = await service.attribute_costs(
        team=request.team,
        repository=request.repository,
        framework=request.framework,
        category=request.category,
        hours=request.hours,
    )
    return CostAttributionResponse(**_serialize(attribution))


@router.get(
    "/attributions", response_model=CostAttributionListResponse, summary="List cost attributions"
)
async def list_attributions(
    db: DB,
    team: str | None = None,
    framework: str | None = None,
) -> CostAttributionListResponse:
    """List cost attributions with optional team and framework filters."""
    from app.services.cost_engine import CostAttributionEngine as CostEngineService

    service = CostEngineService(db=db)
    result = await service.list_attributions(team=team, framework=framework)
    return CostAttributionListResponse(
        attributions=[CostAttributionResponse(**_serialize(a)) for a in result["attributions"]],
        total=result["total"],
        total_hours=result["total_hours"],
        total_cost=result["total_cost"],
    )


@router.get(
    "/team/{team_name}", response_model=TeamCostSummaryResponse, summary="Get team cost summary"
)
async def get_team_costs(team_name: str, db: DB) -> TeamCostSummaryResponse:
    """Get a cost summary for a specific team."""
    from app.services.cost_engine import CostAttributionEngine as CostEngineService

    service = CostEngineService(db=db)
    summary = await service.get_team_summary(team_name=team_name)
    if not summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return TeamCostSummaryResponse(**_serialize(summary))


@router.get(
    "/framework/{framework}", response_model=FrameworkCostResponse, summary="Get framework costs"
)
async def get_framework_costs(framework: str, db: DB) -> FrameworkCostResponse:
    """Get cost breakdown for a specific compliance framework."""
    from app.services.cost_engine import CostAttributionEngine as CostEngineService

    service = CostEngineService(db=db)
    costs = await service.get_framework_costs(framework=framework)
    if not costs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Framework not found")
    return FrameworkCostResponse(**_serialize(costs))


@router.post("/forecast", response_model=ForecastResponse, summary="Generate cost forecast")
async def generate_forecast(request: ForecastRequest, db: DB) -> ForecastResponse:
    """Generate a cost forecast based on historical data."""
    from app.services.cost_engine import CostAttributionEngine as CostEngineService

    service = CostEngineService(db=db)
    forecast = await service.generate_forecast(months_ahead=request.months_ahead)
    return ForecastResponse(**_serialize(forecast))


@router.get("/roi", response_model=RoiReportResponse, summary="Calculate ROI report")
async def get_roi_report(db: DB) -> RoiReportResponse:
    """Calculate the return on investment for compliance activities."""
    from app.services.cost_engine import CostAttributionEngine as CostEngineService

    service = CostEngineService(db=db)
    report = await service.calculate_roi()
    return RoiReportResponse(**_serialize(report))
