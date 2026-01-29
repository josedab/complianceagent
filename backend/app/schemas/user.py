"""User schemas."""

from datetime import datetime

from pydantic import EmailStr, Field

from app.schemas.base import BaseSchema, IDSchema, TimestampSchema


class UserCreate(BaseSchema):
    """Schema for creating a user."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=255)


class UserUpdate(BaseSchema):
    """Schema for updating a user."""

    full_name: str | None = Field(None, min_length=1, max_length=255)
    password: str | None = Field(None, min_length=8, max_length=100)


class UserRead(IDSchema, TimestampSchema):
    """Schema for reading a user."""

    email: str
    full_name: str
    is_active: bool
    is_verified: bool
    last_login_at: datetime | None


class Token(BaseSchema):
    """JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseSchema):
    """JWT token payload."""

    sub: str
    org_id: str | None = None
    exp: datetime
    iat: datetime
    type: str


class LoginRequest(BaseSchema):
    """Login request."""

    email: EmailStr
    password: str
