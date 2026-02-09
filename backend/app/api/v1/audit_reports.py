"""API endpoints for Automatic Audit Report Generation."""

from datetime import datetime
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CurrentOrganization, OrgMember
from app.services.audit_reports import (
    AuditFramework,
    AuditorRole,
    AuditReportService,
    ReportFormat,
)


logger = structlog.get_logger()
router = APIRouter()


# --- Request Models ---


class GenerateReportRequest(BaseModel):
    framework: AuditFramework = Field(..., description="Compliance framework to generate report for")
    period_start: datetime = Field(..., description="Start of the audit period")
    period_end: datetime = Field(..., description="End of the audit period")
    format: ReportFormat = Field(ReportFormat.PDF, description="Output format for the report")


class CollectEvidenceRequest(BaseModel):
    framework: AuditFramework = Field(..., description="Framework to collect evidence for")


class InviteAuditorRequest(BaseModel):
    framework: AuditFramework = Field(..., description="Framework the auditor will review")
    auditor_email: str = Field(..., description="Email address of the auditor")
    auditor_name: str = Field(..., description="Full name of the auditor")
    role: AuditorRole = Field(AuditorRole.AUDITOR, description="Role assigned to the auditor")


class AuditorCommentRequest(BaseModel):
    session_id: str = Field(..., description="Auditor session ID")
    control_id: str = Field(..., description="Control being commented on")
    comment: str = Field(..., description="Auditor comment text")
    requires_response: bool = Field(False, description="Whether a response is required from the org")


# --- Response Models ---


class EvidenceItemSchema(BaseModel):
    id: str
    type: str
    title: str
    description: str
    source: str
    url: str
    collected_at: str
    verified: bool


class ControlResultSchema(BaseModel):
    control_id: str
    control_name: str
    control_description: str
    category: str
    status: str
    evidence: list[EvidenceItemSchema]
    findings: str
    remediation: str
    last_assessed: str | None


class EvidenceSummarySchema(BaseModel):
    total_controls: int
    compliant: int
    partially_compliant: int
    non_compliant: int
    not_applicable: int
    coverage_pct: float
    evidence_count: int
    auto_collected: int
    manual_uploaded: int


class ControlGapSchema(BaseModel):
    control_id: str
    control_name: str
    status: str
    severity: str
    remediation_steps: list[str]
    estimated_effort_hours: float
    deadline: str | None


class AuditReportSchema(BaseModel):
    id: str
    org_id: str
    framework: str
    title: str
    generated_at: str
    period_start: str
    period_end: str
    overall_status: str
    control_results: list[ControlResultSchema]
    evidence_summary: EvidenceSummarySchema
    executive_summary: str
    gaps: list[ControlGapSchema]
    format: str


class AuditReportSummarySchema(BaseModel):
    id: str
    framework: str
    title: str
    generated_at: str
    overall_status: str
    total_controls: int
    coverage_pct: float
    format: str


class FrameworkDefinitionSchema(BaseModel):
    framework: str
    version: str
    total_controls: int
    categories: list[str]
    description: str


class AuditorSessionSchema(BaseModel):
    id: str
    auditor_email: str
    auditor_name: str
    role: str
    framework: str
    created_at: str
    expires_at: str
    access_token: str
    permissions: list[str]


class AuditorCommentSchema(BaseModel):
    id: str
    session_id: str
    control_id: str
    comment: str
    created_at: str
    requires_response: bool


class ExportPackageSchema(BaseModel):
    report_id: str
    framework: str
    title: str
    generated_at: str
    period_start: str
    period_end: str
    overall_status: str
    executive_summary: str
    total_controls: int
    compliant_controls: int
    coverage_pct: float
    evidence_files: list[dict]
    gap_count: int


# --- Helpers ---


def _evidence_to_schema(e) -> EvidenceItemSchema:
    return EvidenceItemSchema(
        id=str(e.id),
        type=e.type.value,
        title=e.title,
        description=e.description,
        source=e.source,
        url=e.url,
        collected_at=e.collected_at.isoformat(),
        verified=e.verified,
    )


def _control_result_to_schema(cr) -> ControlResultSchema:
    return ControlResultSchema(
        control_id=cr.control_id,
        control_name=cr.control_name,
        control_description=cr.control_description,
        category=cr.category,
        status=cr.status.value,
        evidence=[_evidence_to_schema(e) for e in cr.evidence],
        findings=cr.findings,
        remediation=cr.remediation,
        last_assessed=cr.last_assessed.isoformat() if cr.last_assessed else None,
    )


