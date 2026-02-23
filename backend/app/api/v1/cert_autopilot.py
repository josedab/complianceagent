"""API endpoints for Certification Autopilot."""

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
