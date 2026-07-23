"""HTTP contract tests for durable IDE learning features."""

import hashlib
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient

from app.models import APIKeyRecord, IDERuleEventRecord, Organization, User


pytestmark = pytest.mark.asyncio


async def test_team_suppression_lifecycle_is_persistent(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    created = await client.post(
        "/api/v1/ide/suppressions",
        headers=auth_headers,
        json={
            "rule_id": "GDPR-PII-001",
            "pattern": "tests/.*\\.py",
            "reason": "Approved test fixture data",
        },
    )
    assert created.status_code == 201
    suppression_id = created.json()["id"]
    assert created.json()["approved"] is False

    listed = await client.get("/api/v1/ide/suppressions", headers=auth_headers)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [suppression_id]

    approved = await client.put(
        f"/api/v1/ide/suppressions/{suppression_id}/approve",
        headers=auth_headers,
    )
    assert approved.status_code == 200
    assert approved.json()["approved"] is True
    assert approved.json()["approved_by"]

    used = await client.post(
        f"/api/v1/ide/suppressions/{suppression_id}/usage",
        headers=auth_headers,
    )
    assert used.status_code == 200
    assert used.json()["usage_count"] == 1

    deleted = await client.delete(
        f"/api/v1/ide/suppressions/{suppression_id}",
        headers=auth_headers,
    )
    assert deleted.status_code == 200
    assert deleted.json() == {"status": "deleted"}

    listed_after_delete = await client.get(
        "/api/v1/ide/suppressions",
        headers=auth_headers,
    )
    assert listed_after_delete.status_code == 200
    assert listed_after_delete.json() == []


async def test_team_suppression_rejects_invalid_regex(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await client.post(
        "/api/v1/ide/suppressions",
        headers=auth_headers,
        json={
            "rule_id": "GDPR-PII-001",
            "pattern": "[invalid",
            "reason": "Invalid regex",
        },
    )
    assert response.status_code == 422


async def test_feedback_updates_durable_rule_statistics(
    client: AsyncClient,
    auth_headers: dict[str, str],
    db_session,
    test_organization: Organization,
    test_user: User,
) -> None:
    db_session.add(
        IDERuleEventRecord(
            organization_id=test_organization.id,
            user_id=test_user.id,
            rule_id="GDPR-PII-001",
            event_type="detection",
            file_path="file:///src/users.py",
            event_metadata={
                "severity": "warning",
                "line": 10,
                "detected_at": datetime.now(UTC).isoformat(),
            },
        )
    )
    await db_session.flush()

    feedback = await client.post(
        "/api/v1/ide/feedback",
        headers=auth_headers,
        json={
            "type": "false_positive",
            "user_action": "suppressed",
            "issue": {
                "requirementId": "GDPR-PII-001",
                "file": "src/users.py",
                "line": 10,
            },
            "context": {"file": "src/users.py", "language": "python"},
            "reason": "Synthetic fixture data",
        },
    )
    assert feedback.status_code == 200

    batch = await client.post(
        "/api/v1/ide/feedback/batch",
        headers=auth_headers,
        json={
            "items": [
                {
                    "type": "helpful",
                    "user_action": "fixed",
                    "issue": {"requirementId": "GDPR-PII-001"},
                    "time_to_fix_minutes": 12.0,
                }
            ]
        },
    )
    assert batch.status_code == 200
    assert batch.json() == {"status": "received", "accepted": 1}

    stats = await client.get(
        "/api/v1/ide/stats/rules/GDPR-PII-001",
        headers=auth_headers,
    )
    assert stats.status_code == 200
    assert stats.json() == {
        "rule_id": "GDPR-PII-001",
        "total_detections": 1,
        "false_positive_rate": 1.0,
        "fix_rate": 1.0,
        "suppression_rate": 1.0,
        "avg_time_to_fix_minutes": 12.0,
    }


async def test_api_key_resolves_organization_for_ide_endpoints(
    client: AsyncClient,
    db_session,
    test_organization: Organization,
    test_user: User,
) -> None:
    raw_key = "ca_extension_test_key"
    db_session.add(
        APIKeyRecord(
            key_prefix=raw_key[:10],
            key_hash=hashlib.sha256(raw_key.encode()).hexdigest(),
            name="VS Code extension",
            organization_id=test_organization.id,
            created_by=test_user.id,
            status="active",
            scopes=["read:compliance", "write:compliance"],
        )
    )
    await db_session.commit()
    headers = {"X-API-Key": raw_key}

    listed = await client.get("/api/v1/ide/suppressions", headers=headers)
    assert listed.status_code == 200
    assert listed.json() == []

    feedback = await client.post(
        "/api/v1/ide/feedback",
        headers=headers,
        json={
            "type": "helpful",
            "user_action": "fixed",
            "issue": {"requirementId": "SOC2-CRED-001"},
        },
    )
    assert feedback.status_code == 200
