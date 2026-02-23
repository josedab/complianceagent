"""Auto-Healing Compliance Pipeline models."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class PipelineState(str, Enum):
    """Auto-healing pipeline state."""

    TRIGGERED = "triggered"
    ANALYZING = "analyzing"
    GENERATING_FIXES = "generating_fixes"
    TESTING = "testing"
    AWAITING_APPROVAL = "awaiting_approval"
    MERGING = "merging"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class TriggerType(str, Enum):
    """What triggered the auto-healing pipeline."""

    REGULATION_CHANGE = "regulation_change"
    SCAN_VIOLATION = "scan_violation"
    DRIFT_DETECTED = "drift_detected"
    MANUAL = "manual"
    SCHEDULED = "scheduled"


class ApprovalPolicy(str, Enum):
    """How fixes are approved."""

    AUTO_MERGE_LOW_RISK = "auto_merge_low_risk"
    REQUIRE_REVIEW = "require_review"
    REQUIRE_TEAM_LEAD = "require_team_lead"
    REQUIRE_COMPLIANCE_OFFICER = "require_compliance_officer"


@dataclass
class PipelineRun:
    """A single auto-healing pipeline execution."""

    id: UUID = field(default_factory=uuid4)
    trigger_type: TriggerType = TriggerType.MANUAL
    trigger_source: str = ""
    state: PipelineState = PipelineState.TRIGGERED
    repository: str = ""
    branch: str = "main"
    regulation: str = ""
    violations_detected: int = 0
    fixes_generated: int = 0
    fixes_applied: int = 0
    tests_passed: bool = False
    pr_number: int | None = None
    pr_url: str | None = None
    approval_policy: ApprovalPolicy = ApprovalPolicy.REQUIRE_REVIEW
    approved_by: str | None = None
    error_message: str | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    history: list[dict[str, Any]] = field(default_factory=list)

    def transition(self, new_state: PipelineState, actor: str = "system") -> None:
        self.history.append(
            {
                "from": self.state.value,
                "to": new_state.value,
                "actor": actor,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        self.state = new_state


@dataclass
class PipelineConfig:
    """Configuration for the auto-healing pipeline."""

    enabled: bool = True
    auto_merge_low_risk: bool = False
    require_tests_pass: bool = True
    max_fixes_per_run: int = 20
    approval_policy: ApprovalPolicy = ApprovalPolicy.REQUIRE_REVIEW
    notify_channels: list[str] = field(default_factory=lambda: ["slack"])
    excluded_paths: list[str] = field(default_factory=list)
    cooldown_minutes: int = 30


@dataclass
class PipelineMetrics:
    """Metrics for auto-healing pipeline performance."""

    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    rejected_runs: int = 0
    avg_time_to_fix_hours: float = 0.0
    auto_merge_rate: float = 0.0
    fix_acceptance_rate: float = 0.0
    violations_resolved: int = 0
