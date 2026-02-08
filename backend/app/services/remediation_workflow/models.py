"""Automated Compliance Remediation Workflow models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class WorkflowState(str, Enum):
    DETECTED = "detected"
    PLANNING = "planning"
    GENERATING = "generating"
    REVIEW = "review"
    APPROVED = "approved"
    MERGING = "merging"
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class RemediationPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ApprovalType(str, Enum):
    AUTO = "auto"
    MANUAL = "manual"
    TEAM_LEAD = "team_lead"


@dataclass
class RemediationFix:
    """A generated code fix for a compliance violation."""
    id: UUID = field(default_factory=uuid4)
    file_path: str = ""
    original_code: str = ""
    fixed_code: str = ""
    description: str = ""
    violation_ref: str = ""
    confidence: float = 0.0


@dataclass
class RemediationWorkflow:
    """An end-to-end remediation workflow instance."""
    id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    state: WorkflowState = WorkflowState.DETECTED
    priority: RemediationPriority = RemediationPriority.MEDIUM
    approval_type: ApprovalType = ApprovalType.MANUAL
    violation_id: str = ""
    framework: str = ""
    repository: str = ""
    fixes: list[RemediationFix] = field(default_factory=list)
    pr_number: int | None = None
    pr_url: str | None = None
    ticket_id: str | None = None
    ticket_url: str | None = None
    approved_by: str | None = None
    rollback_available: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None
    completed_at: datetime | None = None
    history: list[dict] = field(default_factory=list)

    def transition(self, new_state: WorkflowState, actor: str = "system") -> None:
        self.history.append({
            "from": self.state.value, "to": new_state.value,
            "actor": actor, "timestamp": datetime.now().isoformat(),
        })
        self.state = new_state
        self.updated_at = datetime.now()


@dataclass
class WorkflowConfig:
    """Configuration for remediation workflows."""
    auto_merge_low_risk: bool = False
    require_ci_pass: bool = True
    require_review: bool = True
    max_auto_fixes_per_day: int = 10
    notification_channels: list[str] = field(default_factory=lambda: ["slack"])
    approval_timeout_hours: int = 48
