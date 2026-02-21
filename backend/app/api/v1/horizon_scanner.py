"""Regulatory Horizon Scanner API endpoints."""

from uuid import UUID

import structlog
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep
from app.services.horizon_scanner import HorizonScannerService


logger = structlog.get_logger()
router = APIRouter()


class TimelineResponse(BaseModel):
    total_tracked: int
    high_impact_count: int
    upcoming: list[dict]
    alerts: list[dict]


class ImpactRequest(BaseModel):
    repo_url: str = Field(default="", description="Repository URL for impact analysis")


class ImpactResponse(BaseModel):
    affected_files: int
    affected_modules: list[str]
    estimated_effort_days: float
    impact_severity: str
    recommendations: list[str]
    confidence_score: float


@router.get("/timeline", response_model=TimelineResponse)
async def get_horizon_timeline(
    db: DB,
    jurisdiction: str | None = Query(None, description="Filter by jurisdiction (EU, US, UK, etc.)"),
    framework: str | None = Query(None, description="Filter by framework (GDPR, HIPAA, etc.)"),
    months_ahead: int = Query(24, ge=1, le=60, description="Months to look ahead"),
) -> TimelineResponse:
    """Get the regulatory horizon timeline showing upcoming legislation."""
    svc = HorizonScannerService(db)
    timeline = await svc.get_timeline(jurisdiction=jurisdiction, framework=framework, months_ahead=months_ahead)

    return TimelineResponse(
        total_tracked=timeline.total_tracked,
        high_impact_count=timeline.high_impact_count,
        upcoming=[
            {
                "id": str(leg.id),
                "title": leg.title,
                "jurisdiction": leg.jurisdiction,
                "status": leg.status.value,
                "confidence": leg.confidence.value,
                "frameworks_affected": leg.frameworks_affected,
                "expected_effective_date": leg.expected_effective_date.isoformat() if leg.expected_effective_date else None,
                "tags": leg.tags,
            }
            for leg in timeline.upcoming
        ],
        alerts=[
            {
                "id": str(a.id),
                "title": a.title,
                "message": a.message,
                "severity": a.severity.value,
                "months_until_effective": a.months_until_effective,
            }
            for a in timeline.alerts
        ],
    )


@router.get("/alerts")
async def get_horizon_alerts(
    db: DB,
    severity: str | None = Query(None, description="Filter by severity"),
) -> list[dict]:
    """Get active regulatory horizon alerts."""
    from app.services.horizon_scanner.models import ImpactSeverity

    svc = HorizonScannerService(db)
    sev = ImpactSeverity(severity) if severity else None
    alerts = await svc.get_alerts(severity=sev)
    return [
        {
            "id": str(a.id),
            "title": a.title,
            "message": a.message,
            "severity": a.severity.value,
            "months_until_effective": a.months_until_effective,
        }
        for a in alerts
    ]


@router.post("/predict-impact/{legislation_id}", response_model=ImpactResponse)
async def predict_impact(
    legislation_id: UUID,
    request: ImpactRequest,
    db: DB,
    copilot: CopilotDep,
) -> ImpactResponse:
    """Predict codebase impact for a pending regulation."""
    svc = HorizonScannerService(db, copilot_client=copilot)
    prediction = await svc.predict_impact(legislation_id, repo_url=request.repo_url)

    return ImpactResponse(
        affected_files=prediction.affected_files,
        affected_modules=prediction.affected_modules,
        estimated_effort_days=prediction.estimated_effort_days,
        impact_severity=prediction.impact_severity.value,
        recommendations=prediction.recommendations,
        confidence_score=prediction.confidence_score,
    )
