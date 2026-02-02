"""Vendor and dependency compliance assessment API endpoints."""

from datetime import datetime
from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep, CurrentOrganization, OrgMember
from app.services.vendor_assessment import (
    VendorAssessmentService,
    VendorRiskLevel,
    VendorStatus,
)


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---

class CreateVendorRequest(BaseModel):
    """Request to create a vendor."""
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    website: str = ""
    vendor_type: str = Field(..., description="saas, paas, iaas, consultant, etc.")
    category: str = ""
    certifications: list[str] = Field(default_factory=list)
    data_types_processed: list[str] = Field(default_factory=list)
    data_processing_locations: list[str] = Field(default_factory=list)
    data_access_level: str = "none"


class VendorSchema(BaseModel):
    """Vendor response."""
    id: UUID
    name: str
    description: str
    website: str
    vendor_type: str
    category: str
    certifications: list[str]
    data_types_processed: list[str]
    data_processing_locations: list[str]
    risk_level: str
    status: str
    last_assessment_date: datetime | None = None
    next_review_date: datetime | None = None
    created_at: datetime


class AssessmentRequest(BaseModel):
    """Request for vendor assessment."""
    assessment_type: str = "initial"
    target_frameworks: list[str] = Field(default=["SOC2", "GDPR"])


class AssessmentSchema(BaseModel):
    """Assessment response."""
    id: UUID
    vendor_id: UUID | None
    assessment_type: str
    assessment_date: datetime
    overall_score: float
    security_score: float
    privacy_score: float
    operational_score: float
    risk_level: str
    status: str
    recommendation: str
    compliance_gaps: list[dict] = Field(default_factory=list)
    required_actions: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    valid_until: datetime | None = None


class DependencyScanRequest(BaseModel):
    """Request for dependency scan."""
    manifest_content: str = Field(..., description="Content of package.json, requirements.txt, etc.")
    package_manager: str = Field("npm", description="npm, pip, maven, etc.")
    target_frameworks: list[str] = Field(default=["SOC2", "GDPR"])


class DependencyRiskSchema(BaseModel):
    """Dependency risk response."""
    name: str
    version: str
    license: str
    license_risk: str
    risk_level: str
    risk_score: float
    has_vulnerabilities: bool
    vulnerability_count: int
    issues: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class DependencyScanResultSchema(BaseModel):
    """Dependency scan result response."""
    id: UUID
    scan_date: datetime
    total_dependencies: int
    direct_dependencies: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    total_vulnerabilities: int
    license_violations: int
    health_score: float
    frameworks_affected: list[str]
    compliance_impact: dict[str, str]
    dependencies: list[DependencyRiskSchema] = Field(default_factory=list)


# --- Helper Functions ---

def _vendor_to_schema(vendor) -> VendorSchema:
    """Convert Vendor to response schema."""
    return VendorSchema(
        id=vendor.id,
        name=vendor.name,
        description=vendor.description,
        website=vendor.website,
        vendor_type=vendor.vendor_type,
        category=vendor.category,
        certifications=vendor.certifications,
        data_types_processed=vendor.data_types_processed,
        data_processing_locations=vendor.data_processing_locations,
        risk_level=vendor.risk_level.value,
        status=vendor.status.value,
        last_assessment_date=vendor.last_assessment_date,
        next_review_date=vendor.next_review_date,
        created_at=vendor.created_at,
    )


def _assessment_to_schema(assessment) -> AssessmentSchema:
    """Convert VendorAssessment to response schema."""
    return AssessmentSchema(
        id=assessment.id,
        vendor_id=assessment.vendor_id,
        assessment_type=assessment.assessment_type,
        assessment_date=assessment.assessment_date,
        overall_score=assessment.overall_score,
        security_score=assessment.security_score,
        privacy_score=assessment.privacy_score,
        operational_score=assessment.operational_score,
        risk_level=assessment.risk_level.value,
        status=assessment.status.value,
        recommendation=assessment.recommendation,
        compliance_gaps=assessment.compliance_gaps,
        required_actions=assessment.required_actions,
        conditions=assessment.conditions,
        valid_until=assessment.valid_until,
    )


# --- Vendor Endpoints ---

@router.post(
    "/vendors",
    response_model=VendorSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create vendor",
    description="Create a new third-party vendor record",
)
async def create_vendor(
    request: CreateVendorRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
) -> VendorSchema:
    """Create a new vendor."""
    service = VendorAssessmentService(db=db, copilot=copilot)
    
    vendor = await service.create_vendor(
        organization_id=organization.id,
        name=request.name,
        description=request.description,
        website=request.website,
        vendor_type=request.vendor_type,
        category=request.category,
        certifications=request.certifications,
        data_types_processed=request.data_types_processed,
        data_processing_locations=request.data_processing_locations,
        created_by=member.user_id,
    )
    
    return _vendor_to_schema(vendor)


