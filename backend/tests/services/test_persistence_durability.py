"""Cross-instance durability tests for persisted services.

Each test creates data via one service instance/session, then reads it via another,
proving that state survives across service instances. Also validates tenant isolation,
invalid-transition rejection, and tamper detection.
"""

import json
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.organization import Organization
from app.models.user import User


pytestmark = pytest.mark.asyncio


# ── Helpers ──────────────────────────────────────────────────────────────


def _other_session(async_engine) -> async_sessionmaker[AsyncSession]:
    """Create a *separate* session factory to simulate a different service instance."""
    return async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )


# ── 1. Evidence Generation ──────────────────────────────────────────────


async def test_evidence_generation_cross_instance(
    async_engine,
    db_session: AsyncSession,
    test_organization: Organization,
):
    """Package generated in session A is readable from session B."""
    from app.services.evidence_generation.service import EvidenceGenerationService

    svc_a = EvidenceGenerationService(db=db_session, organization_id=test_organization.id)
    pkg = await svc_a.generate_evidence_package("soc2")
    await db_session.commit()

    factory = _other_session(async_engine)
    async with factory() as session_b:
        svc_b = EvidenceGenerationService(db=session_b, organization_id=test_organization.id)
        pkg_b = await svc_b.get_package("soc2")
        assert pkg_b is not None
        assert pkg_b.controls_total == pkg.controls_total
        assert len(pkg_b.items) > 0


async def test_evidence_generation_tenant_isolation(
    async_engine,
    db_session: AsyncSession,
    test_organization: Organization,
):
    """Evidence from org A is not visible to org B."""
    from app.services.evidence_generation.service import EvidenceGenerationService

    other_org_id = uuid4()
    svc_a = EvidenceGenerationService(db=db_session, organization_id=test_organization.id)
    await svc_a.generate_evidence_package("soc2")
    await db_session.commit()

    factory = _other_session(async_engine)
    async with factory() as session_b:
        svc_b = EvidenceGenerationService(db=session_b, organization_id=other_org_id)
        pkg = await svc_b.get_package("soc2")
        assert pkg is None


# ── 2. Cert Pipeline ────────────────────────────────────────────────────


async def test_cert_pipeline_cross_instance(
    async_engine,
    db_session: AsyncSession,
    test_organization: Organization,
):
    from app.services.cert_pipeline.service import CertPipelineService

    svc_a = CertPipelineService(db=db_session, organization_id=test_organization.id)
    run = await svc_a.start_certification("soc2_type2")
    await db_session.commit()

    factory = _other_session(async_engine)
    async with factory() as session_b:
        svc_b = CertPipelineService(db=session_b, organization_id=test_organization.id)
        fetched = await svc_b.get_run(str(run.id))
        assert fetched is not None
        assert fetched.total_controls == run.total_controls
        gaps = await svc_b.get_gaps(run_id=str(run.id))
        assert len(gaps) > 0


async def test_cert_pipeline_tenant_isolation(
    async_engine,
    db_session: AsyncSession,
    test_organization: Organization,
):
    from app.services.cert_pipeline.service import CertPipelineService

    svc = CertPipelineService(db=db_session, organization_id=test_organization.id)
    await svc.start_certification("soc2_type2")
    await db_session.commit()

    factory = _other_session(async_engine)
    async with factory() as session_b:
        svc_b = CertPipelineService(db=session_b, organization_id=uuid4())
        runs = await svc_b.list_runs()
        assert len(runs) == 0


# ── 3. Auto-Remediation ─────────────────────────────────────────────────


async def test_auto_remediation_cross_instance(
    async_engine,
    db_session: AsyncSession,
    test_organization: Organization,
):
    from app.services.auto_remediation.service import AutoRemediationService

    svc_a = AutoRemediationService(db=db_session, organization_id=test_organization.id)
    pipeline = await svc_a.trigger_pipeline(
        repo="test/repo",
        violations=[{"severity": "low", "rule_id": "R1", "file_path": "a.py", "message": "m"}],
    )
    await db_session.commit()

    factory = _other_session(async_engine)
    async with factory() as session_b:
        svc_b = AutoRemediationService(db=session_b, organization_id=test_organization.id)
        fetched = await svc_b.get_pipeline(str(pipeline.id))
        assert fetched is not None
        fixes = await svc_b.get_fixes(pipeline.id)
        assert len(fixes) > 0


