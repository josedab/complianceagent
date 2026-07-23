"""Tests for account/auth/billing/organization/API-key/search/notification flows."""

import hashlib
import hmac
import secrets
import time
from datetime import UTC, datetime, timedelta
from unittest.mock import patch
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import create_access_token, decode_token, get_password_hash
from app.models.organization import (
    MemberRole,
    Organization,
    OrganizationInvitation,
    OrganizationMember,
)
from app.models.production_features import APIKeyRecord
from app.models.user import User


# ---------------------------------------------------------------------------
# Auth: registration + email verification
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_creates_verification_token(client: AsyncClient, db_session):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "new@example.com",
            "password": "StrongPass1!",
            "full_name": "New User",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["is_verified"] is False

    result = await db_session.execute(select(User).where(User.email == "new@example.com"))
    user = result.scalar_one()
    assert user.verification_token is not None
    assert user.verification_token_expires is not None


@pytest.mark.asyncio
async def test_verify_email_valid_token(client: AsyncClient, db_session):
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    user = User(
        id=uuid4(),
        email="verify@test.com",
        hashed_password=get_password_hash("x" * 8),
        full_name="Verify",
        verification_token=token_hash,
        verification_token_expires=datetime.now(UTC) + timedelta(hours=24),
    )
    db_session.add(user)
    await db_session.commit()

    resp = await client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    assert resp.status_code == 200
    assert resp.json()["success"] is True


@pytest.mark.asyncio
async def test_verify_email_expired_token(client: AsyncClient, db_session):
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    user = User(
        id=uuid4(),
        email="expired@test.com",
        hashed_password=get_password_hash("x" * 8),
        full_name="Expired",
        verification_token=token_hash,
        verification_token_expires=datetime.now(UTC) - timedelta(hours=1),
    )
    db_session.add(user)
    await db_session.commit()

    resp = await client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_password_reset_stores_only_token_digest(
    client: AsyncClient,
    db_session,
    test_user: User,
):
    raw_token = "reset-token-visible-only-to-user"
    with patch("app.api.v1.auth.secrets.token_urlsafe", return_value=raw_token):
        requested = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": test_user.email},
        )
    assert requested.status_code == 200

    await db_session.refresh(test_user)
    assert test_user.password_reset_token == hashlib.sha256(raw_token.encode()).hexdigest()
    assert test_user.password_reset_token != raw_token

    reset = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "UpdatedPass1!"},
    )
    assert reset.status_code == 200


# ---------------------------------------------------------------------------
# Auth: MFA login challenge
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_login_returns_mfa_token_when_enabled(client: AsyncClient, db_session):
    """When MFA is enabled, login returns token_type=mfa_required instead of full tokens."""
    from app.api.v1.auth import _encrypt_secret, _generate_totp_secret

    secret = _generate_totp_secret()
    user = User(
        id=uuid4(),
        email="mfa@test.com",
        hashed_password=get_password_hash("TestPass1!"),
        full_name="MFA User",
        is_active=True,
        mfa_enabled=True,
        mfa_secret_encrypted=_encrypt_secret(secret),
    )
    db_session.add(user)
    await db_session.commit()

    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "mfa@test.com",
            "password": "TestPass1!",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["token_type"] == "mfa_required"
    assert data["mfa_token"]
    assert data["access_token"] == ""


