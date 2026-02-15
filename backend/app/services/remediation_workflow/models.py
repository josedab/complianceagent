"""Automated Compliance Remediation Workflow models."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
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


class ApprovalStatus(str, Enum):
    """Status of an approval in the chain."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"


@dataclass
class ApprovalStep:
    """A step in the approval chain."""
    id: UUID = field(default_factory=uuid4)
    approver_role: str = ""
    approver_name: str = ""
    status: ApprovalStatus = ApprovalStatus.PENDING
    comment: str = ""
    decided_at: datetime | None = None
    order: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "approver_role": self.approver_role,
            "approver_name": self.approver_name,
            "status": self.status.value,
            "comment": self.comment,
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
            "order": self.order,
        }


@dataclass
class ApprovalChain:
    """Multi-level approval chain for a remediation workflow."""
    id: UUID = field(default_factory=uuid4)
    workflow_id: UUID | None = None
    steps: list[ApprovalStep] = field(default_factory=list)
    current_step: int = 0
    is_complete: bool = False
    final_status: str = "pending"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "workflow_id": str(self.workflow_id) if self.workflow_id else None,
            "steps": [s.to_dict() for s in self.steps],
            "current_step": self.current_step,
            "is_complete": self.is_complete,
            "final_status": self.final_status,
        }


@dataclass
class RollbackRecord:
    """Record of a workflow rollback."""
    id: UUID = field(default_factory=uuid4)
    workflow_id: UUID | None = None
    reason: str = ""
    rolled_back_by: str = ""
    original_state: str = ""
    rolled_back_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    files_reverted: list[str] = field(default_factory=list)
    success: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "workflow_id": str(self.workflow_id) if self.workflow_id else None,
            "reason": self.reason,
            "rolled_back_by": self.rolled_back_by,
            "original_state": self.original_state,
            "rolled_back_at": self.rolled_back_at.isoformat(),
            "files_reverted": self.files_reverted,
            "success": self.success,
        }


@dataclass
class RemediationAnalytics:
    """Analytics for remediation workflows."""
    total_workflows: int = 0
    completed_workflows: int = 0
    in_progress_workflows: int = 0
    failed_workflows: int = 0
    rolled_back_workflows: int = 0
    avg_time_to_remediate_hours: float = 0.0
    fix_success_rate: float = 0.0
    auto_fix_rate: float = 0.0
    top_violation_types: list[dict[str, Any]] = field(default_factory=list)
    monthly_trend: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_workflows": self.total_workflows,
            "completed_workflows": self.completed_workflows,
            "in_progress_workflows": self.in_progress_workflows,
            "failed_workflows": self.failed_workflows,
            "rolled_back_workflows": self.rolled_back_workflows,
            "avg_time_to_remediate_hours": self.avg_time_to_remediate_hours,
            "fix_success_rate": self.fix_success_rate,
            "auto_fix_rate": self.auto_fix_rate,
            "top_violation_types": self.top_violation_types,
            "monthly_trend": self.monthly_trend,
        }
