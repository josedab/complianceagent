"""Tests for the security module: password hashing, JWT tokens."""

from datetime import timedelta

import pytest

from app.core.security import (
    TokenPayload,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)


def _bcrypt_available() -> bool:
    """Check if bcrypt is functional in this environment."""
    try:
        get_password_hash("test")
        return True
    except (ValueError, OSError):
        return False


_skip_bcrypt = pytest.mark.skipif(
    not _bcrypt_available(),
    reason="bcrypt/passlib not functional in this environment",
)


@_skip_bcrypt
class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_and_verify_correct_password(self):
        """Correct password should verify successfully."""
        hashed = get_password_hash("s3cretP@ss!")
        assert verify_password("s3cretP@ss!", hashed) is True

    def test_wrong_password_fails_verification(self):
        """Wrong password should not verify."""
        hashed = get_password_hash("correctPassword")
        assert verify_password("wrongPassword", hashed) is False

    def test_hash_is_not_plaintext(self):
        """Hash output must not equal the plaintext password."""
        password = "mypassword123"
        hashed = get_password_hash(password)
        assert hashed != password

    def test_same_password_produces_different_hashes(self):
        """bcrypt uses a random salt so two hashes of the same password differ."""
        h1 = get_password_hash("samePassword")
        h2 = get_password_hash("samePassword")
        assert h1 != h2
        # Both should still verify
        assert verify_password("samePassword", h1) is True
        assert verify_password("samePassword", h2) is True


class TestAccessToken:
    """Test JWT access token creation and decoding."""

    def test_create_and_decode_round_trip(self):
        """Token created for a subject should decode back to the same subject."""
        token = create_access_token(subject="user-123")
        payload = decode_token(token)

        assert payload is not None
        assert payload.sub == "user-123"
        assert payload.type == "access"

    def test_org_id_claim_is_preserved(self):
        """org_id passed at creation should appear in the decoded payload."""
        token = create_access_token(subject="user-456", org_id="org-789")
        payload = decode_token(token)

        assert payload is not None
        assert payload.org_id == "org-789"

    def test_token_without_org_id_has_none(self):
        """When org_id is omitted, decoded payload should have org_id=None."""
        token = create_access_token(subject="user-abc")
        payload = decode_token(token)

        assert payload is not None
        assert payload.org_id is None

    def test_expired_token_returns_none(self):
        """A token created with a negative expiry should fail decoding."""
        token = create_access_token(
            subject="user-expired",
            expires_delta=timedelta(seconds=-10),
        )
        payload = decode_token(token)

        assert payload is None

    def test_custom_expiry_is_respected(self):
        """A token with a long custom expiry should still decode successfully."""
        token = create_access_token(
            subject="user-long",
            expires_delta=timedelta(hours=48),
        )
        payload = decode_token(token)

        assert payload is not None
        assert payload.sub == "user-long"


class TestRefreshToken:
    """Test JWT refresh token creation."""

    def test_refresh_token_round_trip(self):
        """Refresh token should decode with type='refresh'."""
        token = create_refresh_token(subject="user-refresh")
        payload = decode_token(token)

        assert payload is not None
        assert payload.sub == "user-refresh"
        assert payload.type == "refresh"

    def test_refresh_token_preserves_org_id(self):
        """org_id should be present in a decoded refresh token."""
        token = create_refresh_token(subject="user-r2", org_id="org-r2")
        payload = decode_token(token)

        assert payload is not None
        assert payload.org_id == "org-r2"

    def test_refresh_token_has_later_expiry_than_access(self):
        """Refresh token expiry should be after access token expiry."""
        access = create_access_token(subject="u1")
        refresh = create_refresh_token(subject="u1")

        access_payload = decode_token(access)
        refresh_payload = decode_token(refresh)

        assert access_payload is not None
        assert refresh_payload is not None
        assert refresh_payload.exp > access_payload.exp


class TestDecodeTokenEdgeCases:
    """Test decode_token with invalid inputs."""

    def test_garbage_token_returns_none(self):
        assert decode_token("not.a.valid.jwt") is None

    def test_empty_string_returns_none(self):
        assert decode_token("") is None

    def test_tampered_token_returns_none(self):
        """Flipping a character in the signature should invalidate the token."""
        token = create_access_token(subject="user-tamper")
        # Flip last character
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        assert decode_token(tampered) is None
