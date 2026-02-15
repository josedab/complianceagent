"""Predictive Compliance Cost Calculator models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class ComplexityLevel(str, Enum):
    """Complexity level for compliance implementations."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RegulationCategory(str, Enum):
    """Category of compliance regulation."""

    DATA_PRIVACY = "data_privacy"
    AI_GOVERNANCE = "ai_governance"
    FINANCIAL = "financial"
    HEALTHCARE = "healthcare"
    SECURITY = "security"
    INDUSTRY_SPECIFIC = "industry_specific"


@dataclass
class CostBreakdownItem:
    """Individual cost breakdown line item."""

    category: str
    description: str
    developer_days: float
    cost_usd: float
    complexity: ComplexityLevel


@dataclass
class ComparableImpl:
    """A comparable past implementation for reference."""

    regulation: str
    industry: str
    company_size: str
    actual_days: float
    actual_cost: float
    year: int


@dataclass
class CostPrediction:
    """Predicted cost for a compliance regulation implementation."""

    id: UUID
    regulation: str
    category: RegulationCategory
    affected_files: int
    affected_modules: int
    estimated_developer_days: float
    estimated_cost_usd: float
    confidence_pct: float
    cost_range_low: float
    cost_range_high: float
    risk_score: float
    breakdown: list[CostBreakdownItem] = field(default_factory=list)
    comparable_implementations: list[ComparableImpl] = field(default_factory=list)
    predicted_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ScenarioComparison:
    """Comparison of multiple compliance implementation scenarios."""

    id: UUID
    scenarios: list[CostPrediction] = field(default_factory=list)
    recommendation: str = ""
    total_cost_now: float = 0.0
    total_cost_delayed: float = 0.0
    delay_risk_premium_pct: float = 0.0


@dataclass
class CostHistory:
    """Historical record of predicted vs actual compliance cost."""

    id: UUID
    regulation: str
    predicted_cost: float
    actual_cost: float
    accuracy_pct: float
    completed_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ROISummary:
    """ROI summary for automated compliance vs manual."""

    annual_manual_cost: float
    annual_automated_cost: float
    annual_savings: float
    roi_pct: float
    payback_months: float
    compared_to: str = "manual"


@dataclass
class ExecutiveReport:
    """CFO-ready executive compliance cost report."""

    id: UUID = field(default_factory=uuid4)
    org_id: str = ""
    total_portfolio_cost: float = 0.0
    total_risk_exposure: float = 0.0
    annual_fine_risk: float = 0.0
    roi_with_automation: float = 0.0
    payback_period_months: float = 0.0
    priority_regulations: list[dict[str, Any]] = field(default_factory=list)
    cost_by_regulation: dict[str, float] = field(default_factory=dict)
    three_year_projection: dict[str, float] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)
