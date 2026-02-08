"""API endpoints for Regulatory Change Impact Timeline."""

from datetime import datetime
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep
from app.services.impact_timeline import ImpactTimelineService, TaskStatus, TimelineEventType

logger = structlog.get_logger()
router = APIRouter()


class AddEventRequest(BaseModel):
    title: str = Field(..., min_length=1)
    framework: str = Field(...)
    jurisdiction: str = Field(...)
    effective_date: str = Field(..., description="ISO 8601 date")
    event_type: str = Field(default="regulation_effective")
    impact_score: float = Field(default=5.0)
    effort_hours: float = Field(default=0.0)
    affected_repos: list[str] = Field(default_factory=list)


class EventSchema(BaseModel):
    id: str
    title: str
    event_type: str
    framework: str
    jurisdiction: str
    days_remaining: int
    impact_score: float
    estimated_effort_hours: float
    affected_repos: list[str]
    is_predicted: bool
    confidence: float


class TaskSchema(BaseModel):
    id: str
    title: str
    priority: str
    status: str
    estimated_hours: float
    due_date: str | None


class TimelineSchema(BaseModel):
    events: list[EventSchema]
    total_events: int
    upcoming_deadlines: int
    overdue_count: int
    total_effort_hours: float


@router.get("/timeline", response_model=TimelineSchema, summary="Get regulatory change timeline")
async def get_timeline(db: DB, copilot: CopilotDep, framework: str | None = None,
                       jurisdiction: str | None = None, days_ahead: int = 365) -> TimelineSchema:
    service = ImpactTimelineService(db=db, copilot_client=copilot)
    view = await service.get_timeline(framework=framework, jurisdiction=jurisdiction, days_ahead=days_ahead)
    return TimelineSchema(
        events=[EventSchema(
            id=str(e.id), title=e.title, event_type=e.event_type.value,
            framework=e.framework, jurisdiction=e.jurisdiction,
            days_remaining=e.days_remaining, impact_score=e.impact_score,
            estimated_effort_hours=e.estimated_effort_hours,
            affected_repos=e.affected_repos, is_predicted=e.is_predicted, confidence=e.confidence,
        ) for e in view.events],
        total_events=view.total_events, upcoming_deadlines=view.upcoming_deadlines,
        overdue_count=view.overdue_count, total_effort_hours=view.total_effort_hours,
    )


@router.post("/events", response_model=EventSchema, status_code=status.HTTP_201_CREATED, summary="Add timeline event")
async def add_event(request: AddEventRequest, db: DB, copilot: CopilotDep) -> EventSchema:
    service = ImpactTimelineService(db=db, copilot_client=copilot)
    try:
        et = TimelineEventType(request.event_type)
    except ValueError:
        et = TimelineEventType.REGULATION_EFFECTIVE

    effective = datetime.fromisoformat(request.effective_date)
    event = await service.add_event(
        title=request.title, framework=request.framework, jurisdiction=request.jurisdiction,
        effective_date=effective, event_type=et, impact_score=request.impact_score,
        effort_hours=request.effort_hours, affected_repos=request.affected_repos,
    )
    return EventSchema(
        id=str(event.id), title=event.title, event_type=event.event_type.value,
        framework=event.framework, jurisdiction=event.jurisdiction,
        days_remaining=event.days_remaining, impact_score=event.impact_score,
        estimated_effort_hours=event.estimated_effort_hours,
        affected_repos=event.affected_repos, is_predicted=event.is_predicted, confidence=event.confidence,
    )


@router.post("/events/{event_id}/tasks", response_model=list[TaskSchema], summary="Generate tasks from event")
async def generate_tasks(event_id: str, db: DB, copilot: CopilotDep) -> list[TaskSchema]:
    service = ImpactTimelineService(db=db, copilot_client=copilot)
    try:
        tasks = await service.generate_tasks(UUID(event_id))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return [TaskSchema(
        id=str(t.id), title=t.title, priority=t.priority.value, status=t.status.value,
        estimated_hours=t.estimated_hours,
        due_date=t.due_date.isoformat() if t.due_date else None,
    ) for t in tasks]


@router.get("/tasks", response_model=list[TaskSchema], summary="List remediation tasks")
async def list_tasks(db: DB, copilot: CopilotDep, task_status: str | None = None) -> list[TaskSchema]:
    service = ImpactTimelineService(db=db, copilot_client=copilot)
    ts = TaskStatus(task_status) if task_status else None
    tasks = await service.get_tasks(status=ts)
    return [TaskSchema(
        id=str(t.id), title=t.title, priority=t.priority.value, status=t.status.value,
        estimated_hours=t.estimated_hours,
        due_date=t.due_date.isoformat() if t.due_date else None,
    ) for t in tasks]
