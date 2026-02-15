"""Compliance Debt Securitization models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID


class DebtPriority(str, Enum):
    """Priority of compliance debt."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CreditRating(str, Enum):
    """Compliance credit rating."""

    AAA = "AAA"
    AA = "AA"
    A = "A"
    BBB = "BBB"
    BB = "BB"
    B = "B"
    CCC = "CCC"
    D = "D"


@dataclass
class ComplianceDebtItem:
    """A single compliance debt item."""

    id: UUID
    title: str
    description: str
    priority: DebtPriority
    framework: str
    control: str = ""
    risk_score: float = 0.0
    cost_of_delay_per_day: float = 50.0
    accrued_interest: float = 0.0
    remediation_cost: float = 500.0
    days_outstanding: int = 0
    assigned_team: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    due_date: datetime | None = None


@dataclass
class ComplianceBond:
    """A compliance debt instrument visualization."""

    id: UUID
    name: str
    face_value: float
    current_value: float
    interest_rate: float = 0.05
    maturity_date: datetime | None = None
    framework: str = ""
    debt_items_count: int = 0
    yield_spread: float = 0.0


@dataclass
class DebtPortfolio:
    """Aggregate view of compliance debt."""

    total_debt_value: float = 0.0
    total_items: int = 0
    critical_items: int = 0
    high_items: int = 0
    medium_items: int = 0
    low_items: int = 0
    avg_days_outstanding: float = 0.0
    daily_accrual_rate: float = 0.0
    credit_rating: CreditRating = CreditRating.BBB
    debt_by_framework: dict[str, float] = field(default_factory=dict)
    remediation_velocity: float = 0.0
    projected_payoff_days: int = 0
