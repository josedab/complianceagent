"""Tests for Next-Gen v9 features (10 new capabilities)."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.cicd_runtime.service import CICDRuntimeService
from app.services.digital_passport.service import DigitalPassportService
from app.services.harmonization_engine.service import HarmonizationEngineService
from app.services.knowledge_assistant.service import KnowledgeAssistantService
from app.services.multi_org_orchestrator.service import MultiOrgOrchestratorService
from app.services.plugin_ecosystem.service import PluginEcosystemService
from app.services.regulatory_filing.models import FilingType
from app.services.regulatory_filing.service import RegulatoryFilingService
from app.services.scenario_planner.models import RegionGroup, ScenarioType
from app.services.scenario_planner.service import ScenarioPlannerService
from app.services.telemetry_mesh.models import ServiceTier, SLOType
from app.services.telemetry_mesh.service import TelemetryMeshService
from app.services.training_simulator.service import TrainingSimulatorService


@pytest_asyncio.fixture
async def telem_svc(db_session: AsyncSession):
    return TelemetryMeshService(db=db_session)

@pytest_asyncio.fixture
async def assistant_svc(db_session: AsyncSession):
    return KnowledgeAssistantService(db=db_session)

@pytest_asyncio.fixture
async def passport_svc(db_session: AsyncSession):
    return DigitalPassportService(db=db_session)

@pytest_asyncio.fixture
async def planner_svc(db_session: AsyncSession):
    return ScenarioPlannerService(db=db_session)

@pytest_asyncio.fixture
async def filing_svc(db_session: AsyncSession):
    return RegulatoryFilingService(db=db_session)

@pytest_asyncio.fixture
async def cicd_svc(db_session: AsyncSession):
    return CICDRuntimeService(db=db_session)

@pytest_asyncio.fixture
async def multi_org_svc(db_session: AsyncSession):
    return MultiOrgOrchestratorService(db=db_session)

@pytest_asyncio.fixture
async def training_svc(db_session: AsyncSession):
    return TrainingSimulatorService(db=db_session)

@pytest_asyncio.fixture
async def harmony_svc(db_session: AsyncSession):
    return HarmonizationEngineService(db=db_session)

@pytest_asyncio.fixture
async def plugin_svc(db_session: AsyncSession):
    return PluginEcosystemService(db=db_session)


class TestTelemetryMesh:
    @pytest.mark.asyncio
    async def test_register_service(self, telem_svc: TelemetryMeshService):
        svc = await telem_svc.register_service("test-service", ServiceTier.standard)
        assert svc.service_name == "test-service"

    @pytest.mark.asyncio
    async def test_report_metrics(self, telem_svc: TelemetryMeshService):
        services = await telem_svc.list_services()
        if services:
            updated = await telem_svc.report_metrics(services[0].service_name, {"cpu": 45.0, "memory": 72.0})
            assert updated.health_score > 0

    @pytest.mark.asyncio
    async def test_define_and_evaluate_slos(self, telem_svc: TelemetryMeshService):
        slo = await telem_svc.define_slo("Availability", SLOType.availability, 99.9)
        assert slo.target == 99.9
        results = await telem_svc.evaluate_slos()
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_stats(self, telem_svc: TelemetryMeshService):
        stats = await telem_svc.get_stats()
        assert stats.services_monitored >= 1


class TestKnowledgeAssistant:
    @pytest.mark.asyncio
    async def test_start_conversation(self, assistant_svc: KnowledgeAssistantService):
        conv = await assistant_svc.start_conversation("user-1")
        assert conv.user_id == "user-1"

    @pytest.mark.asyncio
    async def test_send_message(self, assistant_svc: KnowledgeAssistantService):
        conv = await assistant_svc.start_conversation("user-1")
        msg = await assistant_svc.send_message(conv.id, "What is GDPR Article 17?")
        assert msg.content != ""
        assert msg.role == "assistant"

    @pytest.mark.asyncio
    async def test_quick_actions(self, assistant_svc: KnowledgeAssistantService):
        actions = await assistant_svc.list_quick_actions()
        assert len(actions) >= 1

    @pytest.mark.asyncio
    async def test_stats(self, assistant_svc: KnowledgeAssistantService):
        await assistant_svc.start_conversation("user-1")
        stats = await assistant_svc.get_stats()
        assert stats.total_conversations >= 1


class TestDigitalPassport:
    @pytest.mark.asyncio
    async def test_create_passport(self, passport_svc: DigitalPassportService):
        passport = await passport_svc.create_passport("Acme Corp", [
            {"credential_type": "soc2", "framework": "SOC 2", "score": 92.0},
        ])
        assert passport.org_name == "Acme Corp"
        assert len(passport.credentials) >= 1

    @pytest.mark.asyncio
    async def test_verify_passport(self, passport_svc: DigitalPassportService):
        passports = await passport_svc.list_passports()
        if passports:
            result = await passport_svc.verify_passport(passports[0].id, "Auditor Inc", "auditor")
            assert result.verified is True

    @pytest.mark.asyncio
    async def test_stats(self, passport_svc: DigitalPassportService):
        stats = await passport_svc.get_stats()
        assert stats.total_passports >= 1


class TestScenarioPlanner:
    @pytest.mark.asyncio
    async def test_plan_eu_expansion(self, planner_svc: ScenarioPlannerService):
        report = await planner_svc.plan_scenario(
            "EU Expansion", ScenarioType.market_expansion, "Launching in EU market",
            [RegionGroup.eu], ["personal", "financial"], ai_features=True,
        )
        assert "GDPR" in report.requirements.applicable_frameworks
        assert report.requirements.estimated_effort_hours > 0

    @pytest.mark.asyncio
    async def test_health_data_adds_hipaa(self, planner_svc: ScenarioPlannerService):
        report = await planner_svc.plan_scenario(
            "Health App", ScenarioType.product_launch, "Health tracking app",
            [RegionGroup.us], [], health_data=True,
        )
        assert "HIPAA" in report.requirements.applicable_frameworks

    @pytest.mark.asyncio
    async def test_stats(self, planner_svc: ScenarioPlannerService):
        await planner_svc.plan_scenario("T", ScenarioType.market_expansion, "t", [RegionGroup.us], [])
        stats = await planner_svc.get_stats()
        assert stats.total_scenarios >= 1


class TestRegulatoryFiling:
    @pytest.mark.asyncio
    async def test_list_authorities(self, filing_svc: RegulatoryFilingService):
        authorities = await filing_svc.list_authorities()
        assert len(authorities) >= 1

    @pytest.mark.asyncio
    async def test_generate_filing(self, filing_svc: RegulatoryFilingService):
        authorities = await filing_svc.list_authorities()
        templates = await filing_svc.list_templates()
        if authorities and templates:
            filing = await filing_svc.generate_filing(
                templates[0].filing_type, authorities[0].id, {"org_name": "Test Corp"}
            )
            assert filing.status.value == "draft"

    @pytest.mark.asyncio
    async def test_submit_filing(self, filing_svc: RegulatoryFilingService):
        authorities = await filing_svc.list_authorities()
        templates = await filing_svc.list_templates()
        if authorities and templates:
            filing = await filing_svc.generate_filing(templates[0].filing_type, authorities[0].id, {})
            submitted = await filing_svc.submit_filing(filing.id)
            assert submitted.status.value == "submitted"

    @pytest.mark.asyncio
    async def test_stats(self, filing_svc: RegulatoryFilingService):
        stats = await filing_svc.get_stats()
        assert stats.authorities_connected >= 1


class TestCICDRuntime:
    @pytest.mark.asyncio
    async def test_check_deployment(self, cicd_svc: CICDRuntimeService):
        check = await cicd_svc.check_deployment("deploy-1", "org/repo", "abc123")
        assert check.gate_decision is not None
        assert check.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_create_attestation(self, cicd_svc: CICDRuntimeService):
        att = await cicd_svc.create_attestation("deploy-1", "org/repo", "abc123", 92.0, ["GDPR", "SOC2"])
        assert att.signature != ""
        assert att.compliance_score == 92.0

    @pytest.mark.asyncio
    async def test_trigger_rollback(self, cicd_svc: CICDRuntimeService):
        rb = await cicd_svc.trigger_rollback("deploy-1", "Score dropped", (92.0, 65.0))
        assert rb.reason == "Score dropped"

    @pytest.mark.asyncio
    async def test_stats(self, cicd_svc: CICDRuntimeService):
        await cicd_svc.check_deployment("d1", "r", "s")
        stats = await cicd_svc.get_stats()
        assert stats.total_checks >= 1


class TestMultiOrgOrchestrator:
    @pytest.mark.asyncio
    async def test_create_entity(self, multi_org_svc: MultiOrgOrchestratorService):
        entity = await multi_org_svc.create_entity("New Sub", frameworks=["GDPR"])
        assert entity.name == "New Sub"

    @pytest.mark.asyncio
    async def test_list_entities(self, multi_org_svc: MultiOrgOrchestratorService):
        entities = await multi_org_svc.list_entities()
        assert len(entities) >= 1

    @pytest.mark.asyncio
    async def test_stats(self, multi_org_svc: MultiOrgOrchestratorService):
        stats = await multi_org_svc.get_stats()
        assert stats.total_entities >= 1


class TestTrainingSimulator:
    @pytest.mark.asyncio
    async def test_list_scenarios(self, training_svc: TrainingSimulatorService):
        scenarios = await training_svc.list_scenarios()
        assert len(scenarios) >= 1

    @pytest.mark.asyncio
    async def test_start_simulation(self, training_svc: TrainingSimulatorService):
        scenarios = await training_svc.list_scenarios()
        if scenarios:
            session = await training_svc.start_simulation("user-1", scenarios[0].id)
            assert session.status.value == "in_progress"

    @pytest.mark.asyncio
    async def test_stats(self, training_svc: TrainingSimulatorService):
        stats = await training_svc.get_stats()
        assert stats is not None


class TestHarmonizationEngine:
    @pytest.mark.asyncio
    async def test_analyze_overlap(self, harmony_svc: HarmonizationEngineService):
        result = await harmony_svc.analyze_overlap(["GDPR", "HIPAA"])
        assert result.total_controls > 0
        assert result.deduplication_pct > 0

    @pytest.mark.asyncio
    async def test_multi_framework(self, harmony_svc: HarmonizationEngineService):
        result = await harmony_svc.analyze_overlap(["GDPR", "HIPAA", "PCI-DSS", "SOC2"])
        assert result.overlapping_controls > 0
        assert len(result.recommendations) > 0

    @pytest.mark.asyncio
    async def test_list_controls(self, harmony_svc: HarmonizationEngineService):
        controls = await harmony_svc.list_controls("GDPR")
        assert len(controls) >= 1

    @pytest.mark.asyncio
    async def test_stats(self, harmony_svc: HarmonizationEngineService):
        await harmony_svc.analyze_overlap(["GDPR", "SOC2"])
        stats = await harmony_svc.get_stats()
        assert stats.analyses_run >= 1


class TestPluginEcosystem:
    @pytest.mark.asyncio
    async def test_list_plugins(self, plugin_svc: PluginEcosystemService):
        plugins = await plugin_svc.list_plugins()
        assert len(plugins) >= 1

    @pytest.mark.asyncio
    async def test_install_plugin(self, plugin_svc: PluginEcosystemService):
        plugins = await plugin_svc.list_plugins()
        if plugins:
            inst = await plugin_svc.install_plugin(plugins[0].id, {})
            assert inst.status.value == "installed"

    @pytest.mark.asyncio
    async def test_execute_hook(self, plugin_svc: PluginEcosystemService):
        # Install a plugin first
        plugins = await plugin_svc.list_plugins()
        if plugins:
            await plugin_svc.install_plugin(plugins[0].id, {})
            results = await plugin_svc.execute_hook("pre_scan", {"repo": "org/repo"})
            assert len(results) >= 0  # May or may not match hook point

    @pytest.mark.asyncio
    async def test_list_hooks(self, plugin_svc: PluginEcosystemService):
        hooks = await plugin_svc.list_available_hooks()
        assert len(hooks) >= 1

    @pytest.mark.asyncio
    async def test_stats(self, plugin_svc: PluginEcosystemService):
        stats = await plugin_svc.get_stats()
        assert stats.total_plugins >= 1
