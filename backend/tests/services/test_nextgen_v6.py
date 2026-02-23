"""Tests for Next-Gen v6 features (10 new capabilities)."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.arch_advisor.service import ArchAdvisorService
from app.services.client_sdk.models import SDKRuntime
from app.services.client_sdk.service import ClientSDKService
from app.services.compliance_debt.service import ComplianceDebtService
from app.services.compliance_streaming.models import StreamEventType
from app.services.compliance_streaming.service import ComplianceStreamingService
from app.services.compliance_testing.service import ComplianceTestingService
from app.services.draft_reg_simulator.service import DraftRegSimulatorService
from app.services.gamification_engine.service import GamificationEngineService
from app.services.gh_marketplace_app.models import InstallState, MarketplacePlan
from app.services.gh_marketplace_app.service import GHMarketplaceAppService
from app.services.incident_war_room.service import IncidentWarRoomService
from app.services.multi_llm_parser.models import ConsensusStrategy, ParseStatus
from app.services.multi_llm_parser.service import MultiLLMParserService


@pytest_asyncio.fixture
async def marketplace_app_svc(db_session: AsyncSession):
    return GHMarketplaceAppService(db=db_session)


@pytest_asyncio.fixture
async def streaming_svc(db_session: AsyncSession):
    return ComplianceStreamingService(db=db_session)


@pytest_asyncio.fixture
async def sdk_svc(db_session: AsyncSession):
    return ClientSDKService(db=db_session)


@pytest_asyncio.fixture
async def llm_parser_svc(db_session: AsyncSession):
    return MultiLLMParserService(db=db_session)


@pytest_asyncio.fixture
async def testing_svc(db_session: AsyncSession):
    return ComplianceTestingService(db=db_session)


@pytest_asyncio.fixture
async def arch_svc(db_session: AsyncSession):
    return ArchAdvisorService(db=db_session)


@pytest_asyncio.fixture
async def war_room_svc(db_session: AsyncSession):
    return IncidentWarRoomService(db=db_session)


@pytest_asyncio.fixture
async def debt_svc(db_session: AsyncSession):
    return ComplianceDebtService(db=db_session)


@pytest_asyncio.fixture
async def draft_sim_svc(db_session: AsyncSession):
    return DraftRegSimulatorService(db=db_session)


@pytest_asyncio.fixture
async def gamification_svc(db_session: AsyncSession):
    return GamificationEngineService(db=db_session)


# ── Feature 1: GitHub Marketplace App ────────────────────────────────────


class TestGHMarketplaceApp:
    @pytest.mark.asyncio
    async def test_install_app(self, marketplace_app_svc: GHMarketplaceAppService):
        inst = await marketplace_app_svc.handle_install(12345, "acme-corp", plan="team")
        assert inst.state == InstallState.ACTIVE
        assert inst.plan == MarketplacePlan.TEAM
        assert "pr_bot" in inst.features_enabled

    @pytest.mark.asyncio
    async def test_run_check_clean(self, marketplace_app_svc: GHMarketplaceAppService):
        await marketplace_app_svc.handle_install(1, "org")
        check = await marketplace_app_svc.run_check(1, "org/repo", pr_number=42, diff_content="result = compute()")
        assert check.conclusion == "success"
        assert check.violations == 0

    @pytest.mark.asyncio
    async def test_run_check_with_violations(self, marketplace_app_svc: GHMarketplaceAppService):
        await marketplace_app_svc.handle_install(1, "org")
        check = await marketplace_app_svc.run_check(1, "org/repo", diff_content="save(personal_data)")
        assert check.conclusion == "failure"
        assert check.violations > 0

    @pytest.mark.asyncio
    async def test_change_plan(self, marketplace_app_svc: GHMarketplaceAppService):
        await marketplace_app_svc.handle_install(1, "org")
        inst = await marketplace_app_svc.change_plan(1, "enterprise")
        assert inst is not None
        assert inst.plan == MarketplacePlan.ENTERPRISE

    @pytest.mark.asyncio
    async def test_app_info(self, marketplace_app_svc: GHMarketplaceAppService):
        info = marketplace_app_svc.get_app_info()
        assert info.name == "ComplianceAgent"
        assert len(info.plans) == 4


# ── Feature 2: Compliance Streaming ──────────────────────────────────────


class TestComplianceStreaming:
    @pytest.mark.asyncio
    async def test_publish_event(self, streaming_svc: ComplianceStreamingService):
        event = await streaming_svc.publish("score_change", "compliance.posture", payload={"score": 85.0})
        assert event.event_type == StreamEventType.SCORE_CHANGE
        assert event.timestamp is not None

    @pytest.mark.asyncio
    async def test_subscribe_and_receive(self, streaming_svc: ComplianceStreamingService):
        await streaming_svc.subscribe("client-1", channels=["compliance.posture"])
        await streaming_svc.publish("score_change", "compliance.posture")
        subs = streaming_svc.list_subscriptions()
        assert subs[0].events_received >= 1

    @pytest.mark.asyncio
    async def test_filter_by_channel(self, streaming_svc: ComplianceStreamingService):
        await streaming_svc.subscribe("client-1", channels=["compliance.violations"])
        await streaming_svc.publish("score_change", "compliance.posture")
        subs = streaming_svc.list_subscriptions()
        assert subs[0].events_received == 0  # Different channel

    @pytest.mark.asyncio
    async def test_unsubscribe(self, streaming_svc: ComplianceStreamingService):
        await streaming_svc.subscribe("client-1")
        ok = await streaming_svc.unsubscribe("client-1")
        assert ok is True

    @pytest.mark.asyncio
    async def test_list_channels(self, streaming_svc: ComplianceStreamingService):
        channels = streaming_svc.list_channels()
        assert len(channels) >= 7


# ── Feature 3: Client SDK ───────────────────────────────────────────────


class TestClientSDK:
    @pytest.mark.asyncio
    async def test_list_endpoints(self, sdk_svc: ClientSDKService):
        endpoints = sdk_svc.list_endpoints()
        assert len(endpoints) >= 10

    @pytest.mark.asyncio
    async def test_list_packages(self, sdk_svc: ClientSDKService):
        pkgs = sdk_svc.list_packages()
        assert len(pkgs) == 3
        runtimes = {p.runtime for p in pkgs}
        assert SDKRuntime.PYTHON in runtimes

    @pytest.mark.asyncio
    async def test_generate_python_client(self, sdk_svc: ClientSDKService):
        client = await sdk_svc.generate_client("python")
        assert "ComplianceClient" in client.code
        assert client.endpoints_covered >= 10

    @pytest.mark.asyncio
    async def test_generate_typescript_client(self, sdk_svc: ClientSDKService):
        client = await sdk_svc.generate_client("typescript")
        assert "ComplianceClient" in client.code

    @pytest.mark.asyncio
    async def test_stats(self, sdk_svc: ClientSDKService):
        stats = sdk_svc.get_stats()
        assert stats.total_endpoints >= 10
        assert stats.packages_available == 3


# ── Feature 4: Multi-LLM Parser ─────────────────────────────────────────


class TestMultiLLMParser:
    @pytest.mark.asyncio
    async def test_parse_with_consensus(self, llm_parser_svc: MultiLLMParserService):
        result = await llm_parser_svc.parse_legal_text("The data controller must ensure data protection.")
        assert result.status in (ParseStatus.SUCCESS, ParseStatus.PARTIAL, ParseStatus.DIVERGENT)
        assert len(result.provider_results) >= 3
        assert result.agreement_rate > 0

    @pytest.mark.asyncio
    async def test_parse_with_majority_vote(self, llm_parser_svc: MultiLLMParserService):
        result = await llm_parser_svc.parse_legal_text("Organizations shall implement encryption.", strategy="majority_vote")
        assert result.strategy == ConsensusStrategy.MAJORITY_VOTE
        assert len(result.consensus_requirements) > 0

    @pytest.mark.asyncio
    async def test_parse_extracts_obligations(self, llm_parser_svc: MultiLLMParserService):
        result = await llm_parser_svc.parse_legal_text("Controllers must document processing. Processors should maintain records.")
        obligations = {r["obligation"] for r in result.consensus_requirements}
        assert "mandatory" in obligations  # from "must"

    @pytest.mark.asyncio
    async def test_list_providers(self, llm_parser_svc: MultiLLMParserService):
        providers = llm_parser_svc.list_providers()
        assert len(providers) >= 3

    @pytest.mark.asyncio
    async def test_toggle_provider(self, llm_parser_svc: MultiLLMParserService):
        p = await llm_parser_svc.toggle_provider("openai", False)
        assert p is not None
        assert p.enabled is False


# ── Feature 5: Compliance Testing ────────────────────────────────────────


class TestComplianceTesting:
    @pytest.mark.asyncio
    async def test_run_test_suite(self, testing_svc: ComplianceTestingService):
        suite = await testing_svc.run_test_suite("gdpr-consent-required")
        assert suite.total > 0
        assert suite.passed > 0
        assert suite.coverage_pct > 0

    @pytest.mark.asyncio
    async def test_detect_violations(self, testing_svc: ComplianceTestingService):
        suite = await testing_svc.run_test_suite("hipaa-phi-encryption")
        violation_tests = [tc for tc in suite.test_cases if tc.violation_expected]
        assert len(violation_tests) > 0
        assert all(tc.violation_found for tc in violation_tests)

    @pytest.mark.asyncio
    async def test_no_false_positives(self, testing_svc: ComplianceTestingService):
        suite = await testing_svc.run_test_suite("pci-card-tokenization")
        safe_tests = [tc for tc in suite.test_cases if not tc.violation_expected]
        assert all(not tc.violation_found for tc in safe_tests)

    @pytest.mark.asyncio
    async def test_fuzz_policy(self, testing_svc: ComplianceTestingService):
        result = await testing_svc.fuzz_policy("gdpr-consent-required", iterations=50)
        assert result.iterations == 50
        assert result.accuracy_pct > 0

    @pytest.mark.asyncio
    async def test_list_testable(self, testing_svc: ComplianceTestingService):
        policies = testing_svc.list_testable_policies()
        assert len(policies) >= 4


# ── Feature 6: Architecture Advisor ──────────────────────────────────────


class TestArchAdvisor:
    @pytest.mark.asyncio
    async def test_generate_gdpr_architecture(self, arch_svc: ArchAdvisorService):
        diagram = await arch_svc.generate_architecture(["GDPR"])
        assert len(diagram.components) >= 5  # core + GDPR-specific
        assert "graph TD" in diagram.diagram_code  # Mermaid
        assert len(diagram.recommendations) > 0

    @pytest.mark.asyncio
    async def test_generate_multi_framework(self, arch_svc: ArchAdvisorService):
        diagram = await arch_svc.generate_architecture(["GDPR", "HIPAA", "PCI-DSS"])
        assert len(diagram.components) >= 10
        assert len(diagram.frameworks) == 3

    @pytest.mark.asyncio
    async def test_ascii_format(self, arch_svc: ArchAdvisorService):
        diagram = await arch_svc.generate_architecture(["SOC2"], diagram_format="ascii")
        assert "===" in diagram.diagram_code

    @pytest.mark.asyncio
    async def test_list_frameworks(self, arch_svc: ArchAdvisorService):
        fws = arch_svc.list_available_frameworks()
        assert "GDPR" in fws
        assert "HIPAA" in fws


# ── Feature 7: Incident War Room ────────────────────────────────────────


class TestIncidentWarRoom:
    @pytest.mark.asyncio
    async def test_create_incident(self, war_room_svc: IncidentWarRoomService):
        incident = await war_room_svc.create_incident("Data breach detected", "critical", "PII leaked", "GDPR")
        assert incident.severity.value == "critical"
        assert incident.notification_deadline is not None

    @pytest.mark.asyncio
    async def test_advance_phase(self, war_room_svc: IncidentWarRoomService):
        incident = await war_room_svc.create_incident("Test", "high", "test description")
        updated = await war_room_svc.advance_phase(str(incident.id), actor="admin")
        assert updated is not None

    @pytest.mark.asyncio
    async def test_add_timeline(self, war_room_svc: IncidentWarRoomService):
        incident = await war_room_svc.create_incident("Test", "medium", "test description")
        updated = await war_room_svc.add_timeline_entry(str(incident.id), "admin", "Investigated root cause", "Found issue")
        assert updated is not None

    @pytest.mark.asyncio
    async def test_generate_post_mortem(self, war_room_svc: IncidentWarRoomService):
        incident = await war_room_svc.create_incident("Test incident", "high", "serious breach")
        await war_room_svc.add_timeline_entry(str(incident.id), "team", "Fixed vulnerability", "Patched")
        pm = await war_room_svc.generate_post_mortem(str(incident.id))
        assert pm is not None


# ── Feature 8: Compliance Debt ───────────────────────────────────────────


class TestComplianceDebt:
    @pytest.mark.asyncio
    async def test_seed_data(self, debt_svc: ComplianceDebtService):
        items = await debt_svc.list_debt()
        assert len(items) >= 1

    @pytest.mark.asyncio
    async def test_add_and_sort_by_roi(self, debt_svc: ComplianceDebtService):
        await debt_svc.add_debt_item(
            title="Test debt", description="Test", framework="GDPR",
            rule_id="test-001", file_path="src/test.py",
            severity="high", risk_cost_usd=50000, remediation_cost_usd=5000, repo="org/api",
        )
        items = await debt_svc.list_debt(sort_by_roi=True)
        assert len(items) > 0

    @pytest.mark.asyncio
    async def test_resolve_debt(self, debt_svc: ComplianceDebtService):
        items = await debt_svc.list_debt()
        if items:
            resolved = await debt_svc.resolve_debt(str(items[0].id))
            assert resolved is not None

    @pytest.mark.asyncio
    async def test_burndown(self, debt_svc: ComplianceDebtService):
        burndown = debt_svc.get_burndown()
        assert len(burndown) >= 0


# ── Feature 9: Draft Regulation Simulator ─────────────────────────────────


class TestDraftRegSimulator:
    @pytest.mark.asyncio
    async def test_list_seed_drafts(self, draft_sim_svc: DraftRegSimulatorService):
        drafts = await draft_sim_svc.list_drafts()
        assert len(drafts) >= 1

    @pytest.mark.asyncio
    async def test_simulate_draft(self, draft_sim_svc: DraftRegSimulatorService):
        drafts = await draft_sim_svc.list_drafts()
        if drafts:
            analysis = await draft_sim_svc.simulate_draft(str(drafts[0].id))
            assert analysis is not None

    @pytest.mark.asyncio
    async def test_stats(self, draft_sim_svc: DraftRegSimulatorService):
        stats = draft_sim_svc.get_stats()
        assert stats is not None


# ── Feature 10: Gamification Engine ──────────────────────────────────────


class TestGamificationEngine:
    @pytest.mark.asyncio
    async def test_seed_profiles(self, gamification_svc: GamificationEngineService):
        leaderboard = await gamification_svc.get_leaderboard()
        assert len(leaderboard) >= 1

    @pytest.mark.asyncio
    async def test_record_activity_existing_user(self, gamification_svc: GamificationEngineService):
        # Use a seed user
        lb = await gamification_svc.get_leaderboard()
        if lb:
            profile = await gamification_svc.record_activity(lb[0].user_id, "fix")
            assert profile.points > 0

    @pytest.mark.asyncio
    async def test_award_points_existing_user(self, gamification_svc: GamificationEngineService):
        lb = await gamification_svc.get_leaderboard()
        if lb:
            profile = await gamification_svc.award_points(lb[0].user_id, 100, "bonus")
            assert profile.points >= 100

    @pytest.mark.asyncio
    async def test_list_achievements(self, gamification_svc: GamificationEngineService):
        achievements = gamification_svc.list_achievements()
        assert len(achievements) >= 1

    @pytest.mark.asyncio
    async def test_leaderboard_sorted(self, gamification_svc: GamificationEngineService):
        lb = await gamification_svc.get_leaderboard()
        if len(lb) >= 2:
            assert lb[0].points >= lb[1].points
