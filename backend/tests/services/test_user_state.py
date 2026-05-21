"""Tests for user state models (copilot sessions, gamification, workflows)."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.models.user import User
from app.models.user_state import (
    AgentMarketplaceRecord,
    CopilotSessionRecord,
    GamificationEventRecord,
    GamificationProfileRecord,
    TrustAttestationRecord,
    WorkflowDefinitionRecord,
    WorkflowExecutionRecord,
)


pytestmark = pytest.mark.asyncio


async def test_copilot_session_record_create(
    db_session: AsyncSession,
    test_organization: Organization,
    test_user: User,
):
    """Can create and retrieve a CopilotSessionRecord."""
    record = CopilotSessionRecord(
        organization_id=test_organization.id,
        user_id=test_user.id,
        session_type="compliance_query",
        status="active",
    )
    db_session.add(record)
    await db_session.commit()

    result = await db_session.execute(
        select(CopilotSessionRecord).where(CopilotSessionRecord.id == record.id)
    )
    fetched = result.scalar_one()
    assert fetched.session_type == "compliance_query"
    assert fetched.user_id == test_user.id


async def test_agent_marketplace_record_create(
    db_session: AsyncSession,
    test_organization: Organization,
):
    """Can create an AgentMarketplaceRecord."""
    record = AgentMarketplaceRecord(
        organization_id=test_organization.id,
        name="GDPR Compliance Agent",
        description="Automates GDPR compliance checks",
        agent_type="compliance",
        version="1.0.0",
    )
    db_session.add(record)
    await db_session.commit()

    result = await db_session.execute(
        select(AgentMarketplaceRecord).where(AgentMarketplaceRecord.id == record.id)
    )
    fetched = result.scalar_one()
    assert fetched.name == "GDPR Compliance Agent"
    assert fetched.version == "1.0.0"


async def test_trust_attestation_record_create(
    db_session: AsyncSession,
    test_organization: Organization,
    test_user: User,
):
    """Can create a TrustAttestationRecord."""
    record = TrustAttestationRecord(
        organization_id=test_organization.id,
        attested_by=test_user.id,
        attestation_type="annual_review",
        regulation="SOC2",
        status="active",
    )
    db_session.add(record)
    await db_session.commit()

    result = await db_session.execute(
        select(TrustAttestationRecord).where(TrustAttestationRecord.id == record.id)
    )
    fetched = result.scalar_one()
    assert fetched.attestation_type == "annual_review"
    assert fetched.regulation == "SOC2"


async def test_gamification_profile_and_event_create(
    db_session: AsyncSession,
    test_organization: Organization,
    test_user: User,
):
    """Can create GamificationProfileRecord and GamificationEventRecord."""
    profile = GamificationProfileRecord(
        organization_id=test_organization.id,
        user_id=test_user.id,
        level=3,
        xp_total=500,
    )
    db_session.add(profile)
    await db_session.flush()

    event = GamificationEventRecord(
        organization_id=test_organization.id,
        user_id=test_user.id,
        event_type="control_passed",
        xp_awarded=50,
    )
    db_session.add(event)
    await db_session.commit()

    result = await db_session.execute(
        select(GamificationProfileRecord).where(GamificationProfileRecord.id == profile.id)
    )
    fetched = result.scalar_one()
    assert fetched.level == 3
    assert fetched.xp_total == 500


async def test_workflow_definition_and_execution_create(
    db_session: AsyncSession,
    test_organization: Organization,
):
    """Can create WorkflowDefinitionRecord and WorkflowExecutionRecord."""
    defn = WorkflowDefinitionRecord(
        organization_id=test_organization.id,
        name="GDPR Audit Workflow",
        description="Full GDPR audit automation",
        trigger_type="scheduled",
    )
    db_session.add(defn)
    await db_session.flush()

    execution = WorkflowExecutionRecord(
        organization_id=test_organization.id,
        definition_id=defn.id,
        status="running",
        triggered_by="cron",
    )
    db_session.add(execution)
    await db_session.commit()

    result = await db_session.execute(
        select(WorkflowExecutionRecord).where(WorkflowExecutionRecord.id == execution.id)
    )
    fetched = result.scalar_one()
    assert fetched.triggered_by == "cron"
    assert fetched.definition_id == defn.id