async def test_auto_remediation_invalid_transition(
    db_session: AsyncSession,
    test_organization: Organization,
):
    from app.services.auto_remediation.service import AutoRemediationService

    svc = AutoRemediationService(db=db_session, organization_id=test_organization.id)
    pipeline = await svc.trigger_pipeline(repo="test/repo", violations=[])
    await db_session.flush()

    # Pipeline is already in pr_created or similar terminal state for low-risk,
    # trying to approve should raise or return error
    if pipeline.status.value == "pr_created":
        with pytest.raises(ValueError):
            await svc.approve_pipeline(pipeline.id, "user1")


# ── 4. Compliance Copilot ───────────────────────────────────────────────


async def test_compliance_copilot_cross_instance(
    async_engine,
    db_session: AsyncSession,
    test_organization: Organization,
):
    from app.services.compliance_copilot.service import ComplianceCopilotService

    shared_user_id = uuid4()
    svc_a = ComplianceCopilotService(
        db=db_session, organization_id=test_organization.id, user_id=shared_user_id
    )
    session = await svc_a.start_session("test/repo")
    await db_session.commit()

    factory = _other_session(async_engine)
    async with factory() as session_b:
        svc_b = ComplianceCopilotService(
            db=session_b, organization_id=test_organization.id, user_id=shared_user_id
        )
        fetched = await svc_b.get_session(str(session.id))
        assert fetched is not None
        assert fetched.repo == "test/repo"


# ── 5. Agents Marketplace ───────────────────────────────────────────────


async def test_agents_marketplace_install_cross_instance(
    async_engine,
    db_session: AsyncSession,
    test_organization: Organization,
):
    from app.services.agents_marketplace.service import AgentsMarketplaceService

    svc_a = AgentsMarketplaceService(db=db_session, organization_id=test_organization.id)
    install = await svc_a.install_agent(
        slug="gdpr-data-flow-scanner",
        organization_id=str(test_organization.id),
    )
    assert install is not None
    await db_session.commit()

    factory = _other_session(async_engine)
    async with factory() as session_b:
        svc_b = AgentsMarketplaceService(db=session_b, organization_id=test_organization.id)
        installs = await svc_b.list_installations(str(test_organization.id))
        assert len(installs) >= 1


# ── 6. Trust Network (integrity hash) ───────────────────────────────────


async def test_trust_network_cross_instance(
    async_engine,
    db_session: AsyncSession,
    test_organization: Organization,
):
    from app.services.trust_network.service import TrustNetworkService

    svc_a = TrustNetworkService(
        db=db_session, organization_id=test_organization.id, user_id=uuid4()
    )
    att = await svc_a.create_attestation(
        org_name="TestCo",
        attestation_type="soc2_compliant",
        framework="SOC2",
        score=95.0,
    )
    await db_session.commit()

    factory = _other_session(async_engine)
    async with factory() as session_b:
        svc_b = TrustNetworkService(
            db=session_b, organization_id=test_organization.id, user_id=uuid4()
        )
        result = await svc_b.verify_attestation(att.id)
        assert result.is_valid


async def test_trust_network_tamper_detection(
    db_session: AsyncSession,
    test_organization: Organization,
):
    """Modifying the stored hash should trigger tamper detection."""
    from sqlalchemy import select

    from app.models.user_state import TrustAttestationRecord
    from app.services.trust_network.service import TrustNetworkService

    user_id = uuid4()
    svc = TrustNetworkService(db=db_session, organization_id=test_organization.id, user_id=user_id)
    att = await svc.create_attestation(
        org_name="TamperCo",
        attestation_type="gdpr_compliant",
        framework="GDPR",
        score=80.0,
    )
    await db_session.flush()

    # Tamper: modify the stored notes (which contain the merkle_root)
    stmt = select(TrustAttestationRecord).where(TrustAttestationRecord.id == att.id)
    result = await db_session.execute(stmt)
    rec = result.scalar_one()
    notes_data = json.loads(rec.notes) if rec.notes else {}
    notes_data["merkle_root"] = "tampered_hash_value"
    rec.notes = json.dumps(notes_data)
    await db_session.flush()

    # Verification should now detect tamper
    result = await svc.verify_attestation(att.id)
    assert not result.is_valid
    assert "mismatch" in result.message.lower() or "tamper" in result.message.lower()


