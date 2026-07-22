"""API endpoints for Draft Regulation Simulator."""

import structlog
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.draft_reg_simulator import (
    DraftRegSimulatorService,
    DraftRegulation,
    ImpactAnalysis,
    SimulationStats,
)


logger = structlog.get_logger()
router = APIRouter()


# --- Request / Response Schemas ---


class SimulateDraftRequest(BaseModel):
    repos: list[str] | None = Field(
        None, description="Repositories to assess for regulatory impact"
    )


# --- Endpoints ---


@router.post("/simulate/{draft_id}")
async def simulate_draft(draft_id: str, request: SimulateDraftRequest, db: DB) -> ImpactAnalysis:
    """Simulate the impact of a known draft regulation on the codebase."""
    svc = DraftRegSimulatorService(db)
    return await svc.simulate_draft(draft_id, repos=request.repos)


@router.get("/drafts")
async def list_drafts(db: DB) -> list[DraftRegulation]:
    """List all draft regulation simulations."""
    svc = DraftRegSimulatorService(db)
    return await svc.list_drafts()


@router.get("/analysis/{analysis_id}")
async def get_analysis(analysis_id: str, db: DB) -> ImpactAnalysis:
    """Get the analysis results for a specific simulation."""
    svc = DraftRegSimulatorService(db)
    return await svc.get_analysis(analysis_id)


@router.get("/stats")
async def get_stats(db: DB) -> SimulationStats:
    """Get draft regulation simulator statistics."""
    svc = DraftRegSimulatorService(db)
    return svc.get_stats()
