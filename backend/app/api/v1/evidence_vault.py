"""API endpoints for Compliance Evidence Vault."""

from typing import Any

import structlog
from fastapi import APIRouter, status
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


class CoverageMetricsSchema(BaseModel):
    """Coverage metrics response."""

    framework: str
    total_controls: int
    controls_with_evidence: int
    controls_partial: int
    controls_missing: int
    coverage_percentage: float
    evidence_freshness_avg_days: float
    stale_evidence_count: int
    control_breakdown: list[dict[str, Any]]


class ChainVerificationSchema(BaseModel):
    """Chain verification result response."""

    framework: str
    chain_length: int
    is_valid: bool
    verified_at: str
    invalid_links: list[dict[str, str]]
    tamper_detected: bool
    verification_time_ms: float
    hash_algorithm: str
    root_hash: str


class EvidenceGapSchema(BaseModel):
    """Evidence gap response."""

    control_id: str
    control_name: str
    framework: str
    gap_type: str
    last_evidence_date: str | None
    required_evidence_types: list[str]
    remediation_suggestion: str
    priority: str


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


@router.get(
    "/coverage/{framework}",
    response_model=CoverageMetricsSchema,
    summary="Get coverage metrics",
    description="Get detailed coverage metrics for a compliance framework",
)
async def get_coverage_metrics(framework: str, db: DB) -> CoverageMetricsSchema:
    """Get detailed coverage metrics for a compliance framework."""
    service = EvidenceVaultService(db=db)
    metrics = await service.get_coverage_metrics(ControlFramework(framework))
    return CoverageMetricsSchema(**metrics.to_dict())


@router.get(
    "/verify-enhanced/{framework}",
    response_model=ChainVerificationSchema,
    summary="Enhanced chain verification",
    description="Perform enhanced hash chain verification with detailed results",
)
async def verify_chain_enhanced(framework: str, db: DB) -> ChainVerificationSchema:
    """Perform enhanced hash chain verification with detailed results."""
    service = EvidenceVaultService(db=db)
    result = await service.verify_chain_enhanced(ControlFramework(framework))
    return ChainVerificationSchema(**result.to_dict())


@router.get(
    "/gaps/{framework}",
    response_model=list[EvidenceGapSchema],
    summary="Identify evidence gaps",
    description="Identify gaps in evidence coverage for a framework",
)
async def identify_evidence_gaps(framework: str, db: DB) -> list[EvidenceGapSchema]:
    """Identify gaps in evidence coverage for a framework."""
    service = EvidenceVaultService(db=db)
    gaps = await service.identify_evidence_gaps(ControlFramework(framework))
    return [EvidenceGapSchema(**g.to_dict()) for g in gaps]


# --- Blockchain Anchoring Schemas ---


class BlockchainAnchorSchema(BaseModel):
    """Blockchain anchor response."""

    id: str
    framework: str
    chain_hash: str
    evidence_count: int
    anchor_hash: str
    blockchain_network: str
    transaction_id: str
    block_number: int
    status: str
    anchored_at: str
    confirmed_at: str | None
    cost_usd: float


class BatchVerificationRequestSchema(BaseModel):
    """Request for batch verification."""

    evidence_ids: list[str] | None = Field(default=None, description="Evidence IDs to verify (all if omitted)")


class BatchVerificationResultSchema(BaseModel):
    """Batch verification result response."""

    id: str
    items_verified: int
    items_valid: int
    items_invalid: int
    items_missing: int
    chain_intact: bool
    blockchain_verified: bool
    invalid_items: list[dict[str, Any]]
    verification_duration_ms: float
    verified_at: str


class AuditTimelineEventSchema(BaseModel):
    """Audit timeline event response."""

    id: str
    event_type: str
    description: str
    framework: str
    actor: str
    metadata: dict[str, Any]
    timestamp: str


# --- Blockchain Anchoring Endpoints ---


