"""API endpoints for Telemetry Mesh observability."""

from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.telemetry_mesh import ServiceTier, SLOType, TelemetryMeshService


logger = structlog.get_logger()
router = APIRouter()


class ServiceRegistrationRequest(BaseModel):
    name: str = Field(...)
    tier: str = Field(...)


class MetricsReportRequest(BaseModel):
    metrics: dict[str, float] = Field(...)


class SLODefinitionRequest(BaseModel):
    name: str = Field(...)
    slo_type: str = Field(...)
    target: float = Field(...)
    window_hours: int = Field(default=24)


@router.post("/services", status_code=status.HTTP_201_CREATED, summary="Register a service")
async def register_service(request: ServiceRegistrationRequest, db: DB) -> dict:
    """Register a new service for monitoring."""
    service = TelemetryMeshService(db=db)
    result = await service.register_service(
        name=request.name,
        tier=ServiceTier(request.tier),
    )
    return {
        "service_name": result.service_name,
        "tier": result.tier.value,
        "health_score": result.health_score,
        "last_heartbeat": result.last_heartbeat.isoformat() if result.last_heartbeat else None,
    }


@router.post("/services/{name}/metrics", summary="Report metrics for a service")
async def report_metrics(name: str, request: MetricsReportRequest, db: DB) -> dict:
    """Report metrics for a service and update health score."""
    service = TelemetryMeshService(db=db)
    try:
        result = await service.report_metrics(
            service_name=name,
            metrics=request.metrics,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    return {
        "service_name": result.service_name,
        "tier": result.tier.value,
        "metrics": result.metrics,
        "health_score": result.health_score,
        "last_heartbeat": result.last_heartbeat.isoformat() if result.last_heartbeat else None,
    }


@router.post("/slos", status_code=status.HTTP_201_CREATED, summary="Define an SLO")
async def define_slo(request: SLODefinitionRequest, db: DB) -> dict:
    """Define a new SLO."""
    service = TelemetryMeshService(db=db)
    result = await service.define_slo(
        name=request.name,
        slo_type=SLOType(request.slo_type),
        target=request.target,
        window_hours=request.window_hours,
    )
    return {
        "id": str(result.id),
        "name": result.name,
        "slo_type": result.slo_type.value,
        "target": result.target,
        "current": result.current,
        "window_hours": result.window_hours,
        "in_compliance": result.in_compliance,
    }


@router.post("/slos/evaluate", summary="Evaluate all SLOs")
async def evaluate_slos(db: DB) -> list[dict]:
    """Evaluate all SLOs against current metrics."""
    service = TelemetryMeshService(db=db)
    results = await service.evaluate_slos()
    return [
        {
            "id": str(s.id),
            "name": s.name,
            "slo_type": s.slo_type.value,
            "target": s.target,
            "current": s.current,
            "in_compliance": s.in_compliance,
            "last_evaluated": s.last_evaluated.isoformat() if s.last_evaluated else None,
        }
        for s in results
    ]


@router.post("/services/{name}/anomalies", summary="Detect anomalies for a service")
async def detect_anomalies(name: str, db: DB) -> list[dict]:
    """Detect anomalies for a service."""
    service = TelemetryMeshService(db=db)
    try:
        anomalies = await service.detect_anomalies(service_name=name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    return [
        {
            "id": str(a.id),
            "service_name": a.service_name,
            "anomaly_type": a.anomaly_type.value,
            "metric_name": a.metric_name,
            "expected_value": a.expected_value,
            "actual_value": a.actual_value,
            "deviation_pct": a.deviation_pct,
            "severity": a.severity,
            "detected_at": a.detected_at.isoformat() if a.detected_at else None,
        }
        for a in anomalies
    ]


@router.post("/anomalies/{anomaly_id}/resolve", summary="Resolve an anomaly")
async def resolve_anomaly(anomaly_id: UUID, db: DB) -> dict:
    """Resolve a detected anomaly."""
    service = TelemetryMeshService(db=db)
    try:
        result = await service.resolve_anomaly(anomaly_id=anomaly_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    return {
        "id": str(result.id),
        "service_name": result.service_name,
        "resolved": result.resolved,
    }


@router.get("/services", summary="List all services")
async def list_services(db: DB) -> list[dict]:
    """List all monitored services."""
    service = TelemetryMeshService(db=db)
    services = await service.list_services()
    return [
        {
            "service_name": s.service_name,
            "tier": s.tier.value,
            "metrics": s.metrics,
            "health_score": s.health_score,
            "last_heartbeat": s.last_heartbeat.isoformat() if s.last_heartbeat else None,
        }
        for s in services
    ]


@router.get("/slos", summary="List all SLOs")
async def list_slos(db: DB) -> list[dict]:
    """List all defined SLOs."""
    service = TelemetryMeshService(db=db)
    slos = await service.list_slos()
    return [
        {
            "id": str(s.id),
            "name": s.name,
            "slo_type": s.slo_type.value,
            "target": s.target,
            "current": s.current,
            "in_compliance": s.in_compliance,
        }
        for s in slos
    ]


@router.get("/anomalies", summary="List all anomalies")
async def list_anomalies(db: DB, active_only: bool = False) -> list[dict]:
    """List detected anomalies."""
    service = TelemetryMeshService(db=db)
    anomalies = await service.list_anomalies(active_only=active_only)
    return [
        {
            "id": str(a.id),
            "service_name": a.service_name,
            "anomaly_type": a.anomaly_type.value,
            "metric_name": a.metric_name,
            "severity": a.severity,
            "resolved": a.resolved,
            "detected_at": a.detected_at.isoformat() if a.detected_at else None,
        }
        for a in anomalies
    ]


@router.get("/stats", summary="Get telemetry mesh stats")
async def get_stats(db: DB) -> dict:
    """Get aggregate telemetry statistics."""
    service = TelemetryMeshService(db=db)
    stats = await service.get_stats()
    return {
        "services_monitored": stats.services_monitored,
        "slos_defined": stats.slos_defined,
        "slos_in_compliance": stats.slos_in_compliance,
        "anomalies_detected": stats.anomalies_detected,
        "anomalies_active": stats.anomalies_active,
        "avg_health_score": stats.avg_health_score,
    }
