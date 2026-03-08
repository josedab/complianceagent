"""User and organization settings endpoints."""

from fastapi import APIRouter, HTTPException, status
from pydantic import EmailStr, Field
from sqlalchemy import select

from app.api.v1.deps import DB, CurrentUser
from app.core.security import get_password_hash, revoke_all_user_tokens, verify_password
from app.models.user import User
from app.schemas.base import BaseSchema, MessageResponse


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


class PasswordChangeRequest(BaseSchema):
    """Change password request."""

    current_password: str = Field(..., min_length=1, max_length=200)
    new_password: str = Field(..., min_length=8, max_length=100)


class NotificationPreferences(BaseSchema):
    """Notification preferences (stored as JSON on user model for now)."""

    email_enabled: bool = True
    email_digest: str = Field("daily", pattern=r"^(realtime|daily|weekly|never)$")
    slack_enabled: bool = False
    slack_webhook_url: str | None = Field(None, max_length=500)
    webhook_enabled: bool = False
    webhook_url: str | None = Field(None, max_length=2048)


# ---------------------------------------------------------------------------
# Profile endpoints
# ---------------------------------------------------------------------------


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(user: CurrentUser) -> dict:
    """Get the current user's profile."""
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "oauth_provider": user.oauth_provider,
    }


@router.patch("/profile", response_model=ProfileResponse)
async def update_profile(body: ProfileUpdateRequest, user: CurrentUser, db: DB) -> dict:
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

    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "oauth_provider": user.oauth_provider,
    }


# ---------------------------------------------------------------------------
# Password change
# ---------------------------------------------------------------------------


@router.post("/password", response_model=MessageResponse)
async def change_password(body: PasswordChangeRequest, user: CurrentUser, db: DB) -> dict:
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

    # Revoke all existing tokens so user must re-authenticate
    revoke_all_user_tokens(str(user.id))

    return {"message": "Password changed successfully", "success": True}


# ---------------------------------------------------------------------------
# Notification preferences
# ---------------------------------------------------------------------------


@router.get("/notifications", response_model=NotificationPreferences)
async def get_notification_preferences(user: CurrentUser, db: DB) -> dict:
    """Get the current user's notification preferences."""
    from app.models.production_features import NotificationPreferenceRecord

    result = await db.execute(
        select(NotificationPreferenceRecord).where(
            NotificationPreferenceRecord.user_id == user.id
        )
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
) -> dict:
    """Update the current user's notification preferences."""
    from app.models.production_features import NotificationPreferenceRecord

    result = await db.execute(
        select(NotificationPreferenceRecord).where(
            NotificationPreferenceRecord.user_id == user.id
        )
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
