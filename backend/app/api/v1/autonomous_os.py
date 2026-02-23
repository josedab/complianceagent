"""API endpoints for Autonomous OS."""

import structlog
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.autonomous_os import AutonomousOSService


logger = structlog.get_logger()
router = APIRouter()


class ProcessEventRequest(BaseModel):
    event_type: str = Field(...)
    source_service: str = Field(...)
    payload: dict = Field(default_factory=dict)


class SetAutonomyLevelRequest(BaseModel):
    level: str = Field(...)


class EventSchema(BaseModel):
    id: str
    event_type: str
    source_service: str
    payload: dict
    processed: bool
    created_at: str | None


class DecisionSchema(BaseModel):
    id: str
    decision_type: str
    description: str
    confidence: float
    autonomous: bool
    created_at: str | None


class HealthSchema(BaseModel):
    status: str
    autonomy_level: str
    uptime_seconds: float
    active_services: int


class StatsSchema(BaseModel):
    total_events: int
    total_decisions: int
    autonomous_decisions: int
    avg_confidence: float
    autonomy_level: str


@router.post("/events", status_code=status.HTTP_201_CREATED, summary="Process event")
async def process_event(request: ProcessEventRequest, db: DB) -> dict:
    """Process an incoming autonomous OS event."""
    service = AutonomousOSService(db=db)
    result = await service.process_event(
        event_type=request.event_type,
        source_service=request.source_service,
        payload=request.payload,
    )
    return result


@router.put("/autonomy", summary="Set autonomy level")
async def set_autonomy_level(request: SetAutonomyLevelRequest, db: DB) -> dict:
    """Set the autonomy level for the OS."""
    service = AutonomousOSService(db=db)
    result = await service.set_autonomy_level(level=request.level)
    return result


@router.get("/health", response_model=HealthSchema, summary="Get health status")
async def get_health(db: DB) -> HealthSchema:
    """Get the health status of the autonomous OS."""
    service = AutonomousOSService(db=db)
    health = service.get_health()
    return HealthSchema(
        status=health.status,
        autonomy_level=health.autonomy_level,
        uptime_seconds=health.uptime_seconds,
        active_services=health.active_services,
    )


@router.get("/events", response_model=list[EventSchema], summary="List events")
async def list_events(db: DB) -> list[EventSchema]:
    """List all processed events."""
    service = AutonomousOSService(db=db)
    events = service.list_events()
    return [
        EventSchema(
            id=str(e.id),
            event_type=e.event_type,
            source_service=e.source_service,
            payload=e.payload,
            processed=e.processed,
            created_at=e.created_at.isoformat() if e.created_at else None,
        )
        for e in events
    ]


@router.get("/decisions", response_model=list[DecisionSchema], summary="List decisions")
async def list_decisions(
    db: DB, decision_type: str | None = None
) -> list[DecisionSchema]:
    """List autonomous decisions with optional type filter."""
    service = AutonomousOSService(db=db)
    decisions = service.list_decisions(decision_type=decision_type)
    return [
        DecisionSchema(
            id=str(d.id),
            decision_type=d.decision_type,
            description=d.description,
            confidence=d.confidence,
            autonomous=d.autonomous,
            created_at=d.created_at.isoformat() if d.created_at else None,
        )
        for d in decisions
    ]


@router.get("/stats", response_model=StatsSchema, summary="Get stats")
async def get_stats(db: DB) -> StatsSchema:
    """Get autonomous OS statistics."""
    service = AutonomousOSService(db=db)
    stats = service.get_stats()
    return StatsSchema(
        total_events=stats.total_events,
        total_decisions=stats.total_decisions,
        autonomous_decisions=stats.autonomous_decisions,
        avg_confidence=stats.avg_confidence,
        autonomy_level=stats.autonomy_level,
    )
