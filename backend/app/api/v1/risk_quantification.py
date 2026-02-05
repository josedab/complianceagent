"""API endpoints for Compliance Risk Quantification (CRQ)."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CurrentOrganization, OrgMember
from app.services.risk_quantification import (
    get_risk_quantification_service,
)


router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================


class OrganizationContextRequest(BaseModel):
    """Request to set organization context."""

    annual_revenue: float | None = Field(None, ge=0, description="Annual revenue in USD")
    employee_count: int | None = Field(None, ge=1, description="Number of employees")
    data_subject_count: int | None = Field(None, ge=0, description="Number of data subjects/users")
    jurisdictions: list[str] | None = Field(None, description="Operating jurisdictions (e.g., US, EU)")


class AssessViolationRequest(BaseModel):
    """Request to assess a violation's risk."""

    rule_id: str
    regulation: str
    severity: str = "medium"
    file_path: str | None = None
    affected_records: int | None = Field(None, ge=0)
    aggravating_factors: list[str] | None = None
    mitigating_factors: list[str] | None = None


class ViolationRiskResponse(BaseModel):
    """Response containing violation risk assessment."""

    id: str
    rule_id: str
    regulation: str
    severity: str
    category: str
    min_exposure: float
    max_exposure: float
    expected_exposure: float
    confidence: float
    likelihood: float
    aggravating_factors: list[str]
    mitigating_factors: list[str]
    assessed_at: str


class RepositoryViolation(BaseModel):
    """Violation input for repository profile."""

    rule_id: str
    regulation: str
    severity: str = "medium"
    file_path: str | None = None
    affected_records: int | None = None


class GenerateRepoProfileRequest(BaseModel):
    """Request to generate repository risk profile."""

    repository_id: str
    repository_name: str
    violations: list[RepositoryViolation]


class RepositoryProfileResponse(BaseModel):
    """Response containing repository risk profile."""

    id: str
    repository_id: str | None
    repository_name: str
    total_violations: int
    critical_violations: int
    high_violations: int
    medium_violations: int
    low_violations: int
    total_min_exposure: float
    total_max_exposure: float
    total_expected_exposure: float
    exposure_by_regulation: dict[str, float]
    overall_risk_score: float
    data_privacy_score: float
    security_score: float
    compliance_score: float


class DashboardResponse(BaseModel):
    """Response containing organization risk dashboard."""

    organization_id: str | None
    annual_revenue: float
    employee_count: int
    data_subject_count: int
    jurisdictions: list[str]
    total_min_exposure: float
    total_max_exposure: float
    total_expected_exposure: float
    exposure_by_regulation: dict[str, dict[str, float]]
    exposure_by_repository: dict[str, float]
    exposure_by_severity: dict[str, float]
    overall_risk_score: float
    risk_grade: str
    risk_trend: str
    top_risks: list[dict[str, Any]]
    recommended_actions: list[dict[str, Any]]
    industry_benchmark: float | None
    percentile_rank: float | None
    generated_at: str


class WhatIfRequest(BaseModel):
    """Request to run a what-if scenario."""

    scenario_type: str = Field(
        ...,
        description="Type: fix_violations, data_breach, new_regulation, revenue_change",
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Scenario-specific parameters",
    )


class WhatIfResponse(BaseModel):
    """Response containing what-if scenario results."""

    id: str
    name: str
    description: str
    scenario_type: str
    parameters: dict[str, Any]
    baseline_exposure: float
    scenario_exposure: float
    exposure_delta: float
    exposure_delta_percent: float
    affected_regulations: list[str]
    recommendation: str
    priority: str


class GenerateReportRequest(BaseModel):
    """Request to generate executive report."""

    report_type: str = Field(default="monthly", description="Type: monthly, quarterly, annual, adhoc")
    period_start: str | None = Field(None, description="Period start date (ISO format)")
    period_end: str | None = Field(None, description="Period end date (ISO format)")


class ReportResponse(BaseModel):
    """Response containing executive report."""

    id: str
    report_type: str
    title: str
    summary: str
    key_findings: list[str]
    key_recommendations: list[str]
    total_exposure: float
    risk_score: float
    risk_grade: str
    exposure_by_regulation: dict[str, float]
    remediation_roadmap: list[dict[str, Any]]
    projected_exposure_after_remediation: float
    industry_comparison: dict[str, Any]
    generated_at: str


