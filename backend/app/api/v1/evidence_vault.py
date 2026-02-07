"""API endpoints for Compliance Evidence Vault."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB

from app.services.evidence_vault import (
    AuditorRole,
    ControlFramework,
    EvidenceType,
    EvidenceVaultService,
)

logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---


class StoreEvidenceRequest(BaseModel):
    """Request to store evidence."""

    evidence_type: str = Field(..., description="Type of evidence")
    title: str = Field(..., min_length=1)
    description: str = Field(default="")
    content: str = Field(..., min_length=1)
    framework: str = Field(..., description="Control framework")
    control_id: str = Field(..., description="Control identifier")
    control_name: str = Field(default="")
    source: str = Field(default="")
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceItemSchema(BaseModel):
    """Evidence item response."""

    id: str
    evidence_type: str
    title: str
    description: str
    content_hash: str
    framework: str
    control_id: str
    control_name: str
    collected_at: str | None
    source: str


class ControlMappingSchema(BaseModel):
    """Control mapping response."""

    control_id: str
    control_name: str
    framework: str
    evidence_count: int
    coverage_pct: float
    status: str


class CreateAuditorSessionRequest(BaseModel):
    """Request to create an auditor session."""

    auditor_email: str = Field(...)
    auditor_name: str = Field(...)
    firm: str = Field(default="")
    role: str = Field(default="viewer")
    frameworks: list[str] = Field(default_factory=lambda: ["soc2"])
    expires_hours: int = Field(default=72)


class AuditorSessionSchema(BaseModel):
    """Auditor session response."""

    id: str
    auditor_email: str
    auditor_name: str
    firm: str
    role: str
    frameworks: list[str]
    expires_at: str | None
    is_active: bool


class AuditReportSchema(BaseModel):
    """Audit report response."""

    id: str
    framework: str
    title: str
    total_controls: int
    controls_with_evidence: int
    coverage_pct: float
    generated_at: str | None


class GenerateReportRequest(BaseModel):
    """Generate report request."""

    framework: str = Field(...)
    report_format: str = Field(default="pdf")


# --- Endpoints ---


@router.post(
    "/evidence",
    response_model=EvidenceItemSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Store evidence",
    description="Store a new piece of compliance evidence in the immutable vault",
)
async def store_evidence(request: StoreEvidenceRequest, db: DB) -> EvidenceItemSchema:
    """Store compliance evidence."""
    service = EvidenceVaultService(db=db)
    item = await service.store_evidence(
        evidence_type=EvidenceType(request.evidence_type),
        title=request.title,
        description=request.description,
        content=request.content,
        framework=ControlFramework(request.framework),
        control_id=request.control_id,
        control_name=request.control_name,
        source=request.source,
        metadata=request.metadata,
    )
    return EvidenceItemSchema(
        id=str(item.id), evidence_type=item.evidence_type.value,
        title=item.title, description=item.description,
        content_hash=item.content_hash, framework=item.framework.value,
        control_id=item.control_id, control_name=item.control_name,
        collected_at=item.collected_at.isoformat() if item.collected_at else None,
        source=item.source,
    )


@router.get(
    "/evidence",
    response_model=list[EvidenceItemSchema],
    summary="Query evidence",
)
async def query_evidence(
    db: DB,
    framework: str | None = None,
    control_id: str | None = None,
    evidence_type: str | None = None,
    limit: int = 50,
) -> list[EvidenceItemSchema]:
    """Query evidence items."""
    service = EvidenceVaultService(db=db)
    fw = ControlFramework(framework) if framework else None
    et = EvidenceType(evidence_type) if evidence_type else None
    items = await service.get_evidence(framework=fw, control_id=control_id, evidence_type=et, limit=limit)
    return [
        EvidenceItemSchema(
            id=str(i.id), evidence_type=i.evidence_type.value,
            title=i.title, description=i.description,
            content_hash=i.content_hash, framework=i.framework.value,
            control_id=i.control_id, control_name=i.control_name,
            collected_at=i.collected_at.isoformat() if i.collected_at else None,
            source=i.source,
        )
        for i in items
    ]


@router.get(
    "/verify/{framework}",
    summary="Verify evidence chain",
)
async def verify_chain(framework: str, db: DB) -> dict:
    """Verify integrity of an evidence chain."""
    service = EvidenceVaultService(db=db)
    verified = await service.verify_chain(ControlFramework(framework))
    return {"framework": framework, "verified": verified}


@router.get(
    "/controls/{framework}",
    response_model=list[ControlMappingSchema],
    summary="Get control mappings",
)
async def get_control_mappings(framework: str, db: DB) -> list[ControlMappingSchema]:
    """Get control-to-evidence mappings."""
    service = EvidenceVaultService(db=db)
    mappings = await service.get_control_mappings(ControlFramework(framework))
    return [
        ControlMappingSchema(
            control_id=m.control_id, control_name=m.control_name,
            framework=m.framework.value, evidence_count=len(m.evidence_ids),
            coverage_pct=m.coverage_pct, status=m.status,
        )
        for m in mappings
    ]


@router.post(
    "/auditor-sessions",
    response_model=AuditorSessionSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create auditor session",
)
async def create_auditor_session(
    request: CreateAuditorSessionRequest, db: DB,
) -> AuditorSessionSchema:
    """Create a read-only auditor portal session."""
    service = EvidenceVaultService(db=db)
    session = await service.create_auditor_session(
        auditor_email=request.auditor_email,
        auditor_name=request.auditor_name,
        firm=request.firm,
        role=AuditorRole(request.role),
        frameworks=[ControlFramework(f) for f in request.frameworks],
        expires_hours=request.expires_hours,
    )
    return AuditorSessionSchema(
        id=str(session.id), auditor_email=session.auditor_email,
        auditor_name=session.auditor_name, firm=session.firm,
        role=session.role.value,
        frameworks=[f.value for f in session.frameworks],
        expires_at=session.expires_at.isoformat() if session.expires_at else None,
        is_active=session.is_active,
    )


@router.get(
    "/auditor-sessions",
    response_model=list[AuditorSessionSchema],
    summary="List auditor sessions",
)
async def list_auditor_sessions(db: DB) -> list[AuditorSessionSchema]:
    """List all auditor sessions."""
    service = EvidenceVaultService(db=db)
    sessions = await service.list_auditor_sessions()
    return [
        AuditorSessionSchema(
            id=str(s.id), auditor_email=s.auditor_email,
            auditor_name=s.auditor_name, firm=s.firm,
            role=s.role.value,
            frameworks=[f.value for f in s.frameworks],
            expires_at=s.expires_at.isoformat() if s.expires_at else None,
            is_active=s.is_active,
        )
        for s in sessions
    ]


@router.post(
    "/reports",
    response_model=AuditReportSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Generate audit report",
)
async def generate_report(request: GenerateReportRequest, db: DB) -> AuditReportSchema:
    """Generate an audit report."""
    service = EvidenceVaultService(db=db)
    report = await service.generate_report(
        framework=ControlFramework(request.framework),
        report_format=request.report_format,
    )
    return AuditReportSchema(
        id=str(report.id), framework=report.framework.value,
        title=report.title, total_controls=report.total_controls,
        controls_with_evidence=report.controls_with_evidence,
        coverage_pct=report.coverage_pct,
        generated_at=report.generated_at.isoformat() if report.generated_at else None,
    )
