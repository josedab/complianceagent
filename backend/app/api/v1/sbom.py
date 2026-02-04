"""API endpoints for SBOM (Software Bill of Materials) compliance."""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CurrentOrganization, OrgMember
from app.services.sbom import (
    SBOMFormat,
    SBOMGenerator,
    SBOMComplianceAnalyzer,
    get_sbom_generator,
    get_sbom_analyzer,
)


router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================


class GenerateSBOMRequest(BaseModel):
    """Request to generate an SBOM."""
    
    name: str = Field(description="Project/application name")
    version: str = Field(description="Project version")
    dependency_files: dict[str, str] = Field(
        description="Dictionary of filename -> file content (e.g., {'package.json': '{...}'}"
    )
    format: str = Field(
        default="cyclonedx-json",
        description="Output format: spdx-json, spdx-xml, cyclonedx-json, cyclonedx-xml"
    )
    include_vulnerabilities: bool = Field(
        default=True,
        description="Check for known vulnerabilities"
    )
    include_licenses: bool = Field(
        default=True,
        description="Include license information"
    )
    repository_id: str | None = Field(
        default=None,
        description="Optional repository ID to associate"
    )


class ComponentResponse(BaseModel):
    """SBOM component response."""
    
    id: str
    name: str
    version: str
    purl: str | None
    license: str | None
    license_risk: str
    type: str
    is_direct: bool
    supplier: str | None
    vulnerabilities_count: int
    compliance_issues_count: int


class VulnerabilityResponse(BaseModel):
    """Vulnerability response."""
    
    id: str
    severity: str
    cvss_score: float | None
    description: str
    fixed_in_version: str | None
    component_name: str
    component_version: str


class SBOMResponse(BaseModel):
    """Complete SBOM response."""
    
    id: str
    name: str
    version: str
    format: str
    created_at: datetime
    total_components: int
    direct_dependencies: int
    transitive_dependencies: int
    total_vulnerabilities: int
    critical_vulnerabilities: int
    high_vulnerabilities: int
    compliance_score: float
    high_risk_licenses: int
    unknown_licenses: int
    license_summary: dict[str, int]
    generation_time_ms: float | None
    signature: str | None


class SBOMDetailResponse(SBOMResponse):
    """Detailed SBOM response with components."""
    
    components: list[ComponentResponse]
    vulnerabilities: list[VulnerabilityResponse]


class ComplianceIssueResponse(BaseModel):
    """Compliance issue response."""
    
    id: str
    issue_type: str
    regulation: str
    requirement: str
    article: str | None
    impact: str
    description: str
    remediation: str | None
    deadline: datetime | None


class VulnerabilityMappingResponse(BaseModel):
    """Vulnerability to compliance mapping response."""
    
    vulnerability_id: str
    regulation: str
    requirement: str
    article: str | None
    impact: str
    rationale: str
    remediation_deadline_days: int | None
    evidence_required: list[str]


class ComplianceReportResponse(BaseModel):
    """SBOM compliance report response."""
    
    id: str
    sbom_id: str
    generated_at: datetime
    overall_compliance_score: float
    vulnerability_score: float
    license_score: float
    supply_chain_score: float
    regulation_compliance: dict[str, float]
    critical_risks: list[str]
    high_risks: list[str]
    recommendations: list[str]
    immediate_actions: list[str]
    short_term_actions: list[str]
    long_term_actions: list[str]


