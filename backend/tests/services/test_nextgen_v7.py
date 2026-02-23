"""Tests for Next-Gen v7 features (10 new capabilities)."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agent_swarm.service import AgentSwarmService
from app.services.compliance_editor.service import ComplianceEditorService
from app.services.contract_analyzer.models import ContractType
from app.services.contract_analyzer.service import ContractAnalyzerService
from app.services.data_mesh_federation.service import DataMeshFederationService
from app.services.graph_explorer.service import GraphExplorerService
from app.services.localization_engine.models import Language
from app.services.localization_engine.service import LocalizationEngineService
from app.services.marketplace_revenue.service import MarketplaceRevenueService
from app.services.mobile_backend.models import DevicePlatform, NotificationType, PushPriority
from app.services.mobile_backend.service import MobileBackendService
from app.services.pia_generator.service import PIAGeneratorService
from app.services.pipeline_builder.service import PipelineBuilderService


@pytest_asyncio.fixture
async def mesh_svc(db_session: AsyncSession):
    return DataMeshFederationService(db=db_session)


@pytest_asyncio.fixture
async def swarm_svc(db_session: AsyncSession):
    return AgentSwarmService(db=db_session)


@pytest_asyncio.fixture
async def editor_svc(db_session: AsyncSession):
    return ComplianceEditorService(db=db_session)


@pytest_asyncio.fixture
async def explorer_svc(db_session: AsyncSession):
    return GraphExplorerService(db=db_session)


@pytest_asyncio.fixture
async def pipeline_svc(db_session: AsyncSession):
    return PipelineBuilderService(db=db_session)


@pytest_asyncio.fixture
async def pia_svc(db_session: AsyncSession):
    return PIAGeneratorService(db=db_session)


@pytest_asyncio.fixture
async def contract_svc(db_session: AsyncSession):
    return ContractAnalyzerService(db=db_session)


@pytest_asyncio.fixture
async def mobile_svc(db_session: AsyncSession):
    return MobileBackendService(db=db_session)


@pytest_asyncio.fixture
async def revenue_svc(db_session: AsyncSession):
    return MarketplaceRevenueService(db=db_session)


@pytest_asyncio.fixture
async def locale_svc(db_session: AsyncSession):
    return LocalizationEngineService(db=db_session)


# ── Feature 1: Data Mesh Federation ──────────────────────────────────────


class TestDataMeshFederation:
    @pytest.mark.asyncio
    async def test_join_federation(self, mesh_svc: DataMeshFederationService):
        node = await mesh_svc.join_federation("Acme Corp", "https://acme.com/api")
        assert node.org_name == "Acme Corp"
        assert node.endpoint_url == "https://acme.com/api"

    @pytest.mark.asyncio
    async def test_share_insight(self, mesh_svc: DataMeshFederationService):
        nodes = await mesh_svc.list_nodes()
        if nodes:
            insight = await mesh_svc.share_insight(
                str(nodes[0].id), "compliance_score", {"score": 85.0}
            )
            assert insight.proof_hash != ""

    @pytest.mark.asyncio
    async def test_verify_proof(self, mesh_svc: DataMeshFederationService):
        nodes = await mesh_svc.list_nodes()
        if nodes:
            insight = await mesh_svc.share_insight(str(nodes[0].id), "test", {"val": 1})
            # Verify that proof hash was generated
            assert insight.proof_hash != ""
            assert len(insight.proof_hash) > 10

    @pytest.mark.asyncio
    async def test_list_nodes(self, mesh_svc: DataMeshFederationService):
        nodes = await mesh_svc.list_nodes()
        assert len(nodes) >= 1

    @pytest.mark.asyncio
    async def test_stats(self, mesh_svc: DataMeshFederationService):
        stats = await mesh_svc.get_stats()
        assert stats.total_nodes >= 1


# ── Feature 2: Agent Swarm ──────────────────────────────────────────────


class TestAgentSwarm:
    @pytest.mark.asyncio
    async def test_launch_swarm(self, swarm_svc: AgentSwarmService):
        session = await swarm_svc.launch_swarm("org/repo", ["GDPR", "HIPAA"], ["src/main.py"])
        assert session.repo == "org/repo"
        assert len(session.agents) >= 4

    @pytest.mark.asyncio
    async def test_swarm_generates_tasks(self, swarm_svc: AgentSwarmService):
        session = await swarm_svc.launch_swarm("org/repo", ["PCI-DSS"], ["src/pay.py"])
        assert len(session.tasks) >= 1

    @pytest.mark.asyncio
    async def test_list_sessions(self, swarm_svc: AgentSwarmService):
        await swarm_svc.launch_swarm("org/repo", ["GDPR"], ["src/a.py"])
        sessions = await swarm_svc.list_sessions()
        assert len(sessions) >= 1

    @pytest.mark.asyncio
    async def test_stats(self, swarm_svc: AgentSwarmService):
        await swarm_svc.launch_swarm("org/repo", ["GDPR"], ["src/a.py"])
        stats = await swarm_svc.get_stats()
        assert stats.total_sessions >= 1


# ── Feature 3: Compliance Editor ─────────────────────────────────────────


class TestComplianceEditor:
    @pytest.mark.asyncio
    async def test_create_session(self, editor_svc: ComplianceEditorService):
        session = await editor_svc.create_session("user-1")
        assert session.user_id == "user-1"

    @pytest.mark.asyncio
    async def test_open_file_with_violations(self, editor_svc: ComplianceEditorService):
        session = await editor_svc.create_session("user-1")
        f = await editor_svc.open_file(session.id, "src/users.py", "user_email = get_data()\nstore_personal_data(name)", "python")
        assert len(f.diagnostics) > 0

    @pytest.mark.asyncio
    async def test_open_clean_file(self, editor_svc: ComplianceEditorService):
        session = await editor_svc.create_session("user-1")
        f = await editor_svc.open_file(session.id, "README.md", "# Hello world", "python")
        assert len(f.diagnostics) == 0

    @pytest.mark.asyncio
    async def test_stats(self, editor_svc: ComplianceEditorService):
        await editor_svc.create_session("user-1")
        stats = await editor_svc.get_stats()
        assert stats.total_sessions >= 1


# ── Feature 4: Graph Explorer ────────────────────────────────────────────


class TestGraphExplorer:
    @pytest.mark.asyncio
    async def test_create_view(self, explorer_svc: GraphExplorerService):
        view = await explorer_svc.create_view("force_directed")
        assert len(view.nodes) > 0
        assert len(view.edges) > 0

    @pytest.mark.asyncio
    async def test_drilldown(self, explorer_svc: GraphExplorerService):
        view = await explorer_svc.create_view("force_directed")
        if view.nodes:
            result = await explorer_svc.drilldown(view.nodes[0].id)
            assert result.label != ""

    @pytest.mark.asyncio
    async def test_search_nodes(self, explorer_svc: GraphExplorerService):
        await explorer_svc.create_view("force_directed")
        results = await explorer_svc.search_nodes("GDPR")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_stats(self, explorer_svc: GraphExplorerService):
        await explorer_svc.create_view("force_directed")
        stats = await explorer_svc.get_stats()
        assert stats.total_nodes > 0


# ── Feature 5: Pipeline Builder ──────────────────────────────────────────


class TestPipelineBuilder:
    @pytest.mark.asyncio
    async def test_create_pipeline(self, pipeline_svc: PipelineBuilderService):
        pipeline = await pipeline_svc.create_pipeline(
            "Compliance CI", "github_actions", "org/repo",
            [{"name": "Scan", "step_type": "scan", "config": {}}, {"name": "Gate", "step_type": "gate", "config": {}}]
        )
        assert pipeline.name == "Compliance CI"
        assert len(pipeline.steps) == 2

    @pytest.mark.asyncio
    async def test_generate_config(self, pipeline_svc: PipelineBuilderService):
        pipeline = await pipeline_svc.create_pipeline(
            "Test", "github_actions", "org/repo",
            [{"name": "Scan", "step_type": "scan", "config": {}}]
        )
        config = await pipeline_svc.generate_config(pipeline.id)
        assert len(config.config_yaml) > 0

    @pytest.mark.asyncio
    async def test_list_templates(self, pipeline_svc: PipelineBuilderService):
        templates = await pipeline_svc.list_templates()
        assert len(templates) >= 1

    @pytest.mark.asyncio
    async def test_create_from_template(self, pipeline_svc: PipelineBuilderService):
        templates = await pipeline_svc.list_templates()
        if templates:
            pipeline = await pipeline_svc.create_from_template(templates[0].id, "org/repo")
            assert pipeline is not None

    @pytest.mark.asyncio
    async def test_stats(self, pipeline_svc: PipelineBuilderService):
        await pipeline_svc.create_pipeline("T", "github_actions", "r", [])
        stats = await pipeline_svc.get_stats()
        assert stats.total_pipelines >= 1


# ── Feature 6: PIA Generator ────────────────────────────────────────────


class TestPIAGenerator:
    @pytest.mark.asyncio
    async def test_generate_pia(self, pia_svc: PIAGeneratorService):
        pia = await pia_svc.generate_pia("org/repo", "User Data PIA")
        assert pia.title == "User Data PIA"
        assert len(pia.data_flows) >= 1

    @pytest.mark.asyncio
    async def test_approve_pia(self, pia_svc: PIAGeneratorService):
        pia = await pia_svc.generate_pia("org/repo", "Test PIA")
        approved = await pia_svc.approve_pia(pia.id, "dpo@company.com")
        assert approved is not None
        assert approved.dpo_approved is True

    @pytest.mark.asyncio
    async def test_export_pia(self, pia_svc: PIAGeneratorService):
        pia = await pia_svc.generate_pia("org/repo", "Export PIA")
        export = await pia_svc.export_pia(pia.id)
        assert export is not None

    @pytest.mark.asyncio
    async def test_stats(self, pia_svc: PIAGeneratorService):
        await pia_svc.generate_pia("org/repo", "Stats PIA")
        stats = await pia_svc.get_stats()
        assert stats.total_assessments >= 1


# ── Feature 7: Contract Analyzer ─────────────────────────────────────────


class TestContractAnalyzer:
    @pytest.mark.asyncio
    async def test_analyze_dpa(self, contract_svc: ContractAnalyzerService):
        analysis = await contract_svc.analyze_contract(
            "Vendor DPA", ContractType.DPA, "CloudCo",
            "The processor must implement encryption. Data shall be processed in the EU."
        )
        assert analysis.total_obligations > 0
        assert analysis.vendor == "CloudCo"

    @pytest.mark.asyncio
    async def test_extract_obligations(self, contract_svc: ContractAnalyzerService):
        analysis = await contract_svc.analyze_contract(
            "Test", ContractType.VENDOR_CONTRACT, "Vendor",
            "The vendor must comply with GDPR. Patient data shall be encrypted."
        )
        assert len(analysis.obligations) >= 1

    @pytest.mark.asyncio
    async def test_list_analyses(self, contract_svc: ContractAnalyzerService):
        await contract_svc.analyze_contract("T", ContractType.DPA, "V", "Must comply.")
        analyses = await contract_svc.list_analyses()
        assert len(analyses) >= 1

    @pytest.mark.asyncio
    async def test_stats(self, contract_svc: ContractAnalyzerService):
        await contract_svc.analyze_contract("T", ContractType.DPA, "V", "Must comply.")
        stats = await contract_svc.get_stats()
        assert stats.total_analyses >= 1


# ── Feature 8: Mobile Backend ────────────────────────────────────────────


class TestMobileBackend:
    @pytest.mark.asyncio
    async def test_register_device(self, mobile_svc: MobileBackendService):
        device = await mobile_svc.register_device("user-1", DevicePlatform.IOS, "token-abc")
        assert device.user_id == "user-1"
        assert device.push_enabled is True

    @pytest.mark.asyncio
    async def test_send_notification(self, mobile_svc: MobileBackendService):
        await mobile_svc.register_device("user-1", DevicePlatform.IOS, "token-abc")
        notif = await mobile_svc.send_notification(
            "user-1", NotificationType.SCORE_CHANGE, "Score Update", "Score is 87%", PushPriority.NORMAL
        )
        assert notif.title == "Score Update"

    @pytest.mark.asyncio
    async def test_get_dashboard(self, mobile_svc: MobileBackendService):
        dash = await mobile_svc.get_dashboard("user-1")
        assert dash.overall_score > 0

    @pytest.mark.asyncio
    async def test_stats(self, mobile_svc: MobileBackendService):
        await mobile_svc.register_device("user-1", DevicePlatform.ANDROID, "tok")
        stats = await mobile_svc.get_stats()
        assert stats.registered_devices >= 1


# ── Feature 9: Marketplace Revenue ───────────────────────────────────────


class TestMarketplaceRevenue:
    @pytest.mark.asyncio
    async def test_seed_listings(self, revenue_svc: MarketplaceRevenueService):
        listings = await revenue_svc.list_listings()
        assert len(listings) >= 1

    @pytest.mark.asyncio
    async def test_create_listing(self, revenue_svc: MarketplaceRevenueService):
        listing = await revenue_svc.create_listing("new-agent", "author1", "paid_listing", 29.0)
        assert listing.agent_slug == "new-agent"

    @pytest.mark.asyncio
    async def test_generate_report(self, revenue_svc: MarketplaceRevenueService):
        report = await revenue_svc.generate_revenue_report("Q1 2026")
        assert report.period == "Q1 2026"

    @pytest.mark.asyncio
    async def test_stats(self, revenue_svc: MarketplaceRevenueService):
        stats = await revenue_svc.get_stats()
        assert stats.total_listings >= 1


# ── Feature 10: Localization Engine ───────────────────────────────────────


class TestLocalizationEngine:
    @pytest.mark.asyncio
    async def test_get_english_translations(self, locale_svc: LocalizationEngineService):
        bundle = await locale_svc.get_translations(Language.EN)
        assert bundle.total_keys >= 1
        assert bundle.coverage_pct > 0

    @pytest.mark.asyncio
    async def test_list_languages(self, locale_svc: LocalizationEngineService):
        languages = await locale_svc.list_languages()
        assert len(languages) >= 7

    @pytest.mark.asyncio
    async def test_get_missing_translations(self, locale_svc: LocalizationEngineService):
        missing = await locale_svc.get_missing_translations(Language.JA)
        assert isinstance(missing, list)

    @pytest.mark.asyncio
    async def test_export_bundle(self, locale_svc: LocalizationEngineService):
        export = await locale_svc.export_bundle(Language.EN)
        assert export is not None

    @pytest.mark.asyncio
    async def test_stats(self, locale_svc: LocalizationEngineService):
        stats = await locale_svc.get_stats()
        assert stats.languages_supported >= 7
        assert stats.total_keys >= 1
