"""Data models for Compliance Pattern Marketplace."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


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

    CODE_PATTERN = "code_pattern"  # Regex-based code pattern
    TEMPLATE = "template"  # Code template/snippet
    RULE = "rule"  # Custom compliance rule
    POLICY = "policy"  # Rego/OPA policy
    CHECKLIST = "checklist"  # Compliance checklist
    PLAYBOOK = "playbook"  # Remediation playbook


class LicenseType(str, Enum):
    """License types for patterns."""

    FREE = "free"  # Free for all
    ATTRIBUTION = "attribution"  # Free with attribution required
    COMMERCIAL = "commercial"  # Paid license
    ENTERPRISE = "enterprise"  # Enterprise-only
    CUSTOM = "custom"  # Custom license terms


class PublishStatus(str, Enum):
    """Publication status of a pattern."""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    PUBLISHED = "published"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass
class PatternVersion:
    """A version of a pattern."""

    version: str = "1.0.0"
    changelog: str = ""
    content: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    deprecated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "changelog": self.changelog,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "deprecated": self.deprecated,
        }


@dataclass
class PatternRating:
    """A rating for a pattern."""

    id: UUID = field(default_factory=uuid4)
    pattern_id: UUID | None = None
    user_id: UUID | None = None
    organization_id: UUID | None = None
    rating: int = 5  # 1-5 stars
    review: str = ""
    helpful_votes: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "pattern_id": str(self.pattern_id) if self.pattern_id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "rating": self.rating,
            "review": self.review,
            "helpful_votes": self.helpful_votes,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class CompliancePattern:
    """A compliance pattern in the marketplace."""

    id: UUID = field(default_factory=uuid4)
    slug: str = ""
    name: str = ""
    description: str = ""
    long_description: str = ""

    # Classification
    category: PatternCategory = PatternCategory.OTHER
    pattern_type: PatternType = PatternType.CODE_PATTERN
    regulations: list[str] = field(default_factory=list)  # e.g., ["GDPR", "CCPA"]
    languages: list[str] = field(default_factory=list)  # e.g., ["python", "javascript"]
    tags: list[str] = field(default_factory=list)

    # Content
    content: dict[str, Any] = field(default_factory=dict)
    # For code_pattern: {"pattern": "regex", "message": "...", "severity": "warning"}
    # For template: {"code": "...", "placeholders": [...]}
    # For rule: {"conditions": [...], "actions": [...]}
    # For policy: {"rego": "...", "input_schema": {...}}

    # Versioning
    current_version: str = "1.0.0"
    versions: list[PatternVersion] = field(default_factory=list)

    # Publisher
    publisher_org_id: UUID | None = None
    publisher_name: str = ""
    publisher_verified: bool = False

    # Licensing
    license_type: LicenseType = LicenseType.FREE
    price: float = 0.0  # Price per month or one-time
    price_type: str = "one_time"  # "one_time", "monthly", "per_use"

    # Status
    status: PublishStatus = PublishStatus.DRAFT
    published_at: datetime | None = None
    review_notes: str = ""

    # Metrics
    downloads: int = 0
    active_users: int = 0
    avg_rating: float = 0.0
    rating_count: int = 0
    fork_count: int = 0

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    forked_from: UUID | None = None  # If this is a fork

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "slug": self.slug,
            "name": self.name,
            "description": self.description,
            "long_description": self.long_description,
            "category": self.category.value,
            "pattern_type": self.pattern_type.value,
            "regulations": self.regulations,
            "languages": self.languages,
            "tags": self.tags,
            "content": self.content,
            "current_version": self.current_version,
            "versions": [v.to_dict() for v in self.versions],
            "publisher_org_id": str(self.publisher_org_id) if self.publisher_org_id else None,
            "publisher_name": self.publisher_name,
            "publisher_verified": self.publisher_verified,
            "license_type": self.license_type.value,
            "price": self.price,
            "price_type": self.price_type,
            "status": self.status.value,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "downloads": self.downloads,
            "active_users": self.active_users,
            "avg_rating": self.avg_rating,
            "rating_count": self.rating_count,
            "fork_count": self.fork_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "forked_from": str(self.forked_from) if self.forked_from else None,
        }


@dataclass
class PatternInstallation:
    """Record of a pattern installed by an organization."""

    id: UUID = field(default_factory=uuid4)
    pattern_id: UUID | None = None
    organization_id: UUID | None = None
    installed_version: str = ""
    auto_update: bool = True
    enabled: bool = True
    custom_config: dict[str, Any] = field(default_factory=dict)
    installed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_used_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "pattern_id": str(self.pattern_id) if self.pattern_id else None,
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "installed_version": self.installed_version,
            "auto_update": self.auto_update,
            "enabled": self.enabled,
            "custom_config": self.custom_config,
            "installed_at": self.installed_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
        }


@dataclass
class PublisherProfile:
    """Profile for a pattern publisher."""

    id: UUID = field(default_factory=uuid4)
    organization_id: UUID | None = None
    display_name: str = ""
    description: str = ""
    website: str = ""
    support_email: str = ""
    logo_url: str = ""

    # Verification
    verified: bool = False
    verified_at: datetime | None = None

    # Revenue
    revenue_share_percent: float = 70.0  # Publisher gets 70% by default
    total_earnings: float = 0.0
    pending_payout: float = 0.0
    payout_method: str = ""  # "stripe", "paypal", etc.
    payout_account_id: str = ""

    # Metrics
    total_patterns: int = 0
    total_downloads: int = 0
    avg_rating: float = 0.0
    follower_count: int = 0

    # Status
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "display_name": self.display_name,
            "description": self.description,
            "website": self.website,
            "support_email": self.support_email,
            "logo_url": self.logo_url,
            "verified": self.verified,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "revenue_share_percent": self.revenue_share_percent,
            "total_earnings": self.total_earnings,
            "total_patterns": self.total_patterns,
            "total_downloads": self.total_downloads,
            "avg_rating": self.avg_rating,
            "follower_count": self.follower_count,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class PatternPurchase:
    """Record of a pattern purchase."""

    id: UUID = field(default_factory=uuid4)
    pattern_id: UUID | None = None
    organization_id: UUID | None = None
    user_id: UUID | None = None
    price_paid: float = 0.0
    license_type: LicenseType = LicenseType.COMMERCIAL
    stripe_payment_id: str = ""
    purchased_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None  # For subscriptions
    refunded: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "pattern_id": str(self.pattern_id) if self.pattern_id else None,
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "price_paid": self.price_paid,
            "license_type": self.license_type.value,
            "purchased_at": self.purchased_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "refunded": self.refunded,
        }


@dataclass
class MarketplaceStats:
    """Marketplace statistics."""

    total_patterns: int = 0
    total_publishers: int = 0
    total_downloads: int = 0
    total_revenue: float = 0.0

    # By category
    patterns_by_category: dict[str, int] = field(default_factory=dict)
    downloads_by_category: dict[str, int] = field(default_factory=dict)

    # By regulation
    patterns_by_regulation: dict[str, int] = field(default_factory=dict)

    # Top items
    top_patterns: list[dict[str, Any]] = field(default_factory=list)
    top_publishers: list[dict[str, Any]] = field(default_factory=list)
    trending_patterns: list[dict[str, Any]] = field(default_factory=list)

    # Time-based
    new_patterns_this_month: int = 0
    downloads_this_month: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_patterns": self.total_patterns,
            "total_publishers": self.total_publishers,
            "total_downloads": self.total_downloads,
            "total_revenue": self.total_revenue,
            "patterns_by_category": self.patterns_by_category,
            "downloads_by_category": self.downloads_by_category,
            "patterns_by_regulation": self.patterns_by_regulation,
            "top_patterns": self.top_patterns,
            "top_publishers": self.top_publishers,
            "trending_patterns": self.trending_patterns,
            "new_patterns_this_month": self.new_patterns_this_month,
            "downloads_this_month": self.downloads_this_month,
        }
