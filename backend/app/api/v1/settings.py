"""User and organization settings endpoints."""

import asyncio
from typing import Any
from uuid import uuid4

import structlog
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, HTTPException, UploadFile, status
from pydantic import EmailStr, Field
from sqlalchemy import select

from app.api.v1.deps import DB, CurrentUser
from app.core.config import settings
from app.core.security import get_password_hash, revoke_all_user_tokens, verify_password
from app.models.user import User
from app.schemas.base import BaseSchema, MessageResponse


logger = structlog.get_logger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class ProfileUpdateRequest(BaseSchema):
    """Update the current user's profile."""

    full_name: str | None = Field(None, min_length=1, max_length=255)
    email: EmailStr | None = None


class ProfileResponse(BaseSchema):
    """Current user profile."""

    id: str
    email: str
    full_name: str
    is_active: bool
    is_verified: bool
    last_login_at: str | None = None
    oauth_provider: str | None = None
    avatar_url: str | None = None
    mfa_enabled: bool = False


class PasswordChangeRequest(BaseSchema):
    """Change password request."""

    current_password: str = Field(..., min_length=1, max_length=200)
    new_password: str = Field(..., min_length=8, max_length=100)


class NotificationPreferences(BaseSchema):
    """Notification preferences (stored as JSON on user model for now)."""

    email_enabled: bool = True
    email_digest: str = Field(default="daily", pattern=r"^(realtime|daily|weekly|never)$")
    slack_enabled: bool = False
    slack_webhook_url: str | None = Field(default=None, max_length=500)
    webhook_enabled: bool = False
    webhook_url: str | None = Field(default=None, max_length=2048)


# ---------------------------------------------------------------------------
# Avatar storage adapter (mockable)
# ---------------------------------------------------------------------------

_ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png", "image/webp"}
_MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2 MB


class _AvatarStorage:
    """Private S3-compatible avatar storage with signed read URLs."""

    def _configured(self) -> bool:
        return bool(
            settings.avatar_bucket
            and (settings.s3_endpoint_url or settings.environment in ("staging", "production"))
        )

    def _client(self) -> Any:
        import boto3

        return boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url or None,
            aws_access_key_id=settings.s3_access_key or None,
            aws_secret_access_key=settings.s3_secret_key or None,
            region_name=settings.s3_region,
        )

    async def upload(self, user_id: str, data: bytes, content_type: str) -> str:
        if not self._configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Object storage is not configured. Set AVATAR_BUCKET.",
            )

        ext = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}[content_type]
        key = f"avatars/{user_id}/{uuid4().hex}.{ext}"

        try:
            await asyncio.to_thread(
                self._client().put_object,
                Bucket=settings.avatar_bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
                ServerSideEncryption="AES256",
            )
        except (BotoCoreError, ClientError) as exc:
            logger.exception("avatar.upload_failed", user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Avatar upload failed",
            ) from exc

        return f"s3://{settings.avatar_bucket}/{key}"

    async def delete(self, location: str) -> None:
        parsed = self._parse_location(location)
        if not self._configured() or parsed is None:
            return
        bucket, key = parsed
        try:
            await asyncio.to_thread(
                self._client().delete_object,
                Bucket=bucket,
                Key=key,
            )
        except (BotoCoreError, ClientError):
            logger.exception("avatar.delete_failed", bucket=bucket, key=key)

    def public_url(self, location: str | None) -> str | None:
        parsed = self._parse_location(location)
        if parsed is None:
            return location
        bucket, key = parsed
        try:
            return str(
                self._client().generate_presigned_url(
                    "get_object",
                    Params={"Bucket": bucket, "Key": key},
                    ExpiresIn=3600,
                )
            )
        except (BotoCoreError, ClientError):
            logger.exception("avatar.presign_failed", bucket=bucket, key=key)
            return None

    @staticmethod
    def _parse_location(location: str | None) -> tuple[str, str] | None:
        if not location or not location.startswith("s3://"):
            return None
        bucket, separator, key = location[5:].partition("/")
        if not separator or not bucket or not key:
            return None
        return bucket, key


_avatar_storage = _AvatarStorage()


# ---------------------------------------------------------------------------
# Profile endpoints
# ---------------------------------------------------------------------------


def _profile_dict(user: User) -> dict[str, Any]:
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "oauth_provider": user.oauth_provider,
        "avatar_url": _avatar_storage.public_url(user.avatar_url),
        "mfa_enabled": user.mfa_enabled,
    }


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(user: CurrentUser) -> dict[str, Any]:
    """Get the current user's profile."""
    return _profile_dict(user)


