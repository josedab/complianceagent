"""API endpoints for Compliance Digital Twin Simulation."""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.twin_simulation import TwinSimulationService


logger = structlog.get_logger()
router = APIRouter()


class CaptureSnapshotRequest(BaseModel):
    repo: str = Field(...)
    name: str = Field(default="")


class SnapshotSchema(BaseModel):
    id: str
    name: str
    repo: str
    score: float
    frameworks: dict[str, float]
    violation_count: int
    captured_at: str | None


class SimulateRequest(BaseModel):
    repo: str = Field(...)
    changes: list[dict[str, Any]] = Field(...)


class SimulationResultSchema(BaseModel):
    id: str
    status: str
    score_before: float
    score_after: float
    score_delta: float
    framework_impacts: list[dict[str, Any]]
    risk_assessment: str
    recommendations: list[str]
    warnings: list[str]
    simulation_time_ms: float
    created_at: str | None


class HistorySchema(BaseModel):
    total_simulations: int
    avg_score_delta: float
    prevented_regressions: int
    by_change_type: dict[str, int]


@router.post(
    "/snapshot",
    response_model=SnapshotSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Capture snapshot",
)
async def capture_snapshot(request: CaptureSnapshotRequest, db: DB) -> SnapshotSchema:
    service = TwinSimulationService(db=db)
    s = await service.capture_snapshot(repo=request.repo, name=request.name)
    return SnapshotSchema(
        id=str(s.id),
        name=s.name,
        repo=s.repo,
        score=s.score,
        frameworks=s.frameworks,
        violation_count=s.violation_count,
        captured_at=s.captured_at.isoformat() if s.captured_at else None,
    )


@router.get("/snapshot/{repo:path}", response_model=SnapshotSchema, summary="Get snapshot")
async def get_snapshot(repo: str, db: DB) -> SnapshotSchema:
    service = TwinSimulationService(db=db)
    s = service.get_snapshot(repo)
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Snapshot not found")
    return SnapshotSchema(
        id=str(s.id),
        name=s.name,
        repo=s.repo,
        score=s.score,
        frameworks=s.frameworks,
        violation_count=s.violation_count,
        captured_at=s.captured_at.isoformat() if s.captured_at else None,
    )


@router.post("/simulate", response_model=SimulationResultSchema, summary="Run simulation")
async def run_simulation(request: SimulateRequest, db: DB) -> SimulationResultSchema:
    service = TwinSimulationService(db=db)
    r = await service.simulate(repo=request.repo, changes=request.changes)
    return SimulationResultSchema(
        id=str(r.id),
        status=r.status.value,
        score_before=r.score_before,
        score_after=r.score_after,
        score_delta=r.score_delta,
        framework_impacts=r.framework_impacts,
        risk_assessment=r.risk_assessment,
        recommendations=r.recommendations,
        warnings=r.warnings,
        simulation_time_ms=r.simulation_time_ms,
        created_at=r.created_at.isoformat() if r.created_at else None,
    )


@router.get("/simulations", response_model=list[SimulationResultSchema], summary="List simulations")
async def list_simulations(db: DB, limit: int = 20) -> list[SimulationResultSchema]:
    service = TwinSimulationService(db=db)
    sims = service.list_simulations(limit=limit)
    return [
        SimulationResultSchema(
            id=str(r.id),
            status=r.status.value,
            score_before=r.score_before,
            score_after=r.score_after,
            score_delta=r.score_delta,
            framework_impacts=r.framework_impacts,
            risk_assessment=r.risk_assessment,
            recommendations=r.recommendations,
            warnings=r.warnings,
            simulation_time_ms=r.simulation_time_ms,
            created_at=r.created_at.isoformat() if r.created_at else None,
        )
        for r in sims
    ]


@router.get("/history", response_model=HistorySchema, summary="Get simulation history")
async def get_history(db: DB) -> HistorySchema:
    service = TwinSimulationService(db=db)
    h = service.get_history()
    return HistorySchema(
        total_simulations=h.total_simulations,
        avg_score_delta=h.avg_score_delta,
        prevented_regressions=h.prevented_regressions,
        by_change_type=h.by_change_type,
    )
