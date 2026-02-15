"""Data models for Federated Compliance Intelligence Network."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ThreatCategory(str, Enum):
    """Categories of compliance threats."""

    REGULATORY_CHANGE = "regulatory_change"
    ENFORCEMENT_ACTION = "enforcement_action"
    SECURITY_VULNERABILITY = "security_vulnerability"
    DATA_BREACH_PATTERN = "data_breach_pattern"
    COMPLIANCE_GAP = "compliance_gap"
    EMERGING_RISK = "emerging_risk"
    AUDIT_FINDING = "audit_finding"
    VENDOR_RISK = "vendor_risk"


class IntelligenceType(str, Enum):
    """Types of intelligence."""

    THREAT = "threat"
    PATTERN = "pattern"
    BEST_PRACTICE = "best_practice"
    REGULATORY_UPDATE = "regulatory_update"
    INDUSTRY_BENCHMARK = "industry_benchmark"


class SharingLevel(str, Enum):
    """Data sharing levels."""

    PUBLIC = "public"  # Visible to all network members
    INDUSTRY = "industry"  # Shared within same industry
    PRIVATE = "private"  # Only aggregated/anonymized stats shared
    RESTRICTED = "restricted"  # Organization-only


class Severity(str, Enum):
    """Severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ComplianceThreat(BaseModel):
    """A compliance threat shared in the network."""

    id: UUID = Field(default_factory=uuid4)

    # Threat details
    title: str
    description: str
    category: ThreatCategory
    severity: Severity

    # Affected areas
    regulations: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    regions: list[str] = Field(default_factory=list)

    # Technical details (anonymized)
    indicators: list[str] = Field(default_factory=list)  # Patterns/indicators
    affected_systems: list[str] = Field(default_factory=list)
    attack_vectors: list[str] = Field(default_factory=list)

    # Impact
    potential_impact: str | None = None
    financial_impact_range: str | None = None

    # Response
    recommended_actions: list[str] = Field(default_factory=list)
    mitigation_strategies: list[str] = Field(default_factory=list)

    # Sharing
    sharing_level: SharingLevel = SharingLevel.INDUSTRY
    contributor_id: UUID | None = None  # Anonymized
    contributor_industry: str | None = None

    # Verification
    verified: bool = False
    verified_by_count: int = 0

    # Metadata
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    expiry_date: datetime | None = None


class CompliancePattern(BaseModel):
    """A compliance pattern (positive or negative) shared in the network."""

    id: UUID = Field(default_factory=uuid4)

    # Pattern details
    name: str
    description: str
    pattern_type: str  # "anti-pattern" or "best-practice"

    # Context
    regulations: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)

    # Pattern definition
    detection_rules: list[str] = Field(default_factory=list)
    code_patterns: list[str] = Field(default_factory=list)
    config_patterns: list[str] = Field(default_factory=list)

    # Impact
    compliance_risk: str | None = None
    frequency: str | None = None  # How often seen across network

    # Resolution
    recommended_fix: str | None = None
    example_fix: str | None = None

    # Stats (aggregated from network)
    seen_count: int = 0
    fixed_count: int = 0
    average_fix_time_days: float | None = None

    # Sharing
    sharing_level: SharingLevel = SharingLevel.INDUSTRY

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class IntelligenceReport(BaseModel):
    """Aggregated intelligence report."""

    id: UUID = Field(default_factory=uuid4)

    # Report details
    title: str
    report_type: IntelligenceType
    period: str  # e.g., "2024-Q4", "2024-W52"

    # Summary
    summary: str
    key_findings: list[str] = Field(default_factory=list)

    # Threats
    active_threats: int = 0
    new_threats: int = 0
    resolved_threats: int = 0
    top_threats: list[dict[str, Any]] = Field(default_factory=list)

    # Patterns
    emerging_patterns: list[str] = Field(default_factory=list)
    declining_patterns: list[str] = Field(default_factory=list)

    # Regulatory
    regulatory_updates: list[str] = Field(default_factory=list)
    upcoming_deadlines: list[dict[str, str]] = Field(default_factory=list)

    # Industry benchmarks
    industry_benchmarks: dict[str, Any] = Field(default_factory=dict)

    # Recommendations
    recommendations: list[str] = Field(default_factory=list)
    priority_actions: list[str] = Field(default_factory=list)

    generated_at: datetime = Field(default_factory=datetime.utcnow)


