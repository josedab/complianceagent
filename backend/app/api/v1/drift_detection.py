"""API endpoints for Compliance Drift Detection."""

from datetime import datetime
from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB

from app.services.drift_detection import (
    AlertChannel,
    AlertConfig,
    CICDGateDecision,
    CICDGateResult,
    DriftDetectionService,
    DriftSeverity,
    DriftType,
)

logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---


class CaptureBaselineRequest(BaseModel):
    """Request to capture a compliance baseline."""

    repo: str = Field(..., description="Repository full name")
    branch: str = Field(default="main")
    commit_sha: str = Field(default="")


class DetectDriftRequest(BaseModel):
    """Request to detect drift."""

    repo: str = Field(..., description="Repository full name")
    branch: str = Field(default="main")
    commit_sha: str = Field(default="")
    current_findings: list[dict[str, Any]] = Field(default_factory=list)
    current_score: float = Field(default=100.0)


class DriftEventSchema(BaseModel):
    """Drift event response."""

    id: str
    repo: str
    branch: str
    drift_type: str
    severity: str
    regulation: str
    description: str
    file_path: str
    commit_sha: str
    previous_score: float
    current_score: float
    detected_at: str | None
    resolved_at: str | None


class BaselineSchema(BaseModel):
    """Baseline response."""

    id: str
    repo: str
    branch: str
    commit_sha: str
    score: float
    findings_count: int
    captured_at: str | None


class AlertConfigRequest(BaseModel):
    """Alert configuration request."""

    channels: list[str] = Field(default_factory=lambda: ["email"])
    severity_threshold: str = Field(default="medium")
    recipients: dict[str, list[str]] = Field(default_factory=dict)
    batch_interval_seconds: int = Field(default=300)
    slack_webhook_url: str = Field(default="")
    teams_webhook_url: str = Field(default="")


class DriftReportSchema(BaseModel):
    """Drift report response."""

    repo: str
    total_events: int
    events_by_severity: dict[str, int]
    events_by_type: dict[str, int]
    top_drifting_files: list[dict[str, Any]]


class CICDGateRequest(BaseModel):
    """CI/CD compliance gate request."""

    repo: str = Field(..., description="Repository full name")
    branch: str = Field(default="main")
    commit_sha: str = Field(default="")
    current_score: float = Field(default=100.0, ge=0, le=100)
    current_findings: list[dict[str, Any]] = Field(default_factory=list)
    threshold_score: float = Field(default=80.0, ge=0, le=100)
    block_on_critical: bool = Field(default=True, description="Block pipeline on critical violations")


class CICDGateSchema(BaseModel):
    """CI/CD gate decision response."""

    id: str
    repo: str
    branch: str
    commit_sha: str
    decision: str
    current_score: float
    threshold_score: float
    violations_found: int
    critical_violations: int
    blocking_findings: list[str]
    warnings: list[str]
    checked_at: str | None


class DriftTrendSchema(BaseModel):
    """Drift trend response."""

    repo: str
    period: str
    data_points: list[dict[str, Any]]
    trend_direction: str
    avg_score: float
    min_score: float
    max_score: float
    volatility: float


class TopDriftingFileSchema(BaseModel):
    """Top drifting file response."""

    file_path: str
    drift_count: int
    total_delta: float
    last_drift_at: str
    regulations_affected: list[str]


class WebhookDeliverySchema(BaseModel):
    """Webhook delivery response."""

    id: str
    channel: str
    url: str
    event_id: str
    status: str
    response_code: int | None
    delivered_at: str | None
    attempts: int


# --- Endpoints ---


@router.post(
    "/baseline",
    response_model=BaselineSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Capture compliance baseline",
)
async def capture_baseline(
    request: CaptureBaselineRequest,
    db: DB,
) -> BaselineSchema:
    """Capture current compliance state as baseline."""
    service = DriftDetectionService(db=db)
    baseline = await service.capture_baseline(
        repo=request.repo, branch=request.branch, commit_sha=request.commit_sha,
    )
    return BaselineSchema(
        id=str(baseline.id), repo=baseline.repo, branch=baseline.branch,
        commit_sha=baseline.commit_sha, score=baseline.score,
        findings_count=baseline.findings_count,
        captured_at=baseline.captured_at.isoformat() if baseline.captured_at else None,
    )


@router.post(
    "/detect",
    response_model=list[DriftEventSchema],
    summary="Detect compliance drift",
)
async def detect_drift(
    request: DetectDriftRequest,
    db: DB,
) -> list[DriftEventSchema]:
    """Detect compliance drift against baseline."""
    service = DriftDetectionService(db=db)
    events = await service.detect_drift(
        repo=request.repo, branch=request.branch, commit_sha=request.commit_sha,
        current_findings=request.current_findings, current_score=request.current_score,
    )
    return [
        DriftEventSchema(
            id=str(e.id), repo=e.repo, branch=e.branch,
            drift_type=e.drift_type.value, severity=e.severity.value,
            regulation=e.regulation, description=e.description,
            file_path=e.file_path, commit_sha=e.commit_sha,
            previous_score=e.previous_score, current_score=e.current_score,
            detected_at=e.detected_at.isoformat() if e.detected_at else None,
            resolved_at=e.resolved_at.isoformat() if e.resolved_at else None,
        )
        for e in events
    ]


