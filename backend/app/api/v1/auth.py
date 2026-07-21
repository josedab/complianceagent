"""Authentication endpoints.

Includes registration with email verification, login with optional
TOTP 2FA challenge, password reset, and account deactivation/deletion.
"""

import base64
import hashlib
import hmac as _hmac
import secrets
import struct
import threading
import time
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import UUID

import structlog
from fastapi import APIRouter, Cookie, HTTPException, Request, Response, status
from pydantic import Field
from sqlalchemy import select

from app.api.v1.deps import DB, CurrentUser
from app.core.config import settings
from app.core.security import (
    SyncRedisClient,
    create_access_token,
    create_mfa_challenge_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    revoke_all_user_tokens,
    revoke_token,
    verify_password,
)
from app.models.organization import OrganizationMember
from app.models.user import User
from app.schemas.base import BaseSchema, MessageResponse
from app.schemas.user import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserRead,
)


logger = structlog.get_logger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Account lockout tracking (Redis-backed with in-memory fallback)
# ---------------------------------------------------------------------------
_MAX_FAILED_ATTEMPTS = 5
_LOCKOUT_SECONDS = 900  # 15 minutes
_REDIS_PREFIX = "login_lockout:"


class _LoginLockout:
    """Distributed login lockout with Redis and in-memory fallback."""

    def __init__(self) -> None:
        self._memory_attempts: dict[str, list[float]] = {}
        self._memory_locked: dict[str, float] = {}
        self._lock = threading.Lock()
        self._redis: SyncRedisClient | None = None
        self._redis_checked = False

    def _get_redis(self) -> SyncRedisClient | None:
        if self._redis_checked:
            return self._redis
        self._redis_checked = True
        try:
            import redis as redis_lib

            client = redis_lib.Redis.from_url(
                settings.redis_url, decode_responses=True, socket_connect_timeout=2
            )
            client.ping()
            self._redis = client
        except Exception:
            self._redis = None
        return self._redis

    def is_locked_out(self, email: str) -> bool:
        r = self._get_redis()
        if r is not None:
            try:
                return bool(cast("int", r.exists(f"{_REDIS_PREFIX}locked:{email}")) > 0)
            except Exception:
                pass
        with self._lock:
            until = self._memory_locked.get(email)
            if until and datetime.now(UTC).timestamp() < until:
                return True
            if until:
                del self._memory_locked[email]
                self._memory_attempts.pop(email, None)
            return False

    def record_failed(self, email: str) -> None:
        now = datetime.now(UTC).timestamp()
        r = self._get_redis()
        if r is not None:
            try:
                key = f"{_REDIS_PREFIX}attempts:{email}"
                r.zadd(key, {str(now): now})
                r.zremrangebyscore(key, 0, now - _LOCKOUT_SECONDS)
                r.expire(key, _LOCKOUT_SECONDS)
                count = cast("int", r.zcard(key))
                if count >= _MAX_FAILED_ATTEMPTS:
                    r.setex(f"{_REDIS_PREFIX}locked:{email}", _LOCKOUT_SECONDS, "1")
                    logger.warning("auth.account_locked", email=email, backend="redis")
                return
            except Exception:
                pass
        with self._lock:
            attempts = self._memory_attempts.setdefault(email, [])
            attempts.append(now)
            cutoff = now - _LOCKOUT_SECONDS
            self._memory_attempts[email] = [a for a in attempts if a > cutoff]
            if len(self._memory_attempts[email]) >= _MAX_FAILED_ATTEMPTS:
                self._memory_locked[email] = now + _LOCKOUT_SECONDS
                logger.warning("auth.account_locked", email=email, backend="memory")

    def clear(self, email: str) -> None:
        r = self._get_redis()
        if r is not None:
            try:
                r.delete(f"{_REDIS_PREFIX}attempts:{email}", f"{_REDIS_PREFIX}locked:{email}")
                return
            except Exception:
                pass
        with self._lock:
            self._memory_attempts.pop(email, None)
            self._memory_locked.pop(email, None)


