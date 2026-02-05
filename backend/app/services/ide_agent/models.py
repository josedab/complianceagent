"""Data models for Compliance Co-Pilot IDE Agent."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class AgentActionType(str, Enum):
    """Types of actions the IDE agent can perform."""

    ANALYZE = "analyze"
    REFACTOR = "refactor"
    CREATE_ISSUE = "create_issue"
    CREATE_PR = "create_pr"
    SUGGEST_FIX = "suggest_fix"
    BULK_FIX = "bulk_fix"
    EXPLAIN = "explain"


class AgentTriggerType(str, Enum):
    """Types of events that trigger the agent."""

    FILE_SAVE = "file_save"
    FILE_OPEN = "file_open"
    BRANCH_CREATE = "branch_create"
    PRE_COMMIT = "pre_commit"
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    PR_OPEN = "pr_open"


class AgentStatus(str, Enum):
    """Status of an agent session."""

    IDLE = "idle"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FixConfidence(str, Enum):
    """Confidence level for suggested fixes."""

    HIGH = "high"  # >90% - auto-apply recommended
    MEDIUM = "medium"  # 70-90% - review recommended
    LOW = "low"  # <70% - manual review required


@dataclass
class CodeLocation:
    """Location of code in a file."""

    file_path: str
    start_line: int
    end_line: int
    start_column: int = 0
    end_column: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "start_column": self.start_column,
            "end_column": self.end_column,
        }


@dataclass
class ComplianceViolation:
    """A detected compliance violation."""

    id: UUID = field(default_factory=uuid4)
    rule_id: str = ""
    rule_name: str = ""
    regulation: str = ""
    article_reference: str | None = None
    severity: str = "warning"
    message: str = ""
    location: CodeLocation | None = None
    original_code: str = ""
    confidence: float = 0.0
    detected_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "regulation": self.regulation,
            "article_reference": self.article_reference,
            "severity": self.severity,
            "message": self.message,
            "location": self.location.to_dict() if self.location else None,
            "original_code": self.original_code,
            "confidence": self.confidence,
            "detected_at": self.detected_at.isoformat(),
        }


@dataclass
class ProposedFix:
    """A proposed fix for a compliance violation."""

    id: UUID = field(default_factory=uuid4)
    violation_id: UUID | None = None
    fixed_code: str = ""
    explanation: str = ""
    confidence: FixConfidence = FixConfidence.MEDIUM
    confidence_score: float = 0.0
    imports_to_add: list[str] = field(default_factory=list)
    files_affected: list[str] = field(default_factory=list)
    breaking_changes: bool = False
    test_suggestions: list[str] = field(default_factory=list)
    rollback_available: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "violation_id": str(self.violation_id) if self.violation_id else None,
            "fixed_code": self.fixed_code,
            "explanation": self.explanation,
            "confidence": self.confidence.value,
            "confidence_score": self.confidence_score,
            "imports_to_add": self.imports_to_add,
            "files_affected": self.files_affected,
            "breaking_changes": self.breaking_changes,
            "test_suggestions": self.test_suggestions,
            "rollback_available": self.rollback_available,
        }


@dataclass
class AgentAction:
    """An action performed or proposed by the agent."""

    id: UUID = field(default_factory=uuid4)
    action_type: AgentActionType = AgentActionType.ANALYZE
    description: str = ""
    target_files: list[str] = field(default_factory=list)
    violations: list[ComplianceViolation] = field(default_factory=list)
    proposed_fixes: list[ProposedFix] = field(default_factory=list)
    requires_approval: bool = True
    approved: bool = False
    executed: bool = False
    result: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    executed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "action_type": self.action_type.value,
            "description": self.description,
            "target_files": self.target_files,
            "violations": [v.to_dict() for v in self.violations],
            "proposed_fixes": [f.to_dict() for f in self.proposed_fixes],
            "requires_approval": self.requires_approval,
            "approved": self.approved,
            "executed": self.executed,
            "result": self.result,
            "created_at": self.created_at.isoformat(),
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
        }


@dataclass
class AgentSession:
    """A session of the IDE agent."""

    id: UUID = field(default_factory=uuid4)
    organization_id: UUID | None = None
    user_id: UUID | None = None
    repository_id: UUID | None = None

    # Trigger
    trigger_type: AgentTriggerType = AgentTriggerType.MANUAL
    trigger_context: dict[str, Any] = field(default_factory=dict)

    # State
    status: AgentStatus = AgentStatus.IDLE
    current_step: str = ""
    progress: float = 0.0  # 0-100

    # Actions
    actions: list[AgentAction] = field(default_factory=list)
    pending_approval_count: int = 0

    # Results
    violations_found: int = 0
    fixes_applied: int = 0
    issues_created: int = 0
    prs_created: int = 0

    # Metadata
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "repository_id": str(self.repository_id) if self.repository_id else None,
            "trigger_type": self.trigger_type.value,
            "trigger_context": self.trigger_context,
            "status": self.status.value,
            "current_step": self.current_step,
            "progress": self.progress,
            "actions": [a.to_dict() for a in self.actions],
            "pending_approval_count": self.pending_approval_count,
            "violations_found": self.violations_found,
            "fixes_applied": self.fixes_applied,
            "issues_created": self.issues_created,
            "prs_created": self.prs_created,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
        }


@dataclass
class AgentConfig:
    """Configuration for the IDE agent."""

    organization_id: UUID | None = None

    # Trigger settings
    enabled_triggers: list[AgentTriggerType] = field(default_factory=lambda: [
        AgentTriggerType.FILE_SAVE,
        AgentTriggerType.PRE_COMMIT,
        AgentTriggerType.MANUAL,
    ])

    # Auto-fix settings
    auto_fix_enabled: bool = False
    auto_fix_confidence_threshold: float = 0.9  # Only auto-fix high confidence
    auto_fix_max_files: int = 5  # Max files to auto-fix in one session

    # Approval settings
    require_approval_for_refactor: bool = True
    require_approval_for_issues: bool = True
    require_approval_for_prs: bool = True

    # Scope settings
    enabled_regulations: list[str] = field(default_factory=lambda: [
        "GDPR", "CCPA", "HIPAA", "EU AI Act", "SOC2", "PCI-DSS"
    ])
    excluded_paths: list[str] = field(default_factory=lambda: [
        "node_modules/", "vendor/", ".git/", "__pycache__/", "dist/", "build/"
    ])
    included_languages: list[str] = field(default_factory=lambda: [
        "python", "javascript", "typescript", "java", "go", "csharp"
    ])

    # Notification settings
    notify_on_violations: bool = True
    notify_on_auto_fix: bool = True
    notification_channels: list[str] = field(default_factory=lambda: ["ide", "email"])

    def to_dict(self) -> dict[str, Any]:
        return {
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "enabled_triggers": [t.value for t in self.enabled_triggers],
            "auto_fix_enabled": self.auto_fix_enabled,
            "auto_fix_confidence_threshold": self.auto_fix_confidence_threshold,
            "auto_fix_max_files": self.auto_fix_max_files,
            "require_approval_for_refactor": self.require_approval_for_refactor,
            "require_approval_for_issues": self.require_approval_for_issues,
            "require_approval_for_prs": self.require_approval_for_prs,
            "enabled_regulations": self.enabled_regulations,
            "excluded_paths": self.excluded_paths,
            "included_languages": self.included_languages,
            "notify_on_violations": self.notify_on_violations,
            "notify_on_auto_fix": self.notify_on_auto_fix,
            "notification_channels": self.notification_channels,
        }


@dataclass
class RefactorPlan:
    """A plan for refactoring code to be compliant."""

    id: UUID = field(default_factory=uuid4)
    session_id: UUID | None = None

    # Analysis results
    total_violations: int = 0
    fixable_violations: int = 0
    manual_review_required: int = 0

    # Grouped changes
    changes_by_file: dict[str, list[ProposedFix]] = field(default_factory=dict)
    changes_by_regulation: dict[str, list[ProposedFix]] = field(default_factory=dict)

    # Execution plan
    execution_order: list[str] = field(default_factory=list)  # File paths in order
    estimated_impact: str = "low"  # low, medium, high

    # Risks
    breaking_change_risk: bool = False
    test_coverage_gaps: list[str] = field(default_factory=list)

    # Preview
    diff_preview: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "session_id": str(self.session_id) if self.session_id else None,
            "total_violations": self.total_violations,
            "fixable_violations": self.fixable_violations,
            "manual_review_required": self.manual_review_required,
            "changes_by_file": {
                path: [f.to_dict() for f in fixes]
                for path, fixes in self.changes_by_file.items()
            },
            "changes_by_regulation": {
                reg: [f.to_dict() for f in fixes]
                for reg, fixes in self.changes_by_regulation.items()
            },
            "execution_order": self.execution_order,
            "estimated_impact": self.estimated_impact,
            "breaking_change_risk": self.breaking_change_risk,
            "test_coverage_gaps": self.test_coverage_gaps,
            "diff_preview": self.diff_preview,
        }
