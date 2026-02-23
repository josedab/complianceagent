"""Compliance Debt Tracker models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class DebtPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DebtStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ACCEPTED_RISK = "accepted_risk"


@dataclass
class ComplianceDebtItem:
    id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    framework: str = ""
    rule_id: str = ""
    file_path: str = ""
    severity: DebtPriority = DebtPriority.MEDIUM
    status: DebtStatus = DebtStatus.OPEN
    risk_cost_usd: float = 0.0
    remediation_cost_usd: float = 0.0
    roi: float = 0.0
    days_open: int = 0
    repo: str = ""
    created_at: datetime | None = None


@dataclass
class SprintBurndown:
    sprint_name: str = ""
    start_items: int = 0
    resolved: int = 0
    remaining: int = 0
    velocity: float = 0.0


@dataclass
class DebtStats:
    total_items: int = 0
    by_priority: dict[str, int] = field(default_factory=dict)
    by_status: dict[str, int] = field(default_factory=dict)
    by_framework: dict[str, int] = field(default_factory=dict)
    total_risk_usd: float = 0.0
    total_remediation_usd: float = 0.0
    avg_roi: float = 0.0
