"""White Label Platform models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class PartnerTier(str, Enum):
    """Partner tier levels."""

    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class InstanceStatus(str, Enum):
    """Status of a white-label instance."""

    PROVISIONING = "provisioning"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DECOMMISSIONED = "decommissioned"


class BrandingElement(str, Enum):
    """Branding elements that can be customised."""

    LOGO = "logo"
    COLOR_PRIMARY = "color_primary"
    COLOR_SECONDARY = "color_secondary"
    FAVICON = "favicon"
    COMPANY_NAME = "company_name"
    DOMAIN = "domain"


@dataclass
class PartnerConfig:
    """Configuration for a white-label partner."""

    id: UUID = field(default_factory=uuid4)
    partner_name: str = ""
    tier: PartnerTier = PartnerTier.SILVER
    domain: str = ""
    branding: dict[str, str] = field(default_factory=dict)
    features_enabled: list[str] = field(default_factory=list)
    max_tenants: int = 10
    status: InstanceStatus = InstanceStatus.PROVISIONING
    onboarded_at: datetime | None = None


@dataclass
class WhiteLabelInstance:
    """A white-label tenant instance."""

    id: UUID = field(default_factory=uuid4)
    partner_id: UUID = field(default_factory=uuid4)
    tenant_name: str = ""
    tenant_slug: str = ""
    status: InstanceStatus = InstanceStatus.PROVISIONING
    users: int = 0
    repos: int = 0
    created_at: datetime | None = None


@dataclass
class PartnerAnalytics:
    """Analytics for a specific partner."""

    partner_id: UUID = field(default_factory=uuid4)
    total_tenants: int = 0
    total_users: int = 0
    total_repos: int = 0
    mrr: float = 0.0
    usage_hours: float = 0.0


@dataclass
class WhiteLabelStats:
    """Overall white-label platform statistics."""

    total_partners: int = 0
    total_instances: int = 0
    by_tier: dict = field(default_factory=dict)
    total_mrr: float = 0.0
    by_status: dict = field(default_factory=dict)
