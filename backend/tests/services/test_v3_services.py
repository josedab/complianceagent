"""Service-level tests for v3.0 Next-Gen Features."""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock

from app.services.telemetry import TelemetryService, MetricType, TelemetryEventType, AlertSeverity
from app.services.nl_query import NLQueryService, QueryIntent
from app.services.remediation_workflow import RemediationWorkflowService, RemediationPriority, WorkflowState
from app.services.posture_scoring import PostureScoringService
from app.services.org_hierarchy import OrgHierarchyService, OrgNodeType, OrgRole
from app.services.policy_sdk import PolicySDKService, PolicyCategory, PolicyLanguage
from app.services.audit_autopilot import AuditAutopilotService, AuditFramework
from app.services.impact_timeline import ImpactTimelineService, TaskStatus
from app.services.compliance_intel import ComplianceIntelService, PrivacyLevel
from app.services.self_hosted import SelfHostedService, DeploymentMode, LicenseType


class TestTelemetryService:
    @pytest.mark.asyncio
    async def test_get_snapshot(self, db_session):
        service = TelemetryService(db=db_session)
        snapshot = await service.get_current_snapshot()
        assert snapshot.overall_score > 0
        assert snapshot.timestamp is not None

    @pytest.mark.asyncio
    async def test_record_metric(self, db_session):
        service = TelemetryService(db=db_session)
        metric = await service.record_metric(MetricType.COMPLIANCE_SCORE, 92.5, framework="gdpr")
        assert metric.value == 92.5
        assert metric.metric_type == MetricType.COMPLIANCE_SCORE

    @pytest.mark.asyncio
    async def test_emit_event(self, db_session):
        service = TelemetryService(db=db_session)
        event = await service.emit_event(TelemetryEventType.VIOLATION_DETECTED, "Test violation")
        assert event.title == "Test violation"
        assert event.severity == AlertSeverity.INFO

    @pytest.mark.asyncio
    async def test_get_time_series(self, db_session):
        service = TelemetryService(db=db_session)
        series = await service.get_time_series(MetricType.COMPLIANCE_SCORE, period="24h")
        assert len(series.data_points) > 0

    @pytest.mark.asyncio
    async def test_threshold_breach(self, db_session):
        service = TelemetryService(db=db_session)
        metric = await service.record_metric(MetricType.COMPLIANCE_SCORE, 50.0)
        events = await service.get_events(event_type=TelemetryEventType.THRESHOLD_BREACH)
        assert len(events) > 0

    @pytest.mark.asyncio
    async def test_heatmap(self, db_session):
        service = TelemetryService(db=db_session)
        heatmap = await service.get_heatmap_data("7d")
        assert "frameworks" in heatmap
        assert len(heatmap["frameworks"]) > 0


class TestNLQueryService:
    @pytest.mark.asyncio
    async def test_regulation_query(self, db_session):
        service = NLQueryService(db=db_session)
        result = await service.query("What does GDPR Article 17 require?")
        assert result.intent == QueryIntent.REGULATION_LOOKUP
        assert len(result.sources) > 0
        assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_violation_query(self, db_session):
        service = NLQueryService(db=db_session)
        result = await service.query("Show me all current violations")
        assert result.intent == QueryIntent.VIOLATION_QUERY
        assert "violation" in result.answer.lower() or "breach" in result.answer.lower() or "Critical" in result.answer

    @pytest.mark.asyncio
    async def test_code_search_query(self, db_session):
        service = NLQueryService(db=db_session)
        result = await service.query("Which code files handle user consent?")
        assert result.intent == QueryIntent.CODE_SEARCH
        assert len(result.code_references) > 0

    @pytest.mark.asyncio
    async def test_follow_up_suggestions(self, db_session):
        service = NLQueryService(db=db_session)
        result = await service.query("What is our compliance status?")
        assert len(result.follow_up_suggestions) > 0


