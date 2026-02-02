"""Audit trail and compliance action models."""

import hashlib
import json
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import ArrayType, Base, JSONBType, UUIDType
from app.models.base import TimestampMixin, UUIDMixin


class AuditEventType(str, Enum):
    """Types of audit events."""

    # Detection
    REGULATION_DETECTED = "regulation_detected"
    CHANGE_DETECTED = "change_detected"

    # Analysis
    REQUIREMENTS_EXTRACTED = "requirements_extracted"
    RELEVANCE_ASSESSED = "relevance_assessed"
    CODEBASE_MAPPED = "codebase_mapped"
    IMPACT_ASSESSED = "impact_assessed"

    # Implementation
    CODE_GENERATED = "code_generated"
    PR_CREATED = "pr_created"
    PR_UPDATED = "pr_updated"
    PR_MERGED = "pr_merged"
    PR_CLOSED = "pr_closed"
    PR_ANALYZED = "pr_analyzed"

    # Review
    HUMAN_REVIEW_REQUESTED = "human_review_requested"
    HUMAN_REVIEW_COMPLETED = "human_review_completed"
    REQUIREMENT_APPROVED = "requirement_approved"
    REQUIREMENT_REJECTED = "requirement_rejected"

    # Compliance
    COMPLIANCE_VERIFIED = "compliance_verified"
    COMPLIANCE_FAILED = "compliance_failed"
    COMPLIANCE_STATUS_CHANGED = "compliance_status_changed"

    # System
    SYSTEM_ERROR = "system_error"
    MANUAL_OVERRIDE = "manual_override"


class ComplianceActionStatus(str, Enum):
    """Status of compliance action."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"
    VERIFIED = "verified"
    CLOSED = "closed"


class AuditTrail(Base, UUIDMixin, TimestampMixin):
    """Immutable audit trail entry."""

    __tablename__ = "audit_trails"

    # Organization scope
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Related entities
    regulation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType,
        ForeignKey("regulations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    requirement_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType,
        ForeignKey("requirements.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    repository_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType,
        ForeignKey("repositories.id", ondelete="SET NULL"),
        nullable=True,
    )
    mapping_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType,
        ForeignKey("codebase_mappings.id", ondelete="SET NULL"),
        nullable=True,
    )
    compliance_action_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType,
        ForeignKey("compliance_actions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Event details
    event_type: Mapped[AuditEventType] = mapped_column(String(100), nullable=False, index=True)
    event_description: Mapped[str] = mapped_column(Text, nullable=False)
    event_data: Mapped[dict] = mapped_column(JSONBType, default=dict)

    # Actor
    actor_type: Mapped[str] = mapped_column(String(50), nullable=False)  # user, system, ai
    actor_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    actor_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # AI metadata (if applicable)
    ai_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Tamper-proof hash
    previous_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entry_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Metadata
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<AuditTrail {self.event_type} at {self.created_at}>"

    def compute_hash(self) -> str:
        """Compute hash for tamper detection."""
        data = {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "event_type": self.event_type,
            "event_data": self.event_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "previous_hash": self.previous_hash,
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


class ComplianceAction(Base, UUIDMixin, TimestampMixin):
    """A compliance action tracking requirement implementation."""

    __tablename__ = "compliance_actions"

    # Organization scope
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Related entities
    regulation_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("regulations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requirement_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("requirements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
    )
    mapping_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType,
        ForeignKey("codebase_mappings.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Action details
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ComplianceActionStatus] = mapped_column(
        String(50), default=ComplianceActionStatus.PENDING, index=True
    )
    priority: Mapped[str] = mapped_column(String(50), default="medium")

    # Timeline
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Assignment
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Impact assessment
    impact_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    affected_files_count: Mapped[int] = mapped_column(Integer, default=0)
    estimated_effort_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Code generation
    generated_code: Mapped[dict | None] = mapped_column(JSONBType, nullable=True)
    generated_tests: Mapped[dict | None] = mapped_column(JSONBType, nullable=True)

    # PR tracking
    pr_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    pr_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pr_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    pr_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pr_merged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Verification
    verification_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    verification_results: Mapped[dict | None] = mapped_column(JSONBType, nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True)

    # Metadata
    tags: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)
    extra_metadata: Mapped[dict] = mapped_column(JSONBType, default=dict)

    def __repr__(self) -> str:
        return f"<ComplianceAction {self.title[:50]} ({self.status})>"