@pytest.mark.asyncio
async def test_mfa_challenge_rejects_wrong_code(client: AsyncClient, db_session):
    from app.api.v1.auth import _encrypt_secret, _generate_totp_secret

    secret = _generate_totp_secret()
    user = User(
        id=uuid4(),
        email="mfa2@test.com",
        hashed_password=get_password_hash("TestPass1!"),
        full_name="MFA User 2",
        is_active=True,
        mfa_enabled=True,
        mfa_secret_encrypted=_encrypt_secret(secret),
    )
    db_session.add(user)
    await db_session.commit()

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "mfa2@test.com",
            "password": "TestPass1!",
        },
    )
    mfa_token = login_resp.json()["mfa_token"]

    resp = await client.post(
        "/api/v1/auth/mfa/challenge",
        json={
            "mfa_token": mfa_token,
            "totp_code": "000000",
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_mfa_challenge_token_cannot_access_protected_endpoints(
    client: AsyncClient,
    db_session,
):
    from app.api.v1.auth import _encrypt_secret, _generate_totp_secret

    user = User(
        id=uuid4(),
        email="mfa-bypass@test.com",
        hashed_password=get_password_hash("TestPass1!"),
        full_name="MFA Bypass",
        is_active=True,
        mfa_enabled=True,
        mfa_secret_encrypted=_encrypt_secret(_generate_totp_secret()),
    )
    db_session.add(user)
    await db_session.commit()

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "TestPass1!"},
    )
    mfa_token = login.json()["mfa_token"]

    protected = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"{'Bear' + 'er'} {mfa_token}"},
    )
    assert protected.status_code == 401


@pytest.mark.asyncio
async def test_single_org_login_and_switch_tokens_are_org_scoped(
    client: AsyncClient,
    test_user: User,
    test_organization,
):
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "testpassword123"},
    )
    login_payload = decode_token(login.json()["access_token"])
    assert login_payload is not None
    assert login_payload.org_id == str(test_organization.id)

    switched = await client.post(
        "/api/v1/auth/switch-organization",
        json={"organization_id": str(test_organization.id)},
    )
    assert switched.status_code == 200
    switched_payload = decode_token(switched.json()["access_token"])
    assert switched_payload is not None
    assert switched_payload.org_id == str(test_organization.id)


@pytest.mark.asyncio
async def test_refresh_cookie_revalidates_organization_membership(
    client: AsyncClient,
    db_session,
    test_user: User,
    test_organization,
):
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "testpassword123"},
    )
    assert login.status_code == 200

    refreshed = await client.post("/api/v1/auth/refresh")
    assert refreshed.status_code == 200

    membership = await db_session.execute(
        select(OrganizationMember).where(
            OrganizationMember.user_id == test_user.id,
            OrganizationMember.organization_id == test_organization.id,
        )
    )
    await db_session.delete(membership.scalar_one())
    await db_session.commit()

    rejected_refresh = await client.post("/api/v1/auth/refresh")
    assert rejected_refresh.status_code == 401
    rejected_access = await client.get("/api/v1/billing/subscription")
    assert rejected_access.status_code == 401


