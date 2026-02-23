"""API endpoints for Compliance Observability Pipeline."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.compliance_observability import ComplianceObservabilityService


logger = structlog.get_logger()
router = APIRouter()


class EmitMetricRequest(BaseModel):
    name: str = Field(...)
    value: float = Field(...)
    metric_type: str = Field(default="gauge")
    labels: dict[str, str] = Field(default_factory=dict)
    unit: str = Field(default="")


class MetricSchema(BaseModel):
    name: str
    metric_type: str
    value: float
    labels: dict[str, str]
    unit: str
    recorded_at: str | None


class ConfigureExporterRequest(BaseModel):
    exporter_type: str = Field(...)
    endpoint: str = Field(default="")
    api_key: str = Field(default="")
    labels: dict[str, str] = Field(default_factory=dict)
    flush_interval: int = Field(default=60)


class ExporterSchema(BaseModel):
    id: str
    exporter_type: str
    endpoint: str
    enabled: bool
    flush_interval_seconds: int
    configured_at: str | None


class DashboardSchema(BaseModel):
    name: str
    exporter_type: str
    panels: list[dict[str, Any]]
    url: str


class AlertSchema(BaseModel):
    id: str
    metric_name: str
    condition: str
    threshold: float
    current_value: float
    severity: str
    message: str
    fired_at: str | None
    resolved_at: str | None


class PipelineStatsSchema(BaseModel):
    metrics_emitted: int
    exporters_configured: int
    active_alerts: int
    metrics_by_type: dict[str, int]


@router.post(
    "/metrics",
    response_model=MetricSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Emit metric",
)
async def emit_metric(request: EmitMetricRequest, db: DB) -> MetricSchema:
    service = ComplianceObservabilityService(db=db)
    m = await service.emit_metric(
        name=request.name,
        value=request.value,
        metric_type=request.metric_type,
        labels=request.labels,
        unit=request.unit,
    )
    return MetricSchema(
        name=m.name,
        metric_type=m.metric_type.value,
        value=m.value,
        labels=m.labels,
        unit=m.unit,
        recorded_at=m.recorded_at.isoformat() if m.recorded_at else None,
    )


@router.get("/metrics", response_model=list[MetricSchema], summary="List metrics")
async def list_metrics(db: DB, name_prefix: str | None = None) -> list[MetricSchema]:
    service = ComplianceObservabilityService(db=db)
    metrics = service.list_metrics(name_prefix=name_prefix)
    return [
        MetricSchema(
            name=m.name,
            metric_type=m.metric_type.value,
            value=m.value,
            labels=m.labels,
            unit=m.unit,
            recorded_at=m.recorded_at.isoformat() if m.recorded_at else None,
        )
        for m in metrics
    ]


@router.post(
    "/exporters",
    response_model=ExporterSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Configure exporter",
)
async def configure_exporter(request: ConfigureExporterRequest, db: DB) -> ExporterSchema:
    service = ComplianceObservabilityService(db=db)
    e = await service.configure_exporter(
        exporter_type=request.exporter_type,
        endpoint=request.endpoint,
        api_key=request.api_key,
        labels=request.labels,
        flush_interval=request.flush_interval,
    )
    return ExporterSchema(
        id=str(e.id),
        exporter_type=e.exporter_type.value,
        endpoint=e.endpoint,
        enabled=e.enabled,
        flush_interval_seconds=e.flush_interval_seconds,
        configured_at=e.configured_at.isoformat() if e.configured_at else None,
    )


@router.get("/exporters", response_model=list[ExporterSchema], summary="List exporters")
async def list_exporters(db: DB) -> list[ExporterSchema]:
    service = ComplianceObservabilityService(db=db)
    exporters = service.list_exporters()
    return [
        ExporterSchema(
            id=str(e.id),
            exporter_type=e.exporter_type.value,
            endpoint=e.endpoint,
            enabled=e.enabled,
            flush_interval_seconds=e.flush_interval_seconds,
            configured_at=e.configured_at.isoformat() if e.configured_at else None,
        )
        for e in exporters
    ]


@router.get("/dashboards", response_model=list[DashboardSchema], summary="List dashboards")
async def list_dashboards(db: DB) -> list[DashboardSchema]:
    service = ComplianceObservabilityService(db=db)
    return [
        DashboardSchema(
            name=d.name,
            exporter_type=d.exporter_type.value,
            panels=d.panels,
            url=d.url,
        )
        for d in service.list_dashboards()
    ]


@router.get("/alerts", response_model=list[AlertSchema], summary="List alerts")
async def list_alerts(db: DB, active_only: bool = True) -> list[AlertSchema]:
    service = ComplianceObservabilityService(db=db)
    alerts = service.list_alerts(active_only=active_only)
    return [
        AlertSchema(
            id=str(a.id),
            metric_name=a.metric_name,
            condition=a.condition,
            threshold=a.threshold,
            current_value=a.current_value,
            severity=a.severity.value,
            message=a.message,
            fired_at=a.fired_at.isoformat() if a.fired_at else None,
            resolved_at=a.resolved_at.isoformat() if a.resolved_at else None,
        )
        for a in alerts
    ]


@router.post("/alerts/{alert_id}/resolve", summary="Resolve alert")
async def resolve_alert(alert_id: UUID, db: DB) -> dict:
    service = ComplianceObservabilityService(db=db)
    a = await service.resolve_alert(alert_id)
    if not a:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return {"status": "resolved"}


@router.get("/stats", response_model=PipelineStatsSchema, summary="Get pipeline stats")
async def get_stats(db: DB) -> PipelineStatsSchema:
    service = ComplianceObservabilityService(db=db)
    s = service.get_stats()
    return PipelineStatsSchema(
        metrics_emitted=s.metrics_emitted,
        exporters_configured=s.exporters_configured,
        active_alerts=s.active_alerts,
        metrics_by_type=s.metrics_by_type,
    )