_lockout = _LoginLockout()


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Set HttpOnly cookies for authentication tokens."""
    is_production = settings.environment == "production"
    cookie_domain = settings.auth_cookie_domain or None
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
        domain=cookie_domain,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/",
        domain=cookie_domain,
    )


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _is_expired(value: datetime | None) -> bool:
    if value is None:
        return True
    normalized = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    return normalized < datetime.now(UTC)


_VERIFICATION_EXPIRY_HOURS = 24


async def _send_verification_email(email: str, token: str) -> None:
    """Deliver a verification email without logging the bearer token."""
    verify_url = f"{settings.next_public_app_url.rstrip('/')}/verify-email#token={token}"
    if settings.environment in ("development", "test") and not (
        settings.smtp_host or settings.email_api_endpoint
    ):
        logger.info("auth.verification_email_sink", email=email)
        return
    if not settings.smtp_host and not settings.email_api_endpoint:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Transactional email is not configured",
        )

    from app.services.notification import (
        Notification,
        NotificationType,
        create_notification_service,
    )

    service = create_notification_service(
        smtp_host=settings.smtp_host or None,
        smtp_port=settings.smtp_port,
        smtp_username=settings.smtp_user or None,
        smtp_password=settings.smtp_password or None,
        smtp_from_email=settings.smtp_from_email,
        email_api_endpoint=settings.email_api_endpoint or None,
        email_api_key=settings.email_api_key or None,
    )
    notification = Notification(
        type=NotificationType.ACTION_REQUIRED,
        title="Verify your email",
        message="Use the secure verification link to activate your account.",
        action_url=verify_url,
    )
    results = await service.send_notification(
        notification,
        channels=["email"],
        channel_configs={"email": {"email": email}},
    )
    if not results.get("email"):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Verification email delivery failed",
        )
    logger.info("auth.verification_email_sent", email=email)


async def _send_password_reset_email(email: str, token: str) -> None:
    """Deliver a reset link without logging or storing the raw token."""
    reset_url = f"{settings.next_public_app_url.rstrip('/')}/reset-password#token={token}"
    if settings.environment in ("development", "test") and not (
        settings.smtp_host or settings.email_api_endpoint
    ):
        logger.info("auth.password_reset_email_sink", email=email)
        return
    if not settings.smtp_host and not settings.email_api_endpoint:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Transactional email is not configured",
        )

    from app.services.notification import (
        Notification,
        NotificationType,
        create_notification_service,
    )

    service = create_notification_service(
        smtp_host=settings.smtp_host or None,
        smtp_port=settings.smtp_port,
        smtp_username=settings.smtp_user or None,
        smtp_password=settings.smtp_password or None,
        smtp_from_email=settings.smtp_from_email,
        email_api_endpoint=settings.email_api_endpoint or None,
        email_api_key=settings.email_api_key or None,
    )
    results = await service.send_notification(
        Notification(
            type=NotificationType.ACTION_REQUIRED,
            title="Reset your password",
            message="Use the secure reset link to choose a new password.",
            action_url=reset_url,
        ),
        channels=["email"],
        channel_configs={"email": {"email": email}},
    )
    if not results.get("email"):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Password reset email delivery failed",
        )
    logger.info("auth.password_reset_email_sent", email=email)


# ---------------------------------------------------------------------------
# TOTP helpers (RFC 6238 with HMAC-SHA1, 6-digit, 30-second step)
# ---------------------------------------------------------------------------


def _encrypt_secret(secret: bytes) -> str:
    """Encrypt TOTP secret at rest using Fernet (derived from settings.secret_key)."""
    from cryptography.fernet import Fernet

    key = base64.urlsafe_b64encode(hashlib.sha256(settings.secret_key.encode()).digest())
    return Fernet(key).encrypt(secret).decode()


def _decrypt_secret(encrypted: str) -> bytes:
    from cryptography.fernet import Fernet

    key = base64.urlsafe_b64encode(hashlib.sha256(settings.secret_key.encode()).digest())
    return Fernet(key).decrypt(encrypted.encode())


def _generate_totp_secret() -> bytes:
    return secrets.token_bytes(20)


def _totp_code(secret: bytes, time_step: int | None = None) -> str:
    if time_step is None:
        time_step = int(time.time()) // 30
    msg = struct.pack(">Q", time_step)
    h = _hmac.new(secret, msg, hashlib.sha1).digest()
    offset = h[-1] & 0x0F
    code = struct.unpack(">I", h[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(code % 1_000_000).zfill(6)


def _verify_totp(secret: bytes, code: str, window: int = 1) -> bool:
    """Verify TOTP code within ±window steps."""
    now_step = int(time.time()) // 30
    for offset in range(-window, window + 1):
        if _hmac.compare_digest(_totp_code(secret, now_step + offset), code):
            return True
    return False


def _generate_recovery_codes(count: int = 8) -> tuple[list[str], list[str]]:
    """Return (raw_codes, hashed_codes)."""
    raw = [secrets.token_hex(4).upper() for _ in range(count)]
    hashed = [_hash_token(c) for c in raw]
    return raw, hashed


async def _resolve_single_org_id(db: DB, user_id: UUID) -> str | None:
    result = await db.execute(
        select(OrganizationMember.organization_id).where(OrganizationMember.user_id == user_id)
    )
    organization_ids = [row[0] for row in result.all()]
    return str(organization_ids[0]) if len(organization_ids) == 1 else None


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class MFAChallengeRequest(BaseSchema):
    """Complete a 2FA challenge after login."""

    mfa_token: str = Field(..., min_length=1, max_length=512)
    totp_code: str = Field(..., min_length=6, max_length=32)


class MFASetupResponse(BaseSchema):
    secret: str
    otpauth_uri: str
    recovery_codes: list[str]


class MFAConfirmRequest(BaseSchema):
    totp_code: str = Field(..., min_length=6, max_length=6)


class AccountDeactivateRequest(BaseSchema):
    password: str = Field(..., min_length=1)
    confirm: bool = True


class SwitchOrganizationRequest(BaseSchema):
    """Select the organization embedded in newly issued tokens."""

    organization_id: str = Field(..., min_length=36, max_length=36)


class VerifyEmailRequest(BaseSchema):
    """Verify an email using a token supplied in the request body."""

    token: str = Field(..., min_length=1, max_length=255)


# ---------------------------------------------------------------------------
# Registration with email verification
# ---------------------------------------------------------------------------


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: DB) -> User:
    """Register a new user and send a verification email."""
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    raw_token = secrets.token_urlsafe(32)
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        verification_token=_hash_token(raw_token),
        verification_token_expires=datetime.now(UTC) + timedelta(hours=_VERIFICATION_EXPIRY_HOURS),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    await _send_verification_email(user.email, raw_token)

    return user


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(body: VerifyEmailRequest, db: DB) -> dict[str, Any]:
    """Verify a user's email address using the emailed token."""
    token_hash = _hash_token(body.token)
    result = await db.execute(select(User).where(User.verification_token == token_hash))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token",
        )

    if _is_expired(user.verification_token_expires):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired",
        )

    user.is_verified = True
    user.verified_at = datetime.now(UTC)
    user.verification_token = None
    user.verification_token_expires = None
    await db.flush()

    return {"message": "Email verified successfully", "success": True}


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(email: str, db: DB) -> dict[str, Any]:
    """Resend the verification email (always returns success to prevent enumeration)."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user and not user.is_verified and user.is_active:
        raw_token = secrets.token_urlsafe(32)
        user.verification_token = _hash_token(raw_token)
        user.verification_token_expires = datetime.now(UTC) + timedelta(
            hours=_VERIFICATION_EXPIRY_HOURS
        )
        await db.flush()
        await _send_verification_email(user.email, raw_token)

    return {
        "message": "If that email exists and is unverified, a new link has been sent.",
        "success": True,
    }


# ---------------------------------------------------------------------------
# Login (with 2FA challenge when MFA is enabled)
# ---------------------------------------------------------------------------


@router.post("/login", response_model=Token)
async def login(login_request: LoginRequest, db: DB, response: Response) -> dict[str, Any]:
    """Login and get access token.

    When MFA is enabled the response contains a short-lived ``mfa_token``
    instead of the real access/refresh tokens. The client must call
    ``/auth/mfa/challenge`` with the TOTP code to receive full tokens.
    """
    if _lockout.is_locked_out(login_request.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again later.",
        )

    result = await db.execute(select(User).where(User.email == login_request.email))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password:
        _lockout.record_failed(login_request.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(login_request.password, user.hashed_password):
        _lockout.record_failed(login_request.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    _lockout.clear(login_request.email)
    user.last_login_at = datetime.now(UTC)
    await db.flush()

    # If MFA is enabled, return a challenge token instead of full tokens
    if user.mfa_enabled:
        mfa_token = create_mfa_challenge_token(subject=str(user.id))
        return {
            "access_token": "",
            "refresh_token": "",
            "token_type": "mfa_required",
            "expires_in": 300,
            "mfa_token": mfa_token,
        }

    org_id = await _resolve_single_org_id(db, user.id)
    access_token = create_access_token(subject=str(user.id), org_id=org_id)
    refresh_token = create_refresh_token(subject=str(user.id), org_id=org_id)
    _set_auth_cookies(response, access_token, refresh_token)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


@router.post("/mfa/challenge", response_model=Token)
async def mfa_challenge(body: MFAChallengeRequest, db: DB, response: Response) -> dict[str, Any]:
    """Complete the MFA challenge with a TOTP code to receive full tokens."""
    payload = decode_token(body.mfa_token)
    if not payload or payload.type != "mfa_challenge":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired MFA token",
        )

    result = await db.execute(select(User).where(User.id == UUID(payload.sub)))
    user = result.scalar_one_or_none()
    if not user or not user.mfa_enabled or not user.mfa_secret_encrypted:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="MFA not configured")

    secret = _decrypt_secret(user.mfa_secret_encrypted)

    # Check TOTP code
    if _verify_totp(secret, body.totp_code):
        pass  # Valid TOTP
    elif user.mfa_recovery_codes:
        # Try recovery codes
        code_hash = _hash_token(body.totp_code)
        if code_hash in user.mfa_recovery_codes:
            codes = list(user.mfa_recovery_codes)
            codes.remove(code_hash)
            user.mfa_recovery_codes = codes
        else:
            _lockout.record_failed(user.email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid TOTP code",
            )
    else:
        _lockout.record_failed(user.email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid TOTP code")

    revoke_token(body.mfa_token)

    org_id = await _resolve_single_org_id(db, user.id)
    access_token = create_access_token(subject=str(user.id), org_id=org_id)
    refresh_token = create_refresh_token(subject=str(user.id), org_id=org_id)
    _set_auth_cookies(response, access_token, refresh_token)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


@router.post("/switch-organization", response_model=Token)
async def switch_organization(
    body: SwitchOrganizationRequest,
    user: CurrentUser,
    db: DB,
    response: Response,
) -> dict[str, Any]:
    """Issue new tokens scoped to an organization the user belongs to."""
    try:
        organization_id = UUID(body.organization_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid organization id",
        ) from exc

    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.user_id == user.id,
            OrganizationMember.organization_id == organization_id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization",
        )

    org_id = str(organization_id)
    access_token = create_access_token(subject=str(user.id), org_id=org_id)
    refresh_token = create_refresh_token(subject=str(user.id), org_id=org_id)
    _set_auth_cookies(response, access_token, refresh_token)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


# ---------------------------------------------------------------------------
# MFA setup / confirm / disable
# ---------------------------------------------------------------------------


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def mfa_setup(user: CurrentUser, db: DB) -> dict[str, Any]:
    """Generate a TOTP secret for the current user."""
    if user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled",
        )

    raw_secret = _generate_totp_secret()
    b32_secret = base64.b32encode(raw_secret).decode()

    user.mfa_secret_encrypted = _encrypt_secret(raw_secret)
    await db.flush()

    otpauth = (
        f"otpauth://totp/ComplianceAgent:{user.email}?secret={b32_secret}&issuer=ComplianceAgent"
    )

    raw_codes, hashed_codes = _generate_recovery_codes()
    user.mfa_recovery_codes = hashed_codes
    await db.flush()

    return {
        "secret": b32_secret,
        "otpauth_uri": otpauth,
        "recovery_codes": raw_codes,
    }


@router.post("/mfa/confirm", response_model=MessageResponse)
async def mfa_confirm(body: MFAConfirmRequest, user: CurrentUser, db: DB) -> dict[str, Any]:
    """Confirm MFA setup by providing a valid TOTP code."""
    if user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled",
        )
    if not user.mfa_secret_encrypted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Run /mfa/setup first")

    secret = _decrypt_secret(user.mfa_secret_encrypted)
    if not _verify_totp(secret, body.totp_code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid TOTP code")

    user.mfa_enabled = True
    await db.flush()

    return {"message": "Two-factor authentication enabled", "success": True}


@router.post("/mfa/disable", response_model=MessageResponse)
async def mfa_disable(body: MFAConfirmRequest, user: CurrentUser, db: DB) -> dict[str, Any]:
    """Disable MFA (requires a valid TOTP code)."""
    if not user.mfa_enabled or not user.mfa_secret_encrypted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is not enabled")

    secret = _decrypt_secret(user.mfa_secret_encrypted)
    if not _verify_totp(secret, body.totp_code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid TOTP code")

    user.mfa_enabled = False
    user.mfa_secret_encrypted = None
    user.mfa_recovery_codes = None
    await db.flush()

    return {"message": "Two-factor authentication disabled", "success": True}


# ---------------------------------------------------------------------------
# Account deactivation / deletion
# ---------------------------------------------------------------------------


@router.post("/deactivate", response_model=MessageResponse)
async def deactivate_account(
    body: AccountDeactivateRequest, user: CurrentUser, db: DB
) -> dict[str, Any]:
    """Deactivate (soft-delete) the current user's account.

    * Revokes all tokens
    * Cancels any Stripe subscriptions for owned organizations
    * Removes memberships (except as last owner — blocked)
    * Anonymizes PII (email → hash, full_name → 'Deleted User')
    * Schedules hard deletion 30 days out
    """
    if not user.hashed_password or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")

    # Check not the sole owner of any org
    for m in user.memberships or []:
        if m.role == "owner":
            from sqlalchemy import func

            owner_count = (
                await db.execute(
                    select(func.count())
                    .select_from(OrganizationMember)
                    .where(
                        OrganizationMember.organization_id == m.organization_id,
                        OrganizationMember.role == "owner",
                    )
                )
            ).scalar_one()
            if owner_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Transfer organization ownership before deactivating",
                )

    # Cancel Stripe subscriptions for owned orgs (best-effort)
    for m in user.memberships or []:
        if m.role == "owner":
            from app.models.organization import Organization as OrgModel

            org_result = await db.execute(select(OrgModel).where(OrgModel.id == m.organization_id))
            org = org_result.scalar_one_or_none()
            if org and org.stripe_subscription_id and settings.stripe_api_key:
                try:
                    from app.services.billing import StripeService

                    svc = StripeService(api_key=settings.stripe_api_key)
                    async with svc:
                        await svc.cancel_subscription(
                            org.stripe_subscription_id,
                            at_period_end=False,
                        )
                except Exception:
                    logger.warning("deactivate.stripe_cancel_failed", org_id=str(org.id))

    # Remove memberships
    for m in list(user.memberships or []):
        await db.delete(m)

    # Anonymize PII
    user.is_active = False
    user.deactivated_at = datetime.now(UTC)
    user.deletion_scheduled_at = datetime.now(UTC) + timedelta(days=30)
    user.full_name = "Deleted User"
    user.email = f"deleted_{_hash_token(user.email)[:16]}@deactivated.local"
    user.hashed_password = None
    user.avatar_url = None
    user.mfa_enabled = False
    user.mfa_secret_encrypted = None
    user.mfa_recovery_codes = None

    await db.flush()
    revoke_all_user_tokens(str(user.id))

    return {"message": "Account deactivated. Data will be deleted in 30 days.", "success": True}


# ---------------------------------------------------------------------------
# Standard auth endpoints
# ---------------------------------------------------------------------------


@router.post("/refresh", response_model=Token)
async def refresh_token(
    db: DB,
    response: Response,
    body: RefreshTokenRequest | None = None,
    refresh_token_cookie: str | None = Cookie(default=None, alias="refresh_token"),
) -> dict[str, Any]:
    """Refresh access token."""
    token = body.refresh_token if body is not None else refresh_token_cookie
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is required",
        )

    payload = decode_token(token)
    if not payload or payload.type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    result = await db.execute(select(User).where(User.id == UUID(payload.sub)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    if payload.org_id:
        membership = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.user_id == user.id,
                OrganizationMember.organization_id == UUID(payload.org_id),
            )
        )
        if membership.scalar_one_or_none() is None:
            revoke_token(token)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Organization membership is no longer active",
            )

    revoke_token(token)

    access_token = create_access_token(subject=str(user.id), org_id=payload.org_id)
    new_refresh_token = create_refresh_token(subject=str(user.id), org_id=payload.org_id)

    _set_auth_cookies(response, access_token, new_refresh_token)

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    access_token: str | None = Cookie(default=None),
    refresh_token: str | None = Cookie(default=None),
) -> None:
    """Logout by revoking tokens and clearing auth cookies."""
    bearer_token: str | None = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        bearer_token = auth_header[7:]

    token_to_revoke = access_token or bearer_token
    if token_to_revoke:
        revoke_token(token_to_revoke)
    if refresh_token:
        revoke_token(refresh_token)

    is_production = settings.environment == "production"
    response.delete_cookie(
        key="access_token",
        path="/",
        secure=is_production,
        httponly=True,
        domain=settings.auth_cookie_domain or None,
    )
    response.delete_cookie(
        key="refresh_token",
        path="/",
        secure=is_production,
        httponly=True,
        domain=settings.auth_cookie_domain or None,
    )


_RESET_TOKEN_EXPIRY_HOURS = 1


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(body: ForgotPasswordRequest, db: DB) -> dict[str, Any]:
    """Request a password reset token."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user and user.is_active:
        token = secrets.token_urlsafe(32)
        user.password_reset_token = _hash_token(token)
        user.password_reset_expires = datetime.now(UTC) + timedelta(hours=_RESET_TOKEN_EXPIRY_HOURS)
        await db.flush()
        await _send_password_reset_email(user.email, token)

    return {
        "message": "If that email exists, a password reset link has been sent.",
        "success": True,
    }


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(body: ResetPasswordRequest, db: DB) -> dict[str, Any]:
    """Reset password using a token from forgot-password."""
    result = await db.execute(
        select(User).where(User.password_reset_token == _hash_token(body.token))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    if _is_expired(user.password_reset_expires):
        user.password_reset_token = None
        user.password_reset_expires = None
        await db.flush()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired",
        )

    user.hashed_password = get_password_hash(body.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    await db.flush()

    revoke_all_user_tokens(str(user.id))
    logger.info("auth.password_reset_completed", user_id=str(user.id))

    return {
        "message": "Password has been reset. Please log in with your new password.",
        "success": True,
    }