# ── 7. Gamification Engine (transaction-safe) ───────────────────────────


async def test_gamification_cross_instance(
    async_engine,
    db_session: AsyncSession,
    test_organization: Organization,
    test_user: User,
):
    from app.services.gamification_engine.service import GamificationEngineService

    svc_a = GamificationEngineService(
        db=db_session, organization_id=test_organization.id, user_id=test_user.id
    )
    # Create profile first
    from app.models.user_state import GamificationProfileRecord

    profile_rec = GamificationProfileRecord(
        organization_id=test_organization.id,
        user_id=test_user.id,
        level=1,
        xp_total=0,
        badges=[],
        streak_days=0,
        profile_metadata={"display_name": "Test", "fixes_count": 0, "violations_resolved": 0},
    )
    db_session.add(profile_rec)
    await db_session.flush()

    profile = await svc_a.award_points(str(test_user.id), 100, "test award")
    assert profile.points >= 100
    await db_session.commit()

    factory = _other_session(async_engine)
    async with factory() as session_b:
        svc_b = GamificationEngineService(
            db=session_b, organization_id=test_organization.id, user_id=test_user.id
        )
        fetched = await svc_b.get_profile(str(test_user.id))
        assert fetched.points >= 100


# ── 8. Workflow Automation ───────────────────────────────────────────────


async def test_workflow_automation_cross_instance(
    async_engine,
    db_session: AsyncSession,
    test_organization: Organization,
):
    from app.services.workflow_automation.service import WorkflowAutomationService

    svc_a = WorkflowAutomationService(db=db_session, organization_id=test_organization.id)
    wf = await svc_a.create_workflow(
        name="Test WF",
        description="A test workflow",
        trigger_type="manual",
        actions=[{"type": "notify_slack"}],
    )
    await db_session.commit()

    factory = _other_session(async_engine)
    async with factory() as session_b:
        svc_b = WorkflowAutomationService(db=session_b, organization_id=test_organization.id)
        fetched = await svc_b.get_workflow(str(wf.id))
        assert fetched is not None
        assert fetched.name == "Test WF"


async def test_workflow_execution_persists(
    async_engine,
    db_session: AsyncSession,
    test_organization: Organization,
):
    from app.services.workflow_automation.service import WorkflowAutomationService

    svc = WorkflowAutomationService(db=db_session, organization_id=test_organization.id)
    wf = await svc.create_workflow(name="Exec WF", trigger_type="manual")
    await svc.execute_workflow(str(wf.id))
    await db_session.commit()

    factory = _other_session(async_engine)
    async with factory() as session_b:
        svc_b = WorkflowAutomationService(db=session_b, organization_id=test_organization.id)
        execs = await svc_b.list_executions(str(wf.id))
        assert len(execs) >= 1


# ── 9. Drift Detection ──────────────────────────────────────────────────


async def test_drift_detection_cross_instance(
    async_engine,
    db_session: AsyncSession,
    test_organization: Organization,
):
    from app.services.drift_detection.service import DriftDetectionService

    svc_a = DriftDetectionService(db=db_session, organization_id=test_organization.id)
    await svc_a.capture_baseline("test/repo", "main", "abc123")
    await db_session.commit()

    factory = _other_session(async_engine)
    async with factory() as session_b:
        svc_b = DriftDetectionService(db=session_b, organization_id=test_organization.id)
        fetched = await svc_b.get_baseline("test/repo", "main")
        assert fetched is not None


async def test_drift_events_persist(
    async_engine,
    db_session: AsyncSession,
    test_organization: Organization,
):
    from app.services.drift_detection.service import DriftDetectionService

    svc = DriftDetectionService(db=db_session, organization_id=test_organization.id)
    await svc.capture_baseline("test/repo", "main", "abc123")
    await svc.detect_drift(
        repo="test/repo",
        branch="main",
        current_score=70.0,
        current_findings=[{"severity": "high", "description": "test drift"}],
    )
    await db_session.commit()

    factory = _other_session(async_engine)
    async with factory() as session_b:
        svc_b = DriftDetectionService(db=session_b, organization_id=test_organization.id)
        listed = await svc_b.list_events(repo="test/repo")
        assert len(listed) >= 1


