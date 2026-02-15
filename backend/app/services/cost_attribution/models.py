"""Compliance Cost Attribution Engine models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class CostCategory(str, Enum):
    ENGINEERING = "engineering"
    LEGAL_REVIEW = "legal_review"
    AUDIT = "audit"
    FINES = "fines"
    TOOLING = "tooling"
    TRAINING = "training"
    CONSULTING = "consulting"


class CostPeriod(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


@dataclass
class CostEntry:
    """A single compliance cost entry."""

    id: UUID = field(default_factory=uuid4)
    regulation: str = ""
    category: CostCategory = CostCategory.ENGINEERING
    amount: float = 0.0
    currency: str = "USD"
    description: str = ""
    code_module: str = ""
    period: CostPeriod = CostPeriod.MONTHLY
    recorded_at: datetime | None = None


@dataclass
class RegulationCostSummary:
    """Cost summary for a regulation."""

    regulation: str = ""
    total_cost: float = 0.0
    cost_by_category: dict[str, float] = field(default_factory=dict)
    trend_pct: float = 0.0
    top_modules: list[dict] = field(default_factory=list)
    period: str = ""


@dataclass
class ROIAnalysis:
    """ROI analysis for compliance investment."""

    id: UUID = field(default_factory=uuid4)
    regulation: str = ""
    investment: float = 0.0
    savings: float = 0.0
    roi_pct: float = 0.0
    payback_months: int = 0
    assumptions: list[str] = field(default_factory=list)
    analyzed_at: datetime | None = None


@dataclass
class MarketExitScenario:
    """Market exit cost scenario."""

    id: UUID = field(default_factory=uuid4)
    jurisdiction: str = ""
    current_cost: float = 0.0
    exit_cost: float = 0.0
    revenue_at_risk: float = 0.0
    recommendation: str = ""
    breakeven_months: int = 0


@dataclass
class CostDashboard:
    """Overall compliance cost dashboard."""

    total_compliance_cost: float = 0.0
    cost_by_regulation: dict[str, float] = field(default_factory=dict)
    cost_by_category: dict[str, float] = field(default_factory=dict)
    month_over_month_change: float = 0.0
    top_cost_drivers: list[dict] = field(default_factory=list)
    roi_summary: dict = field(default_factory=dict)
    generated_at: datetime | None = None
