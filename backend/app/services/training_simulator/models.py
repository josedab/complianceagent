"""Training simulator models."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ScenarioCategory(str, Enum):
    """Category of training scenario."""

    breach_response = "breach_response"
    data_request = "data_request"
    vendor_incident = "vendor_incident"
    audit_prep = "audit_prep"
    policy_violation = "policy_violation"


class DifficultyLevel(str, Enum):
    """Difficulty level for a scenario."""

    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"
    expert = "expert"


class SimStatus(str, Enum):
    """Status of a simulation session."""

    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"
    timed_out = "timed_out"


@dataclass
class TrainingScenario:
    """A compliance training scenario."""

    id: str = ""
    title: str = ""
    category: ScenarioCategory = ScenarioCategory.breach_response
    difficulty: DifficultyLevel = DifficultyLevel.beginner
    description: str = ""
    time_limit_minutes: int = 30
    steps: list[dict] = field(default_factory=list)
    passing_score: float = 70.0


@dataclass
class SimulationSession:
    """An active simulation session for a user."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_id: str = ""
    scenario_id: str = ""
    status: SimStatus = SimStatus.not_started
    current_step: int = 0
    score: float = 0.0
    time_elapsed_seconds: float = 0.0
    responses: list[dict] = field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class TrainingCertificate:
    """Certificate awarded on scenario completion."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_id: str = ""
    scenario_id: str = ""
    score: float = 0.0
    issued_at: datetime | None = None
    valid_until: datetime | None = None


@dataclass
class SimulatorStats:
    """Aggregate statistics for the training simulator."""

    total_sessions: int = 0
    completed: int = 0
    pass_rate: float = 0.0
    avg_score: float = 0.0
    by_category: dict = field(default_factory=dict)
    certificates_issued: int = 0