def _gap_to_schema(g) -> ControlGapSchema:
    return ControlGapSchema(
        control_id=g.control_id,
        control_name=g.control_name,
        status=g.status.value,
        severity=g.severity,
        remediation_steps=g.remediation_steps,
        estimated_effort_hours=g.estimated_effort_hours,
        deadline=g.deadline.isoformat() if g.deadline else None,
    )


def _report_to_schema(r) -> AuditReportSchema:
    return AuditReportSchema(
        id=str(r.id),
        org_id=str(r.org_id),
        framework=r.framework.value,
        title=r.title,
        generated_at=r.generated_at.isoformat(),
        period_start=r.period_start.isoformat(),
        period_end=r.period_end.isoformat(),
        overall_status=r.overall_status.value,
        control_results=[_control_result_to_schema(cr) for cr in r.control_results],
        evidence_summary=EvidenceSummarySchema(
            total_controls=r.evidence_summary.total_controls,
            compliant=r.evidence_summary.compliant,
            partially_compliant=r.evidence_summary.partially_compliant,
            non_compliant=r.evidence_summary.non_compliant,
            not_applicable=r.evidence_summary.not_applicable,
            coverage_pct=r.evidence_summary.coverage_pct,
            evidence_count=r.evidence_summary.evidence_count,
            auto_collected=r.evidence_summary.auto_collected,
            manual_uploaded=r.evidence_summary.manual_uploaded,
        ),
        executive_summary=r.executive_summary,
        gaps=[_gap_to_schema(g) for g in r.gaps],
        format=r.format.value,
    )


def _report_to_summary(r) -> AuditReportSummarySchema:
    return AuditReportSummarySchema(
        id=str(r.id),
        framework=r.framework.value,
        title=r.title,
        generated_at=r.generated_at.isoformat(),
        overall_status=r.overall_status.value,
        total_controls=r.evidence_summary.total_controls,
        coverage_pct=r.evidence_summary.coverage_pct,
        format=r.format.value,
    )


# --- Endpoints ---


