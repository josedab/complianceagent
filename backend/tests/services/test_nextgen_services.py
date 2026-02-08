"""Service-level tests for Next-Gen Strategic Features."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.benchmarking import BenchmarkingService
from app.services.pr_copilot import PRCopilotService, SuggestionAction, SuggestionFeedback
from app.services.industry_packs import IndustryPacksService, IndustryVertical
from app.services.drift_detection import DriftDetectionService
from app.services.multi_llm import MultiLLMService, ConsensusStrategy
from app.services.evidence_vault import EvidenceVaultService, ControlFramework, EvidenceType
from app.services.public_api import PublicAPIService, APIKeyScope, RateLimitTier
from app.services.impact_simulator import ImpactSimulatorService, RegulatoryChange, ScenarioType
from app.services.marketplace_app import MarketplaceAppService, AppPlatform, WebhookEvent


class TestBenchmarkingService:
    """Tests for the BenchmarkingService."""

    @pytest.mark.asyncio
    async def test_list_corpora(self, db_session):
        service = BenchmarkingService(db=db_session)
        corpora = await service.list_corpora()
        assert len(corpora) >= 1
        assert corpora[0].framework == "gdpr"

    @pytest.mark.asyncio
    async def test_run_benchmark(self, db_session):
        service = BenchmarkingService(db=db_session)
        result = await service.run_benchmark(framework="gdpr")
        assert result.status.value == "completed"
        assert result.total_passages > 0
        assert result.overall_f1 > 0

    @pytest.mark.asyncio
    async def test_get_scorecard(self, db_session):
        service = BenchmarkingService(db=db_session)
        await service.run_benchmark(framework="gdpr")
        scorecard = await service.get_scorecard()
        assert scorecard is not None
        assert "overall" in scorecard
        assert "frameworks" in scorecard


class TestPRCopilotService:
    """Tests for the PRCopilotService."""

    @pytest.mark.asyncio
    async def test_analyze_pr_with_findings(self, db_session):
        service = PRCopilotService(db=db_session)
        result = await service.analyze_pr(
            repo="test/repo",
            pr_number=1,
            diff="+ email = request.form['email']\n+ log(user.ssn)",
            files_changed=["src/users.py"],
        )
        assert result.status.value == "completed"
        assert len(result.findings) > 0
        assert result.risk_level in ("none", "low", "medium", "high", "critical")

    @pytest.mark.asyncio
    async def test_analyze_pr_clean(self, db_session):
        service = PRCopilotService(db=db_session)
        result = await service.analyze_pr(
            repo="test/repo",
            pr_number=2,
            diff="+ x = 1 + 2",
            files_changed=["src/math.py"],
        )
        assert result.status.value == "completed"

    @pytest.mark.asyncio
    async def test_submit_feedback(self, db_session):
        service = PRCopilotService(db=db_session)
        feedback = SuggestionFeedback(action=SuggestionAction.ACCEPTED, reason="Good suggestion")
        result = await service.submit_feedback(feedback)
        assert result.action == SuggestionAction.ACCEPTED

    @pytest.mark.asyncio
    async def test_learning_stats(self, db_session):
        service = PRCopilotService(db=db_session)
        stats = await service.get_learning_stats()
        assert stats.total_suggestions == 0


class TestIndustryPacksService:
    """Tests for the IndustryPacksService."""

    @pytest.mark.asyncio
    async def test_list_packs(self, db_session):
        service = IndustryPacksService(db=db_session)
        packs = await service.list_packs()
        assert len(packs) >= 4

    @pytest.mark.asyncio
    async def test_get_fintech_pack(self, db_session):
        service = IndustryPacksService(db=db_session)
        pack = await service.get_pack(IndustryVertical.FINTECH)
        assert pack is not None
        assert pack.name == "Fintech Compliance Pack"
        assert len(pack.regulations) >= 4

    @pytest.mark.asyncio
    async def test_provision_pack(self, db_session):
        service = IndustryPacksService(db=db_session)
        result = await service.provision_pack(IndustryVertical.HEALTHTECH)
        assert result.regulations_activated > 0
        assert result.policies_created > 0
        assert len(result.next_steps) > 0


class TestDriftDetectionService:
    """Tests for the DriftDetectionService."""

    @pytest.mark.asyncio
    async def test_capture_baseline(self, db_session):
        service = DriftDetectionService(db=db_session)
        baseline = await service.capture_baseline("test/repo")
        assert baseline.repo == "test/repo"
        assert baseline.score == 100.0

    @pytest.mark.asyncio
    async def test_detect_drift_with_regression(self, db_session):
        service = DriftDetectionService(db=db_session)
        await service.capture_baseline("test/repo")
        events = await service.detect_drift("test/repo", current_score=70.0)
        assert len(events) > 0
        assert events[0].drift_type.value == "regression"

    @pytest.mark.asyncio
    async def test_detect_no_drift(self, db_session):
        service = DriftDetectionService(db=db_session)
        await service.capture_baseline("test/repo")
        events = await service.detect_drift("test/repo", current_score=98.0)
        assert len(events) == 0


class TestMultiLLMService:
    """Tests for the MultiLLMService."""

    @pytest.mark.asyncio
    async def test_parse_without_copilot(self, db_session):
        service = MultiLLMService(db=db_session)
        result = await service.parse_regulation(
            text="The controller shall process data lawfully.",
            framework="gdpr",
        )
        assert result.status.value in ("completed", "divergent")

    @pytest.mark.asyncio
    async def test_parse_with_mock_copilot(self, db_session, mock_copilot_client):
        service = MultiLLMService(db=db_session, copilot_client=mock_copilot_client)
        result = await service.parse_regulation(
            text="The controller shall process data lawfully.",
        )
        assert result.status.value in ("completed", "divergent")
        assert len(result.obligations) > 0

    @pytest.mark.asyncio
    async def test_list_providers(self, db_session):
        service = MultiLLMService(db=db_session)
        providers = await service.list_providers()
        assert len(providers) >= 1


class TestEvidenceVaultService:
    """Tests for the EvidenceVaultService."""

    @pytest.mark.asyncio
    async def test_store_and_query_evidence(self, db_session):
        service = EvidenceVaultService(db=db_session)
        item = await service.store_evidence(
            evidence_type=EvidenceType.SCAN_RESULT,
            title="Test Scan",
            description="Test scan result",
            content="All clear",
            framework=ControlFramework.SOC2,
            control_id="CC6.1",
        )
        assert item.content_hash != ""
        items = await service.get_evidence(framework=ControlFramework.SOC2)
        assert len(items) >= 1

    @pytest.mark.asyncio
    async def test_verify_chain(self, db_session):
        service = EvidenceVaultService(db=db_session)
        await service.store_evidence(
            evidence_type=EvidenceType.SCAN_RESULT, title="E1", description="",
            content="content1", framework=ControlFramework.SOC2, control_id="CC6.1",
        )
        await service.store_evidence(
            evidence_type=EvidenceType.SCAN_RESULT, title="E2", description="",
            content="content2", framework=ControlFramework.SOC2, control_id="CC6.2",
        )
        verified = await service.verify_chain(ControlFramework.SOC2)
        assert verified is True

    @pytest.mark.asyncio
    async def test_create_auditor_session(self, db_session):
        service = EvidenceVaultService(db=db_session)
        session = await service.create_auditor_session(
            auditor_email="auditor@firm.com",
            auditor_name="Jane Auditor",
        )
        assert session.is_active is True
        assert session.auditor_email == "auditor@firm.com"

    @pytest.mark.asyncio
    async def test_generate_report(self, db_session):
        service = EvidenceVaultService(db=db_session)
        report = await service.generate_report(ControlFramework.SOC2)
        assert report.total_controls > 0


class TestPublicAPIService:
    """Tests for the PublicAPIService."""

    @pytest.mark.asyncio
    async def test_create_and_validate_key(self, db_session):
        service = PublicAPIService(db=db_session)
        key, raw = await service.create_api_key(name="test-key")
        assert raw.startswith("ca_")
        validated = await service.validate_key(raw)
        assert validated is not None
        assert validated.name == "test-key"

    @pytest.mark.asyncio
    async def test_revoke_key(self, db_session):
        service = PublicAPIService(db=db_session)
        key, raw = await service.create_api_key(name="revoke-test")
        await service.revoke_key(key.id)
        validated = await service.validate_key(raw)
        assert validated is None

    @pytest.mark.asyncio
    async def test_list_sdks(self, db_session):
        service = PublicAPIService(db=db_session)
        sdks = await service.list_sdks()
        assert len(sdks) >= 3
        languages = {s.language for s in sdks}
        assert "python" in languages
        assert "typescript" in languages


class TestImpactSimulatorService:
    """Tests for the ImpactSimulatorService."""

    @pytest.mark.asyncio
    async def test_run_simulation(self, db_session):
        service = ImpactSimulatorService(db=db_session)
        change = RegulatoryChange(
            regulation="gdpr",
            article_ref="Art. 17",
            change_description="24h deletion requirement",
            scenario_type=ScenarioType.REGULATION_CHANGE,
            new_requirements=["24h deletion"],
        )
        result = await service.run_simulation("Test Scenario", change)
        assert result.status.value == "completed"
        assert result.blast_radius.total_files > 0
        assert result.risk_score > 0

    @pytest.mark.asyncio
    async def test_run_prebuilt_scenario(self, db_session):
        service = ImpactSimulatorService(db=db_session)
        result = await service.run_prebuilt_scenario("gdpr-deletion-24h")
        assert result.status.value == "completed"
        assert result.scenario_name == "GDPR: 24-Hour Deletion Requirement"

    @pytest.mark.asyncio
    async def test_list_prebuilt_scenarios(self, db_session):
        service = ImpactSimulatorService(db=db_session)
        scenarios = await service.list_prebuilt_scenarios()
        assert len(scenarios) >= 5

    @pytest.mark.asyncio
    async def test_compare_scenarios(self, db_session):
        service = ImpactSimulatorService(db=db_session)
        results = await service.compare_scenarios(
            ["gdpr-deletion-24h", "hipaa-breach-1h"]
        )
        assert len(results) == 2


class TestMarketplaceAppService:
    """Tests for the MarketplaceAppService."""

    @pytest.mark.asyncio
    async def test_handle_installation(self, db_session):
        service = MarketplaceAppService(db=db_session)
        inst = await service.handle_installation(
            platform=AppPlatform.GITHUB,
            external_id=12345,
            account_login="test-org",
            repositories=["test-org/repo1", "test-org/repo2"],
        )
        assert inst.status.value == "active"
        assert len(inst.repositories) == 2

    @pytest.mark.asyncio
    async def test_process_webhook(self, db_session):
        service = MarketplaceAppService(db=db_session)
        event = WebhookEvent(
            event_type="installation",
            action="created",
            installation_id=99999,
            payload={"account": {"login": "webhook-org"}},
        )
        result = await service.process_webhook(event)
        assert result["status"] == "installed"

    @pytest.mark.asyncio
    async def test_get_listing_info(self, db_session):
        service = MarketplaceAppService(db=db_session)
        info = await service.get_listing_info()
        assert info.app_name == "ComplianceAgent"
        assert len(info.plans) == 4