# ── 10. Posture Scoring ─────────────────────────────────────────────────


async def test_posture_scoring_cross_instance(
    async_engine,
    db_session: AsyncSession,
    test_organization: Organization,
):
    from app.services.posture_scoring.service import PostureScoringService

    svc_a = PostureScoringService(db=db_session, organization_id=test_organization.id)
    score = await svc_a.compute_score(industry="saas")
    await db_session.commit()

    factory = _other_session(async_engine)
    async with factory() as session_b:
        svc_b = PostureScoringService(db=session_b, organization_id=test_organization.id)
        history = await svc_b.get_history()
        assert len(history) >= 1
        assert history[0].overall_score == score.overall_score


# ── 11. Evidence Vault ───────────────────────────────────────────────────


async def test_evidence_vault_cross_instance(
    async_engine,
    db_session: AsyncSession,
    test_organization: Organization,
):
    from app.services.evidence_vault.models import ControlFramework, EvidenceType
    from app.services.evidence_vault.service import EvidenceVaultService

    svc_a = EvidenceVaultService(db=db_session, organization_id=test_organization.id)
    await svc_a.store_evidence(
        evidence_type=EvidenceType.SCAN_RESULT,
        title="Test Evidence",
        description="Test description",
        content="test content hash input",
        framework=ControlFramework.SOC2,
        control_id="CC6.1",
        control_name="Access Security",
        source="test",
    )
    await db_session.commit()

    factory = _other_session(async_engine)
    async with factory() as session_b:
        svc_b = EvidenceVaultService(db=session_b, organization_id=test_organization.id)
        items = await svc_b.get_evidence(framework=ControlFramework.SOC2)
        assert len(items) >= 1
        assert items[0].control_id == "CC6.1"


async def test_evidence_vault_chain_verification(
    db_session: AsyncSession,
    test_organization: Organization,
):
    from app.services.evidence_vault.models import ControlFramework, EvidenceType
    from app.services.evidence_vault.service import EvidenceVaultService

    svc = EvidenceVaultService(db=db_session, organization_id=test_organization.id)
    await svc.store_evidence(
        evidence_type=EvidenceType.SCAN_RESULT,
        title="Chain Item 1",
        description="First in chain",
        content="content_1",
        framework=ControlFramework.SOC2,
        control_id="CC6.1",
    )
    await svc.store_evidence(
        evidence_type=EvidenceType.AUDIT_LOG,
        title="Chain Item 2",
        description="Second in chain",
        content="content_2",
        framework=ControlFramework.SOC2,
        control_id="CC6.1",
    )
    await db_session.flush()

    is_valid = await svc.verify_chain(ControlFramework.SOC2)
    assert is_valid


# ── 12. Self-Healing Mesh ────────────────────────────────────────────────


async def test_self_healing_cross_instance(
    async_engine,
    db_session: AsyncSession,
    test_organization: Organization,
):
    from app.services.self_healing_mesh.models import EventType, HealingEvent
    from app.services.self_healing_mesh.service import SelfHealingMeshService

    svc_a = SelfHealingMeshService(db=db_session, organization_id=test_organization.id)
    event = HealingEvent(
        event_type=EventType.VIOLATION_DETECTED,
        source_service="test",
        repo="test/repo",
        severity="low",
        description="Test violation",
    )
    pipeline = await svc_a.ingest_event(event)
    await db_session.commit()

    factory = _other_session(async_engine)
    async with factory() as session_b:
        svc_b = SelfHealingMeshService(db=session_b, organization_id=test_organization.id)
        fetched = await svc_b.get_pipeline(str(pipeline.id))
        assert fetched is not None


# ── 13. MCP Execution History ────────────────────────────────────────────


async def test_mcp_execution_cross_instance(
    async_engine,
    db_session: AsyncSession,
    test_organization: Organization,
):
    from app.services.mcp_server.service import MCPServerService

    svc_a = MCPServerService(db=db_session, organization_id=test_organization.id)
    await svc_a.execute_tool(
        tool_name="compliance/get_posture",
        params={"repo": "test/repo"},
        client_id="test-client",
    )
    await db_session.commit()

    factory = _other_session(async_engine)
    async with factory() as session_b:
        svc_b = MCPServerService(db=session_b, organization_id=test_organization.id)
        history = await svc_b.get_execution_history()
        assert len(history) >= 1
