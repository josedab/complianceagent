"""Security utilities for authentication and authorization."""

from __future__ import annotations

import threading
import uuid
from datetime import UTC, datetime, timedelta

import jwt
import structlog
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import settings


logger = structlog.get_logger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenPayload(BaseModel):
    """JWT token payload."""

    sub: str  # Subject (user_id)
    org_id: str | None = None  # Organization ID for multi-tenancy
    exp: datetime
    iat: datetime
    type: str = "access"  # access or refresh
    jti: str | None = None  # JWT ID for token revocation


class TokenBlacklist:
    """Token blacklist with in-memory and Redis backends.

    Uses Redis in production for distributed revocation. Falls back to
    an in-memory store when Redis is unavailable.
    """

    _REDIS_PREFIX = "token_blacklist:"
    _USER_REVOKE_PREFIX = "user_tokens_revoked:"

    def __init__(self) -> None:
        self._memory_store: dict[str, datetime] = {}
        self._user_revoked: dict[str, datetime] = {}
        self._lock = threading.Lock()
        self._redis: object | None = None
        self._redis_checked = False

    def _get_redis(self) -> object | None:
        """Lazily connect to Redis, returning None if unavailable."""
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
            logger.info("token_blacklist.redis_connected")
        except Exception:
            logger.info("token_blacklist.redis_unavailable_using_memory")
            self._redis = None
        return self._redis

    def revoke(self, jti: str, expires_at: datetime) -> None:
        """Add a token JTI to the blacklist."""
        ttl = int((expires_at - datetime.now(UTC)).total_seconds())
        if ttl <= 0:
            return  # Already expired, no need to blacklist

        r = self._get_redis()
        if r is not None:
            try:
                r.setex(f"{self._REDIS_PREFIX}{jti}", ttl, "1")  # type: ignore[union-attr]
                logger.debug("token_blacklist.revoked", jti=jti, backend="redis")
                return
            except Exception:
                logger.warning("token_blacklist.redis_error_falling_back", jti=jti)

        with self._lock:
            self._memory_store[jti] = expires_at
            self._cleanup_expired()
        logger.debug("token_blacklist.revoked", jti=jti, backend="memory")

    def is_revoked(self, jti: str) -> bool:
        """Check whether a token JTI has been revoked."""
        r = self._get_redis()
        if r is not None:
            try:
                return r.exists(f"{self._REDIS_PREFIX}{jti}") > 0  # type: ignore[union-attr]
            except Exception:
                logger.warning("token_blacklist.redis_check_error", jti=jti)

        with self._lock:
            self._cleanup_expired()
            return jti in self._memory_store

    def revoke_all_user_tokens(self, user_id: str) -> None:
        """Mark all tokens for a user issued before now as revoked.

        Tokens whose ``iat`` is before the recorded timestamp will be
        rejected by ``is_user_revoked``.
        """
        now = datetime.now(UTC)
        r = self._get_redis()
        if r is not None:
            try:
                max_ttl = settings.refresh_token_expire_days * 86400
                r.setex(  # type: ignore[union-attr]
                    f"{self._USER_REVOKE_PREFIX}{user_id}",
                    max_ttl,
                    now.isoformat(),
                )
                logger.info("token_blacklist.user_tokens_revoked", user_id=user_id, backend="redis")
                return
            except Exception:
                logger.warning("token_blacklist.redis_user_revoke_error", user_id=user_id)

        with self._lock:
            self._user_revoked[user_id] = now
        logger.info("token_blacklist.user_tokens_revoked", user_id=user_id, backend="memory")

    def is_user_revoked(self, user_id: str, issued_at: datetime) -> bool:
        """Check if a token was issued before the user's revocation timestamp."""
        r = self._get_redis()
        if r is not None:
            try:
                val = r.get(f"{self._USER_REVOKE_PREFIX}{user_id}")  # type: ignore[union-attr]
                if val:
                    revoked_at = datetime.fromisoformat(val)
                    return issued_at < revoked_at
                return False
            except Exception:
                logger.warning("token_blacklist.redis_user_check_error", user_id=user_id)

        with self._lock:
            revoked_at = self._user_revoked.get(user_id)
            if revoked_at is None:
                return False
            return issued_at < revoked_at

    def _cleanup_expired(self) -> None:
        """Remove expired entries from the in-memory store."""
        now = datetime.now(UTC)
        expired = [jti for jti, exp in self._memory_store.items() if exp <= now]
        for jti in expired:
            del self._memory_store[jti]


# Module-level singleton
token_blacklist = TokenBlacklist()


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
        jti=str(uuid.uuid4()),
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
        jti=str(uuid.uuid4()),
    )

    return jwt.encode(
        payload.model_dump(),
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def decode_token(token: str) -> TokenPayload | None:
    """Decode and validate a JWT token.

    Returns ``None`` when the token is invalid, expired, or has been
    revoked via the blacklist.
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        token_data = TokenPayload(**payload)

        # Check token-level revocation
        if token_data.jti and token_blacklist.is_revoked(token_data.jti):
            logger.debug("decode_token.revoked", jti=token_data.jti)
            return None

        # Check user-level revocation
        if token_blacklist.is_user_revoked(token_data.sub, token_data.iat):
            logger.debug("decode_token.user_revoked", sub=token_data.sub)
            return None

        return token_data
    except jwt.PyJWTError:
        return None


def revoke_token(token: str) -> None:
    """Decode a token and add its JTI to the blacklist.

    Gracefully handles invalid tokens by logging and returning.
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            options={"verify_exp": False},
        )
        token_data = TokenPayload(**payload)
        if token_data.jti:
            token_blacklist.revoke(token_data.jti, token_data.exp)
            logger.info("revoke_token.success", jti=token_data.jti, type=token_data.type)
        else:
            logger.debug("revoke_token.no_jti_skipping")
    except Exception:
        logger.warning("revoke_token.invalid_token_ignored")


def revoke_all_user_tokens(user_id: str) -> None:
    """Revoke all tokens issued to a user before the current moment."""
    token_blacklist.revoke_all_user_tokens(user_id)
    logger.info("revoke_all_user_tokens.success", user_id=user_id)
