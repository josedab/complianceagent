"""Compliance Autonomous Operating System models."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class OrchestratorState(str, Enum):
    IDLE = "idle"
    SCANNING = "scanning"
    HEALING = "healing"
    PREDICTING = "predicting"
    REPORTING = "reporting"


class DecisionType(str, Enum):
    AUTO_FIX = "auto_fix"
    ESCALATE = "escalate"
    MONITOR = "monitor"
    PREDICT = "predict"
    REPORT = "report"


class AutonomyLevel(str, Enum):
    FULL = "full"
    SUPERVISED = "supervised"
    ADVISORY = "advisory"
    MANUAL = "manual"


@dataclass
class OrchestratorEvent:
    id: UUID = field(default_factory=uuid4)
    event_type: str = ""
    source_service: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    decision: DecisionType = DecisionType.MONITOR
    actions_taken: list[str] = field(default_factory=list)
    timestamp: datetime | None = None


@dataclass
class AutonomousDecision:
    id: UUID = field(default_factory=uuid4)
    event_id: UUID = field(default_factory=uuid4)
    decision_type: DecisionType = DecisionType.MONITOR
    confidence: float = 0.0
    reasoning: str = ""
    services_invoked: list[str] = field(default_factory=list)
    outcome: str = ""
    duration_ms: float = 0.0
    decided_at: datetime | None = None


@dataclass
class SystemHealth:
    state: OrchestratorState = OrchestratorState.IDLE
    autonomy_level: AutonomyLevel = AutonomyLevel.SUPERVISED
    services_active: int = 0
    events_processed: int = 0
    decisions_made: int = 0
    auto_fixes_applied: int = 0
    escalations: int = 0
    uptime_hours: float = 0.0
    last_cycle_at: datetime | None = None


@dataclass
class AutonomousOSStats:
    total_events: int = 0
    total_decisions: int = 0
    auto_fix_rate: float = 0.0
    avg_decision_time_ms: float = 0.0
    by_decision_type: dict[str, int] = field(default_factory=dict)
    services_coordinated: int = 175