class NetworkMember(BaseModel):
    """A member of the federated network."""

    id: UUID = Field(default_factory=uuid4)
    organization_id: UUID

    # Member info (anonymized for sharing)
    anonymous_id: str  # Hash-based ID for anonymous sharing
    industry: str
    region: str
    size_category: str  # small, medium, large, enterprise

    # Participation
    sharing_level: SharingLevel = SharingLevel.INDUSTRY
    contributions_count: int = 0
    verifications_count: int = 0
    reputation_score: float = 50.0  # 0-100

    # Preferences
    subscribed_categories: list[ThreatCategory] = Field(default_factory=list)
    subscribed_regulations: list[str] = Field(default_factory=list)
    subscribed_industries: list[str] = Field(default_factory=list)

    # Activity
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)

    is_active: bool = True


class FederatedNetwork(BaseModel):
    """The federated intelligence network."""

    id: UUID = Field(default_factory=uuid4)
    name: str = "ComplianceAgent Intelligence Network"

    # Network stats
    total_members: int = 0
    active_members: int = 0

    # Intelligence
    total_threats: int = 0
    active_threats: int = 0
    total_patterns: int = 0

    # Contributions
    total_contributions: int = 0
    contributions_this_month: int = 0

    # Coverage
    industries_covered: list[str] = Field(default_factory=list)
    regulations_covered: list[str] = Field(default_factory=list)
    regions_covered: list[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PrivacyConfig(BaseModel):
    """Differential privacy and anonymization settings for the network."""

    # Differential privacy
    epsilon: float = Field(default=1.0, ge=0.01, le=10.0, description="Privacy budget (lower = more private)")
    delta: float = Field(default=1e-5, ge=0.0, le=0.1, description="Probability of privacy breach")
    noise_mechanism: str = Field(default="laplace", description="Noise mechanism: laplace or gaussian")

    # Anonymization
    k_anonymity: int = Field(default=5, ge=2, le=100, description="Minimum group size for k-anonymity")
    suppress_small_groups: bool = Field(default=True, description="Suppress groups below k-anonymity threshold")
    generalize_locations: bool = Field(default=True, description="Generalize locations to region level")
    hash_contributor_ids: bool = Field(default=True, description="Hash contributor identifiers")

    # Data retention
    retention_days: int = Field(default=365, ge=30, le=3650, description="Days to retain shared intelligence")
    auto_expire_threats: bool = Field(default=True, description="Auto-expire threats after retention period")

    # Consent
    require_explicit_consent: bool = Field(default=True, description="Require explicit consent before sharing")
    allow_opt_out: bool = Field(default=True, description="Allow members to opt out of data sharing")
    data_minimization: bool = Field(default=True, description="Only share minimum necessary data")


# ============================================================================
# Pre-seeded Intelligence Data
# ============================================================================

INITIAL_THREATS: list[dict[str, Any]] = [
    {
        "title": "EU AI Act Enforcement Preparation",
        "description": "Regulatory bodies ramping up enforcement capabilities for EU AI Act compliance starting August 2025",
        "category": ThreatCategory.REGULATORY_CHANGE,
        "severity": Severity.HIGH,
        "regulations": ["EU AI Act"],
        "industries": ["AI/ML", "Technology", "Finance", "Healthcare"],
        "regions": ["EU", "EEA"],
        "recommended_actions": [
            "Complete AI system inventory",
            "Classify AI systems by risk level",
            "Implement required documentation for high-risk AI",
        ],
    },
    {
        "title": "GDPR Cross-Border Transfer Scrutiny Increase",
        "description": "DPAs increasing scrutiny of US data transfers following Schrems II, multiple enforcement actions expected",
        "category": ThreatCategory.ENFORCEMENT_ACTION,
        "severity": Severity.HIGH,
        "regulations": ["GDPR"],
        "industries": ["All"],
        "regions": ["EU", "US"],
        "recommended_actions": [
            "Review all US data transfers",
            "Complete Transfer Impact Assessments",
            "Implement supplementary measures",
        ],
    },
    {
        "title": "Supply Chain Vulnerability Exploitation Wave",
        "description": "Increased targeting of software supply chains affecting compliance posture",
        "category": ThreatCategory.SECURITY_VULNERABILITY,
        "severity": Severity.CRITICAL,
        "regulations": ["PCI-DSS", "HIPAA", "SOC 2"],
        "industries": ["Technology", "Finance", "Healthcare"],
        "recommended_actions": [
            "Audit SBOM for all production systems",
            "Implement dependency vulnerability scanning",
            "Review vendor security practices",
        ],
    },
    {
        "title": "State Privacy Law Divergence",
        "description": "US state privacy laws diverging, creating compliance complexity",
        "category": ThreatCategory.REGULATORY_CHANGE,
        "severity": Severity.MEDIUM,
        "regulations": ["CCPA", "CPRA", "State Privacy Laws"],
        "industries": ["All"],
        "regions": ["US"],
        "recommended_actions": [
            "Map business operations to state requirements",
            "Implement flexible consent management",
            "Create state-specific privacy notices",
        ],
    },
]

INITIAL_PATTERNS: list[dict[str, Any]] = [
    {
        "name": "Hardcoded Secrets in Repositories",
        "description": "Credentials and API keys committed to source code",
        "pattern_type": "anti-pattern",
        "regulations": ["SOC 2", "PCI-DSS", "GDPR"],
        "code_patterns": ["password =", "api_key =", "secret =", "token ="],
        "compliance_risk": "Unauthorized access to systems and data",
        "recommended_fix": "Use secrets management service (Vault, AWS Secrets Manager)",
        "seen_count": 847,
        "fixed_count": 621,
    },
    {
        "name": "Insufficient Logging for Compliance",
        "description": "Missing audit logs for compliance-relevant events",
        "pattern_type": "anti-pattern",
        "regulations": ["HIPAA", "PCI-DSS", "SOX", "GDPR"],
        "detection_rules": ["Missing access logs", "No audit trail", "Incomplete event capture"],
        "compliance_risk": "Unable to demonstrate compliance during audit",
        "recommended_fix": "Implement structured audit logging with retention",
        "seen_count": 523,
        "fixed_count": 298,
    },
    {
        "name": "Privacy by Design Implementation",
        "description": "Data minimization and privacy controls built into system design",
        "pattern_type": "best-practice",
        "regulations": ["GDPR", "CCPA", "LGPD"],
        "detection_rules": ["Data minimization checks", "Consent tracking", "Purpose limitation"],
        "seen_count": 234,
    },
]


# ============================================================================
# Reputation, Voting, Comparative Analytics & Network Health Models
# ============================================================================


@dataclass
class ContributorScore:
    """Reputation score for a network contributor."""
    member_id: UUID = field(default_factory=uuid4)
    organization_name: str = ""
    total_contributions: int = 0
    verified_contributions: int = 0
    accuracy_score: float = 0.0  # 0-1
    reputation_tier: str = "bronze"  # bronze, silver, gold, platinum
    first_contribution: datetime = field(default_factory=datetime.utcnow)
    last_contribution: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ComparativeInsight:
    """'Companies like yours' comparative insight."""
    insight_id: UUID = field(default_factory=uuid4)
    metric_name: str = ""
    your_value: float = 0.0
    peer_average: float = 0.0
    peer_median: float = 0.0
    percentile: float = 0.0  # Your percentile rank
    sample_size: int = 0
    industry: str = ""
    description: str = ""


@dataclass
class NetworkHealthMetrics:
    """Health metrics for the federated network."""
    total_members: int = 0
    active_members_30d: int = 0
    total_threats_shared: int = 0
    total_patterns_shared: int = 0
    avg_verification_rate: float = 0.0
    avg_contribution_quality: float = 0.0
    network_coverage_industries: int = 0
    network_coverage_regulations: int = 0
    top_contributors: list[ContributorScore] = field(default_factory=list)
    measured_at: datetime = field(default_factory=datetime.utcnow)
