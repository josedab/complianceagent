"""Compliance Cost-Benefit Analyzer models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class CostCategory(str, Enum):
    ENGINEERING = "engineering"
    TOOLING = "tooling"
    AUDIT = "audit"
    LEGAL = "legal"
    TRAINING = "training"
    OPPORTUNITY = "opportunity"


class InvestmentStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class ComplianceInvestment:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    framework: str = ""
    category: CostCategory = CostCategory.ENGINEERING
    cost_usd: float = 0.0
    engineering_hours: float = 0.0
    status: InvestmentStatus = InvestmentStatus.PLANNED
    score_impact: float = 0.0
    risk_reduction_usd: float = 0.0
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class ROICalculation:
    investment_id: UUID = field(default_factory=uuid4)
    investment_name: str = ""
    total_cost: float = 0.0
    risk_reduction: float = 0.0
    roi_pct: float = 0.0
    payback_months: float = 0.0
    net_benefit: float = 0.0
    score_improvement: float = 0.0


@dataclass
class CostBreakdown:
    framework: str = ""
    total_cost: float = 0.0
    by_category: dict[str, float] = field(default_factory=dict)
    engineering_hours: float = 0.0
    cost_per_point: float = 0.0


@dataclass
class ExecutiveReport:
    id: UUID = field(default_factory=uuid4)
    period: str = ""
    total_investment: float = 0.0
    total_risk_reduction: float = 0.0
    overall_roi_pct: float = 0.0
    framework_breakdown: list[CostBreakdown] = field(default_factory=list)
    top_investments: list[ROICalculation] = field(default_factory=list)
    highlights: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    generated_at: datetime | None = None


@dataclass
class CostBenefitStats:
    total_investments: int = 0
    total_spend: float = 0.0
    total_risk_reduction: float = 0.0
    avg_roi_pct: float = 0.0
    by_framework: dict[str, float] = field(default_factory=dict)
    by_category: dict[str, float] = field(default_factory=dict)
