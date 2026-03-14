"""Secondary persistence models for drift detection, posture scoring, evidence vault, and MCP."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import ArrayType, Base, JSONBType, UUIDType
from app.models.base import TimestampMixin, UUIDMixin


class DriftBaselineRecord(Base, UUIDMixin, TimestampMixin):
    """Baseline snapshot for drift detection comparison."""

    __tablename__ = "drift_baseline_records"

    organization_id: Mapped[UUIDType] = mapped_column(
        UUIDType, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    regulation: Mapped[str] = mapped_column(String(100), nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSONBType, default=dict, server_default="{}")
    hash_value: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")


class DriftEventRecord(Base, UUIDMixin, TimestampMixin):
    """A detected drift event from the baseline."""

    __tablename__ = "drift_event_records"

    organization_id: Mapped[UUIDType] = mapped_column(
        UUIDType, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    baseline_id: Mapped[UUIDType] = mapped_column(
        UUIDType,
        ForeignKey("drift_baseline_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    drift_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    affected_controls: Mapped[list] = mapped_column(ArrayType(), default=list, server_default="[]")
    drift_metadata: Mapped[dict] = mapped_column(JSONBType, default=dict, server_default="{}")
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DriftAlertRecord(Base, UUIDMixin, TimestampMixin):
    """Alert raised for a significant drift event."""

    __tablename__ = "drift_alert_records"

    organization_id: Mapped[UUIDType] = mapped_column(
        UUIDType, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    drift_event_id: Mapped[UUIDType] = mapped_column(
        UUIDType,
        ForeignKey("drift_event_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(50), default="open", server_default="open")
    notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    alert_metadata: Mapped[dict] = mapped_column(JSONBType, default=dict, server_default="{}")


class PostureScoreRecord(Base, UUIDMixin, TimestampMixin):
    """Point-in-time compliance posture score snapshot."""

    __tablename__ = "posture_score_records"

    organization_id: Mapped[UUIDType] = mapped_column(
        UUIDType, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    regulation: Mapped[str] = mapped_column(String(100), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    grade: Mapped[str] = mapped_column(String(10), nullable=False)
    controls_passing: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    controls_total: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    score_breakdown: Mapped[dict] = mapped_column(JSONBType, default=dict, server_default="{}")


class EvidenceVaultRecord(Base, UUIDMixin, TimestampMixin):
    """Immutable evidence artifact stored in the compliance vault."""

    __tablename__ = "evidence_vault_records"

    organization_id: Mapped[UUIDType] = mapped_column(
        UUIDType, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    control_id: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    regulation: Mapped[str] = mapped_column(String(100), nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(100), nullable=False)
    artifact_url: Mapped[str] = mapped_column(String(2000), nullable=False)
    hash_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    collected_by: Mapped[str] = mapped_column(String(200), nullable=False)
    vault_metadata: Mapped[dict] = mapped_column(JSONBType, default=dict, server_default="{}")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SelfHealingEventRecord(Base, UUIDMixin, TimestampMixin):
    """Self-healing action taken to automatically remediate a drift or violation."""

    __tablename__ = "self_healing_event_records"

    organization_id: Mapped[UUIDType] = mapped_column(
        UUIDType, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    trigger_type: Mapped[str] = mapped_column(String(100), nullable=False)
    action_taken: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    healing_metadata: Mapped[dict] = mapped_column(JSONBType, default=dict, server_default="{}")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MCPExecutionRecord(Base, UUIDMixin, TimestampMixin):
    """Model Context Protocol tool execution record."""

    __tablename__ = "mcp_execution_records"

    organization_id: Mapped[UUIDType] = mapped_column(
        UUIDType, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tool_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    input_params: Mapped[dict] = mapped_column(JSONBType, default=dict, server_default="{}")
    output_result: Mapped[dict] = mapped_column(JSONBType, default=dict, server_default="{}")
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


__all__ = [
    "DriftAlertRecord",
    "DriftBaselineRecord",
    "DriftEventRecord",
    "EvidenceVaultRecord",
    "MCPExecutionRecord",
    "PostureScoreRecord",
    "SelfHealingEventRecord",
]
