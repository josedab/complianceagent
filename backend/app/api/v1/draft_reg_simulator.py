"""API endpoints for Draft Regulation Simulator."""

import structlog
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.draft_reg_simulator import DraftRegSimulatorService


logger = structlog.get_logger()
router = APIRouter()


# --- Request / Response Schemas ---


class SimulateDraftRequest(BaseModel):
    title: str = Field(..., description="Draft regulation title")
    jurisdiction: str = Field(..., description="Jurisdiction of the regulation")
    draft_text: str = Field(..., description="Full text of the draft regulation")
    source_url: str = Field("", description="URL to the source document")


# --- Endpoints ---


@router.post("/simulate")
async def simulate_draft(request: SimulateDraftRequest, db: DB) -> dict:
    """Simulate the impact of a draft regulation."""
    svc = DraftRegSimulatorService()
    return await svc.simulate_draft(
        db,
        title=request.title,
        jurisdiction=request.jurisdiction,
        draft_text=request.draft_text,
        source_url=request.source_url,
    )


@router.get("/drafts")
async def list_drafts(db: DB) -> list[dict]:
    """List all draft regulation simulations."""
    svc = DraftRegSimulatorService()
    return await svc.list_drafts(db)


@router.get("/analysis/{analysis_id}")
async def get_analysis(analysis_id: str, db: DB) -> dict:
    """Get the analysis results for a specific simulation."""
    svc = DraftRegSimulatorService()
    return await svc.get_analysis(db, analysis_id=analysis_id)


@router.get("/stats")
async def get_stats(db: DB) -> dict:
    """Get draft regulation simulator statistics."""
    svc = DraftRegSimulatorService()
    return await svc.get_stats(db)
