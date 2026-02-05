"""Data models for Compliance Risk Quantification (CRQ)."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class RiskSeverity(str, Enum):
    """Risk severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NEGLIGIBLE = "negligible"


class RiskCategory(str, Enum):
    """Categories of compliance risk."""

    REGULATORY_FINE = "regulatory_fine"
    DATA_BREACH = "data_breach"
    LITIGATION = "litigation"
    REPUTATION = "reputation"
    OPERATIONAL = "operational"
    THIRD_PARTY = "third_party"


class RiskTrend(str, Enum):
    """Risk trend direction."""

    INCREASING = "increasing"
    STABLE = "stable"
    DECREASING = "decreasing"


@dataclass
class RegulationFineStructure:
    """Fine structure for a regulation."""

    regulation: str
    max_fine_absolute: float  # Maximum absolute fine (e.g., $20M for GDPR)
    max_fine_percent_revenue: float  # Maximum as % of annual revenue (e.g., 4% for GDPR)
    per_record_fine: float | None = None  # Fine per affected record
    min_fine: float = 0.0  # Minimum fine
    aggravating_factors: list[str] = field(default_factory=list)
    mitigating_factors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "regulation": self.regulation,
            "max_fine_absolute": self.max_fine_absolute,
            "max_fine_percent_revenue": self.max_fine_percent_revenue,
            "per_record_fine": self.per_record_fine,
            "min_fine": self.min_fine,
            "aggravating_factors": self.aggravating_factors,
            "mitigating_factors": self.mitigating_factors,
        }


@dataclass
class ViolationRisk:
    """Risk assessment for a single violation."""

    id: UUID = field(default_factory=uuid4)
    violation_id: UUID | None = None
    rule_id: str = ""
    regulation: str = ""

    # Risk assessment
    severity: RiskSeverity = RiskSeverity.MEDIUM
    category: RiskCategory = RiskCategory.REGULATORY_FINE

    # Financial estimates
    min_exposure: float = 0.0
    max_exposure: float = 0.0
    expected_exposure: float = 0.0  # Most likely value
    confidence: float = 0.5  # 0-1 confidence in estimate

    # Factors
    likelihood: float = 0.5  # Probability of enforcement (0-1)
    impact_multiplier: float = 1.0  # Based on data volume, user count, etc.
    aggravating_factors: list[str] = field(default_factory=list)
    mitigating_factors: list[str] = field(default_factory=list)

    # Location context
    file_path: str | None = None
    code_location: str | None = None

    # Timestamps
    assessed_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "violation_id": str(self.violation_id) if self.violation_id else None,
            "rule_id": self.rule_id,
            "regulation": self.regulation,
            "severity": self.severity.value,
            "category": self.category.value,
            "min_exposure": self.min_exposure,
            "max_exposure": self.max_exposure,
            "expected_exposure": self.expected_exposure,
            "confidence": self.confidence,
            "likelihood": self.likelihood,
            "impact_multiplier": self.impact_multiplier,
            "aggravating_factors": self.aggravating_factors,
            "mitigating_factors": self.mitigating_factors,
            "file_path": self.file_path,
            "code_location": self.code_location,
            "assessed_at": self.assessed_at.isoformat(),
        }


@dataclass
class RepositoryRiskProfile:
    """Risk profile for a repository."""

    id: UUID = field(default_factory=uuid4)
    repository_id: UUID | None = None
    repository_name: str = ""

    # Aggregate risk
    total_violations: int = 0
    critical_violations: int = 0
    high_violations: int = 0
    medium_violations: int = 0
    low_violations: int = 0

    # Financial exposure
    total_min_exposure: float = 0.0
    total_max_exposure: float = 0.0
    total_expected_exposure: float = 0.0

    # By regulation
    exposure_by_regulation: dict[str, float] = field(default_factory=dict)

    # By category
    exposure_by_category: dict[str, float] = field(default_factory=dict)

    # Risk scores
    overall_risk_score: float = 0.0  # 0-100
    data_privacy_score: float = 0.0
    security_score: float = 0.0
    compliance_score: float = 0.0

    # Metadata
    last_assessed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    assessment_version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "repository_id": str(self.repository_id) if self.repository_id else None,
            "repository_name": self.repository_name,
            "total_violations": self.total_violations,
            "critical_violations": self.critical_violations,
            "high_violations": self.high_violations,
            "medium_violations": self.medium_violations,
            "low_violations": self.low_violations,
            "total_min_exposure": self.total_min_exposure,
            "total_max_exposure": self.total_max_exposure,
            "total_expected_exposure": self.total_expected_exposure,
            "exposure_by_regulation": self.exposure_by_regulation,
            "exposure_by_category": self.exposure_by_category,
            "overall_risk_score": self.overall_risk_score,
            "data_privacy_score": self.data_privacy_score,
            "security_score": self.security_score,
            "compliance_score": self.compliance_score,
            "last_assessed_at": self.last_assessed_at.isoformat(),
            "assessment_version": self.assessment_version,
        }