@router.patch("/profile", response_model=ProfileResponse)
async def update_profile(body: ProfileUpdateRequest, user: CurrentUser, db: DB) -> dict[str, Any]:
    """Update the current user's profile."""
    if body.email and body.email != user.email:
        existing = await db.execute(select(User).where(User.email == body.email))
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use",
            )
        user.email = body.email

    if body.full_name is not None:
        user.full_name = body.full_name

    await db.flush()
    await db.refresh(user)

    return _profile_dict(user)


# ---------------------------------------------------------------------------
# Avatar upload / delete
# ---------------------------------------------------------------------------


@router.post("/avatar", response_model=ProfileResponse)
async def upload_avatar(file: UploadFile, user: CurrentUser, db: DB) -> dict[str, Any]:
    """Upload a profile avatar image."""
    if file.content_type not in _ALLOWED_AVATAR_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(_ALLOWED_AVATAR_TYPES)}",
        )

    data = await file.read()
    if len(data) > _MAX_AVATAR_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {_MAX_AVATAR_SIZE // (1024 * 1024)}MB",
        )

    # Delete old avatar if any
    if user.avatar_url:
        await _avatar_storage.delete(user.avatar_url)

    url = await _avatar_storage.upload(str(user.id), data, file.content_type)
    user.avatar_url = url
    await db.flush()
    await db.refresh(user)

    return _profile_dict(user)


@router.delete("/avatar", response_model=ProfileResponse)
async def delete_avatar(user: CurrentUser, db: DB) -> dict[str, Any]:
    """Remove the user's avatar."""
    if user.avatar_url:
        await _avatar_storage.delete(user.avatar_url)
        user.avatar_url = None
        await db.flush()
        await db.refresh(user)

    return _profile_dict(user)


# ---------------------------------------------------------------------------
# Password change
# ---------------------------------------------------------------------------


@router.post("/password", response_model=MessageResponse)
async def change_password(body: PasswordChangeRequest, user: CurrentUser, db: DB) -> dict[str, Any]:
    """Change the current user's password and revoke all existing tokens."""
    if not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change password for OAuth users",
        )

    if not verify_password(body.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )

    user.hashed_password = get_password_hash(body.new_password)
    await db.flush()

    revoke_all_user_tokens(str(user.id))

    return {"message": "Password changed successfully", "success": True}


# ---------------------------------------------------------------------------
# Notification preferences
# ---------------------------------------------------------------------------


@router.get("/notifications", response_model=NotificationPreferences)
async def get_notification_preferences(user: CurrentUser, db: DB) -> dict[str, Any]:
    """Get the current user's notification preferences."""
    from app.models.production_features import NotificationPreferenceRecord

    result = await db.execute(
        select(NotificationPreferenceRecord).where(NotificationPreferenceRecord.user_id == user.id)
    )
    record = result.scalar_one_or_none()

    if not record:
        return NotificationPreferences().model_dump()

    return {
        "email_enabled": record.email_enabled,
        "email_digest": record.email_digest,
        "slack_enabled": record.slack_enabled,
        "slack_webhook_url": record.slack_webhook_url,
        "webhook_enabled": record.webhook_enabled,
        "webhook_url": record.webhook_url,
    }


@router.put("/notifications", response_model=NotificationPreferences)
async def update_notification_preferences(
    body: NotificationPreferences, user: CurrentUser, db: DB
) -> dict[str, Any]:
    """Update the current user's notification preferences."""
    from app.models.production_features import NotificationPreferenceRecord

    result = await db.execute(
        select(NotificationPreferenceRecord).where(NotificationPreferenceRecord.user_id == user.id)
    )
    record = result.scalar_one_or_none()

    if record:
        record.email_enabled = body.email_enabled
        record.email_digest = body.email_digest
        record.slack_enabled = body.slack_enabled
        record.slack_webhook_url = body.slack_webhook_url
        record.webhook_enabled = body.webhook_enabled
        record.webhook_url = body.webhook_url
    else:
        record = NotificationPreferenceRecord(
            user_id=user.id,
            email_enabled=body.email_enabled,
            email_digest=body.email_digest,
            slack_enabled=body.slack_enabled,
            slack_webhook_url=body.slack_webhook_url,
            webhook_enabled=body.webhook_enabled,
            webhook_url=body.webhook_url,
        )
        db.add(record)

    await db.flush()
    return body.model_dump()
