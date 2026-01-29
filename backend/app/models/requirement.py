"""Requirement model - extracted obligations from regulations."""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import ArrayType, Base, JSONBType, UUIDType
from app.models.base import TimestampMixin, UUIDMixin


if TYPE_CHECKING:
    from app.models.codebase import CodebaseMapping
    from app.models.regulation import Regulation


class ObligationType(str, Enum):
    """Type of obligation."""

    MUST = "must"  # Mandatory requirement
    MUST_NOT = "must_not"  # Prohibition
    SHOULD = "should"  # Recommended
    SHOULD_NOT = "should_not"  # Not recommended
    MAY = "may"  # Optional/permitted


class RequirementCategory(str, Enum):
    """Category of requirement."""

    DATA_COLLECTION = "data_collection"
    DATA_STORAGE = "data_storage"
    DATA_PROCESSING = "data_processing"
    DATA_TRANSFER = "data_transfer"
    DATA_DELETION = "data_deletion"
    DATA_ACCESS = "data_access"
    CONSENT = "consent"
    NOTIFICATION = "notification"
    BREACH_NOTIFICATION = "breach_notification"
    DOCUMENTATION = "documentation"
    SECURITY = "security"
    AUDIT = "audit"
    BREACH_RESPONSE = "breach_response"
    RISK_ASSESSMENT = "risk_assessment"
    VENDOR_MANAGEMENT = "vendor_management"
    AI_TRANSPARENCY = "ai_transparency"
    AI_TESTING = "ai_testing"
    AI_DOCUMENTATION = "ai_documentation"
    AI_RISK_CLASSIFICATION = "ai_risk_classification"
    HUMAN_OVERSIGHT = "human_oversight"
    # ESG/Sustainability categories
    SUSTAINABILITY_REPORTING = "sustainability_reporting"
    GHG_EMISSIONS = "ghg_emissions"
    CLIMATE_RISK = "climate_risk"
    ENVIRONMENTAL_IMPACT = "environmental_impact"
    SOCIAL_IMPACT = "social_impact"
    GOVERNANCE_DISCLOSURE = "governance_disclosure"
    # Accessibility categories
    ACCESSIBILITY = "accessibility"
    OTHER = "other"


class Requirement(Base, UUIDMixin, TimestampMixin):
    """An extracted requirement from a regulation."""

    __tablename__ = "requirements"

    regulation_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("regulations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Requirement identification
    reference_id: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Obligation details
    obligation_type: Mapped[ObligationType] = mapped_column(String(20), nullable=False)
    category: Mapped[RequirementCategory] = mapped_column(String(50), nullable=False)

    # Subject and scope
    subject: Mapped[str] = mapped_column(Text, nullable=False)  # Who must comply
    action: Mapped[str] = mapped_column(Text, nullable=False)  # What they must do
    object: Mapped[str | None] = mapped_column(Text, nullable=True)  # What it applies to

    # Scope definition
    data_types: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)
    processes: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)
    systems: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)
    roles: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)

    # Timing
    timeframe: Mapped[str | None] = mapped_column(String(255), nullable=True)
    deadline_days: Mapped[int | None] = mapped_column(nullable=True)

    # Source text and citations
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list[dict]] = mapped_column(JSONBType, default=list)

    # Penalties
    penalty_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    max_penalty_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    penalty_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)

    # AI extraction metadata
    extraction_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    extracted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    human_reviewed: Mapped[bool] = mapped_column(default=False)
    reviewed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Related requirements (stored as JSON array of UUID strings for cross-DB compatibility)
    related_requirement_ids: Mapped[list[str]] = mapped_column(
        JSONBType, default=list
    )

    # Metadata
    tags: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)
    extra_metadata: Mapped[dict] = mapped_column(JSONBType, default=dict)

    # Relationships
    regulation: Mapped["Regulation"] = relationship("Regulation", back_populates="requirements")
    codebase_mappings: Mapped[list["CodebaseMapping"]] = relationship(
        "CodebaseMapping", back_populates="requirement", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Requirement {self.reference_id}: {self.title[:50]}>"
