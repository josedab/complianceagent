"""Compliance Sandbox Environment models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID


class SandboxStatus(str, Enum):
    """Status of a sandbox environment."""

    PROVISIONING = "provisioning"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    EXPIRED = "expired"
    FAILED = "failed"


class ViolationType(str, Enum):
    """Type of compliance violation seeded in a sandbox."""

    DATA_EXPOSURE = "data_exposure"
    MISSING_ENCRYPTION = "missing_encryption"
    MISSING_CONSENT = "missing_consent"
    EXCESSIVE_RETENTION = "excessive_retention"
    MISSING_AUDIT_LOG = "missing_audit_log"
    WEAK_AUTH = "weak_auth"
    MISSING_ACCESS_CONTROL = "missing_access_control"
    UNPROTECTED_PII = "unprotected_pii"
    MISSING_BREACH_NOTIFICATION = "missing_breach_notification"
    MISSING_DPIA = "missing_dpia"


class DifficultyLevel(str, Enum):
    """Difficulty level for a sandbox scenario."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class SandboxResources:
    """Resource limits for a sandbox environment."""

    cpu_limit: float = 0.5
    memory_limit_mb: int = 512
    storage_limit_mb: int = 256
    max_duration_minutes: int = 60


@dataclass
class SandboxProgress:
    """Progress tracking within a sandbox session."""

    completed_violations: int = 0
    total_violations: int = 0
    score: int = 0
    time_elapsed_minutes: float = 0.0
    hints_used: int = 0
    completed_at: datetime | None = None


@dataclass
class ViolationScenario:
    """A single compliance violation embedded in a sandbox scenario."""

    id: str
    type: ViolationType
    title: str
    description: str
    file_path: str
    code_snippet: str
    hint: str
    solution_snippet: str
    points: int
    regulation_article: str


@dataclass
class SandboxScenario:
    """A pre-built scenario containing multiple violations to find and fix."""

    id: str
    title: str
    description: str
    regulation: str
    violations: list[ViolationScenario] = field(default_factory=list)
    difficulty: DifficultyLevel = DifficultyLevel.BEGINNER
    estimated_minutes: int = 30
    learning_objectives: list[str] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class SandboxEnvironment:
    """An ephemeral sandbox environment instance."""

    id: UUID
    org_id: UUID
    user_id: UUID
    scenario_id: str
    status: SandboxStatus
    created_at: datetime
    expires_at: datetime
    resources: SandboxResources = field(default_factory=SandboxResources)
    connection_info: dict = field(default_factory=dict)
    progress: SandboxProgress = field(default_factory=SandboxProgress)


@dataclass
class SandboxResult:
    """Final result after completing a sandbox session."""

    id: UUID
    sandbox_id: UUID
    scenario_id: str
    score: int
    max_score: int
    completion_pct: float
    time_minutes: float
    violations_fixed: list[str] = field(default_factory=list)
    violations_missed: list[str] = field(default_factory=list)
    feedback: str = ""
    badge_earned: str | None = None


@dataclass
class SandboxBadge:
    """A badge earned through sandbox completion."""

    id: str
    name: str
    description: str
    icon: str
    criteria: str
    earned_at: datetime | None = None
