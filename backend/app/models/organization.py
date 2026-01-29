"""Organization model for multi-tenant support."""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, JSONBType, UUIDType
from app.models.base import TimestampMixin, UUIDMixin


if TYPE_CHECKING:
    from app.models.customer_profile import CustomerProfile
    from app.models.user import User


class PlanType(str, Enum):
    """Organization plan types."""

    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    TRIAL = "trial"


class MemberRole(str, Enum):
    """Organization member roles."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class Organization(Base, UUIDMixin, TimestampMixin):
    """Organization model - top level tenant."""

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan: Mapped[PlanType] = mapped_column(String(50), default=PlanType.TRIAL)
    settings: Mapped[dict] = mapped_column(JSONBType, default=dict)

    # Billing
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Limits based on plan
    max_repositories: Mapped[int] = mapped_column(default=1)
    max_frameworks: Mapped[int] = mapped_column(default=3)
    max_users: Mapped[int] = mapped_column(default=5)

    # Trial
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    members: Mapped[list["OrganizationMember"]] = relationship(
        "OrganizationMember", back_populates="organization", cascade="all, delete-orphan"
    )
    customer_profiles: Mapped[list["CustomerProfile"]] = relationship(
        "CustomerProfile", back_populates="organization", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Organization {self.name}>"


class OrganizationMember(Base, UUIDMixin, TimestampMixin):
    """Organization membership linking users to organizations."""

    __tablename__ = "organization_members"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[MemberRole] = mapped_column(String(50), default=MemberRole.MEMBER)
    invited_by: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="members"
    )
    user: Mapped["User"] = relationship("User", back_populates="memberships")

    def __repr__(self) -> str:
        return f"<OrganizationMember org={self.organization_id} user={self.user_id}>"
