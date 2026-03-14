"""User state and session models for copilot, marketplace, gamification, and workflows."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import ArrayType, Base, JSONBType, UUIDType
from app.models.base import TimestampMixin, UUIDMixin


class CopilotSessionRecord(Base, UUIDMixin, TimestampMixin):
    """Tracks an individual copilot interaction session."""

    __tablename__ = "copilot_session_records"

    organization_id: Mapped[UUIDType] = mapped_column(
        UUIDType, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUIDType] = mapped_column(
        UUIDType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", server_default="active")
    message_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    session_metadata: Mapped[dict] = mapped_column(JSONBType, default=dict, server_default="{}")
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AgentMarketplaceRecord(Base, UUIDMixin, TimestampMixin):
    """Agent listing in the marketplace."""

    __tablename__ = "agent_marketplace_records"

    organization_id: Mapped[UUIDType] = mapped_column(
        UUIDType, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    agent_type: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="published", server_default="published")
    capabilities: Mapped[list] = mapped_column(ArrayType(), default=list, server_default="[]")
    agent_metadata: Mapped[dict] = mapped_column(JSONBType, default=dict, server_default="{}")
    rating: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0")
    install_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class TrustAttestationRecord(Base, UUIDMixin, TimestampMixin):
    """Attestation record for trust and compliance verification."""

    __tablename__ = "trust_attestation_records"

    organization_id: Mapped[UUIDType] = mapped_column(
        UUIDType, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attested_by: Mapped[UUIDType] = mapped_column(
        UUIDType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    attestation_type: Mapped[str] = mapped_column(String(100), nullable=False)
    regulation: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    evidence_references: Mapped[list] = mapped_column(ArrayType(), default=list, server_default="[]")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class GamificationProfileRecord(Base, UUIDMixin, TimestampMixin):
    """Gamification profile for a user in an organization."""

    __tablename__ = "gamification_profile_records"

    organization_id: Mapped[UUIDType] = mapped_column(
        UUIDType, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUIDType] = mapped_column(
        UUIDType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    level: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    xp_total: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    badges: Mapped[list] = mapped_column(ArrayType(), default=list, server_default="[]")
    streak_days: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    profile_metadata: Mapped[dict] = mapped_column(JSONBType, default=dict, server_default="{}")


class GamificationEventRecord(Base, UUIDMixin, TimestampMixin):
    """Individual gamification event (XP award, badge earned, etc.)."""

    __tablename__ = "gamification_event_records"

    organization_id: Mapped[UUIDType] = mapped_column(
        UUIDType, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUIDType] = mapped_column(
        UUIDType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    xp_awarded: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    badge_awarded: Mapped[str | None] = mapped_column(String(100), nullable=True)
    event_metadata: Mapped[dict] = mapped_column(JSONBType, default=dict, server_default="{}")


class WorkflowDefinitionRecord(Base, UUIDMixin, TimestampMixin):
    """Reusable compliance workflow definition."""

    __tablename__ = "workflow_definition_records"

    organization_id: Mapped[UUIDType] = mapped_column(
        UUIDType, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(100), nullable=False)
    steps: Mapped[list] = mapped_column(ArrayType(), default=list, server_default="[]")
    workflow_metadata: Mapped[dict] = mapped_column(JSONBType, default=dict, server_default="{}")
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )


class WorkflowExecutionRecord(Base, UUIDMixin, TimestampMixin):
    """Execution record for a workflow run."""

    __tablename__ = "workflow_execution_records"

    organization_id: Mapped[UUIDType] = mapped_column(
        UUIDType, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    definition_id: Mapped[UUIDType] = mapped_column(
        UUIDType,
        ForeignKey("workflow_definition_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(50), default="running", server_default="running")
    triggered_by: Mapped[str] = mapped_column(String(200), nullable=False)
    execution_log: Mapped[dict] = mapped_column(JSONBType, default=dict, server_default="{}")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


__all__ = [
    "AgentMarketplaceRecord",
    "CopilotSessionRecord",
    "GamificationEventRecord",
    "GamificationProfileRecord",
    "TrustAttestationRecord",
    "WorkflowDefinitionRecord",
    "WorkflowExecutionRecord",
]