@dataclass
class OrganizationRiskDashboard:
    """Organization-wide risk dashboard."""

    organization_id: UUID | None = None

    # Organization context
    annual_revenue: float = 0.0  # Used for percentage-based fines
    employee_count: int = 0
    data_subject_count: int = 0  # Number of users/customers
    jurisdictions: list[str] = field(default_factory=list)

    # Aggregate exposure
    total_min_exposure: float = 0.0
    total_max_exposure: float = 0.0
    total_expected_exposure: float = 0.0

    # Risk breakdown
    exposure_by_regulation: dict[str, dict[str, float]] = field(default_factory=dict)
    exposure_by_repository: dict[str, float] = field(default_factory=dict)
    exposure_by_severity: dict[str, float] = field(default_factory=dict)

    # Risk scores
    overall_risk_score: float = 0.0
    risk_grade: str = "C"  # A, B, C, D, F

    # Trends
    risk_trend: RiskTrend = RiskTrend.STABLE
    exposure_30d_change: float = 0.0
    exposure_90d_change: float = 0.0

    # Top risks
    top_risks: list[ViolationRisk] = field(default_factory=list)
    recommended_actions: list[dict[str, Any]] = field(default_factory=list)

    # Comparison
    industry_benchmark: float | None = None
    percentile_rank: float | None = None

    # Metadata
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "annual_revenue": self.annual_revenue,
            "employee_count": self.employee_count,
            "data_subject_count": self.data_subject_count,
            "jurisdictions": self.jurisdictions,
            "total_min_exposure": self.total_min_exposure,
            "total_max_exposure": self.total_max_exposure,
            "total_expected_exposure": self.total_expected_exposure,
            "exposure_by_regulation": self.exposure_by_regulation,
            "exposure_by_repository": self.exposure_by_repository,
            "exposure_by_severity": self.exposure_by_severity,
            "overall_risk_score": self.overall_risk_score,
            "risk_grade": self.risk_grade,
            "risk_trend": self.risk_trend.value,
            "exposure_30d_change": self.exposure_30d_change,
            "exposure_90d_change": self.exposure_90d_change,
            "top_risks": [r.to_dict() for r in self.top_risks],
            "recommended_actions": self.recommended_actions,
            "industry_benchmark": self.industry_benchmark,
            "percentile_rank": self.percentile_rank,
            "generated_at": self.generated_at.isoformat(),
        }