@router.get(
    "/vendors",
    response_model=list[VendorSchema],
    summary="List vendors",
    description="Get all vendors for the organization",
)
async def list_vendors(
    organization: CurrentOrganization,
    db: DB,
    copilot: CopilotDep,
    status_filter: str | None = None,
    risk_level: str | None = None,
) -> list[VendorSchema]:
    """List all vendors."""
    service = VendorAssessmentService(db=db, copilot=copilot)
    
    status_enum = VendorStatus(status_filter) if status_filter else None
    risk_enum = VendorRiskLevel(risk_level) if risk_level else None
    
    vendors = await service.list_vendors(
        organization_id=organization.id,
        status=status_enum,
        risk_level=risk_enum,
    )
    
    return [_vendor_to_schema(v) for v in vendors]


@router.get(
    "/vendors/{vendor_id}",
    response_model=VendorSchema,
    summary="Get vendor",
    description="Get vendor details",
)
async def get_vendor(
    vendor_id: UUID,
    organization: CurrentOrganization,
    db: DB,
    copilot: CopilotDep,
) -> VendorSchema:
    """Get vendor details."""
    service = VendorAssessmentService(db=db, copilot=copilot)
    vendor = await service.get_vendor(vendor_id)
    
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found",
        )
    
    if vendor.organization_id != organization.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    return _vendor_to_schema(vendor)


@router.post(
    "/vendors/{vendor_id}/assess",
    response_model=AssessmentSchema,
    summary="Assess vendor",
    description="Perform compliance assessment on a vendor",
)
async def assess_vendor(
    vendor_id: UUID,
    request: AssessmentRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
) -> AssessmentSchema:
    """Assess vendor compliance."""
    service = VendorAssessmentService(db=db, copilot=copilot)
    
    try:
        assessment = await service.assess_vendor(
            vendor_id=vendor_id,
            organization_id=organization.id,
            assessor=str(member.user_id),
            assessment_type=request.assessment_type,
            target_frameworks=request.target_frameworks,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    
    return _assessment_to_schema(assessment)


@router.get(
    "/vendors/{vendor_id}/assessments",
    response_model=list[AssessmentSchema],
    summary="List vendor assessments",
    description="Get all assessments for a vendor",
)
async def list_vendor_assessments(
    vendor_id: UUID,
    organization: CurrentOrganization,
    db: DB,
    copilot: CopilotDep,
) -> list[AssessmentSchema]:
    """List assessments for a vendor."""
    service = VendorAssessmentService(db=db, copilot=copilot)
    
    assessments = await service.list_assessments(
        organization_id=organization.id,
        vendor_id=vendor_id,
    )
    
    return [_assessment_to_schema(a) for a in assessments]


# --- Dependency Scanning Endpoints ---

@router.post(
    "/dependencies/scan",
    response_model=DependencyScanResultSchema,
    summary="Scan dependencies",
    description="Scan project dependencies for compliance risks",
)
async def scan_dependencies(
    request: DependencyScanRequest,
    organization: CurrentOrganization,
    db: DB,
    copilot: CopilotDep,
    repository_id: UUID | None = None,
) -> DependencyScanResultSchema:
    """Scan dependencies for compliance and security risks."""
    service = VendorAssessmentService(db=db, copilot=copilot)
    
    result = await service.scan_dependencies(
        repository_id=repository_id or UUID(int=0),
        organization_id=organization.id,
        manifest_content=request.manifest_content,
        package_manager=request.package_manager,
        target_frameworks=request.target_frameworks,
    )
    
    dependencies = [
        DependencyRiskSchema(
            name=r.dependency.name,
            version=r.dependency.version,
            license=r.dependency.license,
            license_risk=r.dependency.license_risk,
            risk_level=r.risk_level.value,
            risk_score=r.risk_score,
            has_vulnerabilities=r.dependency.has_known_vulnerabilities,
            vulnerability_count=r.dependency.vulnerability_count,
            issues=(
                r.license_issues +
                r.maintenance_issues +
                r.compliance_issues
            ),
            recommendations=r.recommendations,
        )
        for r in result.dependency_risks
    ]
    
    return DependencyScanResultSchema(
        id=result.id,
        scan_date=result.scan_date,
        total_dependencies=result.total_dependencies,
        direct_dependencies=result.direct_dependencies,
        critical_count=result.critical_count,
        high_count=result.high_count,
        medium_count=result.medium_count,
        low_count=result.low_count,
        total_vulnerabilities=result.total_vulnerabilities,
        license_violations=result.license_violations,
        health_score=result.health_score,
        frameworks_affected=result.frameworks_affected,
        compliance_impact=result.compliance_impact,
        dependencies=dependencies,
    )


@router.get(
    "/certifications",
    summary="Get certifications",
    description="Get list of recognized vendor certifications",
)
async def get_certifications() -> dict:
    """Get recognized certifications and their compliance mappings."""
    from app.services.vendor_assessment.models import CERTIFICATION_COMPLIANCE_MAP
    
    return {
        "certifications": [
            {
                "code": cert,
                "name": cert.replace("_", " "),
                "frameworks": frameworks,
            }
            for cert, frameworks in CERTIFICATION_COMPLIANCE_MAP.items()
        ]
    }