class AnalyzeComplianceRequest(BaseModel):
    """Request to analyze SBOM for compliance."""
    
    sbom_id: str
    regulations: list[str] | None = Field(
        default=None,
        description="Regulations to check against (default: PCI-DSS, HIPAA, SOC 2, GDPR, NIST CSF)"
    )


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/generate", response_model=SBOMResponse)
async def generate_sbom(
    request: GenerateSBOMRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> SBOMResponse:
    """Generate a Software Bill of Materials (SBOM) from dependency files.
    
    Parses dependency files (package.json, requirements.txt, go.mod, etc.)
    and generates a comprehensive SBOM with:
    - Component inventory
    - License information
    - Known vulnerability detection
    - Compliance metadata
    
    Supports SPDX and CycloneDX output formats.
    """
    generator = get_sbom_generator()
    
    try:
        format_enum = SBOMFormat(request.format)
    except ValueError:
        format_enum = SBOMFormat.CYCLONEDX_JSON
    
    repo_id = UUID(request.repository_id) if request.repository_id else None
    
    sbom = await generator.generate_sbom(
        organization_id=organization.id,
        repository_id=repo_id,
        name=request.name,
        version=request.version,
        dependency_files=request.dependency_files,
        format=format_enum,
        include_vulnerabilities=request.include_vulnerabilities,
        include_licenses=request.include_licenses,
    )
    
    return SBOMResponse(
        id=str(sbom.id),
        name=sbom.name,
        version=sbom.version,
        format=sbom.format.value,
        created_at=sbom.created_at,
        total_components=sbom.total_components,
        direct_dependencies=sbom.direct_dependencies,
        transitive_dependencies=sbom.transitive_dependencies,
        total_vulnerabilities=sbom.total_vulnerabilities,
        critical_vulnerabilities=sbom.critical_vulnerabilities,
        high_vulnerabilities=sbom.high_vulnerabilities,
        compliance_score=sbom.compliance_score,
        high_risk_licenses=sbom.high_risk_licenses,
        unknown_licenses=sbom.unknown_licenses,
        license_summary=sbom.license_types,
        generation_time_ms=sbom.generation_time_ms,
        signature=sbom.signature,
    )


@router.get("/{sbom_id}", response_model=SBOMDetailResponse)
async def get_sbom(
    sbom_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> SBOMDetailResponse:
    """Get detailed SBOM by ID, including all components and vulnerabilities."""
    generator = get_sbom_generator()
    
    try:
        sbom_uuid = UUID(sbom_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid SBOM ID format",
        )
    
    sbom = await generator.get_sbom(sbom_uuid)
    if not sbom or sbom.organization_id != organization.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SBOM not found",
        )
    
    components = [
        ComponentResponse(
            id=str(c.id),
            name=c.name,
            version=c.version,
            purl=c.purl,
            license=c.license,
            license_risk=c.license_risk.value,
            type=c.type,
            is_direct=c.is_direct,
            supplier=c.supplier,
            vulnerabilities_count=len(c.vulnerabilities),
            compliance_issues_count=len(c.compliance_issues),
        )
        for c in sbom.components
    ]
    
    vulnerabilities = [
        VulnerabilityResponse(
            id=v.id,
            severity=v.severity.value,
            cvss_score=v.cvss_score,
            description=v.description,
            fixed_in_version=v.fixed_in_version,
            component_name=c.name,
            component_version=c.version,
        )
        for c in sbom.components
        for v in c.vulnerabilities
    ]
    
    return SBOMDetailResponse(
        id=str(sbom.id),
        name=sbom.name,
        version=sbom.version,
        format=sbom.format.value,
        created_at=sbom.created_at,
        total_components=sbom.total_components,
        direct_dependencies=sbom.direct_dependencies,
        transitive_dependencies=sbom.transitive_dependencies,
        total_vulnerabilities=sbom.total_vulnerabilities,
        critical_vulnerabilities=sbom.critical_vulnerabilities,
        high_vulnerabilities=sbom.high_vulnerabilities,
        compliance_score=sbom.compliance_score,
        high_risk_licenses=sbom.high_risk_licenses,
        unknown_licenses=sbom.unknown_licenses,
        license_summary=sbom.license_types,
        generation_time_ms=sbom.generation_time_ms,
        signature=sbom.signature,
        components=components,
        vulnerabilities=vulnerabilities,
    )


@router.get("/{sbom_id}/export")
async def export_sbom(
    sbom_id: str,
    format: str = "cyclonedx-json",
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> dict[str, Any]:
    """Export SBOM in standard format (SPDX or CycloneDX).
    
    Returns the SBOM in the requested industry-standard format,
    suitable for submission to auditors or integration with other tools.
    """
    generator = get_sbom_generator()
    
    try:
        sbom_uuid = UUID(sbom_id)
        format_enum = SBOMFormat(format)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid SBOM ID or format",
        )
    
    try:
        return await generator.export_sbom(sbom_uuid, format_enum)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/analyze-compliance", response_model=ComplianceReportResponse)
async def analyze_sbom_compliance(
    request: AnalyzeComplianceRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> ComplianceReportResponse:
    """Analyze SBOM for regulatory compliance.
    
    Maps vulnerabilities and license issues to specific regulatory
    requirements, providing:
    - Compliance scores by regulation
    - Vulnerability to regulation mappings
    - Remediation priorities and deadlines
    - Actionable recommendations
    """
    generator = get_sbom_generator()
    analyzer = get_sbom_analyzer()
    
    try:
        sbom_uuid = UUID(request.sbom_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid SBOM ID format",
        )
    
    sbom = await generator.get_sbom(sbom_uuid)
    if not sbom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SBOM not found",
        )
    
    report = await analyzer.analyze_compliance(
        sbom=sbom,
        regulations=request.regulations,
    )
    
    return ComplianceReportResponse(
        id=str(report.id),
        sbom_id=str(report.sbom_id),
        generated_at=report.generated_at,
        overall_compliance_score=report.overall_compliance_score,
        vulnerability_score=report.vulnerability_score,
        license_score=report.license_score,
        supply_chain_score=report.supply_chain_score,
        regulation_compliance=report.regulation_compliance,
        critical_risks=report.critical_risks,
        high_risks=report.high_risks,
        recommendations=report.recommendations,
        immediate_actions=report.immediate_actions,
        short_term_actions=report.short_term_actions,
        long_term_actions=report.long_term_actions,
    )


@router.get("/reports/{report_id}", response_model=ComplianceReportResponse)
async def get_compliance_report(
    report_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> ComplianceReportResponse:
    """Get a compliance report by ID."""
    analyzer = get_sbom_analyzer()
    
    try:
        report_uuid = UUID(report_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report ID format",
        )
    
    report = await analyzer.get_report(report_uuid)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    
    return ComplianceReportResponse(
        id=str(report.id),
        sbom_id=str(report.sbom_id),
        generated_at=report.generated_at,
        overall_compliance_score=report.overall_compliance_score,
        vulnerability_score=report.vulnerability_score,
        license_score=report.license_score,
        supply_chain_score=report.supply_chain_score,
        regulation_compliance=report.regulation_compliance,
        critical_risks=report.critical_risks,
        high_risks=report.high_risks,
        recommendations=report.recommendations,
        immediate_actions=report.immediate_actions,
        short_term_actions=report.short_term_actions,
        long_term_actions=report.long_term_actions,
    )


@router.get("/reports/{report_id}/issues", response_model=dict[str, list[ComplianceIssueResponse]])
async def get_compliance_issues(
    report_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, list[ComplianceIssueResponse]]:
    """Get detailed compliance issues from a report, grouped by regulation."""
    analyzer = get_sbom_analyzer()
    
    try:
        report_uuid = UUID(report_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report ID format",
        )
    
    report = await analyzer.get_report(report_uuid)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    
    result = {}
    for regulation, issues in report.issues_by_regulation.items():
        result[regulation] = [
            ComplianceIssueResponse(
                id=str(issue.id),
                issue_type=issue.issue_type,
                regulation=issue.regulation,
                requirement=issue.requirement,
                article=issue.article,
                impact=issue.impact.value,
                description=issue.description,
                remediation=issue.remediation,
                deadline=issue.deadline,
            )
            for issue in issues
        ]
    
    return result


@router.get("/reports/{report_id}/vulnerability-mappings", response_model=list[VulnerabilityMappingResponse])
async def get_vulnerability_mappings(
    report_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> list[VulnerabilityMappingResponse]:
    """Get vulnerability to compliance requirement mappings.
    
    Shows how each vulnerability maps to specific regulatory requirements,
    useful for audit documentation and remediation prioritization.
    """
    analyzer = get_sbom_analyzer()
    
    try:
        report_uuid = UUID(report_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report ID format",
        )
    
    report = await analyzer.get_report(report_uuid)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    
    return [
        VulnerabilityMappingResponse(
            vulnerability_id=m.vulnerability_id,
            regulation=m.regulation,
            requirement=m.requirement,
            article=m.article,
            impact=m.impact.value,
            rationale=m.rationale,
            remediation_deadline_days=m.remediation_deadline_days,
            evidence_required=m.evidence_required,
        )
        for m in report.vulnerability_mappings
    ]


@router.post("/quick-scan")
async def quick_scan(
    name: str,
    dependency_files: dict[str, str],
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> dict[str, Any]:
    """Perform a quick SBOM scan and compliance analysis in one call.
    
    Combines SBOM generation and compliance analysis for rapid assessment.
    Returns a summary suitable for CI/CD integration.
    """
    generator = get_sbom_generator()
    analyzer = get_sbom_analyzer()
    
    # Generate SBOM
    sbom = await generator.generate_sbom(
        organization_id=organization.id if organization else None,
        repository_id=None,
        name=name,
        version="scan",
        dependency_files=dependency_files,
        format=SBOMFormat.CYCLONEDX_JSON,
    )
    
    # Analyze compliance
    report = await analyzer.analyze_compliance(sbom)
    
    # Determine pass/fail
    passed = (
        sbom.critical_vulnerabilities == 0 and
        report.overall_compliance_score >= 70
    )
    
    return {
        "passed": passed,
        "sbom_id": str(sbom.id),
        "report_id": str(report.id),
        "summary": {
            "total_components": sbom.total_components,
            "vulnerabilities": {
                "critical": sbom.critical_vulnerabilities,
                "high": sbom.high_vulnerabilities,
                "medium": sbom.medium_vulnerabilities,
                "low": sbom.low_vulnerabilities,
            },
            "compliance_score": report.overall_compliance_score,
            "regulation_scores": report.regulation_compliance,
        },
        "critical_issues": report.critical_risks[:5],
        "recommendations": report.recommendations[:3],
        "immediate_actions": report.immediate_actions[:3],
    }
