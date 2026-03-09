"""API endpoints for Certification Autopilot."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.cert_autopilot import CertificationAutopilotService as CertAutopilotService


logger = structlog.get_logger()
router = APIRouter()


def _serialize(obj: Any) -> dict[str, Any]:
    """Convert a dataclass to a JSON-serializable dict."""
    from dataclasses import fields, is_dataclass

    if not is_dataclass(obj):
        return obj

    result = {}
    for f in fields(obj):
        v = getattr(obj, f.name)
        result[f.name] = _ser_val(v)
    return result


def _ser_val(v: Any) -> Any:
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


class StartJourneyRequest(BaseModel):
    framework: str = Field(
        ..., description="Certification framework (e.g. 'SOC2', 'ISO27001', 'HIPAA')"
    )


class JourneyResponse(BaseModel):
    model_config = {"extra": "ignore"}
    id: UUID | None = None
    framework: str = ""
    current_phase: str = ""
    progress_percent: float = 0.0
    started_at: str = ""
    estimated_completion: str = ""
    phases: list[dict[str, Any]] = Field(default_factory=list)


class JourneyListResponse(BaseModel):
    model_config = {"extra": "ignore"}
    journeys: list[JourneyResponse] = Field(default_factory=list)
    total: int = 0


class GapAnalysisResponse(BaseModel):
    model_config = {"extra": "ignore"}
    journey_id: UUID | None = None
    total_controls: int = 0
    controls_met: int = 0
    controls_partial: int = 0
    controls_missing: int = 0
    readiness_score: float = 0.0
    critical_gaps: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class EvidenceCollectionResponse(BaseModel):
    model_config = {"extra": "ignore"}
    journey_id: UUID | None = None
    items_collected: int = 0
    items_pending: int = 0
    items_failed: int = 0
    coverage_percent: float = 0.0
    evidence_items: list[dict[str, Any]] = Field(default_factory=list)


class AdvancePhaseResponse(BaseModel):
    model_config = {"extra": "ignore"}
    journey_id: UUID | None = None
    previous_phase: str = ""
    current_phase: str = ""
    progress_percent: float = 0.0
    next_steps: list[str] = Field(default_factory=list)


class ReadinessDashboardResponse(BaseModel):
    model_config = {"extra": "ignore"}
    journey_id: UUID | None = None
    framework: str = ""
    overall_readiness: float = 0.0
    category_readiness: dict[str, float] = Field(default_factory=dict)
    blockers: list[str] = Field(default_factory=list)
    estimated_days_remaining: int = 0
    details: dict[str, Any] = Field(default_factory=dict)


# --- Endpoints ---


@router.post(
    "/journeys",
    response_model=JourneyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a certification journey",
)
async def start_journey(request: StartJourneyRequest, db: DB) -> JourneyResponse:
    """Start a new certification journey for a framework."""
    from app.services.cert_autopilot import CertificationAutopilotService as CertAutopilotService
    from app.services.cert_autopilot.models import CertificationFramework

    service = CertAutopilotService(db=db)
    journey = await service.start_journey(
        framework=CertificationFramework(request.framework), organization_id="default"
    )
    return JourneyResponse(**_serialize(journey))


@router.get(
    "/journeys", response_model=JourneyListResponse, summary="List active certification journeys"
)
async def list_journeys(db: DB) -> JourneyListResponse:
    """List all active certification journeys."""
    from app.services.cert_autopilot import CertificationAutopilotService as CertAutopilotService

    service = CertAutopilotService(db=db)
    journeys = await service.list_journeys()
    return JourneyListResponse(
        journeys=[JourneyResponse(**_serialize(j)) for j in journeys],
        total=len(journeys),
    )


@router.get(
    "/journeys/{journey_id}",
    response_model=JourneyResponse,
    summary="Get certification journey details",
)
async def get_journey(journey_id: UUID, db: DB) -> JourneyResponse:
    """Get details of a specific certification journey."""
    from app.services.cert_autopilot import CertificationAutopilotService as CertAutopilotService

    service = CertAutopilotService(db=db)
    journey = await service.get_journey(journey_id=journey_id)
    if not journey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journey not found")
    return JourneyResponse(**_serialize(journey))


@router.post(
    "/journeys/{journey_id}/gap-analysis",
    response_model=GapAnalysisResponse,
    summary="Run gap analysis for journey",
)
async def run_gap_analysis(journey_id: UUID, db: DB) -> GapAnalysisResponse:
    """Run a gap analysis for a certification journey."""
    from app.services.cert_autopilot import CertificationAutopilotService as CertAutopilotService

    service = CertAutopilotService(db=db)
    analysis = await service.run_gap_analysis(journey_id=journey_id)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journey not found")
    return GapAnalysisResponse(**_serialize(analysis))


@router.post(
    "/journeys/{journey_id}/collect-evidence",
    response_model=EvidenceCollectionResponse,
    summary="Trigger evidence collection",
)
async def collect_evidence(journey_id: UUID, db: DB) -> EvidenceCollectionResponse:
    """Trigger evidence collection for a certification journey."""
    from app.services.cert_autopilot import CertificationAutopilotService as CertAutopilotService

    service = CertAutopilotService(db=db)
    result = await service.collect_evidence(journey_id=journey_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journey not found")
    return EvidenceCollectionResponse(**_serialize(result))


@router.post(
    "/journeys/{journey_id}/advance",
    response_model=AdvancePhaseResponse,
    summary="Advance to next phase",
)
async def advance_phase(journey_id: UUID, db: DB) -> AdvancePhaseResponse:
    """Advance a certification journey to the next phase."""
    from app.services.cert_autopilot import CertificationAutopilotService as CertAutopilotService

    service = CertAutopilotService(db=db)
    result = await service.advance_phase(journey_id=journey_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journey not found")
    return AdvancePhaseResponse(**_serialize(result))


@router.get(
    "/journeys/{journey_id}/readiness",
    response_model=ReadinessDashboardResponse,
    summary="Get readiness dashboard",
)
async def get_readiness(journey_id: UUID, db: DB) -> ReadinessDashboardResponse:
    """Get the readiness dashboard for a certification journey."""
    from app.services.cert_autopilot import CertificationAutopilotService as CertAutopilotService

    service = CertAutopilotService(db=db)
    dashboard = await service.get_readiness(journey_id=journey_id)
    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journey not found")
    return ReadinessDashboardResponse(**_serialize(dashboard))


# --- Production Endpoints: Evidence Collection, Auditor Portal, Readiness ---


class AutoCollectRequest(BaseModel):
    journey_id: str = Field(..., description="Certification journey ID")
    source_types: list[str] = Field(default_factory=lambda: ["git_commit", "ci_cd_pipeline", "access_log", "cloud_config"])


class AuditorSessionRequest(BaseModel):
    auditor_name: str = Field(..., description="Auditor name")
    auditor_email: str = Field(..., description="Auditor email")
    auditor_firm: str = Field(default="", description="Audit firm name")
    framework: str = Field(default="SOC2", description="Certification framework")
    expires_hours: int = Field(default=72, description="Session expiration in hours")


@router.post("/journeys/{journey_id}/auto-collect", summary="Auto-collect evidence from all sources")
async def auto_collect_evidence(journey_id: str, request: AutoCollectRequest, db: DB) -> dict:
    svc = CertAutopilotService(db=db)
    results = []
    for source_type in request.source_types:
        if source_type == "git_commit":
            evidence = await svc.auto_collect_from_git_commits(journey_id=journey_id)
        elif source_type == "ci_cd_pipeline":
            evidence = await svc.auto_collect_from_cicd(journey_id=journey_id)
        elif source_type == "access_log":
            evidence = await svc.auto_collect_from_access_logs(journey_id=journey_id)
        elif source_type == "cloud_config":
            evidence = await svc.auto_collect_from_cloud_config(journey_id=journey_id)
        else:
            continue
        results.extend(evidence if isinstance(evidence, list) else [evidence])
    return {"collected": len(results), "source_types": request.source_types}


@router.get("/journeys/{journey_id}/auto-collection-stats", summary="Get auto-collection statistics")
async def get_auto_collection_stats(journey_id: str, db: DB) -> dict:
    svc = CertAutopilotService(db=db)
    stats = svc.get_auto_collection_stats(journey_id=journey_id)
    return stats


@router.post("/journeys/{journey_id}/gap-analysis/enhanced", summary="Run enhanced control mapping gap analysis")
async def run_enhanced_gap_analysis(journey_id: str, db: DB) -> dict:
    svc = CertAutopilotService(db=db)
    gaps = svc.run_control_mapping_gap_analysis(journey_id=journey_id)
    return {"total_gaps": len(gaps), "gaps": [{"control_id": g.control_id, "control_name": g.control_name, "status": g.status.value, "auto_collectible": g.auto_collectible} for g in gaps]}


@router.post("/auditor-portal/sessions", summary="Create auditor portal session")
async def create_auditor_session(request: AuditorSessionRequest, db: DB) -> dict:
    svc = CertAutopilotService(db=db)
    session, token = await svc.create_auditor_session(
        auditor_name=request.auditor_name, auditor_email=request.auditor_email,
        auditor_firm=request.auditor_firm, framework=request.framework,
        expires_hours=request.expires_hours,
    )
    return {"session_id": str(session.id), "access_token": token, "expires_at": session.expires_at.isoformat() if session.expires_at else None}


@router.get("/auditor-portal/sessions/{session_id}", summary="Get auditor view")
async def get_auditor_view(session_id: str, access_token: str, db: DB) -> dict:
    svc = CertAutopilotService(db=db)
    valid = svc.validate_auditor_session(session_id=session_id, access_token=access_token)
    if not valid:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Invalid or expired session")
    view = svc.get_auditor_view(session_id=session_id)
    return view


@router.get("/auditor-portal/sessions", summary="List auditor sessions")
async def list_auditor_sessions(db: DB) -> list[dict]:
    svc = CertAutopilotService(db=db)
    sessions = svc.list_auditor_sessions()
    return [{"id": str(s.id), "auditor_name": s.auditor_name, "framework": s.framework, "active": s.active, "expires_at": s.expires_at.isoformat() if hasattr(s, "expires_at") and s.expires_at else None} for s in sessions]


@router.delete("/auditor-portal/sessions/{session_id}", summary="Revoke auditor session")
async def revoke_auditor_session(session_id: str, db: DB) -> dict:
    svc = CertAutopilotService(db=db)
    ok = svc.revoke_auditor_session(session_id=session_id)
    return {"revoked": ok}


@router.post("/journeys/{journey_id}/readiness-report", summary="Generate readiness report")
async def generate_readiness_report(journey_id: str, db: DB) -> dict:
    svc = CertAutopilotService(db=db)
    report = svc.generate_readiness_report(journey_id=journey_id)
    return {
        "framework": report.framework,
        "overall_readiness": report.overall_readiness,
        "auto_collection_rate": report.auto_collection_rate,
        "meets_target": report.auto_collection_rate >= report.target_auto_collection_rate,
        "controls_met": report.controls_met,
        "controls_total": report.controls_total,
        "gap_summary": report.gap_summary,
        "remediation_priorities": report.remediation_priorities,
    }


@router.post("/journeys/{journey_id}/verify-evidence", summary="Verify evidence chain integrity")
async def verify_evidence_chain(journey_id: str, db: DB) -> dict:
    svc = CertAutopilotService(db=db)
    result = svc.verify_evidence_chain(journey_id=journey_id)
    return result
