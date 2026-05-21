"""Tests for notification service and API endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import NotificationRecord
from app.models.organization import Organization
from app.models.user import User
from app.services.notification import (
    InAppChannel,
    Notification,
    NotificationPriority,
    NotificationType,
)


pytestmark = pytest.mark.asyncio

BASE = "/api/v1/notifications"


def _make_notification(org_id, user_id):
    return Notification(
        type=NotificationType.COMPLIANCE_ALERT,
        title="Test Alert",
        message="Something needs attention",
        priority=NotificationPriority.HIGH,
        organization_id=str(org_id),
        user_id=str(user_id),
        metadata={"key": "value"},
        action_url="https://example.com/action",
    )


async def test_inapp_send_with_db_persists_row(
    db_session: AsyncSession,
    test_user: User,
    test_organization: Organization,
):
    channel = InAppChannel(db_session=db_session)
    notif = _make_notification(test_organization.id, test_user.id)
    result = await channel.send(notif, {})
    assert result is True
    count = await db_session.execute(select(func.count()).select_from(NotificationRecord))
    assert count.scalar_one() == 1


async def test_inapp_send_without_db_in_test_env_returns_true():
    channel = InAppChannel(db_session=None)
    notif = Notification(
        type=NotificationType.COMPLIANCE_ALERT,
        title="No DB",
        message="No session",
        organization_id=str(uuid4()),
        user_id=str(uuid4()),
    )
    result = await channel.send(notif, {})
    assert result is True


async def _seed(db_session, org_id, user_id, title="Alert") -> NotificationRecord:
    record = NotificationRecord(
        organization_id=org_id,
        user_id=user_id,
        notification_type=NotificationType.COMPLIANCE_ALERT.value,
        title=title,
        message="Test message",
        priority=NotificationPriority.HIGH.value,
        notification_metadata={},
    )
    db_session.add(record)
    await db_session.flush()
    return record


async def test_api_list_only_current_user_org(
    client: AsyncClient, db_session, test_user, test_organization, auth_headers
):
    await _seed(db_session, test_organization.id, test_user.id, "Mine")
    db_session.add(
        NotificationRecord(
            organization_id=uuid4(),
            user_id=uuid4(),
            notification_type="compliance_alert",
            title="Not mine",
            message="Other",
            priority="low",
            notification_metadata={},
        )
    )
    await db_session.commit()
    resp = await client.get(BASE, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Mine"


async def test_api_pagination(
    client: AsyncClient, db_session, test_user, test_organization, auth_headers
):
    for i in range(5):
        await _seed(db_session, test_organization.id, test_user.id, f"Alert {i}")
    await db_session.commit()
    resp = await client.get(BASE + "?limit=2&offset=0", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2


async def test_api_mark_read(
    client: AsyncClient, db_session, test_user, test_organization, auth_headers
):
    record = await _seed(db_session, test_organization.id, test_user.id)
    await db_session.commit()
    resp = await client.patch(f"{BASE}/{record.id}/read", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["is_read"] is True
    assert resp.json()["read_at"] is not None


async def test_api_mark_all_read(
    client: AsyncClient, db_session, test_user, test_organization, auth_headers
):
    for _ in range(3):
        await _seed(db_session, test_organization.id, test_user.id)
    await db_session.commit()
    resp = await client.post(f"{BASE}/mark-all-read", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["updated"] == 3
    resp2 = await client.post(f"{BASE}/mark-all-read", headers=auth_headers)
    assert resp2.json()["updated"] == 0


async def test_api_delete(
    client: AsyncClient, db_session, test_user, test_organization, auth_headers
):
    record = await _seed(db_session, test_organization.id, test_user.id)
    await db_session.commit()
    resp = await client.delete(f"{BASE}/{record.id}", headers=auth_headers)
    assert resp.status_code == 204
    resp2 = await client.patch(f"{BASE}/{record.id}/read", headers=auth_headers)
    assert resp2.status_code == 404


async def test_api_unread_count(
    client: AsyncClient, db_session, test_user, test_organization, auth_headers
):
    r1 = await _seed(db_session, test_organization.id, test_user.id)
    await _seed(db_session, test_organization.id, test_user.id)
    await db_session.commit()
    resp = await client.get(f"{BASE}/unread-count", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["unread"] == 2
    await client.patch(f"{BASE}/{r1.id}/read", headers=auth_headers)
    resp2 = await client.get(f"{BASE}/unread-count", headers=auth_headers)
    assert resp2.json()["unread"] == 1
