"""Pattern Marketplace database models."""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import ArrayType, Base, JSONBType, UUIDType
from app.models.base import TimestampMixin, UUIDMixin


class PatternCategory(str, Enum):
    """Categories of compliance patterns."""

    DATA_PRIVACY = "data_privacy"
    AUTHENTICATION = "authentication"
    ENCRYPTION = "encryption"
    LOGGING = "logging"
    ACCESS_CONTROL = "access_control"
    DATA_RETENTION = "data_retention"
    CONSENT_MANAGEMENT = "consent_management"
    INCIDENT_RESPONSE = "incident_response"
    AUDIT_TRAIL = "audit_trail"
    AI_SAFETY = "ai_safety"
    FINANCIAL = "financial"
    HEALTHCARE = "healthcare"
    OTHER = "other"


class PatternType(str, Enum):
    """Types of compliance patterns."""

    CODE_PATTERN = "code_pattern"
    TEMPLATE = "template"
    RULE = "rule"
    POLICY = "policy"
    CHECKLIST = "checklist"
    PLAYBOOK = "playbook"


class LicenseType(str, Enum):
    """License types for patterns."""

    FREE = "free"
    ATTRIBUTION = "attribution"
    COMMERCIAL = "commercial"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class PublishStatus(str, Enum):
    """Publication status of a pattern."""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    PUBLISHED = "published"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class CompliancePattern(Base, UUIDMixin, TimestampMixin):
    """A compliance pattern in the marketplace."""

    __tablename__ = "compliance_patterns"

    # Basic info
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    long_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Classification
    category: Mapped[PatternCategory] = mapped_column(
        String(50), default=PatternCategory.OTHER, index=True
    )
    pattern_type: Mapped[PatternType] = mapped_column(
        String(50), default=PatternType.CODE_PATTERN, index=True
    )
    regulations: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)
    languages: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)
    tags: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)

    # Content
    content: Mapped[dict] = mapped_column(JSONBType, default=dict)
    current_version: Mapped[str] = mapped_column(String(50), default="1.0.0")

    # Publisher
    publisher_org_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType,
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    publisher_name: Mapped[str] = mapped_column(String(200), default="")
    publisher_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Licensing
    license_type: Mapped[LicenseType] = mapped_column(String(50), default=LicenseType.FREE)
    price: Mapped[float] = mapped_column(Float, default=0.0)
    price_type: Mapped[str] = mapped_column(String(50), default="one_time")

    # Status
    status: Mapped[PublishStatus] = mapped_column(
        String(50), default=PublishStatus.DRAFT, index=True
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metrics
    downloads: Mapped[int] = mapped_column(Integer, default=0)
    active_users: Mapped[int] = mapped_column(Integer, default=0)
    avg_rating: Mapped[float] = mapped_column(Float, default=0.0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    fork_count: Mapped[int] = mapped_column(Integer, default=0)

    # Forking
    forked_from_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType,
        ForeignKey("compliance_patterns.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    versions: Mapped[list["PatternVersion"]] = relationship(
        "PatternVersion", back_populates="pattern", cascade="all, delete-orphan"
    )
    installations: Mapped[list["PatternInstallation"]] = relationship(
        "PatternInstallation", back_populates="pattern", cascade="all, delete-orphan"
    )
    ratings: Mapped[list["PatternRating"]] = relationship(
        "PatternRating", back_populates="pattern", cascade="all, delete-orphan"
    )
    purchases: Mapped[list["PatternPurchase"]] = relationship(
        "PatternPurchase", back_populates="pattern", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<CompliancePattern {self.name} ({self.status})>"


class PatternVersion(Base, UUIDMixin, TimestampMixin):
    """A version of a pattern."""

    __tablename__ = "pattern_versions"

    pattern_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("compliance_patterns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    changelog: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[dict] = mapped_column(JSONBType, default=dict)
    deprecated: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationship
    pattern: Mapped["CompliancePattern"] = relationship(
        "CompliancePattern", back_populates="versions"
    )

    def __repr__(self) -> str:
        return f"<PatternVersion {self.version}>"


class PatternInstallation(Base, UUIDMixin, TimestampMixin):
    """Record of a pattern installed by an organization."""

    __tablename__ = "pattern_installations"

    pattern_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("compliance_patterns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    installed_version: Mapped[str] = mapped_column(String(50), nullable=False)
    auto_update: Mapped[bool] = mapped_column(Boolean, default=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    custom_config: Mapped[dict] = mapped_column(JSONBType, default=dict)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationship
    pattern: Mapped["CompliancePattern"] = relationship(
        "CompliancePattern", back_populates="installations"
    )

    def __repr__(self) -> str:
        return f"<PatternInstallation {self.pattern_id} -> {self.organization_id}>"


class PatternRating(Base, UUIDMixin, TimestampMixin):
    """A rating for a pattern."""

    __tablename__ = "pattern_ratings"

    pattern_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("compliance_patterns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType,
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    review: Mapped[str | None] = mapped_column(Text, nullable=True)
    helpful_votes: Mapped[int] = mapped_column(Integer, default=0)

    # Relationship
    pattern: Mapped["CompliancePattern"] = relationship(
        "CompliancePattern", back_populates="ratings"
    )

    def __repr__(self) -> str:
        return f"<PatternRating {self.rating}/5 for {self.pattern_id}>"


class PatternPurchase(Base, UUIDMixin, TimestampMixin):
    """Record of a pattern purchase."""

    __tablename__ = "pattern_purchases"

    pattern_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("compliance_patterns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
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
    )
    price_paid: Mapped[float] = mapped_column(Float, nullable=False)
    license_type: Mapped[LicenseType] = mapped_column(String(50), nullable=False)
    stripe_payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_checkout_session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refunded: Mapped[bool] = mapped_column(Boolean, default=False)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationship
    pattern: Mapped["CompliancePattern"] = relationship(
        "CompliancePattern", back_populates="purchases"
    )

    def __repr__(self) -> str:
        return f"<PatternPurchase ${self.price_paid} for {self.pattern_id}>"


class PublisherProfile(Base, UUIDMixin, TimestampMixin):
    """Profile for a pattern publisher."""

    __tablename__ = "publisher_profiles"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    support_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Verification
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Revenue
    revenue_share_percent: Mapped[float] = mapped_column(Float, default=70.0)
    total_earnings: Mapped[float] = mapped_column(Float, default=0.0)
    pending_payout: Mapped[float] = mapped_column(Float, default=0.0)
    payout_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    stripe_connect_account_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<PublisherProfile {self.display_name}>"