@router.post(
    "/anchor/{framework}",
    response_model=BlockchainAnchorSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Anchor to blockchain",
    description="Anchor evidence chain to blockchain for tamper-proof verification",
)
async def anchor_to_blockchain(framework: str, db: DB) -> BlockchainAnchorSchema:
    """Anchor evidence chain to blockchain."""
    service = EvidenceVaultService(db=db)
    anchor = await service.anchor_to_blockchain(ControlFramework(framework))
    return BlockchainAnchorSchema(
        id=str(anchor.id),
        framework=anchor.framework,
        chain_hash=anchor.chain_hash,
        evidence_count=anchor.evidence_count,
        anchor_hash=anchor.anchor_hash,
        blockchain_network=anchor.blockchain_network,
        transaction_id=anchor.transaction_id,
        block_number=anchor.block_number,
        status=anchor.status,
        anchored_at=anchor.anchored_at.isoformat(),
        confirmed_at=anchor.confirmed_at.isoformat() if anchor.confirmed_at else None,
        cost_usd=anchor.cost_usd,
    )


@router.post(
    "/verify-batch/{framework}",
    response_model=BatchVerificationResultSchema,
    summary="Batch verify evidence",
    description="Verify multiple evidence items at once with chain and blockchain checks",
)
async def verify_batch(
    framework: str, db: DB, request: BatchVerificationRequestSchema | None = None,
) -> BatchVerificationResultSchema:
    """Batch verify evidence items."""
    from uuid import UUID as _UUID

    service = EvidenceVaultService(db=db)
    evidence_ids = [_UUID(eid) for eid in request.evidence_ids] if request and request.evidence_ids else None
    result = await service.verify_batch(ControlFramework(framework), evidence_ids=evidence_ids)
    return BatchVerificationResultSchema(
        id=str(result.id),
        items_verified=result.items_verified,
        items_valid=result.items_valid,
        items_invalid=result.items_invalid,
        items_missing=result.items_missing,
        chain_intact=result.chain_intact,
        blockchain_verified=result.blockchain_verified,
        invalid_items=result.invalid_items,
        verification_duration_ms=result.verification_duration_ms,
        verified_at=result.verified_at.isoformat(),
    )


@router.get(
    "/timeline",
    response_model=list[AuditTimelineEventSchema],
    summary="Get audit timeline",
    description="Get chronological audit timeline events",
)
async def get_audit_timeline(
    db: DB, framework: str | None = None, limit: int = 50,
) -> list[AuditTimelineEventSchema]:
    """Get audit timeline events."""
    service = EvidenceVaultService(db=db)
    events = await service.get_audit_timeline(framework=framework, limit=limit)
    return [
        AuditTimelineEventSchema(
            id=str(e.id),
            event_type=e.event_type,
            description=e.description,
            framework=e.framework,
            actor=e.actor,
            metadata=e.metadata,
            timestamp=e.timestamp.isoformat(),
        )
        for e in events
    ]


@router.get(
    "/anchors/{framework}",
    response_model=BlockchainAnchorSchema | None,
    summary="Get blockchain anchor",
    description="Get blockchain anchor for a framework's evidence chain",
)
async def get_blockchain_anchor(framework: str, db: DB) -> BlockchainAnchorSchema | None:
    """Get blockchain anchor for a framework."""
    service = EvidenceVaultService(db=db)
    anchor = service._blockchain_anchors.get(framework)
    if not anchor:
        return None
    return BlockchainAnchorSchema(
        id=str(anchor.id),
        framework=anchor.framework,
        chain_hash=anchor.chain_hash,
        evidence_count=anchor.evidence_count,
        anchor_hash=anchor.anchor_hash,
        blockchain_network=anchor.blockchain_network,
        transaction_id=anchor.transaction_id,
        block_number=anchor.block_number,
        status=anchor.status,
        anchored_at=anchor.anchored_at.isoformat(),
        confirmed_at=anchor.confirmed_at.isoformat() if anchor.confirmed_at else None,
        cost_usd=anchor.cost_usd,
    )
