"""Tests for critical persistence models (evidence generation, certification, remediation)."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.critical_persistence import (
    CertControlGapRecord,
    CertificationRunRecord,
    EvidenceGenerationRecord,
    RemediationApprovalRecord,
    RemediationFixRecord,
    RemediationPipelineRecord,
)
from app.models.organization import Organization


pytestmark = pytest.mark.asyncio


async def test_evidence_generation_record_create(
    db_session: AsyncSession,
    test_organization: Organization,
):
    """Can create and retrieve an EvidenceGenerationRecord."""
    record = EvidenceGenerationRecord(
        organization_id=test_organization.id,
        control_id="CC6.1",
        regulation="SOC2",
        evidence_type="screenshot",
        status="pending",
    )
    db_session.add(record)
    await db_session.commit()

    result = await db_session.execute(
        select(EvidenceGenerationRecord).where(EvidenceGenerationRecord.id == record.id)
    )
    fetched = result.scalar_one()
    assert fetched.control_id == "CC6.1"
    assert fetched.regulation == "SOC2"
    assert fetched.status == "pending"


async def test_certification_run_record_create(
    db_session: AsyncSession,
    test_organization: Organization,
):
    """Can create and retrieve a CertificationRunRecord."""
    record = CertificationRunRecord(
        organization_id=test_organization.id,
        regulation="GDPR",
        run_type="automated",
        status="running",
        controls_total=50,
    )
    db_session.add(record)
    await db_session.commit()

    result = await db_session.execute(
        select(CertificationRunRecord).where(CertificationRunRecord.id == record.id)
    )
    fetched = result.scalar_one()
    assert fetched.regulation == "GDPR"
    assert fetched.controls_total == 50


async def test_cert_control_gap_record_create(
    db_session: AsyncSession,
    test_organization: Organization,
):
    """Can create a CertControlGapRecord linked to a CertificationRunRecord."""
    run = CertificationRunRecord(
        organization_id=test_organization.id,
        regulation="SOC2",
        run_type="manual",
        status="completed",
    )
    db_session.add(run)
    await db_session.flush()

    gap = CertControlGapRecord(
        organization_id=test_organization.id,
        run_id=run.id,
        control_id="CC7.2",
        severity="high",
        description="Logging not configured",
    )
    db_session.add(gap)
    await db_session.commit()

    result = await db_session.execute(
        select(CertControlGapRecord).where(CertControlGapRecord.id == gap.id)
    )
    fetched = result.scalar_one()
    assert fetched.severity == "high"
    assert fetched.run_id == run.id


async def test_remediation_pipeline_and_fix_create(
    db_session: AsyncSession,
    test_organization: Organization,
):
    """Can create a RemediationPipelineRecord with associated fix records."""
    pipeline = RemediationPipelineRecord(
        organization_id=test_organization.id,
        trigger_type="scheduled",
        status="running",
    )
    db_session.add(pipeline)
    await db_session.flush()

    fix = RemediationFixRecord(
        organization_id=test_organization.id,
        pipeline_id=pipeline.id,
        control_id="AC-3",
        fix_type="code_patch",
        status="pending",
    )
    db_session.add(fix)
    await db_session.commit()

    result = await db_session.execute(
        select(RemediationFixRecord).where(RemediationFixRecord.id == fix.id)
    )
    fetched = result.scalar_one()
    assert fetched.fix_type == "code_patch"
    assert fetched.pipeline_id == pipeline.id


async def test_remediation_approval_record_create(
    db_session: AsyncSession,
    test_organization: Organization,
    test_user,
):
    """Can create a RemediationApprovalRecord."""
    pipeline = RemediationPipelineRecord(
        organization_id=test_organization.id,
        trigger_type="manual",
        status="pending",
    )
    db_session.add(pipeline)
    await db_session.flush()

    fix = RemediationFixRecord(
        organization_id=test_organization.id,
        pipeline_id=pipeline.id,
        control_id="SC-28",
        fix_type="config_change",
        status="awaiting_approval",
    )
    db_session.add(fix)
    await db_session.flush()

    approval = RemediationApprovalRecord(
        organization_id=test_organization.id,
        fix_id=fix.id,
        reviewer_id=test_user.id,
        decision="approved",
        notes="Looks good",
    )
    db_session.add(approval)
    await db_session.commit()

    result = await db_session.execute(
        select(RemediationApprovalRecord).where(RemediationApprovalRecord.id == approval.id)
    )
    fetched = result.scalar_one()
    assert fetched.decision == "approved"
    assert fetched.reviewer_id == test_user.id