class TestRemediationWorkflowService:
    @pytest.mark.asyncio
    async def test_create_workflow(self, db_session):
        service = RemediationWorkflowService(db=db_session)
        wf = await service.create_workflow(
            title="Fix GDPR consent", violation_id="VIO-001",
            framework="gdpr", repository="test/repo",
        )
        assert wf.state == WorkflowState.DETECTED
        assert wf.violation_id == "VIO-001"

    @pytest.mark.asyncio
    async def test_generate_fixes(self, db_session):
        service = RemediationWorkflowService(db=db_session)
        wf = await service.create_workflow(
            title="Fix GDPR", violation_id="VIO-002", framework="gdpr", repository="test/repo",
        )
        wf = await service.generate_fixes(wf.id)
        assert wf.state == WorkflowState.REVIEW
        assert len(wf.fixes) > 0
        assert wf.rollback_available is True

    @pytest.mark.asyncio
    async def test_full_workflow_cycle(self, db_session):
        service = RemediationWorkflowService(db=db_session)
        wf = await service.create_workflow(
            title="Fix PCI", violation_id="VIO-003", framework="pci_dss", repository="test/repo",
        )
        wf = await service.generate_fixes(wf.id)
        wf = await service.approve_workflow(wf.id, "admin@test.com")
        assert wf.state == WorkflowState.APPROVED
        wf = await service.merge_workflow(wf.id)
        assert wf.state == WorkflowState.COMPLETED
        assert wf.pr_number is not None


class TestPostureScoringService:
    @pytest.mark.asyncio
    async def test_compute_score(self, db_session):
        service = PostureScoringService(db=db_session)
        score = await service.compute_score(industry="fintech")
        assert 0 <= score.overall_score <= 100
        assert score.grade in ("A+", "A", "A-", "B+", "B", "B-", "C+", "C", "D", "F")
        assert len(score.dimensions) >= 7

    @pytest.mark.asyncio
    async def test_get_benchmark(self, db_session):
        service = PostureScoringService(db=db_session)
        benchmark = await service.get_benchmark("fintech")
        assert benchmark is not None
        assert benchmark.sample_size > 0

    @pytest.mark.asyncio
    async def test_generate_report(self, db_session):
        service = PostureScoringService(db=db_session)
        report = await service.generate_report(industry="saas")
        assert report.title != ""
        assert report.posture.overall_score > 0
        assert len(report.highlights) > 0 or len(report.action_items) > 0


class TestOrgHierarchyService:
    @pytest.mark.asyncio
    async def test_create_node(self, db_session):
        service = OrgHierarchyService(db=db_session)
        node = await service.create_node("Acme Corp", OrgNodeType.ROOT)
        assert node.name == "Acme Corp"
        assert node.depth == 0

    @pytest.mark.asyncio
    async def test_parent_child_hierarchy(self, db_session):
        service = OrgHierarchyService(db=db_session)
        root = await service.create_node("Corp", OrgNodeType.ROOT)
        child = await service.create_node("Engineering", OrgNodeType.BUSINESS_UNIT, parent_id=root.id)
        assert child.depth == 1
        assert child.parent_id == root.id

    @pytest.mark.asyncio
    async def test_add_member(self, db_session):
        service = OrgHierarchyService(db=db_session)
        node = await service.create_node("Team", OrgNodeType.TEAM)
        member = await service.add_member(uuid4(), "user@test.com", node.id, OrgRole.DEVELOPER)
        assert member.user_email == "user@test.com"
        assert member.role == OrgRole.DEVELOPER

    @pytest.mark.asyncio
    async def test_policy_inheritance(self, db_session):
        service = OrgHierarchyService(db=db_session)
        root = await service.create_node("Corp", OrgNodeType.ROOT, policies={"encryption": "required"})
        child = await service.create_node("Team", OrgNodeType.TEAM, parent_id=root.id)
        policies = await service.get_effective_policies(child.id)
        assert "encryption" in policies


class TestPolicySDKService:
    @pytest.mark.asyncio
    async def test_list_builtin_policies(self, db_session):
        service = PolicySDKService(db=db_session)
        policies = await service.list_policies()
        assert len(policies) >= 5

    @pytest.mark.asyncio
    async def test_create_custom_policy(self, db_session):
        service = PolicySDKService(db=db_session)
        policy = await service.create_policy(
            name="my-policy", description="Custom test policy",
            source_code="rules:\n  - id: test\n    pattern: 'test()'",
        )
        assert policy.name == "my-policy"

    @pytest.mark.asyncio
    async def test_validate_policy(self, db_session):
        service = PolicySDKService(db=db_session)
        policy = await service.create_policy(
            name="valid-policy", description="Test",
            source_code="rules:\n  - id: check\n    pattern: 'x()'",
        )
        result = await service.validate_policy(policy.id)
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_sdk_info(self, db_session):
        service = PolicySDKService(db=db_session)
        sdks = await service.get_sdk_info()
        assert len(sdks) >= 3
        langs = {s["language"] for s in sdks}
        assert "python" in langs


