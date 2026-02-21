"""Database models for Round 3 strategic features.

Provides persistent storage for:
- Regulatory horizon scanner (pending legislation, impact predictions)
- Continuous control testing (test definitions, results, evidence)
- Multi-entity rollup (entity nodes, policy inheritance)
- Board reports (generated reports, executive summaries)
- Audit workspace (workspaces, gap analyses, phase tracking)
- Dependency scanner (scan results, risk records)
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import ArrayType, Base, JSONBType, UUIDType
from app.models.base import TimestampMixin, UUIDMixin


# ─── Horizon Scanner ──────────────────────────────────────────────────────


class PendingLegislationRecord(Base, UUIDMixin, TimestampMixin):
    """Tracked pending legislation and regulatory changes."""

    __tablename__ = "pending_legislation"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(50), default="custom")
    source_url: Mapped[str] = mapped_column(String(1000), default="")
    jurisdiction: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    confidence: Mapped[str] = mapped_column(String(20), default="medium")
    expected_effective_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    discovered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    frameworks_affected: Mapped[list] = mapped_column(ArrayType(), default=list)
    tags: Mapped[list] = mapped_column(ArrayType(), default=list)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("organizations.id")
    )


class ImpactPredictionRecord(Base, UUIDMixin, TimestampMixin):
    """Codebase impact predictions for pending legislation."""

    __tablename__ = "impact_predictions"

    legislation_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("pending_legislation.id")
    )
    affected_files: Mapped[int] = mapped_column(Integer, default=0)
    affected_modules: Mapped[list] = mapped_column(ArrayType(), default=list)
    estimated_effort_days: Mapped[float] = mapped_column(Float, default=0.0)
    impact_severity: Mapped[str] = mapped_column(String(20), default="medium")
    recommendations: Mapped[dict] = mapped_column(JSONBType, default=list)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("organizations.id")
    )


# ─── Control Testing ──────────────────────────────────────────────────────


class ControlTestRecord(Base, UUIDMixin, TimestampMixin):
    """Persistent control test definition."""

    __tablename__ = "control_tests"

    control_id: Mapped[str] = mapped_column(String(50), nullable=False)
    framework: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    test_type: Mapped[str] = mapped_column(String(50), default="api_check")
    frequency: Mapped[str] = mapped_column(String(20), default="daily")
    enabled: Mapped[bool] = mapped_column(default=True)
    last_status: Mapped[str] = mapped_column(String(20), default="pending")
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    last_run: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("organizations.id")
    )


class ControlTestResultRecord(Base, UUIDMixin, TimestampMixin):
    """Persistent control test execution result with evidence."""

    __tablename__ = "control_test_results"

    test_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("control_tests.id"))
    control_id: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(Text, default="")
    evidence_data: Mapped[dict] = mapped_column(JSONBType, default=dict)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("organizations.id")
    )


# ─── Entity Rollup ────────────────────────────────────────────────────────


class EntityNodeRecord(Base, UUIDMixin, TimestampMixin):
    """Organizational entity in the compliance hierarchy."""

    __tablename__ = "entity_nodes"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("entity_nodes.id"))
    level: Mapped[int] = mapped_column(Integer, default=0)
    policy_mode: Mapped[str] = mapped_column(String(20), default="inherit")
    compliance_score: Mapped[float] = mapped_column(Float, default=0.0)
    frameworks: Mapped[list] = mapped_column(ArrayType(), default=list)
    member_count: Mapped[int] = mapped_column(Integer, default=0)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("organizations.id")
    )

    children = relationship("EntityNodeRecord", backref="parent", remote_side="EntityNodeRecord.id")


# ─── Board Reports ────────────────────────────────────────────────────────


class BoardReportRecord(Base, UUIDMixin, TimestampMixin):
    """Generated board compliance report."""

    __tablename__ = "board_reports"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    period: Mapped[str] = mapped_column(String(50), default="")
    overall_score: Mapped[float] = mapped_column(Float, default=0.0)
    overall_status: Mapped[str] = mapped_column(String(20), default="yellow")
    narrative: Mapped[str] = mapped_column(Text, default="")
    framework_scores: Mapped[dict] = mapped_column(JSONBType, default=dict)
    highlights: Mapped[dict] = mapped_column(JSONBType, default=list)
    top_risks: Mapped[dict] = mapped_column(JSONBType, default=list)
    action_items: Mapped[dict] = mapped_column(JSONBType, default=list)
    report_format: Mapped[str] = mapped_column(String(20), default="html")
    content: Mapped[str] = mapped_column(Text, default="")
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("organizations.id")
    )


# ─── Audit Workspace ─────────────────────────────────────────────────────


class AuditWorkspaceRecord(Base, UUIDMixin, TimestampMixin):
    """Self-service audit preparation workspace."""

    __tablename__ = "audit_workspaces"

    org_id: Mapped[str] = mapped_column(String(100), nullable=False)
    framework: Mapped[str] = mapped_column(String(50), nullable=False)
    phase: Mapped[str] = mapped_column(String(30), default="gap_analysis")
    evidence_coverage_pct: Mapped[float] = mapped_column(Float, default=0.0)
    remediation_progress_pct: Mapped[float] = mapped_column(Float, default=0.0)
    target_audit_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("organizations.id")
    )


class GapAnalysisRecord(Base, UUIDMixin, TimestampMixin):
    """Gap analysis result for an audit workspace."""

    __tablename__ = "gap_analyses"

    workspace_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("audit_workspaces.id"))
    framework: Mapped[str] = mapped_column(String(50), nullable=False)
    total_controls: Mapped[int] = mapped_column(Integer, default=0)
    fully_met: Mapped[int] = mapped_column(Integer, default=0)
    partially_met: Mapped[int] = mapped_column(Integer, default=0)
    not_met: Mapped[int] = mapped_column(Integer, default=0)
    readiness_pct: Mapped[float] = mapped_column(Float, default=0.0)
    estimated_remediation_days: Mapped[float] = mapped_column(Float, default=0.0)
    gaps: Mapped[dict] = mapped_column(JSONBType, default=list)


# ─── Dependency Scanner ───────────────────────────────────────────────────


class DependencyScanRecord(Base, UUIDMixin, TimestampMixin):
    """Dependency compliance scan result."""

    __tablename__ = "dependency_scans"

    ecosystem: Mapped[str] = mapped_column(String(20), nullable=False)
    total_dependencies: Mapped[int] = mapped_column(Integer, default=0)
    critical_risks: Mapped[int] = mapped_column(Integer, default=0)
    high_risks: Mapped[int] = mapped_column(Integer, default=0)
    license_violations: Mapped[int] = mapped_column(Integer, default=0)
    deprecated_crypto_count: Mapped[int] = mapped_column(Integer, default=0)
    data_sharing_count: Mapped[int] = mapped_column(Integer, default=0)
    risks: Mapped[dict] = mapped_column(JSONBType, default=list)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("organizations.id")
    )
