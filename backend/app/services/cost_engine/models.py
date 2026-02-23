"""Compliance Cost Attribution Engine models."""

from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4


class CostCategory(str, Enum):
    """Categories of compliance costs."""

    SCANNING = "scanning"
    REMEDIATION = "remediation"
    REVIEW = "review"
    TRAINING = "training"
    AUDIT_PREP = "audit_prep"
    CERTIFICATION = "certification"


@dataclass
class CostAttribution:
    """A cost attribution entry."""

    id: UUID = field(default_factory=uuid4)
    team: str = ""
    repository: str = ""
    framework: str = ""
    category: CostCategory = CostCategory.SCANNING
    hours: float = 0.0
    cost_usd: float = 0.0
    period: str = ""


@dataclass
class TeamCostSummary:
    """Summary of compliance costs for a team."""

    team: str = ""
    total_cost: float = 0.0
    total_hours: float = 0.0
    breakdown_by_framework: dict[str, float] = field(default_factory=dict)
    trend_pct: float = 0.0


@dataclass
class CostForecast:
    """Projected compliance costs."""

    period: str = ""
    projected_cost: float = 0.0
    confidence: float = 0.0
    assumptions: list[str] = field(default_factory=list)


@dataclass
class ROIReport:
    """Return on investment report for compliance tooling."""

    compliance_cost_before: float = 0.0
    compliance_cost_after: float = 0.0
    savings: float = 0.0
    roi_pct: float = 0.0
    payback_months: float = 0.0
