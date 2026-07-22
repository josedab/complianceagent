"""API endpoints for Incident War Room."""

import structlog
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.incident_war_room import (
    IncidentWarRoomService,
    PostMortem,
    WarRoomIncident,
    WarRoomStats,
)


logger = structlog.get_logger()
router = APIRouter()


# --- Request / Response Schemas ---


class CreateIncidentRequest(BaseModel):
    title: str = Field(..., description="Incident title")
    severity: str = Field(..., description="Incident severity level")
    description: str = Field(..., description="Incident description")
    regulation: str = Field(..., description="Applicable regulation or framework")


class AddTimelineEntryRequest(BaseModel):
    actor: str = Field(..., description="Person or system performing the action")
    action: str = Field(..., description="Action taken")
    details: str = Field("", description="Additional details")


# --- Endpoints ---


@router.post("/incidents")
async def create_incident(request: CreateIncidentRequest, db: DB) -> WarRoomIncident:
    """Create a new compliance incident."""
    svc = IncidentWarRoomService(db)
    return await svc.create_incident(
        title=request.title,
        severity=request.severity,
        description=request.description,
        regulation=request.regulation,
    )


@router.post("/incidents/{incident_id}/advance")
async def advance_phase(incident_id: str, db: DB) -> WarRoomIncident:
    """Advance an incident to the next phase."""
    svc = IncidentWarRoomService(db)
    return await svc.advance_phase(incident_id=incident_id)


@router.post("/incidents/{incident_id}/timeline")
async def add_timeline_entry(
    incident_id: str,
    request: AddTimelineEntryRequest,
    db: DB,
) -> WarRoomIncident:
    """Add a timeline entry to an incident."""
    svc = IncidentWarRoomService(db)
    return await svc.add_timeline_entry(
        incident_id=incident_id,
        actor=request.actor,
        action=request.action,
        details=request.details,
    )


@router.post("/incidents/{incident_id}/post-mortem")
async def generate_post_mortem(incident_id: str, db: DB) -> PostMortem:
    """Generate a post-mortem report for an incident."""
    svc = IncidentWarRoomService(db)
    return await svc.generate_post_mortem(incident_id=incident_id)


@router.get("/incidents")
async def list_incidents(
    db: DB,
    phase: str | None = Query(None, description="Filter by incident phase"),
) -> list[WarRoomIncident]:
    """List compliance incidents."""
    svc = IncidentWarRoomService(db)
    return await svc.list_incidents(phase=phase)


@router.get("/incidents/{incident_id}")
async def get_incident(incident_id: str, db: DB) -> WarRoomIncident:
    """Get details of a specific incident."""
    svc = IncidentWarRoomService(db)
    return await svc.get_incident(incident_id=incident_id)


@router.get("/stats")
async def get_stats(db: DB) -> WarRoomStats:
    """Get incident war room statistics."""
    svc = IncidentWarRoomService(db)
    return svc.get_stats()
