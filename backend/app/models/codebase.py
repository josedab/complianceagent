"""Codebase mapping models."""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import ArrayType, Base, JSONBType, UUIDType
from app.models.base import TimestampMixin, UUIDMixin


if TYPE_CHECKING:
    from app.models.customer_profile import CustomerProfile
    from app.models.requirement import Requirement


class RepositoryProvider(str, Enum):
    """Git provider."""

    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    AZURE_DEVOPS = "azure_devops"


class ComplianceStatus(str, Enum):
    """Compliance status for a mapping."""

    COMPLIANT = "compliant"
    PARTIAL = "partial"
    NON_COMPLIANT = "non_compliant"
    NOT_APPLICABLE = "not_applicable"
    PENDING_REVIEW = "pending_review"
    IN_PROGRESS = "in_progress"


class GapSeverity(str, Enum):
    """Severity of compliance gap."""

    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    INFO = "info"


class Repository(Base, UUIDMixin, TimestampMixin):
    """A code repository being monitored."""

    __tablename__ = "repositories"

    customer_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("customer_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Repository identification
    provider: Mapped[RepositoryProvider] = mapped_column(String(50), nullable=False)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    default_branch: Mapped[str] = mapped_column(String(255), default="main")
    clone_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Access configuration
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    access_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    installation_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Analysis state
    last_analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_analyzed_commit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    analysis_status: Mapped[str] = mapped_column(String(50), default="pending")

    # Repository metadata
    primary_language: Mapped[str | None] = mapped_column(String(50), nullable=True)
    languages: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)
    file_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    line_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Structure cache
    structure_cache: Mapped[dict] = mapped_column(JSONBType, default=dict)
    structure_cached_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Compliance summary
    compliance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_requirements: Mapped[int] = mapped_column(Integer, default=0)
    compliant_requirements: Mapped[int] = mapped_column(Integer, default=0)
    gaps_critical: Mapped[int] = mapped_column(Integer, default=0)
    gaps_major: Mapped[int] = mapped_column(Integer, default=0)
    gaps_minor: Mapped[int] = mapped_column(Integer, default=0)

    # Settings
    settings: Mapped[dict] = mapped_column(JSONBType, default=dict)

    # Relationships
    customer_profile: Mapped["CustomerProfile"] = relationship(
        "CustomerProfile", back_populates="repositories"
    )
    mappings: Mapped[list["CodebaseMapping"]] = relationship(
        "CodebaseMapping", back_populates="repository", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Repository {self.full_name}>"


class CodebaseMapping(Base, UUIDMixin, TimestampMixin):
    """Mapping between a requirement and code locations."""

    __tablename__ = "codebase_mappings"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requirement_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("requirements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Compliance status
    compliance_status: Mapped[ComplianceStatus] = mapped_column(
        String(50), default=ComplianceStatus.PENDING_REVIEW
    )
    compliance_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Affected code
    affected_files: Mapped[list[dict]] = mapped_column(JSONBType, default=list)
    affected_functions: Mapped[list[dict]] = mapped_column(JSONBType, default=list)
    affected_classes: Mapped[list[dict]] = mapped_column(JSONBType, default=list)

    # Data flow analysis
    data_flows: Mapped[list[dict]] = mapped_column(JSONBType, default=list)

    # Existing compliance implementations
    existing_implementations: Mapped[list[dict]] = mapped_column(JSONBType, default=list)

    # Gaps identified
    gaps: Mapped[list[dict]] = mapped_column(JSONBType, default=list)
    gap_count: Mapped[int] = mapped_column(Integer, default=0)
    critical_gaps: Mapped[int] = mapped_column(Integer, default=0)
    major_gaps: Mapped[int] = mapped_column(Integer, default=0)
    minor_gaps: Mapped[int] = mapped_column(Integer, default=0)

    # Effort estimation
    estimated_effort_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_effort_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # AI analysis metadata
    mapping_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    analyzed_commit: Mapped[str | None] = mapped_column(String(40), nullable=True)

    # Human review
    human_reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
    reviewed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Implementation tracking
    implementation_pr_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    implementation_pr_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    implemented_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Metadata
    extra_metadata: Mapped[dict] = mapped_column(JSONBType, default=dict)

    # Relationships
    repository: Mapped["Repository"] = relationship("Repository", back_populates="mappings")
    requirement: Mapped["Requirement"] = relationship(
        "Requirement", back_populates="codebase_mappings"
    )

    def __repr__(self) -> str:
        return f"<CodebaseMapping repo={self.repository_id} req={self.requirement_id}>"
