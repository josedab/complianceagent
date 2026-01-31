"""Data models for Compliance Digital Twin."""

from dataclasses import dataclass, field
from datetime import datetime
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
    last_assessed: datetime = field(default_factory=datetime.utcnow)


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
    created_at: datetime = field(default_factory=datetime.utcnow)
    
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
class SimulationScenario:
    """A simulation scenario to test."""
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID | None = None
    name: str = ""
    description: str = ""
    scenario_type: ScenarioType = ScenarioType.CODE_CHANGE
    created_by: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Scenario parameters
    parameters: dict[str, Any] = field(default_factory=dict)
    
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


@dataclass
class SimulationResult:
    """Result of running a simulation."""
    id: UUID = field(default_factory=uuid4)
    scenario_id: UUID | None = None
    baseline_snapshot_id: UUID | None = None
    
    # Timing
    started_at: datetime = field(default_factory=datetime.utcnow)
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
    
    @property
    def new_critical_issues(self) -> int:
        return sum(1 for i in self.new_issues if i.severity == "critical")

    @property
    def improvement_percentage(self) -> float:
        if self.baseline_score == 0:
            return 0
        return ((self.simulated_score - self.baseline_score) / self.baseline_score) * 100