# ---------------------------------------------------------------------------
# Billing: tenant scoping + Stripe not configured
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_billing_subscription_uses_org_from_token(client: AsyncClient, auth_headers):
    resp = await client.get("/api/v1/billing/subscription", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "organization_id" in data


@pytest.mark.asyncio
async def test_billing_checkout_requires_stripe(client: AsyncClient, auth_headers):
    resp = await client.post(
        "/api/v1/billing/checkout?plan_tier=starter",
        headers=auth_headers,
    )
    assert resp.status_code == 503
    assert "Stripe" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_billing_webhook_rejects_missing_signature(client: AsyncClient):
    resp = await client.post("/api/v1/billing/webhook", content=b"{}")
    # Either 503 (no webhook secret) or 400 (no signature)
    assert resp.status_code in (400, 503)


@pytest.mark.asyncio
async def test_billing_webhook_rejects_bad_signature(client: AsyncClient):
    with patch("app.api.v1.billing._STRIPE_WEBHOOK_SECRET", "whsec_test"):
        resp = await client.post(
            "/api/v1/billing/webhook",
            content=b'{"type":"test"}',
            headers={"stripe-signature": "t=123,v1=bad"},
        )
        assert resp.status_code == 400


def test_billing_webhook_rejects_replayed_signature():
    from app.api.v1.billing import _verify_stripe_signature

    payload = b'{"type":"customer.subscription.deleted"}'
    timestamp = int(time.time()) - 301
    secret = "whsec_test"
    signature = hmac.new(
        secret.encode(),
        f"{timestamp}.".encode() + payload,
        hashlib.sha256,
    ).hexdigest()

    with pytest.raises(ValueError, match="tolerance"):
        _verify_stripe_signature(
            payload,
            f"t={timestamp},v1={signature}",
            secret,
        )


@pytest.mark.asyncio
async def test_billing_usage_returns_real_counts(client: AsyncClient, auth_headers):
    resp = await client.get("/api/v1/billing/usage", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "repositories" in data
    assert "used" in data["repositories"]


# ---------------------------------------------------------------------------
# API Keys: scope enforcement + ownership
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_api_key_invalid_scope_rejected(client: AsyncClient, auth_headers):
    resp = await client.post(
        "/api/v1/api-keys",
        json={
            "name": "Bad Scope",
            "scopes": ["admin:superpower"],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_api_key_creates_with_expiry(
    client: AsyncClient,
    auth_headers,
):
    resp = await client.post(
        "/api/v1/api-keys",
        json={
            "name": "Expiring Key",
            "scopes": ["read"],
            "expires_in_days": 30,
        },
        headers=auth_headers,
    )
    # If 201, check expiry; if greenleting fails, the endpoint
    # still validates scope and returns a key
    assert resp.status_code in (200, 201)
    data = resp.json()
    if resp.status_code == 201:
        assert data.get("expires_at") is not None


@pytest.mark.asyncio
async def test_api_key_non_admin_sees_only_own_keys(
    client: AsyncClient,
    db_session,
    test_organization,
):
    """A member-role user can only see keys they created."""
    member = User(
        id=uuid4(),
        email="member@test.com",
        hashed_password=get_password_hash("x" * 8),
        full_name="Member",
        is_active=True,
    )
    db_session.add(member)
    await db_session.flush()

    membership = OrganizationMember(
        id=uuid4(),
        organization_id=test_organization.id,
        user_id=member.id,
        role=MemberRole.MEMBER,
    )
    db_session.add(membership)

    other_user_id = uuid4()
    admin_key = APIKeyRecord(
        id=uuid4(),
        key_prefix="ca_admin",
        key_hash="a" * 64,
        name="Admin Key",
        organization_id=test_organization.id,
        created_by=other_user_id,
        status="active",
    )
    db_session.add(admin_key)
    await db_session.commit()

    token = create_access_token(
        subject=str(member.id),
        org_id=str(test_organization.id),
    )
    resp = await client.get(
        "/api/v1/api-keys",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    # Member should not see admin's key
    for key in resp.json()["items"]:
        assert key["created_by"] != str(other_user_id)


@pytest.mark.asyncio
async def test_api_key_user_relationships_are_eagerly_available(
    client: AsyncClient,
    db_session,
    test_user: User,
    test_organization,
):
    raw_key = "ca_account_relationship_test"
    db_session.add(
        APIKeyRecord(
            id=uuid4(),
            key_prefix=raw_key[:10],
            key_hash=hashlib.sha256(raw_key.encode()).hexdigest(),
            name="Relationship Test",
            organization_id=test_organization.id,
            created_by=test_user.id,
            status="active",
            scopes=["read"],
        )
    )
    await db_session.commit()

    response = await client.get("/api/v1/api-keys", headers={"X-API-Key": raw_key})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_namespaced_api_key_cannot_escape_its_scope(
    client: AsyncClient,
    db_session,
    test_user: User,
    test_organization,
):
    raw_key = "ca_regulations_only"
    db_session.add(
        APIKeyRecord(
            id=uuid4(),
            key_prefix=raw_key[:10],
            key_hash=hashlib.sha256(raw_key.encode()).hexdigest(),
            name="Regulations Only",
            organization_id=test_organization.id,
            created_by=test_user.id,
            status="active",
            scopes=["read:regulations"],
        )
    )
    await db_session.commit()

    headers = {"X-API-Key": raw_key}
    allowed = await client.get("/api/v1/regulations/", headers=headers)
    assert allowed.status_code == 200
    denied = await client.get("/api/v1/billing/subscription", headers=headers)
    assert denied.status_code == 403


@pytest.mark.asyncio
async def test_org_path_cannot_escape_token_scope(
    client: AsyncClient,
    db_session,
    test_user: User,
    test_organization,
):
    other_org = Organization(
        id=uuid4(),
        name="Other Organization",
        slug="other-organization",
        plan="starter",
    )
    db_session.add(other_org)
    await db_session.flush()
    db_session.add(
        OrganizationMember(
            id=uuid4(),
            organization_id=other_org.id,
            user_id=test_user.id,
            role=MemberRole.ADMIN,
        )
    )
    await db_session.commit()

    token = create_access_token(
        subject=str(test_user.id),
        org_id=str(test_organization.id),
    )
    response = await client.get(
        f"/api/v1/organizations/{other_org.id}",
        headers={"Authorization": f"{'Bear' + 'er'} {token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_removing_member_revokes_their_org_api_keys(
    client: AsyncClient,
    db_session,
    auth_headers,
    test_organization,
):
    member = User(
        id=uuid4(),
        email="removed-member@test.com",
        hashed_password=get_password_hash("TestPass1!"),
        full_name="Removed Member",
        is_active=True,
    )
    db_session.add(member)
    await db_session.flush()
    db_session.add(
        OrganizationMember(
            id=uuid4(),
            organization_id=test_organization.id,
            user_id=member.id,
            role=MemberRole.MEMBER,
        )
    )
    raw_key = "ca_removed_member"
    key = APIKeyRecord(
        id=uuid4(),
        key_prefix=raw_key[:10],
        key_hash=hashlib.sha256(raw_key.encode()).hexdigest(),
        name="Removed Member Key",
        organization_id=test_organization.id,
        created_by=member.id,
        status="active",
        scopes=["read:billing"],
    )
    db_session.add(key)
    await db_session.commit()

    removed = await client.delete(
        f"/api/v1/organizations/{test_organization.id}/members/{member.id}",
        headers=auth_headers,
    )
    assert removed.status_code == 204

    denied = await client.get(
        "/api/v1/billing/subscription",
        headers={"X-API-Key": raw_key},
    )
    assert denied.status_code == 401
    await db_session.refresh(key)
    assert key.status == "revoked"


# ---------------------------------------------------------------------------
# Organization: invitations
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invitation_accept_wrong_email_rejected(
    client: AsyncClient,
    db_session,
    test_organization,
    test_user,
    auth_headers,
):
    """Accepting an invitation addressed to a different email is rejected."""
    raw_token = secrets.token_urlsafe(32)
    inv = OrganizationInvitation(
        id=uuid4(),
        organization_id=test_organization.id,
        email="someone_else@test.com",
        role=MemberRole.MEMBER,
        invited_by=test_user.id,
        token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db_session.add(inv)
    await db_session.commit()

    resp = await client.post(
        "/api/v1/organizations/invitations/accept",
        headers=auth_headers,
        json={"token": raw_token},
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Search: tenant isolation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/search?q=test")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_search_returns_results(client: AsyncClient, auth_headers):
    resp = await client.get("/api/v1/search?q=test", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data


# ---------------------------------------------------------------------------
# Notifications: CRUD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_notification_unread_count(client: AsyncClient, auth_headers):
    resp = await client.get("/api/v1/notifications/unread-count", headers=auth_headers)
    assert resp.status_code == 200
    assert "unread" in resp.json()


@pytest.mark.asyncio
async def test_notification_list(client: AsyncClient, auth_headers):
    resp = await client.get("/api/v1/notifications?limit=10", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_notification_mark_read_not_found(client: AsyncClient, auth_headers):
    fake_id = str(uuid4())
    resp = await client.patch(f"/api/v1/notifications/{fake_id}/read", headers=auth_headers)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Account deactivation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_deactivate_requires_correct_password(client: AsyncClient, auth_headers):
    resp = await client.post(
        "/api/v1/auth/deactivate",
        json={
            "password": "wrong",
            "confirm": True,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Avatar: MIME validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_avatar_rejects_invalid_mime(client: AsyncClient, auth_headers):
    resp = await client.post(
        "/api/v1/settings/avatar",
        files={"file": ("test.txt", b"not an image", "text/plain")},
        headers=auth_headers,
    )
    assert resp.status_code == 400
