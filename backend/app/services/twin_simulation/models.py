"""Compliance Digital Twin Simulation models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class ChangeType(str, Enum):
    CODE_CHANGE = "code_change"
    DEPENDENCY_ADD = "dependency_add"
    DEPENDENCY_REMOVE = "dependency_remove"
    VENDOR_CHANGE = "vendor_change"
    ARCHITECTURE_CHANGE = "architecture_change"
    CONFIG_CHANGE = "config_change"


class SimulationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProposedChange:
    id: UUID = field(default_factory=uuid4)
    change_type: ChangeType = ChangeType.CODE_CHANGE
    description: str = ""
    target: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class SimulationResult:
    id: UUID = field(default_factory=uuid4)
    changes: list[ProposedChange] = field(default_factory=list)
    status: SimulationStatus = SimulationStatus.COMPLETED
    score_before: float = 85.0
    score_after: float = 85.0
    score_delta: float = 0.0
    framework_impacts: list[dict[str, Any]] = field(default_factory=list)
    risk_assessment: str = ""
    recommendations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    simulation_time_ms: float = 0.0
    created_at: datetime | None = None


@dataclass
class TwinSnapshot:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    repo: str = ""
    score: float = 0.0
    frameworks: dict[str, float] = field(default_factory=dict)
    violation_count: int = 0
    captured_at: datetime | None = None


@dataclass
class SimulationHistory:
    total_simulations: int = 0
    avg_score_delta: float = 0.0
    prevented_regressions: int = 0
    by_change_type: dict[str, int] = field(default_factory=dict)