@dataclass
class WhatIfScenario:
    """What-if scenario for risk analysis."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""

    # Scenario parameters
    scenario_type: str = "violation_fix"  # violation_fix, breach, new_regulation, expansion
    parameters: dict[str, Any] = field(default_factory=dict)

    # Results
    baseline_exposure: float = 0.0
    scenario_exposure: float = 0.0
    exposure_delta: float = 0.0
    exposure_delta_percent: float = 0.0

    # Details
    affected_violations: list[UUID] = field(default_factory=list)
    affected_regulations: list[str] = field(default_factory=list)

    # Recommendations
    recommendation: str = ""
    priority: str = "medium"

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "scenario_type": self.scenario_type,
            "parameters": self.parameters,
            "baseline_exposure": self.baseline_exposure,
            "scenario_exposure": self.scenario_exposure,
            "exposure_delta": self.exposure_delta,
            "exposure_delta_percent": self.exposure_delta_percent,
            "affected_violations": [str(v) for v in self.affected_violations],
            "affected_regulations": self.affected_regulations,
            "recommendation": self.recommendation,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class RiskReport:
    """Executive risk report."""

    id: UUID = field(default_factory=uuid4)
    organization_id: UUID | None = None
    report_type: str = "monthly"  # monthly, quarterly, annual, adhoc

    # Executive summary
    title: str = ""
    summary: str = ""
    key_findings: list[str] = field(default_factory=list)
    key_recommendations: list[str] = field(default_factory=list)

    # Risk overview
    total_exposure: float = 0.0
    exposure_change: float = 0.0
    risk_score: float = 0.0
    risk_grade: str = "C"

    # Breakdown
    exposure_by_regulation: dict[str, float] = field(default_factory=dict)
    exposure_by_category: dict[str, float] = field(default_factory=dict)

    # Trends
    historical_exposure: list[dict[str, Any]] = field(default_factory=list)  # [{date, value}]

    # Comparison
    industry_comparison: dict[str, Any] = field(default_factory=dict)

    # Actions
    remediation_roadmap: list[dict[str, Any]] = field(default_factory=list)
    projected_exposure_after_remediation: float = 0.0

    # Metadata
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    period_start: datetime | None = None
    period_end: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "report_type": self.report_type,
            "title": self.title,
            "summary": self.summary,
            "key_findings": self.key_findings,
            "key_recommendations": self.key_recommendations,
            "total_exposure": self.total_exposure,
            "exposure_change": self.exposure_change,
            "risk_score": self.risk_score,
            "risk_grade": self.risk_grade,
            "exposure_by_regulation": self.exposure_by_regulation,
            "exposure_by_category": self.exposure_by_category,
            "historical_exposure": self.historical_exposure,
            "industry_comparison": self.industry_comparison,
            "remediation_roadmap": self.remediation_roadmap,
            "projected_exposure_after_remediation": self.projected_exposure_after_remediation,
            "generated_at": self.generated_at.isoformat(),
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
        }


# ============================================================================
# Fine Structures by Regulation
# ============================================================================

REGULATION_FINES: dict[str, RegulationFineStructure] = {
    "GDPR": RegulationFineStructure(
        regulation="GDPR",
        max_fine_absolute=20_000_000,  # €20M
        max_fine_percent_revenue=0.04,  # 4% of global turnover
        per_record_fine=None,
        aggravating_factors=[
            "intentional_infringement",
            "lack_of_cooperation",
            "previous_infringements",
            "failure_to_implement_measures",
        ],
        mitigating_factors=[
            "cooperation_with_authority",
            "voluntary_notification",
            "implemented_measures",
            "no_prior_infringements",
        ],
    ),
    "CCPA": RegulationFineStructure(
        regulation="CCPA",
        max_fine_absolute=7_500,  # Per intentional violation
        max_fine_percent_revenue=0.0,
        per_record_fine=7500,  # $7,500 per intentional, $2,500 unintentional
        min_fine=2500,
        aggravating_factors=[
            "intentional_violation",
            "repeated_violations",
            "failure_to_cure",
        ],
        mitigating_factors=[
            "cured_within_30_days",
            "good_faith_effort",
            "cooperation",
        ],
    ),
    "HIPAA": RegulationFineStructure(
        regulation="HIPAA",
        max_fine_absolute=1_500_000,  # Per year, per violation category
        max_fine_percent_revenue=0.0,
        per_record_fine=50_000,  # Max per record for willful neglect
        min_fine=100,
        aggravating_factors=[
            "willful_neglect",
            "repeated_violations",
            "criminal_intent",
        ],
        mitigating_factors=[
            "reasonable_cause",
            "corrected_within_30_days",
            "lack_of_knowledge",
        ],
    ),
    "PCI-DSS": RegulationFineStructure(
        regulation="PCI-DSS",
        max_fine_absolute=500_000,  # Per month
        max_fine_percent_revenue=0.0,
        per_record_fine=None,
        aggravating_factors=[
            "card_data_breach",
            "non_compliance_duration",
            "fraudulent_transactions",
        ],
        mitigating_factors=[
            "quick_remediation",
            "incident_response",
            "forensic_cooperation",
        ],
    ),
    "SOX": RegulationFineStructure(
        regulation="SOX",
        max_fine_absolute=5_000_000,  # Criminal penalties
        max_fine_percent_revenue=0.0,
        per_record_fine=None,
        aggravating_factors=[
            "knowingly_false_certification",
            "fraud",
            "obstruction",
        ],
        mitigating_factors=[
            "cooperation",
            "voluntary_disclosure",
            "remediation_efforts",
        ],
    ),
    "EU AI Act": RegulationFineStructure(
        regulation="EU AI Act",
        max_fine_absolute=35_000_000,  # €35M
        max_fine_percent_revenue=0.07,  # 7% of global turnover
        per_record_fine=None,
        aggravating_factors=[
            "prohibited_ai_practice",
            "high_risk_non_compliance",
            "lack_of_transparency",
        ],
        mitigating_factors=[
            "sme_compliance",
            "voluntary_measures",
            "cooperation",
        ],
    ),
    "NIS2": RegulationFineStructure(
        regulation="NIS2",
        max_fine_absolute=10_000_000,  # €10M
        max_fine_percent_revenue=0.02,  # 2% of global turnover
        per_record_fine=None,
        aggravating_factors=[
            "critical_infrastructure",
            "repeated_violations",
            "security_incident_failure",
        ],
        mitigating_factors=[
            "incident_notification",
            "security_measures",
            "cooperation",
        ],
    ),
}
