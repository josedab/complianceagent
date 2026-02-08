"""API endpoints for Real-Time Compliance Telemetry."""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep
from app.services.telemetry import (
    AlertSeverity,
    MetricType,
    TelemetryEventType,
    TelemetryService,
)

logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---


class RecordMetricRequest(BaseModel):
    metric_type: str = Field(..., description="Type of metric")
    value: float = Field(..., description="Metric value")
    framework: str | None = Field(default=None)
    repository: str | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EmitEventRequest(BaseModel):
    event_type: str = Field(..., description="Event type")
    title: str = Field(..., min_length=1)
    description: str = Field(default="")
    severity: str = Field(default="info")
    framework: str | None = Field(default=None)
    repository: str | None = Field(default=None)
    metric_value: float | None = Field(default=None)


class SetThresholdRequest(BaseModel):
    metric_type: str = Field(...)
    operator: str = Field(..., pattern="^(lt|gt|eq|lte|gte)$")
    value: float = Field(...)
    severity: str = Field(default="warning")
    channels: list[str] = Field(default_factory=lambda: ["websocket"])
    cooldown_minutes: int = Field(default=60, ge=1)


class MetricSchema(BaseModel):
    id: str
    metric_type: str
    value: float
    previous_value: float | None
    framework: str | None
    repository: str | None
    timestamp: str | None


class EventSchema(BaseModel):
    id: str
    event_type: str
    severity: str
    title: str
    description: str
    framework: str | None
    repository: str | None
    metric_value: float | None
    timestamp: str | None


class ThresholdSchema(BaseModel):
    id: str
    metric_type: str
    operator: str
    value: float
    severity: str
    channels: list[str]
    enabled: bool
    cooldown_minutes: int


class TimeSeriesSchema(BaseModel):
    metric_type: str
    period: str
    framework: str | None
    data_points: list[dict[str, Any]]
    latest_value: float | None
    trend: float | None


# --- Endpoints ---


@router.get(
    "/snapshot",
    summary="Get current telemetry snapshot",
    description="Get a real-time snapshot of all key compliance metrics",
)
async def get_snapshot(db: DB, copilot: CopilotDep) -> dict:
    service = TelemetryService(db=db, copilot_client=copilot)
    snapshot = await service.get_current_snapshot()
    return snapshot.to_dict()


