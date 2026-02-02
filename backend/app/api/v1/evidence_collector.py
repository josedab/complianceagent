"""Evidence collection API endpoints."""

from datetime import datetime
from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep, CurrentOrganization, OrgMember
from app.services.evidence_collector import (
    AuditPackageStatus,
    EvidenceCollectorService,
)


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---

class CreatePackageRequest(BaseModel):
    """Request to create an audit package."""
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    frameworks: list[str] = Field(..., min_items=1)
    audit_period_start: datetime
    audit_period_end: datetime


class ControlEvidenceSchema(BaseModel):
    """Control evidence response."""
    control_id: str
    framework: str
    status: str
    coverage_percentage: float
    gaps: list[str] = Field(default_factory=list)
    evidence_count: int
    last_collected: datetime | None = None
    next_collection_due: datetime | None = None


class AuditPackageSchema(BaseModel):
    """Audit package response."""
    id: UUID
    name: str
    description: str
    frameworks: list[str]
    audit_period_start: datetime | None
    audit_period_end: datetime | None
    status: str
    total_controls: int
    controls_with_evidence: int
    coverage_percentage: float
    created_at: datetime
    completed_at: datetime | None = None
    exported_at: datetime | None = None


class PackageDetailSchema(AuditPackageSchema):
    """Detailed audit package with controls."""
    controls: list[ControlEvidenceSchema] = Field(default_factory=list)


class ControlMappingSchema(BaseModel):
    """Control mapping response."""
    control_id: str
    control_name: str
    control_description: str
    required_evidence_types: list[str]
    collection_frequency: str
    automation_level: str


# --- Helper Functions ---

def _package_to_schema(package) -> AuditPackageSchema:
    """Convert AuditPackage to response schema."""
    return AuditPackageSchema(
        id=package.id,
        name=package.name,
        description=package.description,
        frameworks=package.frameworks,
        audit_period_start=package.audit_period_start,
        audit_period_end=package.audit_period_end,
        status=package.status.value,
        total_controls=package.total_controls,
        controls_with_evidence=package.controls_with_evidence,
        coverage_percentage=package.coverage_percentage,
        created_at=package.created_at,
        completed_at=package.completed_at,
        exported_at=package.exported_at,
    )


def _package_to_detail(package) -> PackageDetailSchema:
    """Convert AuditPackage to detailed response."""
    controls = [
        ControlEvidenceSchema(
            control_id=ce.control_id,
            framework=ce.framework,
            status=ce.status,
            coverage_percentage=ce.coverage_percentage,
            gaps=ce.gaps,
            evidence_count=len(ce.evidence_items),
            last_collected=ce.last_collected,
            next_collection_due=ce.next_collection_due,
        )
        for ce in package.control_evidence
    ]
    
    return PackageDetailSchema(
        id=package.id,
        name=package.name,
        description=package.description,
        frameworks=package.frameworks,
        audit_period_start=package.audit_period_start,
        audit_period_end=package.audit_period_end,
        status=package.status.value,
        total_controls=package.total_controls,
        controls_with_evidence=package.controls_with_evidence,
        coverage_percentage=package.coverage_percentage,
        created_at=package.created_at,
        completed_at=package.completed_at,
        exported_at=package.exported_at,
        controls=controls,
    )


# --- Endpoints ---

@router.post(
    "/packages",
    response_model=AuditPackageSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create audit package",
    description="Create a new audit evidence package for specified frameworks",
)
async def create_audit_package(
    request: CreatePackageRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
) -> AuditPackageSchema:
    """Create a new audit evidence package."""
    service = EvidenceCollectorService(db=db, copilot=copilot)
    
    package = await service.create_audit_package(
        organization_id=organization.id,
        name=request.name,
        description=request.description,
        frameworks=request.frameworks,
        audit_period_start=request.audit_period_start,
        audit_period_end=request.audit_period_end,
        created_by=member.user_id,
    )
    
    return _package_to_schema(package)


@router.get(
    "/packages",
    response_model=list[AuditPackageSchema],
    summary="List audit packages",
    description="Get all audit packages for the organization",
)
async def list_audit_packages(
    organization: CurrentOrganization,
    db: DB,
    copilot: CopilotDep,
) -> list[AuditPackageSchema]:
    """List all audit packages."""
    service = EvidenceCollectorService(db=db, copilot=copilot)
    packages = await service.list_packages(organization.id)
    return [_package_to_schema(p) for p in packages]


@router.get(
    "/packages/{package_id}",
    response_model=PackageDetailSchema,
    summary="Get audit package",
    description="Get detailed audit package with control evidence",
)
async def get_audit_package(
    package_id: UUID,
    organization: CurrentOrganization,
    db: DB,
    copilot: CopilotDep,
) -> PackageDetailSchema:
    """Get detailed audit package."""
    service = EvidenceCollectorService(db=db, copilot=copilot)
    package = await service.get_package(package_id)
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit package not found",
        )
    
    if package.organization_id != organization.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    return _package_to_detail(package)


@router.post(
    "/packages/{package_id}/collect",
    response_model=PackageDetailSchema,
    summary="Collect evidence",
    description="Collect evidence for all controls in the audit package",
)
async def collect_evidence(
    package_id: UUID,
    organization: CurrentOrganization,
    db: DB,
    copilot: CopilotDep,
    repository_id: UUID | None = None,
) -> PackageDetailSchema:
    """Trigger evidence collection for an audit package."""
    service = EvidenceCollectorService(db=db, copilot=copilot)
    
    # Verify package exists and belongs to org
    package = await service.get_package(package_id)
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit package not found",
        )
    
    if package.organization_id != organization.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    # Collect evidence
    package = await service.collect_evidence(
        package_id=package_id,
        repository_id=repository_id,
    )
    
    return _package_to_detail(package)


@router.post(
    "/packages/{package_id}/export",
    summary="Export audit package",
    description="Export the audit package for external audit use",
)
async def export_audit_package(
    package_id: UUID,
    organization: CurrentOrganization,
    db: DB,
    copilot: CopilotDep,
    format: str = "json",
) -> dict:
    """Export audit package in specified format."""
    service = EvidenceCollectorService(db=db, copilot=copilot)
    
    # Verify package exists
    package = await service.get_package(package_id)
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit package not found",
        )
    
    if package.organization_id != organization.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    try:
        export_data = await service.export_package(package_id, format)
        return export_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/frameworks",
    summary="Get supported frameworks",
    description="Get list of frameworks with evidence collection support",
)
async def get_supported_frameworks(
    db: DB,
    copilot: CopilotDep,
) -> dict:
    """Get supported compliance frameworks."""
    service = EvidenceCollectorService(db=db, copilot=copilot)
    frameworks = await service.get_supported_frameworks()
    return {"frameworks": frameworks}


@router.get(
    "/frameworks/{framework}/controls",
    response_model=list[ControlMappingSchema],
    summary="Get framework controls",
    description="Get control mappings for a specific framework",
)
async def get_framework_controls(
    framework: str,
    db: DB,
    copilot: CopilotDep,
) -> list[ControlMappingSchema]:
    """Get control mappings for a framework."""
    service = EvidenceCollectorService(db=db, copilot=copilot)
    mappings = await service.get_control_mappings(framework)
    
    if not mappings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Framework not found: {framework}",
        )
    
    return [
        ControlMappingSchema(
            control_id=m.control_id,
            control_name=m.control_name,
            control_description=m.control_description,
            required_evidence_types=[t.value for t in m.required_evidence_types],
            collection_frequency=m.collection_frequency,
            automation_level=m.automation_level,
        )
        for m in mappings
    ]
