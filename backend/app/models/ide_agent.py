"""IDE Agent database models."""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import ArrayType, Base, JSONBType, UUIDType
from app.models.base import TimestampMixin, UUIDMixin


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

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IDEAgentSession(Base, UUIDMixin, TimestampMixin):
    """A session of the IDE agent."""

    __tablename__ = "ide_agent_sessions"

    # Organization scope
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    repository_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType,
        ForeignKey("repositories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Trigger
    trigger_type: Mapped[AgentTriggerType] = mapped_column(
        String(50), default=AgentTriggerType.MANUAL, index=True
    )
    trigger_context: Mapped[dict] = mapped_column(JSONBType, default=dict)

    # State
    status: Mapped[AgentStatus] = mapped_column(
        String(50), default=AgentStatus.IDLE, index=True
    )
    current_step: Mapped[str] = mapped_column(String(255), default="")
    progress: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100

    # Pending approvals
    pending_approval_count: Mapped[int] = mapped_column(Integer, default=0)

    # Results
    violations_found: Mapped[int] = mapped_column(Integer, default=0)
    fixes_applied: Mapped[int] = mapped_column(Integer, default=0)
    issues_created: Mapped[int] = mapped_column(Integer, default=0)
    prs_created: Mapped[int] = mapped_column(Integer, default=0)

    # Timing
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Errors
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_details: Mapped[dict | None] = mapped_column(JSONBType, nullable=True)

    # Relationships
    actions: Mapped[list["IDEAgentAction"]] = relationship(
        "IDEAgentAction", back_populates="session", cascade="all, delete-orphan"
    )
    violations: Mapped[list["IDEAgentViolation"]] = relationship(
        "IDEAgentViolation", back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<IDEAgentSession {self.id} - {self.status}>"


class IDEAgentAction(Base, UUIDMixin, TimestampMixin):
    """An action performed or proposed by the agent."""

    __tablename__ = "ide_agent_actions"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("ide_agent_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Action details
    action_type: Mapped[AgentActionType] = mapped_column(
        String(50), default=AgentActionType.ANALYZE
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    target_files: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)

    # Approval workflow
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=True)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Execution
    executed: Mapped[bool] = mapped_column(Boolean, default=False)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    result: Mapped[dict] = mapped_column(JSONBType, default=dict)

    # Relationship
    session: Mapped["IDEAgentSession"] = relationship(
        "IDEAgentSession", back_populates="actions"
    )
    fixes: Mapped[list["IDEAgentFix"]] = relationship(
        "IDEAgentFix", back_populates="action", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<IDEAgentAction {self.action_type} - {self.executed}>"


class IDEAgentViolation(Base, UUIDMixin, TimestampMixin):
    """A detected compliance violation."""

    __tablename__ = "ide_agent_violations"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("ide_agent_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Violation details
    rule_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    rule_name: Mapped[str] = mapped_column(String(255), nullable=False)
    regulation: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    article_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    severity: Mapped[str] = mapped_column(String(50), default="warning")
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Location
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    start_column: Mapped[int] = mapped_column(Integer, default=0)
    end_column: Mapped[int] = mapped_column(Integer, default=0)

    # Code context
    original_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)

    # Relationship
    session: Mapped["IDEAgentSession"] = relationship(
        "IDEAgentSession", back_populates="violations"
    )
    fix: Mapped["IDEAgentFix | None"] = relationship(
        "IDEAgentFix", back_populates="violation", uselist=False
    )

    def __repr__(self) -> str:
        return f"<IDEAgentViolation {self.rule_id} at {self.file_path}:{self.start_line}>"


class IDEAgentFix(Base, UUIDMixin, TimestampMixin):
    """A proposed fix for a violation."""

    __tablename__ = "ide_agent_fixes"

    action_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("ide_agent_actions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    violation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType,
        ForeignKey("ide_agent_violations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Fix details
    fixed_code: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Confidence
    confidence: Mapped[FixConfidence] = mapped_column(
        String(50), default=FixConfidence.MEDIUM
    )
    confidence_score: Mapped[float] = mapped_column(Float, default=0.5)

    # Metadata
    imports_to_add: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)
    files_affected: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)
    breaking_changes: Mapped[bool] = mapped_column(Boolean, default=False)
    test_suggestions: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)

    # Application status
    applied: Mapped[bool] = mapped_column(Boolean, default=False)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rollback_available: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    action: Mapped["IDEAgentAction"] = relationship(
        "IDEAgentAction", back_populates="fixes"
    )
    violation: Mapped["IDEAgentViolation | None"] = relationship(
        "IDEAgentViolation", back_populates="fix"
    )

    def __repr__(self) -> str:
        return f"<IDEAgentFix {self.confidence} - applied: {self.applied}>"


class IDEAgentConfig(Base, UUIDMixin, TimestampMixin):
    """Configuration for the IDE agent per organization."""

    __tablename__ = "ide_agent_configs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Trigger settings
    enabled_triggers: Mapped[list[str]] = mapped_column(
        ArrayType(String),
        default=list,
    )

    # Auto-fix settings
    auto_fix_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_fix_confidence_threshold: Mapped[float] = mapped_column(Float, default=0.9)
    auto_fix_max_files: Mapped[int] = mapped_column(Integer, default=5)

    # Approval settings
    require_approval_for_refactor: Mapped[bool] = mapped_column(Boolean, default=True)
    require_approval_for_issues: Mapped[bool] = mapped_column(Boolean, default=True)
    require_approval_for_prs: Mapped[bool] = mapped_column(Boolean, default=True)

    # Scope settings
    enabled_regulations: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)
    excluded_paths: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)
    included_languages: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)

    # Notification settings
    notify_on_violations: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_on_auto_fix: Mapped[bool] = mapped_column(Boolean, default=True)
    notification_channels: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)

    def __repr__(self) -> str:
        return f"<IDEAgentConfig org={self.organization_id}>"