class FineStructureResponse(BaseModel):
    """Response containing regulation fine structure."""

    regulation: str
    max_fine_absolute: float
    max_fine_percent_revenue: float
    per_record_fine: float | None
    min_fine: float
    aggravating_factors: list[str]
    mitigating_factors: list[str]


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/context")
async def get_organization_context(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Get current organization context for risk calculations."""
    service = get_risk_quantification_service(db=db, organization_id=organization.id)
    return service.get_organization_context()


@router.put("/context")
async def set_organization_context(
    request: OrganizationContextRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Set organization context for risk calculations.

    This context is used to calculate percentage-based fines (e.g., GDPR's 4% of revenue)
    and to estimate impact based on data subject count.
    """
    service = get_risk_quantification_service(db=db, organization_id=organization.id)

    return service.set_organization_context(
        annual_revenue=request.annual_revenue,
        employee_count=request.employee_count,
        data_subject_count=request.data_subject_count,
        jurisdictions=request.jurisdictions,
    )


@router.post("/assess", response_model=ViolationRiskResponse)
async def assess_violation_risk(
    request: AssessViolationRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> ViolationRiskResponse:
    """Assess the financial risk of a single compliance violation.

    Returns estimated exposure range, likelihood, and confidence score.
    """
    service = get_risk_quantification_service(db=db, organization_id=organization.id)

    risk = service.assess_violation_risk(
        rule_id=request.rule_id,
        regulation=request.regulation,
        severity=request.severity,
        file_path=request.file_path,
        affected_records=request.affected_records,
        aggravating_factors=request.aggravating_factors,
        mitigating_factors=request.mitigating_factors,
    )

    return ViolationRiskResponse(
        id=str(risk.id),
        rule_id=risk.rule_id,
        regulation=risk.regulation,
        severity=risk.severity.value,
        category=risk.category.value,
        min_exposure=risk.min_exposure,
        max_exposure=risk.max_exposure,
        expected_exposure=risk.expected_exposure,
        confidence=risk.confidence,
        likelihood=risk.likelihood,
        aggravating_factors=risk.aggravating_factors,
        mitigating_factors=risk.mitigating_factors,
        assessed_at=risk.assessed_at.isoformat(),
    )


@router.post("/assess/batch", response_model=list[ViolationRiskResponse])
async def assess_violations_batch(
    violations: list[AssessViolationRequest],
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> list[ViolationRiskResponse]:
    """Assess multiple violations in batch."""
    service = get_risk_quantification_service(db=db, organization_id=organization.id)

    results = []
    for v in violations:
        risk = service.assess_violation_risk(
            rule_id=v.rule_id,
            regulation=v.regulation,
            severity=v.severity,
            file_path=v.file_path,
            affected_records=v.affected_records,
            aggravating_factors=v.aggravating_factors,
            mitigating_factors=v.mitigating_factors,
        )
        results.append(ViolationRiskResponse(
            id=str(risk.id),
            rule_id=risk.rule_id,
            regulation=risk.regulation,
            severity=risk.severity.value,
            category=risk.category.value,
            min_exposure=risk.min_exposure,
            max_exposure=risk.max_exposure,
            expected_exposure=risk.expected_exposure,
            confidence=risk.confidence,
            likelihood=risk.likelihood,
            aggravating_factors=risk.aggravating_factors,
            mitigating_factors=risk.mitigating_factors,
            assessed_at=risk.assessed_at.isoformat(),
        ))

    return results


@router.post("/repository-profile", response_model=RepositoryProfileResponse)
async def generate_repository_profile(
    request: GenerateRepoProfileRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> RepositoryProfileResponse:
    """Generate a risk profile for a repository.

    Aggregates risk from all violations and provides overall risk scores.
    """
    service = get_risk_quantification_service(db=db, organization_id=organization.id)

    try:
        repo_id = UUID(request.repository_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid repository ID",
        )

    violations = [
        {
            "rule_id": v.rule_id,
            "regulation": v.regulation,
            "severity": v.severity,
            "file_path": v.file_path,
            "affected_records": v.affected_records,
        }
        for v in request.violations
    ]

    profile = service.generate_repository_profile(
        repository_id=repo_id,
        repository_name=request.repository_name,
        violations=violations,
    )

    return RepositoryProfileResponse(
        id=str(profile.id),
        repository_id=str(profile.repository_id) if profile.repository_id else None,
        repository_name=profile.repository_name,
        total_violations=profile.total_violations,
        critical_violations=profile.critical_violations,
        high_violations=profile.high_violations,
        medium_violations=profile.medium_violations,
        low_violations=profile.low_violations,
        total_min_exposure=profile.total_min_exposure,
        total_max_exposure=profile.total_max_exposure,
        total_expected_exposure=profile.total_expected_exposure,
        exposure_by_regulation=profile.exposure_by_regulation,
        overall_risk_score=profile.overall_risk_score,
        data_privacy_score=profile.data_privacy_score,
        security_score=profile.security_score,
        compliance_score=profile.compliance_score,
    )


@router.get("/dashboard", response_model=DashboardResponse)
async def get_organization_dashboard(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> DashboardResponse:
    """Get organization-wide risk dashboard.

    Provides aggregate risk metrics, trends, and recommendations.
    """
    service = get_risk_quantification_service(db=db, organization_id=organization.id)
    dashboard = service.generate_organization_dashboard()

    return DashboardResponse(
        organization_id=str(dashboard.organization_id) if dashboard.organization_id else None,
        annual_revenue=dashboard.annual_revenue,
        employee_count=dashboard.employee_count,
        data_subject_count=dashboard.data_subject_count,
        jurisdictions=dashboard.jurisdictions,
        total_min_exposure=dashboard.total_min_exposure,
        total_max_exposure=dashboard.total_max_exposure,
        total_expected_exposure=dashboard.total_expected_exposure,
        exposure_by_regulation=dashboard.exposure_by_regulation,
        exposure_by_repository=dashboard.exposure_by_repository,
        exposure_by_severity=dashboard.exposure_by_severity,
        overall_risk_score=dashboard.overall_risk_score,
        risk_grade=dashboard.risk_grade,
        risk_trend=dashboard.risk_trend.value,
        top_risks=[r.to_dict() for r in dashboard.top_risks],
        recommended_actions=dashboard.recommended_actions,
        industry_benchmark=dashboard.industry_benchmark,
        percentile_rank=dashboard.percentile_rank,
        generated_at=dashboard.generated_at.isoformat(),
    )


@router.post("/what-if", response_model=WhatIfResponse)
async def run_what_if_scenario(
    request: WhatIfRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> WhatIfResponse:
    """Run a what-if scenario analysis.

    Supported scenarios:
    - fix_violations: What if we fix specific violations?
    - data_breach: What if a data breach occurs?
    - new_regulation: What if a new regulation applies?
    - revenue_change: What if our revenue changes?
    """
    service = get_risk_quantification_service(db=db, organization_id=organization.id)

    valid_types = ["fix_violations", "data_breach", "new_regulation", "revenue_change"]
    if request.scenario_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scenario_type. Valid types: {valid_types}",
        )

    scenario = service.run_what_if_scenario(
        scenario_type=request.scenario_type,
        parameters=request.parameters,
    )

    return WhatIfResponse(
        id=str(scenario.id),
        name=scenario.name,
        description=scenario.description,
        scenario_type=scenario.scenario_type,
        parameters=scenario.parameters,
        baseline_exposure=scenario.baseline_exposure,
        scenario_exposure=scenario.scenario_exposure,
        exposure_delta=scenario.exposure_delta,
        exposure_delta_percent=scenario.exposure_delta_percent,
        affected_regulations=scenario.affected_regulations,
        recommendation=scenario.recommendation,
        priority=scenario.priority,
    )


@router.post("/report", response_model=ReportResponse)
async def generate_executive_report(
    request: GenerateReportRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> ReportResponse:
    """Generate an executive risk report.

    Provides a comprehensive report suitable for board/executive presentations.
    """
    service = get_risk_quantification_service(db=db, organization_id=organization.id)

    period_start = None
    period_end = None

    if request.period_start:
        try:
            period_start = datetime.fromisoformat(request.period_start.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid period_start format. Use ISO format.",
            )

    if request.period_end:
        try:
            period_end = datetime.fromisoformat(request.period_end.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid period_end format. Use ISO format.",
            )

    report = service.generate_executive_report(
        report_type=request.report_type,
        period_start=period_start,
        period_end=period_end,
    )

    return ReportResponse(
        id=str(report.id),
        report_type=report.report_type,
        title=report.title,
        summary=report.summary,
        key_findings=report.key_findings,
        key_recommendations=report.key_recommendations,
        total_exposure=report.total_exposure,
        risk_score=report.risk_score,
        risk_grade=report.risk_grade,
        exposure_by_regulation=report.exposure_by_regulation,
        remediation_roadmap=report.remediation_roadmap,
        projected_exposure_after_remediation=report.projected_exposure_after_remediation,
        industry_comparison=report.industry_comparison,
        generated_at=report.generated_at.isoformat(),
    )


# ============================================================================
# Reference Data Endpoints
# ============================================================================


@router.get("/regulations", response_model=list[FineStructureResponse])
async def list_regulation_fines(
    db: DB,
) -> list[FineStructureResponse]:
    """List fine structures for all supported regulations."""
    from app.services.risk_quantification import REGULATION_FINES

    return [
        FineStructureResponse(
            regulation=fs.regulation,
            max_fine_absolute=fs.max_fine_absolute,
            max_fine_percent_revenue=fs.max_fine_percent_revenue,
            per_record_fine=fs.per_record_fine,
            min_fine=fs.min_fine,
            aggravating_factors=fs.aggravating_factors,
            mitigating_factors=fs.mitigating_factors,
        )
        for fs in REGULATION_FINES.values()
    ]


@router.get("/regulations/{regulation}", response_model=FineStructureResponse)
async def get_regulation_fines(
    regulation: str,
    db: DB,
) -> FineStructureResponse:
    """Get fine structure for a specific regulation."""
    from app.services.risk_quantification import REGULATION_FINES

    fs = REGULATION_FINES.get(regulation)
    if not fs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fine structure not found for regulation: {regulation}",
        )

    return FineStructureResponse(
        regulation=fs.regulation,
        max_fine_absolute=fs.max_fine_absolute,
        max_fine_percent_revenue=fs.max_fine_percent_revenue,
        per_record_fine=fs.per_record_fine,
        min_fine=fs.min_fine,
        aggravating_factors=fs.aggravating_factors,
        mitigating_factors=fs.mitigating_factors,
    )


@router.get("/quick-estimate")
async def quick_estimate(
    regulation: str = Query(..., description="Regulation name (e.g., GDPR, CCPA)"),
    severity: str = Query("medium", description="Violation severity"),
    affected_records: int | None = Query(None, ge=0),
    annual_revenue: float | None = Query(None, ge=0),
    db: DB = None,
) -> dict[str, Any]:
    """Quick estimate of potential fine without full context.

    Useful for initial assessments and demos.
    """
    from app.services.risk_quantification import REGULATION_FINES

    fs = REGULATION_FINES.get(regulation)
    if not fs:
        # Use generic estimate
        base_fine = 100_000
    else:
        # Calculate based on fine structure
        if annual_revenue and fs.max_fine_percent_revenue > 0:
            revenue_fine = annual_revenue * fs.max_fine_percent_revenue
            base_fine = min(fs.max_fine_absolute, revenue_fine)
        else:
            base_fine = fs.max_fine_absolute

        if affected_records and fs.per_record_fine:
            record_fine = fs.per_record_fine * affected_records
            base_fine = min(base_fine, record_fine)

    # Apply severity multiplier
    severity_multipliers = {
        "critical": 1.0,
        "high": 0.7,
        "medium": 0.4,
        "low": 0.2,
    }
    multiplier = severity_multipliers.get(severity.lower(), 0.4)

    # Calculate likelihood-adjusted exposure
    likelihood = {"critical": 0.8, "high": 0.6, "medium": 0.4, "low": 0.2}.get(severity.lower(), 0.4)
    expected = base_fine * multiplier * likelihood

    return {
        "regulation": regulation,
        "severity": severity,
        "affected_records": affected_records,
        "annual_revenue": annual_revenue,
        "max_potential_fine": base_fine,
        "expected_exposure": expected,
        "confidence": 0.5,  # Lower confidence for quick estimate
        "note": "This is a simplified estimate. Use full assessment for accurate results.",
    }
