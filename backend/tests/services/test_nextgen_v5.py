"""Tests for Next-Gen v5 features (10 new capabilities)."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.api_gateway.service import APIGatewayService
from app.services.cert_pipeline.models import CertFramework, GapStatus
from app.services.cert_pipeline.service import CertPipelineService
from app.services.compliance_data_lake.service import ComplianceDataLakeService
from app.services.compliance_gnn.service import ComplianceGNNService
from app.services.ide_extension.service import IDEExtensionService
from app.services.knowledge_fabric.service import KnowledgeFabricService
from app.services.policy_dsl.service import PolicyDSLService
from app.services.realtime_feed.models import FeedItem, FeedItemType, FeedPriority
from app.services.realtime_feed.service import RealtimeFeedService
from app.services.self_healing_mesh.models import EventType, HealingEvent, PipelineStage
from app.services.self_healing_mesh.service import SelfHealingMeshService
from app.services.workflow_automation.service import WorkflowAutomationService


@pytest_asyncio.fixture
async def fabric_service(db_session: AsyncSession):
    return KnowledgeFabricService(db=db_session)


@pytest_asyncio.fixture
async def mesh_service(db_session: AsyncSession):
    return SelfHealingMeshService(db=db_session)


@pytest_asyncio.fixture
async def ide_ext_service(db_session: AsyncSession):
    return IDEExtensionService(db=db_session)


@pytest_asyncio.fixture
async def lake_service(db_session: AsyncSession):
    return ComplianceDataLakeService(db=db_session)


@pytest_asyncio.fixture
async def dsl_service(db_session: AsyncSession):
    return PolicyDSLService(db=db_session)


@pytest_asyncio.fixture
async def feed_service(db_session: AsyncSession):
    return RealtimeFeedService(db=db_session)


@pytest_asyncio.fixture
async def gnn_service(db_session: AsyncSession):
    return ComplianceGNNService(db=db_session)


@pytest_asyncio.fixture
async def cert_service(db_session: AsyncSession):
    return CertPipelineService(db=db_session)


@pytest_asyncio.fixture
async def gateway_service(db_session: AsyncSession):
    return APIGatewayService(db=db_session)


@pytest_asyncio.fixture
async def workflow_service(db_session: AsyncSession):
    return WorkflowAutomationService(db=db_session)


# ── Feature 1: Knowledge Fabric ──────────────────────────────────────────


class TestKnowledgeFabric:
    @pytest.mark.asyncio
    async def test_search_gdpr(self, fabric_service: KnowledgeFabricService):
        result = await fabric_service.search("GDPR erasure right")
        assert result.total_count > 0
        assert result.rag_answer != ""
        assert result.execution_time_ms >= 0

    @pytest.mark.asyncio
    async def test_search_by_scope(self, fabric_service: KnowledgeFabricService):
        result = await fabric_service.search("encryption", scope="regulations")
        assert all(r.result_type.value in ("regulation", "requirement") for r in result.results)

    @pytest.mark.asyncio
    async def test_search_returns_sources(self, fabric_service: KnowledgeFabricService):
        result = await fabric_service.search("HIPAA PHI")
        assert len(result.sources_cited) > 0

    @pytest.mark.asyncio
    async def test_embedding_stats(self, fabric_service: KnowledgeFabricService):
        stats = fabric_service.get_embedding_stats()
        assert stats.total_documents > 0
        assert len(stats.by_type) > 0

    @pytest.mark.asyncio
    async def test_empty_query_returns_empty(self, fabric_service: KnowledgeFabricService):
        result = await fabric_service.search("zzzznonexistent12345")
        assert result.total_count == 0


# ── Feature 2: Self-Healing Mesh ─────────────────────────────────────────


class TestSelfHealingMesh:
    @pytest.mark.asyncio
    async def test_low_risk_auto_merges(self, mesh_service: SelfHealingMeshService):
        event = HealingEvent(event_type=EventType.VIOLATION_DETECTED, repo="org/api", severity="low", description="Minor violation")
        pipeline = await mesh_service.ingest_event(event)
        assert pipeline.stage == PipelineStage.COMPLETED
        assert pipeline.pr_url != ""

    @pytest.mark.asyncio
    async def test_high_risk_awaits_approval(self, mesh_service: SelfHealingMeshService):
        event = HealingEvent(event_type=EventType.DRIFT_DETECTED, repo="org/api", severity="high", description="Score drop")
        pipeline = await mesh_service.ingest_event(event)
        assert pipeline.stage == PipelineStage.AWAITING_APPROVAL

    @pytest.mark.asyncio
    async def test_critical_escalates(self, mesh_service: SelfHealingMeshService):
        event = HealingEvent(event_type=EventType.VIOLATION_DETECTED, repo="org/api", severity="critical")
        pipeline = await mesh_service.ingest_event(event)
        assert pipeline.stage == PipelineStage.ESCALATED

    @pytest.mark.asyncio
    async def test_approve_pipeline(self, mesh_service: SelfHealingMeshService):
        event = HealingEvent(event_type=EventType.VIOLATION_DETECTED, repo="org/api", severity="medium")
        pipeline = await mesh_service.ingest_event(event)
        approved = await mesh_service.approve_pipeline(str(pipeline.id))
        assert approved is not None
        assert approved.stage == PipelineStage.COMPLETED

    @pytest.mark.asyncio
    async def test_stats(self, mesh_service: SelfHealingMeshService):
        await mesh_service.ingest_event(HealingEvent(repo="org/a", severity="low"))
        stats = mesh_service.get_stats()
        assert stats.total_events >= 1
        assert stats.total_pipelines >= 1


# ── Feature 3: IDE Extension ────────────────────────────────────────────


class TestIDEExtension:
    @pytest.mark.asyncio
    async def test_analyze_file_with_violations(self, ide_ext_service: IDEExtensionService):
        diags = await ide_ext_service.analyze_file("src/users.py", "user_email = get_input()\nstore_forever(data)")
        assert len(diags) > 0
        assert diags[0].framework in ("GDPR", "HIPAA", "PCI-DSS", "SOC 2")

    @pytest.mark.asyncio
    async def test_analyze_clean_file(self, ide_ext_service: IDEExtensionService):
        diags = await ide_ext_service.analyze_file("README.md", "# Documentation\nThis is a readme.")
        assert len(diags) == 0

    @pytest.mark.asyncio
    async def test_get_tooltip(self, ide_ext_service: IDEExtensionService):
        tooltip = ide_ext_service.get_tooltip("GDPR", "Art. 17")
        assert tooltip is not None
        assert "erasure" in tooltip.title.lower()

    @pytest.mark.asyncio
    async def test_posture_sidebar(self, ide_ext_service: IDEExtensionService):
        posture = ide_ext_service.get_posture_sidebar("src/main.py")
        assert posture.file_score > 0
        assert posture.file_grade in ("A", "A-", "B+", "B", "C")

    @pytest.mark.asyncio
    async def test_stats_track_analysis(self, ide_ext_service: IDEExtensionService):
        await ide_ext_service.analyze_file("test.py", "x = 1")
        stats = ide_ext_service.get_stats()
        assert stats.files_analyzed >= 1


# ── Feature 4: Data Lake ────────────────────────────────────────────────


class TestComplianceDataLake:
    @pytest.mark.asyncio
    async def test_ingest_event(self, lake_service: ComplianceDataLakeService):
        event = await lake_service.ingest_event("tenant-1", "score_change", data={"score": 85.0})
        assert event.tenant_id == "tenant-1"
        assert event.timestamp is not None

    @pytest.mark.asyncio
    async def test_ingest_batch(self, lake_service: ComplianceDataLakeService):
        count = await lake_service.ingest_batch([
            {"tenant_id": "t1", "category": "violation", "framework": "GDPR"},
            {"tenant_id": "t1", "category": "scan", "framework": "HIPAA"},
        ])
        assert count == 2

    @pytest.mark.asyncio
    async def test_query_analytics(self, lake_service: ComplianceDataLakeService):
        await lake_service.ingest_event("t1", "violation", framework="GDPR")
        result = await lake_service.query_analytics("t1", category="violation")
        assert result.total_events >= 1

    @pytest.mark.asyncio
    async def test_stats(self, lake_service: ComplianceDataLakeService):
        await lake_service.ingest_event("t1", "scan")
        stats = lake_service.get_stats()
        assert stats.total_events >= 1


# ── Feature 5: Policy DSL ───────────────────────────────────────────────


class TestPolicyDSL:
    @pytest.mark.asyncio
    async def test_list_builtin_policies(self, dsl_service: PolicyDSLService):
        policies = dsl_service.list_policies()
        assert len(policies) >= 3

    @pytest.mark.asyncio
    async def test_validate_valid_dsl(self, dsl_service: PolicyDSLService):
        result = dsl_service.validate_dsl('policy "test" {\n  when: data_type == "personal"\n  then: require("consent")\n}')
        assert result.valid is True

    @pytest.mark.asyncio
    async def test_validate_invalid_dsl(self, dsl_service: PolicyDSLService):
        result = dsl_service.validate_dsl("")
        assert result.valid is False

    @pytest.mark.asyncio
    async def test_compile_to_rego(self, dsl_service: PolicyDSLService):
        compiled = await dsl_service.compile_policy("gdpr-consent-required", "rego")
        assert "package compliance" in compiled.compiled_code
        assert len(compiled.errors) == 0

    @pytest.mark.asyncio
    async def test_compile_to_python(self, dsl_service: PolicyDSLService):
        compiled = await dsl_service.compile_policy("gdpr-consent-required", "python")
        assert "def check_" in compiled.compiled_code

    @pytest.mark.asyncio
    async def test_compile_to_yaml(self, dsl_service: PolicyDSLService):
        compiled = await dsl_service.compile_policy("hipaa-phi-encryption", "yaml")
        assert "policy:" in compiled.compiled_code

    @pytest.mark.asyncio
    async def test_compile_to_typescript(self, dsl_service: PolicyDSLService):
        compiled = await dsl_service.compile_policy("pci-card-tokenization", "typescript")
        assert "export function" in compiled.compiled_code


# ── Feature 6: Real-Time Feed ───────────────────────────────────────────


class TestRealtimeFeed:
    @pytest.mark.asyncio
    async def test_get_seed_feed(self, feed_service: RealtimeFeedService):
        items = feed_service.get_feed()
        assert len(items) >= 5

    @pytest.mark.asyncio
    async def test_publish_and_retrieve(self, feed_service: RealtimeFeedService):
        item = FeedItem(item_type=FeedItemType.REGULATION_CHANGE, priority=FeedPriority.URGENT, title="Test Change", regulation="GDPR", jurisdiction="EU")
        published = await feed_service.publish_item(item)
        assert published.title == "Test Change"
        feed = feed_service.get_feed(priority=FeedPriority.URGENT)
        assert any(i.title == "Test Change" for i in feed)

    @pytest.mark.asyncio
    async def test_subscribe_and_notify(self, feed_service: RealtimeFeedService):
        await feed_service.subscribe("user-1", channels=["slack"], min_priority="high", jurisdictions=["EU"])
        await feed_service.publish_item(FeedItem(priority=FeedPriority.URGENT, jurisdiction="EU"))
        stats = feed_service.get_stats()
        assert stats.notifications_sent >= 1

    @pytest.mark.asyncio
    async def test_slack_card(self, feed_service: RealtimeFeedService):
        item = FeedItem(title="Test", priority=FeedPriority.HIGH, regulation="GDPR", jurisdiction="EU", impact_score=8.0)
        card = feed_service.generate_slack_card(item)
        assert card.title == "Test"
        assert len(card.fields) >= 3


# ── Feature 7: Compliance GNN ───────────────────────────────────────────


class TestComplianceGNN:
    @pytest.mark.asyncio
    async def test_predict_violations(self, gnn_service: ComplianceGNNService):
        predictions = await gnn_service.predict_violations()
        assert len(predictions) > 0
        assert all(p.risk_score >= 0 for p in predictions)
        assert all(p.confidence > 0 for p in predictions)

    @pytest.mark.asyncio
    async def test_predict_specific_files(self, gnn_service: ComplianceGNNService):
        predictions = await gnn_service.predict_violations(file_paths=["src/users.py"])
        assert len(predictions) == 1
        assert predictions[0].file_path == "src/users.py"
        assert predictions[0].risk_score > 0

    @pytest.mark.asyncio
    async def test_get_graph(self, gnn_service: ComplianceGNNService):
        graph = gnn_service.get_graph()
        assert len(graph["nodes"]) > 0
        assert len(graph["edges"]) > 0

    @pytest.mark.asyncio
    async def test_get_neighbors(self, gnn_service: ComplianceGNNService):
        result = gnn_service.get_node_neighbors("src/users.py")
        assert result["node"] is not None
        assert len(result["neighbors"]) > 0

    @pytest.mark.asyncio
    async def test_stats(self, gnn_service: ComplianceGNNService):
        await gnn_service.predict_violations()
        stats = gnn_service.get_stats()
        assert stats.total_nodes > 0
        assert stats.predictions_made > 0


# ── Feature 8: Certification Pipeline ────────────────────────────────────


class TestCertPipeline:
    @pytest.mark.asyncio
    async def test_start_soc2_certification(self, cert_service: CertPipelineService):
        run = await cert_service.start_certification("soc2_type2")
        assert run.framework == CertFramework.SOC2_TYPE2
        assert run.total_controls >= 9
        assert run.gaps_found > 0
        assert run.readiness_pct > 0

    @pytest.mark.asyncio
    async def test_start_iso27001(self, cert_service: CertPipelineService):
        run = await cert_service.start_certification("iso27001")
        assert run.framework == CertFramework.ISO27001
        assert run.total_controls >= 8

    @pytest.mark.asyncio
    async def test_resolve_gap(self, cert_service: CertPipelineService):
        run = await cert_service.start_certification("soc2_type2")
        gaps = cert_service.get_gaps(str(run.id), status=GapStatus.OPEN)
        assert len(gaps) > 0
        resolved = await cert_service.resolve_gap(gaps[0].id, "Implemented RBAC controls")
        assert resolved is not None
        assert resolved.status == GapStatus.RESOLVED

    @pytest.mark.asyncio
    async def test_generate_report(self, cert_service: CertPipelineService):
        run = await cert_service.start_certification("soc2_type2")
        report = await cert_service.generate_report(str(run.id))
        assert report is not None
        assert report.readiness_pct > 0
        assert len(report.recommendations) > 0

    @pytest.mark.asyncio
    async def test_advance_stage(self, cert_service: CertPipelineService):
        run = await cert_service.start_certification("soc2_type2")
        initial_stage = run.stage
        updated = await cert_service.advance_stage(str(run.id))
        assert updated is not None
        assert updated.stage != initial_stage


# ── Feature 9: API Gateway ──────────────────────────────────────────────


class TestAPIGateway:
    @pytest.mark.asyncio
    async def test_create_client(self, gateway_service: APIGatewayService):
        client, secret = await gateway_service.create_client("Test App", tier="starter")
        assert client.client_id.startswith("ca_")
        assert len(secret) > 20
        assert client.rate_limit_per_minute == 300

    @pytest.mark.asyncio
    async def test_authenticate(self, gateway_service: APIGatewayService):
        client, _ = await gateway_service.create_client("Auth Test")
        authed = await gateway_service.authenticate(client.client_id)
        assert authed is not None
        assert authed.client_name == "Auth Test"

    @pytest.mark.asyncio
    async def test_revoke_client(self, gateway_service: APIGatewayService):
        client, _ = await gateway_service.create_client("Revoke Me")
        ok = await gateway_service.revoke_client(client.client_id)
        assert ok is True
        authed = await gateway_service.authenticate(client.client_id)
        assert authed is None

    @pytest.mark.asyncio
    async def test_rate_limit_info(self, gateway_service: APIGatewayService):
        client, _ = await gateway_service.create_client("RL Test", tier="professional")
        rl = gateway_service.get_rate_limit(client.client_id)
        assert rl is not None
        assert rl.limit_per_minute == 1000

    @pytest.mark.asyncio
    async def test_developer_portal(self, gateway_service: APIGatewayService):
        portal = gateway_service.get_developer_portal()
        assert len(portal.sdks) == 3


# ── Feature 10: Workflow Automation ──────────────────────────────────────


class TestWorkflowAutomation:
    @pytest.mark.asyncio
    async def test_create_workflow(self, workflow_service: WorkflowAutomationService):
        wf = await workflow_service.create_workflow(
            name="Score Drop Alert", trigger_type="score_drop",
            actions=[{"type": "notify_slack"}, {"type": "create_ticket"}],
        )
        assert wf.name == "Score Drop Alert"
        assert len(wf.actions) == 2

    @pytest.mark.asyncio
    async def test_execute_workflow(self, workflow_service: WorkflowAutomationService):
        wf = await workflow_service.create_workflow("Test WF", actions=[{"type": "notify_email"}])
        execution = await workflow_service.execute_workflow(str(wf.id), {"score": 65})
        assert execution.status.value == "completed"
        assert len(execution.actions_completed) == 1

    @pytest.mark.asyncio
    async def test_create_from_template(self, workflow_service: WorkflowAutomationService):
        wf = await workflow_service.create_from_template("score-drop-alert")
        assert wf is not None
        assert wf.name == "Score Drop Alert"

    @pytest.mark.asyncio
    async def test_pause_and_resume(self, workflow_service: WorkflowAutomationService):
        wf = await workflow_service.create_workflow("Pause Test")
        paused = await workflow_service.pause_workflow(str(wf.id))
        assert paused.status.value == "paused"
        resumed = await workflow_service.resume_workflow(str(wf.id))
        assert resumed.status.value == "active"

    @pytest.mark.asyncio
    async def test_list_templates(self, workflow_service: WorkflowAutomationService):
        templates = workflow_service.list_templates()
        assert len(templates) >= 5
        categories = {t.category for t in templates}
        assert "alerting" in categories
        assert "automation" in categories
