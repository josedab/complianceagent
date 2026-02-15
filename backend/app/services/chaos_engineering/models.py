"""Compliance Chaos Engineering models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID


class ExperimentType(str, Enum):
    """Type of compliance chaos experiment."""

    REMOVE_ENCRYPTION = "remove_encryption"
    DISABLE_AUDIT_LOGS = "disable_audit_logs"
    EXPOSE_PII = "expose_pii"
    BREAK_AUTH = "break_auth"
    REMOVE_BACKUPS = "remove_backups"
    DISABLE_CONSENT = "disable_consent"
    REMOVE_ACCESS_CONTROL = "remove_access_control"
    BREAK_DATA_RETENTION = "break_data_retention"
    DISABLE_BREACH_NOTIFICATION = "disable_breach_notification"
    REMOVE_DPIA = "remove_dpia"


class ExperimentStatus(str, Enum):
    """Status of a chaos experiment."""

    SCHEDULED = "scheduled"
    RUNNING = "running"
    DETECTED = "detected"
    UNDETECTED = "undetected"
    ROLLED_BACK = "rolled_back"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ChaosExperiment:
    """A compliance chaos engineering experiment."""

    id: UUID
    name: str
    description: str
    experiment_type: ExperimentType
    status: ExperimentStatus = ExperimentStatus.SCHEDULED
    target_service: str = ""
    target_environment: str = "staging"
    blast_radius: str = "single_service"
    affected_frameworks: list[str] = field(default_factory=list)
    time_to_detect_seconds: float | None = None
    time_to_remediate_seconds: float | None = None
    detection_method: str = ""
    auto_rollback: bool = True
    rollback_timeout_seconds: int = 300
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class GameDay:
    """A scheduled compliance game day."""

    id: UUID
    name: str
    description: str
    experiments: list[UUID] = field(default_factory=list)
    participants: list[str] = field(default_factory=list)
    team_readiness_score: float = 0.0
    total_experiments: int = 0
    experiments_detected: int = 0
    avg_detection_time_seconds: float = 0.0
    avg_remediation_time_seconds: float = 0.0
    scheduled_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class ChaosStats:
    """Aggregate chaos engineering statistics."""

    total_experiments: int = 0
    experiments_detected: int = 0
    experiments_undetected: int = 0
    avg_mttd_seconds: float = 0.0
    avg_mttr_seconds: float = 0.0
    detection_rate: float = 0.0
    game_days_completed: int = 0
    controls_validated: int = 0
    blind_spots_found: int = 0