@router.post(
    "/generate",
    response_model=AuditReportSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Generate audit report",
    description="Generate a comprehensive audit-ready compliance report for the specified framework.",
)
async def generate_report(
    request: GenerateReportRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> AuditReportSchema:
    service = AuditReportService(db=db)
    report = await service.generate_report(
        org_id=organization.id,
        framework=request.framework,
        period_start=request.period_start,
        period_end=request.period_end,
        format=request.format.value,
    )
    return _report_to_schema(report)


@router.get(
    "/reports",
    response_model=list[AuditReportSummarySchema],
    summary="List audit reports",
    description="List all generated audit reports for the organization.",
)
async def list_reports(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    framework: AuditFramework | None = Query(None, description="Filter by framework"),
) -> list[AuditReportSummarySchema]:
    service = AuditReportService(db=db)
    reports = await service.list_reports(org_id=organization.id, framework=framework)
    return [_report_to_summary(r) for r in reports]


@router.get(
    "/reports/{report_id}",
    response_model=AuditReportSchema,
    summary="Get audit report",
    description="Get a specific audit report by ID with full control results and evidence.",
)
async def get_report(
    report_id: UUID,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> AuditReportSchema:
    service = AuditReportService(db=db)
    report = await service.get_report(report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return _report_to_schema(report)


@router.get(
    "/frameworks",
    response_model=list[FrameworkDefinitionSchema],
    summary="List supported frameworks",
    description="List all supported compliance audit frameworks.",
)
async def list_frameworks(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> list[FrameworkDefinitionSchema]:
    service = AuditReportService(db=db)
    frameworks = await service.list_frameworks()
    return [
        FrameworkDefinitionSchema(
            framework=f.framework.value,
            version=f.version,
            total_controls=f.total_controls,
            categories=f.categories,
            description=f.description,
        )
        for f in frameworks
    ]


@router.get(
    "/frameworks/{framework}",
    response_model=FrameworkDefinitionSchema,
    summary="Get framework details",
    description="Get detailed information about a specific compliance framework.",
)
async def get_framework(
    framework: AuditFramework,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> FrameworkDefinitionSchema:
    service = AuditReportService(db=db)
    try:
        defn = await service.get_framework_definition(framework)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return FrameworkDefinitionSchema(
        framework=defn.framework.value,
        version=defn.version,
        total_controls=defn.total_controls,
        categories=defn.categories,
        description=defn.description,
    )


@router.post(
    "/evidence/collect",
    response_model=list[EvidenceItemSchema],
    summary="Auto-collect evidence",
    description="Automatically collect evidence artifacts for a compliance framework.",
)
async def collect_evidence(
    request: CollectEvidenceRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> list[EvidenceItemSchema]:
    service = AuditReportService(db=db)
    items = await service.collect_evidence_auto(
        org_id=organization.id,
        framework=request.framework,
    )
    return [_evidence_to_schema(e) for e in items]


@router.get(
    "/gaps/{framework}",
    response_model=list[ControlGapSchema],
    summary="Get gap analysis",
    description="Perform a gap analysis for the specified framework and return identified control gaps.",
)
async def get_gap_analysis(
    framework: AuditFramework,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> list[ControlGapSchema]:
    service = AuditReportService(db=db)
    gaps = await service.get_gap_analysis(org_id=organization.id, framework=framework)
    return [_gap_to_schema(g) for g in gaps]


@router.post(
    "/auditor/invite",
    response_model=AuditorSessionSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Invite auditor",
    description="Create a read-only auditor portal session for an external auditor.",
)
async def invite_auditor(
    request: InviteAuditorRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> AuditorSessionSchema:
    service = AuditReportService(db=db)
    session = await service.create_auditor_session(
        org_id=organization.id,
        framework=request.framework,
        auditor_email=request.auditor_email,
        auditor_name=request.auditor_name,
        role=request.role,
    )
    return AuditorSessionSchema(
        id=str(session.id),
        auditor_email=session.auditor_email,
        auditor_name=session.auditor_name,
        role=session.role.value,
        framework=session.framework.value,
        created_at=session.created_at.isoformat(),
        expires_at=session.expires_at.isoformat(),
        access_token=session.access_token,
        permissions=session.permissions,
    )


@router.get(
    "/auditor/report/{session_id}",
    response_model=AuditReportSummarySchema | dict,
    summary="Auditor read-only view",
    description="Read-only view for an auditor to access the latest report for their framework.",
)
async def auditor_report_view(
    session_id: UUID,
    access_token: str = Query(..., description="Auditor access token"),
    db: DB = ...,
) -> AuditReportSummarySchema | dict:
    service = AuditReportService(db=db)
    session = await service.validate_auditor_session(session_id, access_token)
    if session is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or expired auditor session")

    reports = await service.list_reports(org_id=session.org_id, framework=session.framework)
    if not reports:
        return {"message": "No reports available for this framework"}
    return _report_to_summary(reports[0])


@router.post(
    "/auditor/comment",
    response_model=AuditorCommentSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Submit auditor comment",
    description="Submit a comment from an auditor on a specific control.",
)
async def submit_auditor_comment(
    request: AuditorCommentRequest,
    db: DB,
) -> AuditorCommentSchema:
    service = AuditReportService(db=db)
    try:
        comment = await service.submit_auditor_comment(
            session_id=UUID(request.session_id),
            control_id=request.control_id,
            comment=request.comment,
            requires_response=request.requires_response,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return AuditorCommentSchema(
        id=str(comment.id),
        session_id=str(comment.session_id),
        control_id=comment.control_id,
        comment=comment.comment,
        created_at=comment.created_at.isoformat(),
        requires_response=comment.requires_response,
    )


@router.get(
    "/auditor/comments/{framework}",
    response_model=list[AuditorCommentSchema],
    summary="List auditor comments",
    description="List all auditor comments for a specific framework.",
)
async def list_auditor_comments(
    framework: AuditFramework,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> list[AuditorCommentSchema]:
    service = AuditReportService(db=db)
    comments = await service.get_auditor_comments(org_id=organization.id, framework=framework)
    return [
        AuditorCommentSchema(
            id=str(c.id),
            session_id=str(c.session_id),
            control_id=c.control_id,
            comment=c.comment,
            created_at=c.created_at.isoformat(),
            requires_response=c.requires_response,
        )
        for c in comments
    ]


@router.post(
    "/reports/{report_id}/export",
    response_model=ExportPackageSchema,
    summary="Export evidence package",
    description="Export a complete evidence package for a specific audit report.",
)
async def export_evidence_package(
    report_id: UUID,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> ExportPackageSchema:
    service = AuditReportService(db=db)
    try:
        package = await service.export_evidence_package(report_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return ExportPackageSchema(**package)
