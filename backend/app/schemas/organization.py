"""Organization schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.models.organization import MemberRole, PlanType
from app.schemas.base import BaseSchema, IDSchema, TimestampSchema


class OrganizationCreate(BaseSchema):
    """Schema for creating an organization."""

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: str | None = None


class OrganizationUpdate(BaseSchema):
    """Schema for updating an organization."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    settings: dict | None = None


class OrganizationRead(IDSchema, TimestampSchema):
    """Schema for reading an organization."""

    name: str
    slug: str
    description: str | None
    plan: PlanType
    settings: dict
    max_repositories: int
    max_frameworks: int
    max_users: int
    trial_ends_at: datetime | None


class OrganizationMemberCreate(BaseSchema):
    """Schema for adding organization member."""

    email: EmailStr
    role: MemberRole = MemberRole.MEMBER


class OrganizationMemberRead(IDSchema, TimestampSchema):
    """Schema for reading organization member."""

    organization_id: UUID
    user_id: UUID
    role: MemberRole
    accepted_at: datetime | None

    # Included user info
    user_email: str | None = None
    user_name: str | None = None
