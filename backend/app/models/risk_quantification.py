"""Risk Quantification database models."""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import ArrayType, Base, JSONBType, UUIDType
from app.models.base import TimestampMixin, UUIDMixin


class RiskSeverity(str, Enum):
    """Risk severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NEGLIGIBLE = "negligible"


class RiskCategory(str, Enum):
    """Categories of compliance risk."""

    REGULATORY_FINE = "regulatory_fine"
    DATA_BREACH = "data_breach"
    LITIGATION = "litigation"
    REPUTATION = "reputation"
    OPERATIONAL = "operational"
    THIRD_PARTY = "third_party"


class RiskTrend(str, Enum):
    """Risk trend direction."""

    INCREASING = "increasing"
    STABLE = "stable"
    DECREASING = "decreasing"


class ViolationRisk(Base, UUIDMixin, TimestampMixin):
    """Risk assessment for a compliance violation."""

    __tablename__ = "violation_risks"

    # Organization scope
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Violation reference
    violation_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True, index=True)
    rule_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    regulation: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Risk assessment
    severity: Mapped[RiskSeverity] = mapped_column(
        String(50), default=RiskSeverity.MEDIUM, index=True
    )
    category: Mapped[RiskCategory] = mapped_column(
        String(50), default=RiskCategory.REGULATORY_FINE
    )

    # Financial estimates
    min_exposure: Mapped[float] = mapped_column(Float, default=0.0)
    max_exposure: Mapped[float] = mapped_column(Float, default=0.0)
    expected_exposure: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)

    # Factors
    likelihood: Mapped[float] = mapped_column(Float, default=0.5)
    impact_multiplier: Mapped[float] = mapped_column(Float, default=1.0)
    aggravating_factors: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)
    mitigating_factors: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)

    # Location context
    repository_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType,
        ForeignKey("repositories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    code_location: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    remediated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<ViolationRisk {self.rule_id} - ${self.expected_exposure:,.0f}>"


class RepositoryRiskProfile(Base, UUIDMixin, TimestampMixin):
    """Risk profile for a repository."""

    __tablename__ = "repository_risk_profiles"

    # Organization scope
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Repository reference
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    repository_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Violation counts
    total_violations: Mapped[int] = mapped_column(Integer, default=0)
    critical_violations: Mapped[int] = mapped_column(Integer, default=0)
    high_violations: Mapped[int] = mapped_column(Integer, default=0)
    medium_violations: Mapped[int] = mapped_column(Integer, default=0)
    low_violations: Mapped[int] = mapped_column(Integer, default=0)

    # Financial exposure
    total_min_exposure: Mapped[float] = mapped_column(Float, default=0.0)
    total_max_exposure: Mapped[float] = mapped_column(Float, default=0.0)
    total_expected_exposure: Mapped[float] = mapped_column(Float, default=0.0, index=True)

    # Breakdown
    exposure_by_regulation: Mapped[dict] = mapped_column(JSONBType, default=dict)
    exposure_by_category: Mapped[dict] = mapped_column(JSONBType, default=dict)

    # Risk scores (0-100)
    overall_risk_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    data_privacy_score: Mapped[float] = mapped_column(Float, default=100.0)
    security_score: Mapped[float] = mapped_column(Float, default=100.0)
    compliance_score: Mapped[float] = mapped_column(Float, default=100.0)

    # Assessment metadata
    assessment_version: Mapped[str] = mapped_column(String(50), default="1.0")
    last_full_scan_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<RepositoryRiskProfile {self.repository_name} - Score: {self.overall_risk_score:.1f}>"


class OrganizationRiskSnapshot(Base, UUIDMixin, TimestampMixin):
    """Historical snapshot of organization risk."""

    __tablename__ = "organization_risk_snapshots"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Context at time of snapshot
    annual_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    employee_count: Mapped[int] = mapped_column(Integer, default=0)
    data_subject_count: Mapped[int] = mapped_column(Integer, default=0)
    jurisdictions: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)

    # Aggregate exposure
    total_min_exposure: Mapped[float] = mapped_column(Float, default=0.0)
    total_max_exposure: Mapped[float] = mapped_column(Float, default=0.0)
    total_expected_exposure: Mapped[float] = mapped_column(Float, default=0.0)

    # Breakdown
    exposure_by_regulation: Mapped[dict] = mapped_column(JSONBType, default=dict)
    exposure_by_repository: Mapped[dict] = mapped_column(JSONBType, default=dict)
    exposure_by_severity: Mapped[dict] = mapped_column(JSONBType, default=dict)

    # Scores
    overall_risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_grade: Mapped[str] = mapped_column(String(2), default="C")
    risk_trend: Mapped[RiskTrend] = mapped_column(String(50), default=RiskTrend.STABLE)

    # Snapshot date
    snapshot_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"<OrganizationRiskSnapshot {self.snapshot_date} - Grade: {self.risk_grade}>"


class RiskReport(Base, UUIDMixin, TimestampMixin):
    """Executive risk report."""

    __tablename__ = "risk_reports"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Report type and period
    report_type: Mapped[str] = mapped_column(String(50), default="monthly")  # monthly, quarterly, annual
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Executive summary
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_findings: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)
    key_recommendations: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)

    # Risk overview
    total_exposure: Mapped[float] = mapped_column(Float, default=0.0)
    exposure_change: Mapped[float] = mapped_column(Float, default=0.0)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_grade: Mapped[str] = mapped_column(String(2), default="C")

    # Full report data
    report_data: Mapped[dict] = mapped_column(JSONBType, default=dict)

    # Generation metadata
    generated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<RiskReport {self.title} - {self.risk_grade}>"


class WhatIfScenario(Base, UUIDMixin, TimestampMixin):
    """What-if scenario analysis."""

    __tablename__ = "what_if_scenarios"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Scenario info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    scenario_type: Mapped[str] = mapped_column(String(50), nullable=False)
    parameters: Mapped[dict] = mapped_column(JSONBType, default=dict)

    # Results
    baseline_exposure: Mapped[float] = mapped_column(Float, default=0.0)
    scenario_exposure: Mapped[float] = mapped_column(Float, default=0.0)
    exposure_delta: Mapped[float] = mapped_column(Float, default=0.0)
    exposure_delta_percent: Mapped[float] = mapped_column(Float, default=0.0)

    # Details
    affected_violations: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)
    affected_regulations: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)

    # Recommendation
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(50), default="medium")

    # Created by
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<WhatIfScenario {self.name} - Delta: ${self.exposure_delta:,.0f}>"
