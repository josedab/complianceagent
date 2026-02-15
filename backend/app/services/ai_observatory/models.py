"""AI Model Compliance Observatory models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class AIRiskLevel(str, Enum):
    """EU AI Act risk classification."""

    PROHIBITED = "prohibited"
    HIGH_RISK = "high_risk"
    LIMITED_RISK = "limited_risk"
    MINIMAL_RISK = "minimal_risk"


class ModelStatus(str, Enum):
    """AI model compliance status."""

    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    UNDER_REVIEW = "under_review"
    EXEMPT = "exempt"


class BiasMetricType(str, Enum):
    """Fairness and bias metric type."""

    DEMOGRAPHIC_PARITY = "demographic_parity"
    EQUALIZED_ODDS = "equalized_odds"
    DISPARATE_IMPACT = "disparate_impact"
    CALIBRATION = "calibration"
    INDIVIDUAL_FAIRNESS = "individual_fairness"


@dataclass
class AIModel:
    """A registered AI model."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    model_type: str = ""
    version: str = ""
    framework: str = ""
    use_case: str = ""
    risk_level: AIRiskLevel = AIRiskLevel.MINIMAL_RISK
    status: ModelStatus = ModelStatus.UNDER_REVIEW
    owner: str = ""
    deployed_at: datetime | None = None
    last_assessed_at: datetime | None = None


@dataclass
class BiasMetric:
    """A bias/fairness metric measurement."""

    id: UUID = field(default_factory=uuid4)
    model_id: UUID = field(default_factory=uuid4)
    metric_type: BiasMetricType = BiasMetricType.DEMOGRAPHIC_PARITY
    value: float = 0.0
    threshold: float = 0.0
    is_passing: bool = True
    protected_attribute: str = ""
    measured_at: datetime | None = None


@dataclass
class ExplainabilityReport:
    """Explainability assessment for an AI model."""

    id: UUID = field(default_factory=uuid4)
    model_id: UUID = field(default_factory=uuid4)
    method: str = ""
    feature_importance: dict[str, float] = field(default_factory=dict)
    explanation_coverage: float = 0.0
    gdpr_art22_compliant: bool = False
    eu_ai_act_art13_compliant: bool = False
    generated_at: datetime | None = None


@dataclass
class ModelComplianceReport:
    """Full compliance report for an AI model."""

    id: UUID = field(default_factory=uuid4)
    model_id: UUID = field(default_factory=uuid4)
    risk_level: AIRiskLevel = AIRiskLevel.MINIMAL_RISK
    bias_metrics: list[BiasMetric] = field(default_factory=list)
    explainability: ExplainabilityReport | None = None
    documentation_complete: bool = False
    human_oversight_implemented: bool = False
    technical_documentation: str = ""
    overall_compliant: bool = False
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    assessed_at: datetime | None = None


@dataclass
class ObservatoryDashboard:
    """Dashboard summary for the AI observatory."""

    total_models: int = 0
    by_risk_level: dict = field(default_factory=dict)
    compliant_count: int = 0
    non_compliant_count: int = 0
    avg_bias_score: float = 0.0
    models_needing_review: int = 0
    recent_alerts: list[dict] = field(default_factory=list)
