"""Critical persistence models for evidence generation, certification, and remediation."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, JSONBType, UUIDType
from app.models.base import TimestampMixin, UUIDMixin


class EvidenceGenerationRecord(Base, UUIDMixin, TimestampMixin):
    """Tracks AI-generated compliance evidence artifacts."""

    __tablename__ = "evidence_generation_records"

    organization_id: Mapped[UUIDType] = mapped_column(
        UUIDType, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    control_id: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    regulation: Mapped[str] = mapped_column(String(100), nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", server_default="pending")
    artifact_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    generation_metadata: Mapped[dict] = mapped_column(JSONBType, default=dict, server_default="{}")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CertificationRunRecord(Base, UUIDMixin, TimestampMixin):
    """Tracks full certification audit runs."""

    __tablename__ = "certification_run_records"

    organization_id: Mapped[UUIDType] = mapped_column(
        UUIDType, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    regulation: Mapped[str] = mapped_column(String(100), nullable=False)
    run_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="running", server_default="running")
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    controls_total: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    controls_passed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    controls_failed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    run_metadata: Mapped[dict] = mapped_column(JSONBType, default=dict, server_default="{}")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CertControlGapRecord(Base, UUIDMixin, TimestampMixin):
    """Identifies control gaps discovered during a certification run."""

    __tablename__ = "cert_control_gap_records"

    organization_id: Mapped[UUIDType] = mapped_column(
        UUIDType, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    run_id: Mapped[UUIDType] = mapped_column(
        UUIDType,
        ForeignKey("certification_run_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    control_id: Mapped[str] = mapped_column(String(200), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    remediation_hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    gap_metadata: Mapped[dict] = mapped_column(JSONBType, default=dict, server_default="{}")


class RemediationPipelineRecord(Base, UUIDMixin, TimestampMixin):
    """Tracks a complete AI-driven remediation pipeline run."""

    __tablename__ = "remediation_pipeline_records"

    organization_id: Mapped[UUIDType] = mapped_column(
        UUIDType, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    trigger_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", server_default="pending")
    fixes_total: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    fixes_applied: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    fixes_failed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    pipeline_metadata: Mapped[dict] = mapped_column(JSONBType, default=dict, server_default="{}")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RemediationFixRecord(Base, UUIDMixin, TimestampMixin):
    """A single fix attempt within a remediation pipeline."""

    __tablename__ = "remediation_fix_records"

    organization_id: Mapped[UUIDType] = mapped_column(
        UUIDType, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    pipeline_id: Mapped[UUIDType] = mapped_column(
        UUIDType,
        ForeignKey("remediation_pipeline_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    control_id: Mapped[str] = mapped_column(String(200), nullable=False)
    fix_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", server_default="pending")
    diff_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    fix_metadata: Mapped[dict] = mapped_column(JSONBType, default=dict, server_default="{}")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class RemediationApprovalRecord(Base, UUIDMixin, TimestampMixin):
    """Approval record for a remediation fix requiring human review."""

    __tablename__ = "remediation_approval_records"

    organization_id: Mapped[UUIDType] = mapped_column(
        UUIDType, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fix_id: Mapped[UUIDType] = mapped_column(
        UUIDType,
        ForeignKey("remediation_fix_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reviewer_id: Mapped[UUIDType | None] = mapped_column(UUIDType, nullable=True)
    decision: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


__all__ = [
    "CertControlGapRecord",
    "CertificationRunRecord",
    "EvidenceGenerationRecord",
    "RemediationApprovalRecord",
    "RemediationFixRecord",
    "RemediationPipelineRecord",
]