@router.get(
    "/events",
    response_model=list[DriftEventSchema],
    summary="List drift events",
)
async def list_events(
    db: DB,
    repo: str | None = None,
    severity: str | None = None,
    drift_type: str | None = None,
    limit: int = 50,
) -> list[DriftEventSchema]:
    """List drift events with filters."""
    service = DriftDetectionService(db=db)
    s = DriftSeverity(severity) if severity else None
    dt = DriftType(drift_type) if drift_type else None
    events = await service.list_events(repo=repo, severity=s, drift_type=dt, limit=limit)
    return [
        DriftEventSchema(
            id=str(e.id), repo=e.repo, branch=e.branch,
            drift_type=e.drift_type.value, severity=e.severity.value,
            regulation=e.regulation, description=e.description,
            file_path=e.file_path, commit_sha=e.commit_sha,
            previous_score=e.previous_score, current_score=e.current_score,
            detected_at=e.detected_at.isoformat() if e.detected_at else None,
            resolved_at=e.resolved_at.isoformat() if e.resolved_at else None,
        )
        for e in events
    ]


@router.post(
    "/events/{event_id}/resolve",
    summary="Resolve drift event",
)
async def resolve_event(event_id: UUID, db: DB) -> dict:
    """Mark a drift event as resolved."""
    service = DriftDetectionService(db=db)
    event = await service.resolve_event(event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return {"status": "resolved", "event_id": str(event_id)}


@router.put(
    "/alerts/config",
    summary="Configure alerts",
)
async def configure_alerts(request: AlertConfigRequest, db: DB) -> dict:
    """Update alert configuration."""
    service = DriftDetectionService(db=db)
    config = AlertConfig(
        channels=[AlertChannel(c) for c in request.channels],
        severity_threshold=DriftSeverity(request.severity_threshold),
        recipients=request.recipients,
        batch_interval_seconds=request.batch_interval_seconds,
        slack_webhook_url=request.slack_webhook_url,
        teams_webhook_url=request.teams_webhook_url,
    )
    await service.configure_alerts(config)
    return {"status": "updated"}


@router.get(
    "/report/{repo:path}",
    response_model=DriftReportSchema,
    summary="Get drift report",
)
async def get_report(repo: str, db: DB) -> DriftReportSchema:
    """Generate drift report for a repository."""
    service = DriftDetectionService(db=db)
    report = await service.get_report(repo=repo)
    return DriftReportSchema(
        repo=report.repo, total_events=report.total_events,
        events_by_severity=report.events_by_severity,
        events_by_type=report.events_by_type,
        top_drifting_files=report.top_drifting_files,
    )


@router.post(
    "/cicd-gate",
    response_model=CICDGateSchema,
    summary="CI/CD compliance gate check",
)
async def check_cicd_gate(
    request: CICDGateRequest,
    db: DB,
) -> CICDGateSchema:
    """Check compliance gate for CI/CD pipeline.

    Returns pass/fail/warn decision. Use in GitHub Actions or GitLab CI
    to block merges when compliance score drops below threshold.
    """
    service = DriftDetectionService(db=db)
    result = await service.check_cicd_gate(
        repo=request.repo, branch=request.branch,
        commit_sha=request.commit_sha,
        current_score=request.current_score,
        current_findings=request.current_findings,
        threshold_score=request.threshold_score,
        block_on_critical=request.block_on_critical,
    )
    return CICDGateSchema(
        id=str(result.id), repo=result.repo, branch=result.branch,
        commit_sha=result.commit_sha, decision=result.decision.value,
        current_score=result.current_score, threshold_score=result.threshold_score,
        violations_found=result.violations_found,
        critical_violations=result.critical_violations,
        blocking_findings=result.blocking_findings,
        warnings=result.warnings,
        checked_at=result.checked_at.isoformat() if result.checked_at else None,
    )


@router.get(
    "/trend/{repo:path}",
    response_model=DriftTrendSchema,
    summary="Get compliance drift trend",
)
async def get_drift_trend(
    repo: str,
    db: DB,
    period: str = "7d",
) -> DriftTrendSchema:
    """Get compliance drift trend over time."""
    service = DriftDetectionService(db=db)
    trend = service.get_drift_trend(repo, period)
    return DriftTrendSchema(**trend.to_dict())


@router.get(
    "/top-drifting/{repo:path}",
    response_model=list[TopDriftingFileSchema],
    summary="Get top drifting files",
)
async def get_top_drifting_files(
    repo: str,
    db: DB,
    limit: int = 10,
) -> list[TopDriftingFileSchema]:
    """Get files with the most compliance drift."""
    service = DriftDetectionService(db=db)
    files = service.get_top_drifting_files(repo, limit)
    return [TopDriftingFileSchema(**f.to_dict()) for f in files]


@router.post(
    "/webhook-deliver",
    response_model=WebhookDeliverySchema,
    status_code=status.HTTP_201_CREATED,
    summary="Deliver webhook notification",
)
async def deliver_webhook(
    event_id: str,
    channel: str,
    db: DB,
) -> WebhookDeliverySchema:
    """Deliver a webhook notification for a drift event."""
    service = DriftDetectionService(db=db)
    delivery = await service.deliver_webhook(event_id, channel)
    return WebhookDeliverySchema(**delivery.to_dict())


@router.get(
    "/webhook-deliveries",
    response_model=list[WebhookDeliverySchema],
    summary="Get webhook delivery history",
)
async def get_webhook_deliveries(
    db: DB,
    event_id: str | None = None,
    limit: int = 50,
) -> list[WebhookDeliverySchema]:
    """Get webhook delivery history."""
    service = DriftDetectionService(db=db)
    deliveries = service.get_webhook_deliveries(event_id, limit)
    return [WebhookDeliverySchema(**d.to_dict()) for d in deliveries]
