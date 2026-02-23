"""API endpoints for Realtime Compliance Posture."""

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


class PostureSnapshotResponse(BaseModel):
    model_config = {"extra": "ignore"}
    organization_id: str = ""
    score: float = 0.0
    grade: str = ""
    violations: int = 0
    timestamp: str | None = None


class PostureEventRequest(BaseModel):
    event_type: str = Field(..., description="Type of posture event")
    organization_id: UUID = Field(..., description="Organization that generated the event")
    score_delta: float = Field(..., description="Impact on posture score")
    details: dict[str, Any] = Field(default_factory=dict)


class PostureEventResponse(BaseModel):
    model_config = {"extra": "ignore"}
    id: str = ""
    event_type: str = ""
    organization_id: str = ""
    score_delta: float = 0.0
    details: dict = Field(default_factory=dict)
    timestamp: str | None = None


class PostureEventListResponse(BaseModel):
    model_config = {"extra": "ignore"}
    events: list[PostureEventResponse] = Field(default_factory=list)


class AlertRuleRequest(BaseModel):
    name: str = Field(..., description="Name of the alert rule")
    metric: str = Field(..., description="Metric to monitor")
    threshold: float = Field(..., description="Threshold value to trigger alert")
    channel: str = Field(..., description="Notification channel (e.g. 'slack', 'email')")


class AlertRuleResponse(BaseModel):
    model_config = {"extra": "ignore"}
    id: str = ""
    name: str = ""
    metric: str = ""
    threshold: float = 0.0
    channel: str = ""
    enabled: bool = True


class AlertRuleListResponse(BaseModel):
    model_config = {"extra": "ignore"}
    rules: list[AlertRuleResponse] = Field(default_factory=list)


class AlertCheckResponse(BaseModel):
    model_config = {"extra": "ignore"}
    alerts_triggered: int
    alerts: list[dict[str, Any]] = Field(default_factory=list)


class StreamConfigResponse(BaseModel):
    model_config = {"extra": "ignore"}
    enabled: bool
    interval_seconds: int
    buffer_size: int
    config: dict[str, Any] = Field(default_factory=dict)


# --- Endpoints ---


@router.get(
    "/current", response_model=PostureSnapshotResponse, summary="Get current posture snapshot"
)
async def get_current_posture(db: DB) -> PostureSnapshotResponse:
    """Get the current compliance posture snapshot."""
    from app.services.realtime_posture import RealtimePostureService

    service = RealtimePostureService(db=db)
    snapshot = await service.get_current_posture(organization_id="default")
    return PostureSnapshotResponse(**_serialize(snapshot))


@router.post(
    "/events",
    response_model=PostureEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a posture event",
)
async def record_posture_event(request: PostureEventRequest, db: DB) -> PostureEventResponse:
    """Record a new compliance posture event."""
    from app.services.realtime_posture import RealtimePostureService

    service = RealtimePostureService(db=db)
    from app.services.realtime_posture.models import PostureEvent

    event = await service.record_event(
        event_type=PostureEvent(request.event_type),
        organization_id=str(request.organization_id),
        details=request.details or {},
    )
    return PostureEventResponse(**event) if isinstance(event, dict) else PostureEventResponse(**_serialize(event))


@router.get("/events", response_model=PostureEventListResponse, summary="List posture events")
async def list_posture_events(db: DB, limit: int = 50) -> PostureEventListResponse:
    """List recent compliance posture events."""
    from app.services.realtime_posture import RealtimePostureService

    service = RealtimePostureService(db=db)
    events = await service.list_events(limit=limit)
    return PostureEventListResponse(
        events=[PostureEventResponse(**_serialize(e)) for e in events],
        total=len(events),
    )


@router.post(
    "/alert-rules",
    response_model=AlertRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an alert rule",
)
async def create_alert_rule(request: AlertRuleRequest, db: DB) -> AlertRuleResponse:
    """Create a new posture alert rule."""
    from app.services.realtime_posture import RealtimePostureService
    from app.services.realtime_posture.models import AlertRule as AlertRuleModel

    service = RealtimePostureService(db=db)
    rule_obj = AlertRuleModel(
        name=request.name,
        metric=request.metric,
        threshold=request.threshold,
        channel=request.channel,
    )
    rule = await service.create_alert_rule(rule=rule_obj)
    return AlertRuleResponse(**_serialize(rule))


@router.get("/alert-rules", response_model=AlertRuleListResponse, summary="List alert rules")
async def list_alert_rules(db: DB) -> AlertRuleListResponse:
    """List all posture alert rules."""
    from app.services.realtime_posture import RealtimePostureService

    service = RealtimePostureService(db=db)
    rules = await service.list_alert_rules()
    return AlertRuleListResponse(
        rules=[AlertRuleResponse(**_serialize(r)) for r in rules],
        total=len(rules),
    )


@router.delete(
    "/alert-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete an alert rule"
)
async def delete_alert_rule(rule_id: UUID, db: DB) -> None:
    """Delete a posture alert rule."""
    from app.services.realtime_posture import RealtimePostureService

    service = RealtimePostureService(db=db)
    deleted = await service.delete_alert_rule(rule_id=rule_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert rule not found")


@router.post("/check-alerts", response_model=AlertCheckResponse, summary="Trigger alert check")
async def check_alerts(db: DB) -> AlertCheckResponse:
    """Trigger an immediate alert check against current posture."""
    from app.services.realtime_posture import RealtimePostureService

    service = RealtimePostureService(db=db)
    result = await service.check_alerts(organization_id="default")
    return AlertCheckResponse(**_serialize(result))


@router.get(
    "/stream-config", response_model=StreamConfigResponse, summary="Get streaming configuration"
)
async def get_stream_config(db: DB) -> StreamConfigResponse:
    """Get the realtime posture streaming configuration."""
    from app.services.realtime_posture import RealtimePostureService

    service = RealtimePostureService(db=db)
    config = await service.get_posture_stream_config()
    return StreamConfigResponse(**_serialize(config))