@router.post(
    "/metrics",
    response_model=MetricSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Record a telemetry metric",
)
async def record_metric(request: RecordMetricRequest, db: DB, copilot: CopilotDep) -> MetricSchema:
    service = TelemetryService(db=db, copilot_client=copilot)
    try:
        mt = MetricType(request.metric_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid metric type: {request.metric_type}")

    metric = await service.record_metric(
        metric_type=mt,
        value=request.value,
        framework=request.framework,
        repository=request.repository,
        metadata=request.metadata,
    )
    return MetricSchema(
        id=str(metric.id),
        metric_type=metric.metric_type.value,
        value=metric.value,
        previous_value=metric.previous_value,
        framework=metric.framework,
        repository=metric.repository,
        timestamp=metric.timestamp.isoformat() if metric.timestamp else None,
    )


@router.post(
    "/events",
    response_model=EventSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Emit a telemetry event",
)
async def emit_event(request: EmitEventRequest, db: DB, copilot: CopilotDep) -> EventSchema:
    service = TelemetryService(db=db, copilot_client=copilot)
    try:
        et = TelemetryEventType(request.event_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid event type: {request.event_type}")

    sev = AlertSeverity(request.severity) if request.severity in AlertSeverity.__members__.values() else AlertSeverity.INFO

    event = await service.emit_event(
        event_type=et,
        title=request.title,
        description=request.description,
        severity=sev,
        framework=request.framework,
        repository=request.repository,
        metric_value=request.metric_value,
    )
    return EventSchema(
        id=str(event.id),
        event_type=event.event_type.value,
        severity=event.severity.value,
        title=event.title,
        description=event.description,
        framework=event.framework,
        repository=event.repository,
        metric_value=event.metric_value,
        timestamp=event.timestamp.isoformat() if event.timestamp else None,
    )


@router.get(
    "/events",
    response_model=list[EventSchema],
    summary="List telemetry events",
)
async def list_events(
    db: DB,
    copilot: CopilotDep,
    event_type: str | None = None,
    severity: str | None = None,
    limit: int = 50,
) -> list[EventSchema]:
    service = TelemetryService(db=db, copilot_client=copilot)
    et = TelemetryEventType(event_type) if event_type else None
    sev = AlertSeverity(severity) if severity else None

    events = await service.get_events(event_type=et, severity=sev, limit=limit)
    return [
        EventSchema(
            id=str(e.id),
            event_type=e.event_type.value,
            severity=e.severity.value,
            title=e.title,
            description=e.description,
            framework=e.framework,
            repository=e.repository,
            metric_value=e.metric_value,
            timestamp=e.timestamp.isoformat() if e.timestamp else None,
        )
        for e in events
    ]


@router.get(
    "/time-series/{metric_type}",
    response_model=TimeSeriesSchema,
    summary="Get metric time series",
)
async def get_time_series(
    metric_type: str,
    db: DB,
    copilot: CopilotDep,
    period: str = "24h",
    framework: str | None = None,
) -> TimeSeriesSchema:
    try:
        mt = MetricType(metric_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid metric type: {metric_type}")

    service = TelemetryService(db=db, copilot_client=copilot)
    series = await service.get_time_series(metric_type=mt, period=period, framework=framework)

    return TimeSeriesSchema(
        metric_type=series.metric_type.value,
        period=series.period,
        framework=series.framework,
        data_points=[
            {"value": round(p.value, 2), "timestamp": p.timestamp.isoformat() if p.timestamp else None}
            for p in series.data_points
        ],
        latest_value=round(series.latest_value, 2) if series.latest_value is not None else None,
        trend=round(series.trend, 2) if series.trend is not None else None,
    )


@router.get(
    "/thresholds",
    response_model=list[ThresholdSchema],
    summary="List alert thresholds",
)
async def list_thresholds(db: DB, copilot: CopilotDep) -> list[ThresholdSchema]:
    service = TelemetryService(db=db, copilot_client=copilot)
    thresholds = await service.get_thresholds()
    return [
        ThresholdSchema(
            id=str(t.id),
            metric_type=t.metric_type.value,
            operator=t.operator,
            value=t.value,
            severity=t.severity.value,
            channels=[c.value for c in t.channels],
            enabled=t.enabled,
            cooldown_minutes=t.cooldown_minutes,
        )
        for t in thresholds
    ]


@router.post(
    "/thresholds",
    response_model=ThresholdSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create alert threshold",
)
async def create_threshold(request: SetThresholdRequest, db: DB, copilot: CopilotDep) -> ThresholdSchema:
    from app.services.telemetry.models import AlertChannel

    service = TelemetryService(db=db, copilot_client=copilot)
    try:
        mt = MetricType(request.metric_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid metric type: {request.metric_type}")

    channels = []
    for ch in request.channels:
        try:
            channels.append(AlertChannel(ch))
        except ValueError:
            pass
    if not channels:
        channels = [AlertChannel.WEBSOCKET]

    sev = AlertSeverity(request.severity) if request.severity in [s.value for s in AlertSeverity] else AlertSeverity.WARNING

    threshold = await service.set_threshold(
        metric_type=mt,
        operator=request.operator,
        value=request.value,
        severity=sev,
        channels=channels,
        cooldown_minutes=request.cooldown_minutes,
    )
    return ThresholdSchema(
        id=str(threshold.id),
        metric_type=threshold.metric_type.value,
        operator=threshold.operator,
        value=threshold.value,
        severity=threshold.severity.value,
        channels=[c.value for c in threshold.channels],
        enabled=threshold.enabled,
        cooldown_minutes=threshold.cooldown_minutes,
    )


@router.get(
    "/heatmap",
    summary="Get compliance heatmap data",
    description="Get framework compliance scores by day for heatmap visualization",
)
async def get_heatmap(
    db: DB,
    copilot: CopilotDep,
    period: str = "7d",
) -> dict:
    service = TelemetryService(db=db, copilot_client=copilot)
    return await service.get_heatmap_data(period=period)
