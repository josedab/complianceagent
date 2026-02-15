"""API endpoints for Zero-Trust Compliance Architecture Scanner."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep
from app.services.zero_trust_scanner import (
    ComplianceFramework,
    ViolationStatus,
    ZeroTrustScannerService,
)


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---


class ScanIaCRequest(BaseModel):
    """Request to scan IaC."""

    repo: str = Field(..., description="Repository to scan")
    files: list[str] | None = Field(default=None, description="Specific files to scan")


class PolicySchema(BaseModel):
    """Zero-trust policy response."""

    id: str
    name: str
    framework: str
    resource_types: list[str]
    description: str
    rego_rule: str
    severity: str


class ViolationSchema(BaseModel):
    """Zero-trust violation response."""

    id: str
    policy_id: str
    resource_id: str
    resource_name: str
    violation_type: str
    severity: str
    description: str
    framework: str
    remediation_hint: str
    iac_file: str
    iac_line: int
    status: str
    detected_at: str | None


class ScanResultSchema(BaseModel):
    """Scan result response."""

    id: str
    scan_type: str
    resources_scanned: int
    violations_found: int
    violations: list[ViolationSchema]
    compliance_score: float
    scanned_at: str | None


class RemediationPlanSchema(BaseModel):
    """Remediation plan response."""

    id: str
    violation_id: str
    iac_diff: str
    description: str
    auto_fixable: bool
    risk: str


class SuppressRequest(BaseModel):
    """Request to suppress a violation."""

    reason: str = Field(..., description="Reason for suppression")


class ComplianceSummarySchema(BaseModel):
    """Compliance summary response."""

    summary: dict[str, Any]


# --- Helpers ---


def _violation_to_schema(v) -> ViolationSchema:
    return ViolationSchema(
        id=str(v.id),
        policy_id=str(v.policy_id),
        resource_id=str(v.resource_id),
        resource_name=v.resource_name,
        violation_type=v.violation_type,
        severity=v.severity,
        description=v.description,
        framework=v.framework.value,
        remediation_hint=v.remediation_hint,
        iac_file=v.iac_file,
        iac_line=v.iac_line,
        status=v.status.value,
        detected_at=v.detected_at.isoformat() if v.detected_at else None,
    )


# --- Endpoints ---


@router.post(
    "/scan",
    response_model=ScanResultSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Scan IaC for zero-trust violations",
)
async def scan_iac(
    request: ScanIaCRequest,
    db: DB,
    copilot: CopilotDep,
) -> ScanResultSchema:
    """Scan infrastructure-as-code for zero-trust violations."""
    service = ZeroTrustScannerService(db=db, copilot_client=copilot)
    result = await service.scan_iac(repo=request.repo, files=request.files)
    return ScanResultSchema(
        id=str(result.id),
        scan_type=result.scan_type,
        resources_scanned=result.resources_scanned,
        violations_found=result.violations_found,
        violations=[_violation_to_schema(v) for v in result.violations],
        compliance_score=result.compliance_score,
        scanned_at=result.scanned_at.isoformat() if result.scanned_at else None,
    )


@router.get(
    "/policies",
    response_model=list[PolicySchema],
    summary="List zero-trust policies",
)
async def list_policies(
    db: DB,
    copilot: CopilotDep,
) -> list[PolicySchema]:
    """List all zero-trust policies."""
    service = ZeroTrustScannerService(db=db, copilot_client=copilot)
    policies = await service.list_policies()
    return [
        PolicySchema(
            id=str(p.id),
            name=p.name,
            framework=p.framework.value,
            resource_types=[rt.value for rt in p.resource_types],
            description=p.description,
            rego_rule=p.rego_rule,
            severity=p.severity,
        )
        for p in policies
    ]


@router.get(
    "/violations",
    response_model=list[ViolationSchema],
    summary="List violations",
)
async def list_violations(
    db: DB,
    copilot: CopilotDep,
    status_filter: str | None = None,
    framework: str | None = None,
) -> list[ViolationSchema]:
    """List violations with optional filters."""
    service = ZeroTrustScannerService(db=db, copilot_client=copilot)
    vs = ViolationStatus(status_filter) if status_filter else None
    fw = ComplianceFramework(framework) if framework else None
    violations = await service.list_violations(status=vs, framework=fw)
    return [_violation_to_schema(v) for v in violations]


@router.get(
    "/violations/{violation_id}",
    response_model=ViolationSchema,
    summary="Get violation details",
)
async def get_violation(
    violation_id: UUID,
    db: DB,
    copilot: CopilotDep,
) -> ViolationSchema:
    """Get a violation by ID."""
    service = ZeroTrustScannerService(db=db, copilot_client=copilot)
    v = await service.get_violation(violation_id)
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Violation not found")
    return _violation_to_schema(v)


@router.post(
    "/violations/{violation_id}/remediate",
    response_model=RemediationPlanSchema,
    summary="Generate remediation plan",
)
async def generate_remediation(
    violation_id: UUID,
    db: DB,
    copilot: CopilotDep,
) -> RemediationPlanSchema:
    """Generate a remediation plan for a violation."""
    service = ZeroTrustScannerService(db=db, copilot_client=copilot)
    plan = await service.generate_remediation(violation_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Violation not found")
    return RemediationPlanSchema(
        id=str(plan.id),
        violation_id=str(plan.violation_id),
        iac_diff=plan.iac_diff,
        description=plan.description,
        auto_fixable=plan.auto_fixable,
        risk=plan.risk,
    )


@router.post(
    "/violations/{violation_id}/suppress",
    response_model=ViolationSchema,
    summary="Suppress a violation",
)
async def suppress_violation(
    violation_id: UUID,
    request: SuppressRequest,
    db: DB,
    copilot: CopilotDep,
) -> ViolationSchema:
    """Suppress a violation with a reason."""
    service = ZeroTrustScannerService(db=db, copilot_client=copilot)
    v = await service.suppress_violation(violation_id, reason=request.reason)
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Violation not found")
    return _violation_to_schema(v)


@router.get(
    "/summary",
    response_model=ComplianceSummarySchema,
    summary="Get compliance summary",
)
async def get_compliance_summary(
    db: DB,
    copilot: CopilotDep,
) -> ComplianceSummarySchema:
    """Get compliance score per framework."""
    service = ZeroTrustScannerService(db=db, copilot_client=copilot)
    summary = await service.get_compliance_summary()
    return ComplianceSummarySchema(summary=summary)
