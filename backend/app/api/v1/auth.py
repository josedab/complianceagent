"""Authentication endpoints."""

import secrets
import threading
from datetime import UTC, datetime, timedelta

import structlog
from fastapi import APIRouter, Cookie, HTTPException, Request, Response, status
from sqlalchemy import select

from app.api.v1.deps import DB
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    revoke_all_user_tokens,
    revoke_token,
    verify_password,
)
from app.models.user import User
from app.schemas.base import MessageResponse
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
        self._redis: object | None = None
        self._redis_checked = False

    def _get_redis(self) -> object | None:
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
                return r.exists(f"{_REDIS_PREFIX}locked:{email}") > 0  # type: ignore[union-attr]
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
                r.zadd(key, {str(now): now})  # type: ignore[union-attr]
                r.zremrangebyscore(key, 0, now - _LOCKOUT_SECONDS)  # type: ignore[union-attr]
                r.expire(key, _LOCKOUT_SECONDS)  # type: ignore[union-attr]
                count = r.zcard(key)  # type: ignore[union-attr]
                if count >= _MAX_FAILED_ATTEMPTS:
                    r.setex(f"{_REDIS_PREFIX}locked:{email}", _LOCKOUT_SECONDS, "1")  # type: ignore[union-attr]
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
                r.delete(f"{_REDIS_PREFIX}attempts:{email}", f"{_REDIS_PREFIX}locked:{email}")  # type: ignore[union-attr]
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
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/api/v1/auth",
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: DB) -> User:
    """Register a new user."""
    # Check if user exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    return user


@router.post("/login", response_model=Token)
async def login(login_request: LoginRequest, db: DB, response: Response) -> dict:
    """Login and get access token."""
    # Check account lockout
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

    # Successful login — clear any failed attempts
    _lockout.clear(login_request.email)

    # Update last login
    user.last_login_at = datetime.now(UTC)
    await db.flush()

    # Generate tokens
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))

    _set_auth_cookies(response, access_token, refresh_token)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(body: RefreshTokenRequest, db: DB, response: Response) -> dict:
    """Refresh access token."""
    payload = decode_token(body.refresh_token)
    if not payload or payload.type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    result = await db.execute(select(User).where(User.id == payload.sub))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Revoke the old refresh token before issuing new ones
    revoke_token(body.refresh_token)

    # Generate new tokens
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
    # Try cookies first, then fall back to Authorization header
    bearer_token: str | None = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        bearer_token = auth_header[7:]

    token_to_revoke = access_token or bearer_token
    if token_to_revoke:
        revoke_token(token_to_revoke)
    if refresh_token:
        revoke_token(refresh_token)

    # Clear auth cookies
    is_production = settings.environment == "production"
    response.delete_cookie(key="access_token", path="/", secure=is_production, httponly=True)
    response.delete_cookie(
        key="refresh_token", path="/api/v1/auth", secure=is_production, httponly=True
    )


_RESET_TOKEN_EXPIRY_HOURS = 1


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(body: ForgotPasswordRequest, db: DB) -> dict:
    """Request a password reset token.

    Always returns success to prevent email enumeration. In production,
    the token would be sent via email. In development, it is logged.
    """
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user and user.is_active:
        token = secrets.token_urlsafe(32)
        user.password_reset_token = token
        user.password_reset_expires = datetime.now(UTC) + timedelta(hours=_RESET_TOKEN_EXPIRY_HOURS)
        await db.flush()

        # In production: send email via SES/SendGrid/SMTP
        # For now: log token for development use
        logger.info(
            "auth.password_reset_requested",
            email=body.email,
            reset_url=f"/reset-password?token={token}",
        )

    return {"message": "If that email exists, a password reset link has been sent.", "success": True}


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(body: ResetPasswordRequest, db: DB) -> dict:
    """Reset password using a token from forgot-password."""
    result = await db.execute(
        select(User).where(User.password_reset_token == body.token)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    if not user.password_reset_expires or user.password_reset_expires < datetime.now(UTC):
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

    return {"message": "Password has been reset. Please log in with your new password.", "success": True}
