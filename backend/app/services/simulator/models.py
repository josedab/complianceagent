"""Scenario simulator data models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class ScenarioType(str, Enum):
    """Type of scenario being simulated."""
    CODE_CHANGE = "code_change"           # Proposed code modifications
    ARCHITECTURE_CHANGE = "architecture"  # System architecture changes
    VENDOR_CHANGE = "vendor"             # Adding/changing vendors
    DATA_FLOW_CHANGE = "data_flow"       # Changes to data processing
    REGULATORY_CHANGE = "regulatory"     # New/changed regulation
    EXPANSION = "expansion"              # Geographic/market expansion


class RiskCategory(str, Enum):
    """Categories of compliance risk."""
    DATA_PRIVACY = "data_privacy"
    DATA_SECURITY = "data_security"
    ACCESS_CONTROL = "access_control"
    AUDIT_LOGGING = "audit_logging"
    DATA_RETENTION = "data_retention"
    CONSENT_MANAGEMENT = "consent"
    CROSS_BORDER = "cross_border"
    VENDOR_RISK = "vendor_risk"
    AI_COMPLIANCE = "ai_compliance"


@dataclass
class CodeChangeScenario:
    """Details for code change scenario."""
    file_path: str
    proposed_changes: str
    language: str
    affected_functions: list[str] = field(default_factory=list)


@dataclass
class ArchitectureChangeScenario:
    """Details for architecture change scenario."""
    component_name: str
    change_description: str
    affected_services: list[str] = field(default_factory=list)
    new_data_flows: list[dict] = field(default_factory=list)


@dataclass
class VendorChangeScenario:
    """Details for vendor change scenario."""
    vendor_name: str
    vendor_type: str  # cloud, saas, data_processor, etc.
    data_shared: list[str] = field(default_factory=list)
    jurisdictions: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)


@dataclass
class ExpansionScenario:
    """Details for geographic/market expansion."""
    target_regions: list[str]
    data_types_affected: list[str]
    user_types: list[str] = field(default_factory=list)


@dataclass
class Scenario:
    """A what-if scenario for simulation."""
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID | None = None
    repository_id: UUID | None = None
    
    name: str = ""
    description: str = ""
    scenario_type: ScenarioType = ScenarioType.CODE_CHANGE
    
    # Scenario-specific details (one will be populated)
    code_change: CodeChangeScenario | None = None
    architecture_change: ArchitectureChangeScenario | None = None
    vendor_change: VendorChangeScenario | None = None
    expansion: ExpansionScenario | None = None
    
    # Frameworks to evaluate against
    target_frameworks: list[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: UUID | None = None


@dataclass
class ComplianceDelta:
    """Change in compliance status for a framework."""
    framework: str
    current_score: float
    projected_score: float
    score_change: float
    
    current_grade: str
    projected_grade: str
    grade_changed: bool
    
    new_gaps: list[dict] = field(default_factory=list)
    resolved_gaps: list[dict] = field(default_factory=list)
    
    risk_categories_affected: list[RiskCategory] = field(default_factory=list)


@dataclass
class ImpactPrediction:
    """Predicted impact of a scenario."""
    category: RiskCategory
    severity: str  # critical, high, medium, low
    description: str
    affected_requirements: list[str] = field(default_factory=list)
    mitigation_suggestions: list[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class SimulationResult:
    """Result of scenario simulation."""
    scenario_id: UUID
    scenario_name: str
    scenario_type: ScenarioType
    
    # Overall assessment
    overall_risk_level: str  # critical, high, medium, low
    recommendation: str  # proceed, proceed_with_caution, review_required, not_recommended
    summary: str
    
    # Compliance impact
    compliance_deltas: list[ComplianceDelta] = field(default_factory=list)
    
    # Detailed predictions
    impact_predictions: list[ImpactPrediction] = field(default_factory=list)
    
    # Specific issues
    blocking_issues: list[dict] = field(default_factory=list)
    warnings: list[dict] = field(default_factory=list)
    
    # Recommendations
    required_actions: list[str] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)
    
    # Effort estimation
    estimated_remediation_hours: float = 0.0
    estimated_timeline_days: int = 0
    
    # Metadata
    simulated_at: datetime = field(default_factory=datetime.utcnow)
    confidence: float = 0.0