class TestAuditAutopilotService:
    @pytest.mark.asyncio
    async def test_gap_analysis_soc2(self, db_session):
        service = AuditAutopilotService(db=db_session)
        analysis = await service.run_gap_analysis(AuditFramework.SOC2_TYPE2)
        assert analysis.total_controls > 0
        assert 0 <= analysis.readiness_score <= 100

    @pytest.mark.asyncio
    async def test_evidence_package(self, db_session):
        service = AuditAutopilotService(db=db_session)
        package = await service.generate_evidence_package(AuditFramework.HIPAA)
        assert package.total_controls > 0
        assert package.coverage_percent >= 0

    @pytest.mark.asyncio
    async def test_readiness_report(self, db_session):
        service = AuditAutopilotService(db=db_session)
        report = await service.generate_readiness_report(AuditFramework.ISO_27001)
        assert report.overall_readiness > 0
        assert len(report.recommendations) > 0

    @pytest.mark.asyncio
    async def test_list_frameworks(self, db_session):
        service = AuditAutopilotService(db=db_session)
        frameworks = await service.list_supported_frameworks()
        assert len(frameworks) >= 4


class TestImpactTimelineService:
    @pytest.mark.asyncio
    async def test_get_timeline(self, db_session):
        service = ImpactTimelineService(db=db_session)
        view = await service.get_timeline()
        assert view.total_events > 0
        assert view.total_effort_hours > 0

    @pytest.mark.asyncio
    async def test_filter_timeline(self, db_session):
        service = ImpactTimelineService(db=db_session)
        view = await service.get_timeline(framework="gdpr")
        for event in view.events:
            assert event.framework == "gdpr"

    @pytest.mark.asyncio
    async def test_generate_tasks(self, db_session):
        service = ImpactTimelineService(db=db_session)
        view = await service.get_timeline()
        event = view.events[0]
        tasks = await service.generate_tasks(event.id)
        assert len(tasks) >= 3
        assert all(t.priority.value in ("critical", "high", "medium", "low") for t in tasks)


class TestComplianceIntelService:
    @pytest.mark.asyncio
    async def test_join_network(self, db_session):
        service = ComplianceIntelService(db=db_session)
        participant = await service.join_network("TestOrg", "fintech")
        assert participant.organization_name == "TestOrg"
        assert participant.status.value == "active"

    @pytest.mark.asyncio
    async def test_contribute_pattern(self, db_session):
        service = ComplianceIntelService(db=db_session)
        p = await service.join_network("ContribOrg", "saas")
        pattern = await service.contribute_pattern(
            p.id, "gdpr", "Art.25", "Encryption-first architecture", 85.0,
        )
        assert pattern is not None
        assert pattern.noise_applied is True

    @pytest.mark.asyncio
    async def test_get_insights(self, db_session):
        service = ComplianceIntelService(db=db_session)
        insights = await service.get_insights(industry="saas")
        assert len(insights) > 0

    @pytest.mark.asyncio
    async def test_similar_orgs(self, db_session):
        service = ComplianceIntelService(db=db_session)
        insights = await service.get_similar_orgs_insights("fintech")
        assert len(insights) > 0


class TestSelfHostedService:
    @pytest.mark.asyncio
    async def test_generate_license(self, db_session):
        service = SelfHostedService(db=db_session)
        license = await service.generate_license("TestOrg", LicenseType.TRIAL)
        assert license.license_key.startswith("CA-TRIAL-")
        assert license.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_license(self, db_session):
        service = SelfHostedService(db=db_session)
        lic = await service.generate_license("TestOrg", LicenseType.STANDARD)
        validated = await service.validate_license(lic.license_key)
        assert validated is not None
        assert validated.is_valid is True

    @pytest.mark.asyncio
    async def test_configure_deployment(self, db_session):
        service = SelfHostedService(db=db_session)
        config = await service.configure_deployment(
            mode=DeploymentMode.AIR_GAPPED, local_llm_enabled=True,
        )
        assert config.mode == DeploymentMode.AIR_GAPPED
        assert config.local_llm_enabled is True
        assert config.local_llm_model != ""

    @pytest.mark.asyncio
    async def test_offline_bundles(self, db_session):
        service = SelfHostedService(db=db_session)
        bundles = await service.list_offline_bundles()
        assert len(bundles) >= 4

    @pytest.mark.asyncio
    async def test_system_health(self, db_session):
        service = SelfHostedService(db=db_session)
        health = await service.get_system_health()
        assert health.status in ("healthy", "degraded")
        assert health.database_connected is True

    @pytest.mark.asyncio
    async def test_helm_values(self, db_session):
        service = SelfHostedService(db=db_session)
        values = await service.get_helm_values()
        assert "replicaCount" in values
        assert "image" in values
