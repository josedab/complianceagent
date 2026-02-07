"""SaaS Tenant database models."""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, JSONBType, UUIDType
from app.models.base import TimestampMixin, UUIDMixin


class TenantStatus(str, Enum):
    """Tenant lifecycle status."""

    TRIAL = "trial"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class TenantPlan(str, Enum):
    """Tenant subscription plan."""

    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class SaasTenant(Base, UUIDMixin, TimestampMixin):
    """SaaS tenant for multi-tenant platform."""

    __tablename__ = "saas_tenants"

    # Tenant identity
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)

    # Plan and status
    plan: Mapped[TenantPlan] = mapped_column(
        String(50), default=TenantPlan.FREE, index=True
    )
    status: Mapped[TenantStatus] = mapped_column(
        String(50), default=TenantStatus.TRIAL, index=True
    )

    # Owner
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Optional domain
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)

    # Configuration
    settings: Mapped[dict] = mapped_column(JSONBType, default=dict)
    resource_limits: Mapped[dict] = mapped_column(JSONBType, default=dict)

    # Trial and onboarding
    trial_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    onboarding_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # GitHub integration
    github_installation_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<SaasTenant {self.slug} - {self.plan.value}/{self.status.value}>"


class TenantUsageRecord(Base, UUIDMixin, TimestampMixin):
    """Usage record for a tenant."""

    __tablename__ = "tenant_usage_records"

    # Tenant reference
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("saas_tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Usage data
    metric: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, default=0.0)

    # Period
    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Extra metadata
    record_metadata: Mapped[dict] = mapped_column(JSONBType, default=dict)

    def __repr__(self) -> str:
        return f"<TenantUsageRecord {self.metric}={self.value}>"
