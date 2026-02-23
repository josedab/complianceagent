"""Self-Healing Compliance Mesh models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class PipelineStage(str, Enum):
    DETECTED = "detected"
    ANALYZING = "analyzing"
    FIXING = "fixing"
    TESTING = "testing"
    PR_CREATING = "pr_creating"
    AWAITING_APPROVAL = "awaiting_approval"
    MERGING = "merging"
    COMPLETED = "completed"
    ESCALATED = "escalated"
    FAILED = "failed"


class EventType(str, Enum):
    VIOLATION_DETECTED = "violation_detected"
    DRIFT_DETECTED = "drift_detected"
    SCORE_DROP = "score_drop"
    NEW_REGULATION = "new_regulation"
    DEPENDENCY_VULNERABILITY = "dependency_vulnerability"


class RiskTier(str, Enum):
    AUTO_MERGE = "auto_merge"
    SINGLE_REVIEW = "single_review"
    TEAM_REVIEW = "team_review"
    MANUAL_ONLY = "manual_only"


@dataclass
class HealingEvent:
    id: UUID = field(default_factory=uuid4)
    event_type: EventType = EventType.VIOLATION_DETECTED
    source_service: str = ""
    repo: str = ""
    severity: str = "medium"
    description: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    detected_at: datetime | None = None


@dataclass
class HealingPipeline:
    id: UUID = field(default_factory=uuid4)
    event_id: UUID = field(default_factory=uuid4)
    repo: str = ""
    stage: PipelineStage = PipelineStage.DETECTED
    risk_tier: RiskTier = RiskTier.SINGLE_REVIEW
    stages_completed: list[str] = field(default_factory=list)
    fix_description: str = ""
    files_changed: list[str] = field(default_factory=list)
    test_passed: bool = False
    pr_url: str = ""
    time_to_heal_seconds: float = 0.0
    created_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class MeshConfig:
    enabled: bool = True
    auto_merge_max_risk: str = "low"
    max_concurrent_pipelines: int = 5
    test_required: bool = True
    approval_channels: list[str] = field(default_factory=lambda: ["slack"])
    excluded_repos: list[str] = field(default_factory=list)
    circuit_breaker_threshold: int = 3


@dataclass
class MeshStats:
    total_events: int = 0
    total_pipelines: int = 0
    completed_pipelines: int = 0
    auto_merged: int = 0
    escalated: int = 0
    avg_heal_time_seconds: float = 0.0
    by_stage: dict[str, int] = field(default_factory=dict)
    by_event_type: dict[str, int] = field(default_factory=dict)
