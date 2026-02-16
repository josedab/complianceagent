"""Security utilities for authentication and authorization."""

from datetime import UTC, datetime, timedelta

import jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenPayload(BaseModel):
    """JWT token payload."""

    sub: str  # Subject (user_id)
    org_id: str | None = None  # Organization ID for multi-tenancy
    exp: datetime
    iat: datetime
    type: str = "access"  # access or refresh


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(
    subject: str,
    org_id: str | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token."""
    now = datetime.now(UTC)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    payload = TokenPayload(
        sub=subject,
        org_id=org_id,
        exp=expire,
        iat=now,
        type="access",
    )

    return jwt.encode(
        payload.model_dump(),
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def create_refresh_token(
    subject: str,
    org_id: str | None = None,
) -> str:
    """Create a JWT refresh token."""
    now = datetime.now(UTC)
    expire = now + timedelta(days=settings.refresh_token_expire_days)

    payload = TokenPayload(
        sub=subject,
        org_id=org_id,
        exp=expire,
        iat=now,
        type="refresh",
    )

    return jwt.encode(
        payload.model_dump(),
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def decode_token(token: str) -> TokenPayload | None:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        return TokenPayload(**payload)
    except jwt.PyJWTError:
        return None
