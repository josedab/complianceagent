"""Data models for Compliance Digital Twin."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class ScenarioType(str, Enum):
    """Types of simulation scenarios."""

    CODE_CHANGE = "code_change"
    ARCHITECTURE_CHANGE = "architecture_change"
    VENDOR_CHANGE = "vendor_change"
    REGULATION_ADOPTION = "regulation_adoption"
    DATA_FLOW_CHANGE = "data_flow_change"
    INFRASTRUCTURE_CHANGE = "infrastructure_change"
    JURISDICTION_EXPANSION = "jurisdiction_expansion"
    MERGER_ACQUISITION = "merger_acquisition"


class ComplianceStatus(str, Enum):
    """Compliance status levels."""

    COMPLIANT = "compliant"
    PARTIAL = "partial"
    NON_COMPLIANT = "non_compliant"
    UNKNOWN = "unknown"


@dataclass
class ComplianceIssue:
    """A compliance issue in a snapshot or simulation."""

    id: UUID = field(default_factory=uuid4)
    code: str = ""
    message: str = ""
    severity: str = "medium"
    regulation: str | None = None
    file_path: str | None = None
    line_number: int | None = None
    category: str | None = None
    remediation: str | None = None


@dataclass
class RegulationCompliance:
    """Compliance status for a specific regulation."""

    regulation: str = ""
    status: ComplianceStatus = ComplianceStatus.UNKNOWN
    score: float = 0.0
    issues_count: int = 0
    critical_count: int = 0
    requirements_met: int = 0
    requirements_total: int = 0
    last_assessed: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ComplianceSnapshot:
    """Point-in-time compliance state of a codebase."""

    id: UUID = field(default_factory=uuid4)
    organization_id: UUID | None = None
    repository_id: UUID | None = None
    name: str = ""
    description: str = ""
    commit_sha: str | None = None
    branch: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Compliance state
    overall_score: float = 0.0
    overall_status: ComplianceStatus = ComplianceStatus.UNKNOWN
    regulations: list[RegulationCompliance] = field(default_factory=list)
    issues: list[ComplianceIssue] = field(default_factory=list)

    # Codebase info
    files_analyzed: int = 0
    total_lines: int = 0
    languages: list[str] = field(default_factory=list)

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def critical_issues(self) -> list[ComplianceIssue]:
        return [i for i in self.issues if i.severity == "critical"]

    @property
    def high_issues(self) -> list[ComplianceIssue]:
        return [i for i in self.issues if i.severity == "high"]


@dataclass
class ScenarioParameter:
    """A configurable parameter for scenario simulation."""
    name: str = ""
    param_type: str = "string"  # string, number, boolean, list, enum
    description: str = ""
    default_value: Any = None
    min_value: float | None = None
    max_value: float | None = None
    allowed_values: list[str] = field(default_factory=list)
    required: bool = False


@dataclass
class SimulationScenario:
    """A simulation scenario to test."""

    id: UUID = field(default_factory=uuid4)
    organization_id: UUID | None = None
    name: str = ""
    description: str = ""
    scenario_type: ScenarioType = ScenarioType.CODE_CHANGE
    created_by: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Scenario parameters
    parameters: dict[str, Any] = field(default_factory=dict)
    parameter_schema: list[ScenarioParameter] = field(default_factory=list)

    # Code changes (for code_change scenarios)
    file_changes: list[dict[str, Any]] = field(default_factory=list)

    # Architecture changes
    new_components: list[str] = field(default_factory=list)
    removed_components: list[str] = field(default_factory=list)

    # Vendor changes
    new_vendors: list[dict[str, Any]] = field(default_factory=list)
    removed_vendors: list[str] = field(default_factory=list)

    # Regulation changes
    new_regulations: list[str] = field(default_factory=list)
    removed_regulations: list[str] = field(default_factory=list)

    # Jurisdiction expansion
    target_jurisdictions: list[str] = field(default_factory=list)


@dataclass
class CostEstimate:
    """Cost/effort/timeline estimate for a simulation scenario."""
    engineering_hours: float = 0.0
    engineering_cost_usd: float = 0.0
    legal_review_hours: float = 0.0
    legal_cost_usd: float = 0.0
    tooling_cost_usd: float = 0.0
    training_cost_usd: float = 0.0
    total_cost_usd: float = 0.0
    timeline_weeks: float = 0.0
    confidence: float = 0.7
    breakdown: dict[str, float] = field(default_factory=dict)


@dataclass
class BlastRadiusNode:
    """Node in the blast radius visualization."""
    id: str = ""
    name: str = ""
    node_type: str = ""  # regulation, service, team, vendor
    impact_level: str = "none"  # none, low, medium, high, critical
    distance: int = 0  # hops from change origin


@dataclass
class BlastRadiusMap:
    """Visual blast radius showing impact spread of a change."""
    center: str = ""
    nodes: list[BlastRadiusNode] = field(default_factory=list)
    edges: list[dict[str, str]] = field(default_factory=list)
    max_distance: int = 0
    total_affected: int = 0


@dataclass
class ScenarioComparison:
    """Side-by-side comparison of multiple scenario results."""
    scenarios: list[dict] = field(default_factory=list)
    best_scenario_id: str = ""
    worst_scenario_id: str = ""
    recommendation: str = ""


@dataclass
class ExecutiveDashboard:
    """Executive dashboard data for digital twin status."""
    overall_score: float = 0.0
    score_trend: list[dict[str, float]] = field(default_factory=list)
    active_simulations: int = 0
    completed_simulations: int = 0
    regulation_coverage: dict[str, float] = field(default_factory=dict)
    top_risks: list[dict] = field(default_factory=list)
    recent_scenarios: list[dict] = field(default_factory=list)
    blast_radius: BlastRadiusMap | None = None
    cost_summary: CostEstimate | None = None


@dataclass
class SimulationResult:
    """Result of running a simulation."""

    id: UUID = field(default_factory=uuid4)
    scenario_id: UUID | None = None
    baseline_snapshot_id: UUID | None = None

    # Timing
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    duration_ms: float = 0.0

    # Before/after comparison
    baseline_score: float = 0.0
    simulated_score: float = 0.0
    score_delta: float = 0.0

    compliance_before: dict[str, float] = field(default_factory=dict)
    compliance_after: dict[str, float] = field(default_factory=dict)

    # Issues
    new_issues: list[ComplianceIssue] = field(default_factory=list)
    resolved_issues: list[ComplianceIssue] = field(default_factory=list)
    unchanged_issues: list[ComplianceIssue] = field(default_factory=list)

    # Summary
    passed: bool = True
    risk_delta: float = 0.0
    recommendations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    # Cost/effort/timeline
    cost_estimate: CostEstimate | None = None
    blast_radius: BlastRadiusMap | None = None

    @property
    def new_critical_issues(self) -> int:
        return sum(1 for i in self.new_issues if i.severity == "critical")

    @property
    def improvement_percentage(self) -> float:
        if self.baseline_score == 0:
            return 0
        return ((self.simulated_score - self.baseline_score) / self.baseline_score) * 100
