"""Tests for secondary persistence models (drift, posture, evidence vault, MCP)."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.models.secondary_persistence import (
    DriftAlertRecord,
    DriftBaselineRecord,
    DriftEventRecord,
    EvidenceVaultRecord,
    MCPExecutionRecord,
    PostureScoreRecord,
    SelfHealingEventRecord,
)


pytestmark = pytest.mark.asyncio


async def test_drift_baseline_record_create(
    db_session: AsyncSession,
    test_organization: Organization,
):
    """Can create and retrieve a DriftBaselineRecord."""
    record = DriftBaselineRecord(
        organization_id=test_organization.id,
        regulation="SOC2",
        snapshot={"controls": ["CC6.1", "CC6.2"]},
        hash_value="abc123" * 10 + "abcd",
    )
    db_session.add(record)
    await db_session.commit()

    result = await db_session.execute(
        select(DriftBaselineRecord).where(DriftBaselineRecord.id == record.id)
    )
    fetched = result.scalar_one()
    assert fetched.regulation == "SOC2"
    assert fetched.is_active is True


async def test_drift_event_and_alert_create(
    db_session: AsyncSession,
    test_organization: Organization,
):
    """Can create DriftEventRecord and DriftAlertRecord linked together."""
    baseline = DriftBaselineRecord(
        organization_id=test_organization.id,
        regulation="GDPR",
        snapshot={},
        hash_value="x" * 64,
    )
    db_session.add(baseline)
    await db_session.flush()

    event = DriftEventRecord(
        organization_id=test_organization.id,
        baseline_id=baseline.id,
        drift_type="control_regression",
        severity="high",
        description="CC6.1 no longer passing",
    )
    db_session.add(event)
    await db_session.flush()

    alert = DriftAlertRecord(
        organization_id=test_organization.id,
        drift_event_id=event.id,
        status="open",
    )
    db_session.add(alert)
    await db_session.commit()

    result = await db_session.execute(
        select(DriftAlertRecord).where(DriftAlertRecord.id == alert.id)
    )
    fetched = result.scalar_one()
    assert fetched.status == "open"
    assert fetched.drift_event_id == event.id


async def test_posture_score_record_create(
    db_session: AsyncSession,
    test_organization: Organization,
):
    """Can create a PostureScoreRecord."""
    record = PostureScoreRecord(
        organization_id=test_organization.id,
        regulation="SOC2",
        score=87.5,
        grade="B+",
        controls_passing=35,
        controls_total=40,
    )
    db_session.add(record)
    await db_session.commit()

    result = await db_session.execute(
        select(PostureScoreRecord).where(PostureScoreRecord.id == record.id)
    )
    fetched = result.scalar_one()
    assert fetched.score == pytest.approx(87.5)
    assert fetched.grade == "B+"


async def test_evidence_vault_record_create(
    db_session: AsyncSession,
    test_organization: Organization,
):
    """Can create an EvidenceVaultRecord."""
    record = EvidenceVaultRecord(
        organization_id=test_organization.id,
        control_id="CC6.1",
        regulation="SOC2",
        evidence_type="audit_log",
        artifact_url="s3://evidence-bucket/cc61/audit_log.json",
        hash_sha256="a" * 64,
        collected_by="AutoCollector",
    )
    db_session.add(record)
    await db_session.commit()

    result = await db_session.execute(
        select(EvidenceVaultRecord).where(EvidenceVaultRecord.id == record.id)
    )
    fetched = result.scalar_one()
    assert fetched.evidence_type == "audit_log"
    assert fetched.collected_by == "AutoCollector"


async def test_self_healing_event_record_create(
    db_session: AsyncSession,
    test_organization: Organization,
):
    """Can create a SelfHealingEventRecord."""
    record = SelfHealingEventRecord(
        organization_id=test_organization.id,
        trigger_type="drift_detection",
        action_taken="reapply_config",
        status="completed",
        description="Re-applied encryption settings after drift detected",
    )
    db_session.add(record)
    await db_session.commit()

    result = await db_session.execute(
        select(SelfHealingEventRecord).where(SelfHealingEventRecord.id == record.id)
    )
    fetched = result.scalar_one()
    assert fetched.action_taken == "reapply_config"


async def test_mcp_execution_record_create(
    db_session: AsyncSession,
    test_organization: Organization,
):
    """Can create an MCPExecutionRecord."""
    record = MCPExecutionRecord(
        organization_id=test_organization.id,
        tool_name="check_gdpr_compliance",
        input_params={"regulation": "GDPR", "scope": "all"},
        output_result={"compliant": True, "score": 92},
        status="completed",
        duration_ms=450,
    )
    db_session.add(record)
    await db_session.commit()

    result = await db_session.execute(
        select(MCPExecutionRecord).where(MCPExecutionRecord.id == record.id)
    )
    fetched = result.scalar_one()
    assert fetched.tool_name == "check_gdpr_compliance"
    assert fetched.duration_ms == 450
