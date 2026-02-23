"""API endpoints for Regulatory Simulation."""

import structlog
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.regulatory_simulation import RegulatorySimulationService


logger = structlog.get_logger()
router = APIRouter()


class RunSimulationRequest(BaseModel):
    regulation: str = Field(...)
    jurisdiction: str = Field(...)
    iterations: int = Field(default=1000)
    model: str = Field(default="monte_carlo")


class GenerateForecastRequest(BaseModel):
    regulation: str = Field(...)


class SimulationResultSchema(BaseModel):
    id: str
    regulation: str
    jurisdiction: str
    iterations: int
    model: str
    risk_score: float
    confidence_interval: list[float]
    outcomes: list[dict]
    completed_at: str | None


class ForecastSchema(BaseModel):
    id: str
    regulation: str
    timeline_months: int
    probability_of_change: float
    impact_score: float
    recommendations: list[str]
    generated_at: str | None


class RunSchema(BaseModel):
    id: str
    regulation: str
    jurisdiction: str
    model: str
    status: str
    risk_score: float | None
    created_at: str | None


class StatsSchema(BaseModel):
    total_simulations: int
    total_forecasts: int
    avg_risk_score: float
    regulations_covered: int
    jurisdictions_covered: int


@router.post(
    "/simulate",
    response_model=SimulationResultSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Run simulation",
)
async def run_simulation(
    request: RunSimulationRequest, db: DB
) -> SimulationResultSchema:
    """Run a regulatory simulation."""
    service = RegulatorySimulationService(db=db)
    result = await service.run_simulation(
        regulation=request.regulation,
        jurisdiction=request.jurisdiction,
        iterations=request.iterations,
        model=request.model,
    )
    return SimulationResultSchema(
        id=str(result.id),
        regulation=result.regulation,
        jurisdiction=result.jurisdiction,
        iterations=result.iterations,
        model=result.model,
        risk_score=result.risk_score,
        confidence_interval=result.confidence_interval,
        outcomes=result.outcomes,
        completed_at=result.completed_at.isoformat()
        if result.completed_at
        else None,
    )


@router.post(
    "/forecast",
    response_model=ForecastSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Generate forecast",
)
async def generate_forecast(
    request: GenerateForecastRequest, db: DB
) -> ForecastSchema:
    """Generate a regulatory forecast."""
    service = RegulatorySimulationService(db=db)
    forecast = await service.generate_forecast(regulation=request.regulation)
    return ForecastSchema(
        id=str(forecast.id),
        regulation=forecast.regulation,
        timeline_months=forecast.timeline_months,
        probability_of_change=forecast.probability_of_change,
        impact_score=forecast.impact_score,
        recommendations=forecast.recommendations,
        generated_at=forecast.generated_at.isoformat()
        if forecast.generated_at
        else None,
    )


@router.get("/runs", response_model=list[RunSchema], summary="List runs")
async def list_runs(db: DB) -> list[RunSchema]:
    """List all simulation runs."""
    service = RegulatorySimulationService(db=db)
    runs = service.list_runs()
    return [
        RunSchema(
            id=str(r.id),
            regulation=r.regulation,
            jurisdiction=r.jurisdiction,
            model=r.model,
            status=r.status,
            risk_score=r.risk_score,
            created_at=r.created_at.isoformat() if r.created_at else None,
        )
        for r in runs
    ]


@router.get("/stats", response_model=StatsSchema, summary="Get stats")
async def get_stats(db: DB) -> StatsSchema:
    """Get regulatory simulation statistics."""
    service = RegulatorySimulationService(db=db)
    stats = service.get_stats()
    return StatsSchema(
        total_simulations=stats.total_simulations,
        total_forecasts=stats.total_forecasts,
        avg_risk_score=stats.avg_risk_score,
        regulations_covered=stats.regulations_covered,
        jurisdictions_covered=stats.jurisdictions_covered,
    )
