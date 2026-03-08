"""Extended authentication tests: token revocation, account lockout, health endpoints."""

from datetime import timedelta

import jwt
import pytest
from httpx import ASGITransport, AsyncClient

from app.api.v1.auth import _lockout, _LOCKOUT_SECONDS, _MAX_FAILED_ATTEMPTS
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    revoke_all_user_tokens,
    revoke_token,
    token_blacklist,
)


def _bcrypt_available() -> bool:
    try:
        get_password_hash("test")
        return True
    except (ValueError, OSError):
        return False


_skip_bcrypt = pytest.mark.skipif(
    not _bcrypt_available(),
    reason="bcrypt/passlib not functional in this environment",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clear_blacklist() -> None:
    """Reset the in-memory token blacklist between tests."""
    with token_blacklist._lock:
        token_blacklist._memory_store.clear()
        token_blacklist._user_revoked.clear()


def _clear_lockout(email: str) -> None:
    """Reset lockout state for an email."""
    _lockout.clear(email)


# ---------------------------------------------------------------------------
# 1. Token Revocation
# ---------------------------------------------------------------------------

class TestTokenRevocation:
    """Tests for token-level and user-level revocation."""

    def setup_method(self) -> None:
        _clear_blacklist()

    def test_revoke_token_makes_it_invalid(self):
        """A revoked token should no longer decode successfully."""
        token = create_access_token(subject="user-rev1")
        assert decode_token(token) is not None

        revoke_token(token)
        assert decode_token(token) is None

    def test_revoke_expired_token_is_noop(self):
        """Revoking an already-expired token should not raise."""
        token = create_access_token(
            subject="user-exp",
            expires_delta=timedelta(seconds=-10),
        )
        # Should not error; expired tokens are silently skipped
        revoke_token(token)

    def test_revoke_all_user_tokens(self):
        """revoke_all_user_tokens should invalidate every token for a user."""
        t1 = create_access_token(subject="user-bulk")
        t2 = create_refresh_token(subject="user-bulk")

        assert decode_token(t1) is not None
        assert decode_token(t2) is not None

        revoke_all_user_tokens("user-bulk")

        assert decode_token(t1) is None
        assert decode_token(t2) is None

    def test_token_without_jti_still_works(self):
        """Tokens without a jti (backward compatibility) should decode OK."""
        from datetime import UTC, datetime

        payload = {
            "sub": "user-legacy",
            "org_id": None,
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "iat": datetime.now(UTC),
            "type": "access",
            # no jti
        }
        token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
        result = decode_token(token)
        assert result is not None
        assert result.sub == "user-legacy"
        assert result.jti is None

    def test_revoked_token_does_not_affect_others(self):
        """Revoking one user's token should not affect another user's token."""
        token_a = create_access_token(subject="user-a")
        token_b = create_access_token(subject="user-b")

        revoke_token(token_a)

        assert decode_token(token_a) is None
        assert decode_token(token_b) is not None


# ---------------------------------------------------------------------------
# 2. Account Lockout
# ---------------------------------------------------------------------------

class TestAccountLockout:
    """Tests for the login-attempt lockout mechanism."""

    _EMAIL = "lockout-test@example.com"
    _OTHER = "other-user@example.com"

    def setup_method(self) -> None:
        _clear_lockout(self._EMAIL)
        _clear_lockout(self._OTHER)

    def teardown_method(self) -> None:
        _clear_lockout(self._EMAIL)
        _clear_lockout(self._OTHER)

    def test_not_locked_initially(self):
        """A fresh email should not be locked out."""
        assert _lockout.is_locked_out(self._EMAIL) is False

    def test_lockout_after_max_attempts(self):
        """Recording max failed attempts should trigger lockout."""
        for _ in range(_MAX_FAILED_ATTEMPTS):
            _lockout.record_failed(self._EMAIL)

        assert _lockout.is_locked_out(self._EMAIL) is True

    def test_clear_resets_lockout(self):
        """Clearing lockout state should unlock the account."""
        for _ in range(_MAX_FAILED_ATTEMPTS):
            _lockout.record_failed(self._EMAIL)
        assert _lockout.is_locked_out(self._EMAIL) is True

        _lockout.clear(self._EMAIL)
        assert _lockout.is_locked_out(self._EMAIL) is False

    def test_lockout_for_different_emails_independent(self):
        """Locking one email should not affect another."""
        for _ in range(_MAX_FAILED_ATTEMPTS):
            _lockout.record_failed(self._EMAIL)

        assert _lockout.is_locked_out(self._EMAIL) is True
        assert _lockout.is_locked_out(self._OTHER) is False


# ---------------------------------------------------------------------------
# 3. Health / Readiness Endpoints
# ---------------------------------------------------------------------------

class TestHealthEndpoints:
    """Tests for liveness and readiness probes."""

    @pytest.mark.asyncio
    async def test_liveness_always_200(self):
        """/health should always return 200 with status 'healthy'."""
        from app.main import app

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_readiness_returns_checks_structure(self):
        """/health/ready should include database and redis check results."""
        from app.main import app

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health/ready")

        body = response.json()
        assert "status" in body
        assert "checks" in body
        checks = body["checks"]
        assert "database" in checks
        assert "redis" in checks
        # Each check should report a status string
        assert "status" in checks["database"]
        assert "status" in checks["redis"]


# ---------------------------------------------------------------------------
# 4. Password Hash Security (supplemental)
# ---------------------------------------------------------------------------

@_skip_bcrypt
class TestPasswordHashSecurity:
    """Supplemental password hash assertions."""

    def test_password_hash_not_plaintext(self):
        """The hash must never equal the original plaintext password."""
        password = "SuperSecret!99"
        hashed = get_password_hash(password)
        assert hashed != password
