"""Tests for Round 3 Next-Gen Strategic Features (9 new services)."""

from uuid import uuid4

import pytest

from app.services.audit_workspace import AuditWorkspaceService
from app.services.audit_workspace.service import AuditFramework, WorkspacePhase
from app.services.board_reports import BoardReportsService
from app.services.compliance_knowledge_graph import ComplianceKnowledgeGraphService
from app.services.control_testing import ControlFramework, ControlTestingService, TestStatus
from app.services.dependency_scanner import DependencyScannerService
from app.services.entity_rollup import EntityRollupService
from app.services.gitops_pipeline import GitOpsPipelineService
from app.services.horizon_scanner import (
    ConfidenceLevel,
    HorizonScannerService,
    ImpactSeverity,
    LegislativeSource,
    LegislativeStatus,
    PendingLegislation,
)
from app.services.residency_map import ResidencyMapService


# ─── Horizon Scanner ──────────────────────────────────────────────────────


class TestHorizonScannerService:
    @pytest.mark.asyncio
    async def test_get_timeline(self, db_session):
        svc = HorizonScannerService(db=db_session)
        timeline = await svc.get_timeline()
        assert timeline.total_tracked >= 8
        assert len(timeline.upcoming) > 0
        assert len(timeline.alerts) > 0
        assert timeline.high_impact_count > 0

    @pytest.mark.asyncio
    async def test_timeline_filter_by_jurisdiction(self, db_session):
        svc = HorizonScannerService(db=db_session)
        eu_timeline = await svc.get_timeline(jurisdiction="EU")
        assert all(l.jurisdiction == "EU" for l in eu_timeline.upcoming)

    @pytest.mark.asyncio
    async def test_timeline_filter_by_framework(self, db_session):
        svc = HorizonScannerService(db=db_session)
        timeline = await svc.get_timeline(framework="GDPR")
        for item in timeline.upcoming:
            assert any("GDPR" in fw for fw in item.frameworks_affected)

    @pytest.mark.asyncio
    async def test_predict_impact_heuristic(self, db_session):
        svc = HorizonScannerService(db=db_session)
        timeline = await svc.get_timeline()
        first_id = timeline.upcoming[0].id
        prediction = await svc.predict_impact(first_id)
        assert prediction.affected_files > 0
        assert prediction.estimated_effort_days > 0
        assert len(prediction.recommendations) > 0
        assert prediction.confidence_score > 0

    @pytest.mark.asyncio
    async def test_predict_impact_nonexistent(self, db_session):
        svc = HorizonScannerService(db=db_session)
        prediction = await svc.predict_impact(uuid4())
        assert prediction.affected_files == 0

    @pytest.mark.asyncio
    async def test_add_legislation(self, db_session):
        svc = HorizonScannerService(db=db_session)
        leg = PendingLegislation(
            title="Test Regulation",
            jurisdiction="US",
            source=LegislativeSource.CONGRESS_GOV,
            status=LegislativeStatus.DRAFT,
            confidence=ConfidenceLevel.LOW,
            frameworks_affected=["CCPA"],
        )
        result = await svc.add_legislation(leg)
        assert result.title == "Test Regulation"
        assert result.discovered_at is not None

        fetched = await svc.get_legislation(result.id)
        assert fetched is not None
        assert fetched.title == "Test Regulation"

    @pytest.mark.asyncio
    async def test_get_alerts_filter(self, db_session):
        svc = HorizonScannerService(db=db_session)
        high_alerts = await svc.get_alerts(severity=ImpactSeverity.HIGH)
        assert all(a.severity == ImpactSeverity.HIGH for a in high_alerts)


# ─── Continuous Control Testing ───────────────────────────────────────────


class TestControlTestingService:
    @pytest.mark.asyncio
    async def test_get_soc2_suite(self, db_session):
        svc = ControlTestingService(db=db_session)
        suite = await svc.get_test_suite(ControlFramework.SOC2)
        assert suite.total_tests == 13
        assert suite.framework == ControlFramework.SOC2

    @pytest.mark.asyncio
    async def test_get_iso_suite(self, db_session):
        svc = ControlTestingService(db=db_session)
        suite = await svc.get_test_suite(ControlFramework.ISO27001)
        assert suite.total_tests == 7

    @pytest.mark.asyncio
    async def test_get_hipaa_suite(self, db_session):
        svc = ControlTestingService(db=db_session)
        suite = await svc.get_test_suite(ControlFramework.HIPAA)
        assert suite.total_tests == 6

    @pytest.mark.asyncio
    async def test_run_single_test(self, db_session):
        svc = ControlTestingService(db=db_session)
        suite = await svc.get_test_suite(ControlFramework.SOC2)
        test = suite.tests[0]
        result = await svc.run_test(test.id)
        assert result.status == TestStatus.PASSING
        assert result.control_id == test.control_id
        assert result.duration_ms >= 0
        assert result.evidence_data

    @pytest.mark.asyncio
    async def test_run_suite(self, db_session):
        svc = ControlTestingService(db=db_session)
        results = await svc.run_suite(ControlFramework.SOC2)
        assert len(results) == 13
        assert all(r.status == TestStatus.PASSING for r in results)

    @pytest.mark.asyncio
    async def test_run_nonexistent_test(self, db_session):
        svc = ControlTestingService(db=db_session)
        result = await svc.run_test(uuid4())
        assert result.status == TestStatus.ERROR

    @pytest.mark.asyncio
    async def test_get_results_history(self, db_session):
        svc = ControlTestingService(db=db_session)
        suite = await svc.get_test_suite(ControlFramework.SOC2)
        await svc.run_test(suite.tests[0].id)
        results = await svc.get_results(control_id=suite.tests[0].control_id)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_suite_coverage_after_run(self, db_session):
        svc = ControlTestingService(db=db_session)
        await svc.run_suite(ControlFramework.SOC2)
        suite = await svc.get_test_suite(ControlFramework.SOC2)
        assert suite.passing == 13
        assert suite.coverage_pct == 100.0


# ─── Compliance Knowledge Graph ───────────────────────────────────────────


class TestComplianceKnowledgeGraphService:
    @pytest.mark.asyncio
    async def test_get_stats(self, db_session):
        svc = ComplianceKnowledgeGraphService(db=db_session)
        stats = await svc.get_stats()
        assert stats.total_nodes >= 19
        assert stats.total_edges >= 17
        assert "GDPR" in stats.frameworks_covered
        assert "HIPAA" in stats.frameworks_covered
        assert "SOC 2" in stats.frameworks_covered

    @pytest.mark.asyncio
    async def test_query_gdpr(self, db_session):
        svc = ComplianceKnowledgeGraphService(db=db_session)
        result = await svc.query("GDPR erasure")
        assert result.total_nodes > 0
        assert result.interpretation

    @pytest.mark.asyncio
    async def test_query_hipaa(self, db_session):
        svc = ComplianceKnowledgeGraphService(db=db_session)
        result = await svc.query("HIPAA encryption safeguards")
        assert result.total_nodes > 0

    @pytest.mark.asyncio
    async def test_query_no_results(self, db_session):
        svc = ComplianceKnowledgeGraphService(db=db_session)
        result = await svc.query("zz")
        assert result.total_nodes == 0

    @pytest.mark.asyncio
    async def test_get_neighbors(self, db_session):
        svc = ComplianceKnowledgeGraphService(db=db_session)
        await svc.get_stats()
        # Get first node
        for node_id in svc._nodes:
            result = await svc.get_neighbors(node_id)
            if result.total_nodes > 0:
                assert result.total_edges > 0
                break

    @pytest.mark.asyncio
    async def test_get_node(self, db_session):
        svc = ComplianceKnowledgeGraphService(db=db_session)
        for node_id, node in svc._nodes.items():
            fetched = await svc.get_node(node_id)
            assert fetched is not None
            assert fetched.label == node.label
            break


# ─── Multi-Entity Rollup ──────────────────────────────────────────────────


class TestEntityRollupService:
    @pytest.mark.asyncio
    async def test_get_hierarchy(self, db_session):
        svc = EntityRollupService(db=db_session)
        entities = await svc.get_hierarchy()
        assert len(entities) == 5
        root = [e for e in entities if e.level == 0]
        assert len(root) == 1
        assert root[0].name == "Acme Corp"

    @pytest.mark.asyncio
    async def test_compute_rollup_root(self, db_session):
        svc = EntityRollupService(db=db_session)
        entities = await svc.get_hierarchy()
        root = next(e for e in entities if e.level == 0)
        rollup = await svc.compute_rollup(root.id)
        assert rollup.entity_name == "Acme Corp"
        assert rollup.aggregated_score > 0
        assert rollup.total_members >= 500
        assert len(rollup.child_scores) == 2

    @pytest.mark.asyncio
    async def test_compute_rollup_leaf(self, db_session):
        svc = EntityRollupService(db=db_session)
        entities = await svc.get_hierarchy()
        leaf = next(e for e in entities if e.level == 2)
        rollup = await svc.compute_rollup(leaf.id)
        assert rollup.own_score == rollup.aggregated_score
        assert len(rollup.child_scores) == 0

    @pytest.mark.asyncio
    async def test_resolve_policies_inheritance(self, db_session):
        svc = EntityRollupService(db=db_session)
        entities = await svc.get_hierarchy()
        child = next(e for e in entities if e.level == 2)
        policies = await svc.resolve_policies(child.id)
        assert len(policies.effective_frameworks) > 0
        # Should inherit parent frameworks
        assert len(policies.effective_frameworks) >= len(child.frameworks)

    @pytest.mark.asyncio
    async def test_rollup_nonexistent(self, db_session):
        svc = EntityRollupService(db=db_session)
        rollup = await svc.compute_rollup(uuid4())
        assert rollup.entity_name == ""


# ─── Board Reports ────────────────────────────────────────────────────────


class TestBoardReportsService:
    @pytest.mark.asyncio
    async def test_generate_executive_summary(self, db_session):
        svc = BoardReportsService(db=db_session)
        summary = await svc.generate_executive_summary("test-org")
        assert summary.overall_score > 0
        assert summary.overall_status in ("green", "yellow", "red")
        assert len(summary.highlights) == 4
        assert len(summary.top_risks) > 0
        assert len(summary.action_items) > 0
        assert summary.narrative

    @pytest.mark.asyncio
    async def test_generate_board_report_html(self, db_session):
        svc = BoardReportsService(db=db_session)
        report = await svc.generate_board_report("test-org", report_format="html")
        assert report.content
        assert "<!DOCTYPE html>" in report.content
        assert "ComplianceAgent" in report.content
        assert report.framework_scores
        assert report.compliance_trend

    @pytest.mark.asyncio
    async def test_generate_board_report_json(self, db_session):
        svc = BoardReportsService(db=db_session)
        report = await svc.generate_board_report("test-org", report_format="json")
        assert report.framework_scores
        assert report.upcoming_deadlines
        assert report.budget_summary
        assert report.budget_summary["total_compliance_budget"] > 0

    @pytest.mark.asyncio
    async def test_narrative_fallback_without_copilot(self, db_session):
        svc = BoardReportsService(db=db_session, copilot_client=None)
        summary = await svc.generate_executive_summary("test-org")
        assert "compliance posture" in summary.narrative.lower() or "%" in summary.narrative

    @pytest.mark.asyncio
    async def test_custom_period_and_frameworks(self, db_session):
        svc = BoardReportsService(db=db_session)
        summary = await svc.generate_executive_summary(
            "test-org", period="Q4 2025", frameworks=["GDPR", "SOC 2"]
        )
        assert summary.period == "Q4 2025"
        assert len(summary.highlights) == 2


# ─── GitOps Pipeline ──────────────────────────────────────────────────────


class TestGitOpsPipelineService:
    @pytest.mark.asyncio
    async def test_evaluate_gate_pass(self, db_session):
        svc = GitOpsPipelineService(db=db_session)
        result = await svc.evaluate_gate(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            changed_files=[{"path": "src/math.py", "content": "x = 1 + 2"}],
        )
        assert result.decision.value == "pass"
        assert result.score_delta == 0.0
        assert len(result.violations) == 0

    @pytest.mark.asyncio
    async def test_evaluate_gate_block_critical(self, db_session):
        svc = GitOpsPipelineService(db=db_session)
        result = await svc.evaluate_gate(
            repo="test/repo",
            branch="main",
            commit_sha="def456",
            changed_files=[
                {"path": "src/data.py", "content": "credit_card = user.card_number\ncvv = input()"}
            ],
        )
        assert result.decision.value == "block"
        assert len(result.violations) > 0
        assert any(v["severity"] == "critical" for v in result.violations)

    @pytest.mark.asyncio
    async def test_evaluate_gate_warn(self, db_session):
        svc = GitOpsPipelineService(db=db_session)
        result = await svc.evaluate_gate(
            repo="test/repo",
            branch="main",
            commit_sha="ghi789",
            changed_files=[
                {"path": "src/security.py", "content": "# nosec\nsecurity_disable = True"}
            ],
        )
        assert result.decision.value in ("warn", "block")

    @pytest.mark.asyncio
    async def test_create_remediation_branch(self, db_session):
        svc = GitOpsPipelineService(db=db_session)
        branch = await svc.create_remediation_branch(
            repo="test/repo",
            violations=[{"rule_id": "PCI-DSS-001", "severity": "critical"}],
        )
        assert branch.remediation_branch.startswith("compliance/remediation-")
        assert branch.status.value == "branch_created"
        assert "PCI-DSS-001" in branch.violation_ids

    @pytest.mark.asyncio
    async def test_precommit_config(self, db_session):
        svc = GitOpsPipelineService(db=db_session)
        config = await svc.get_precommit_config()
        assert len(config.enabled_rules) >= 6
        assert config.max_scan_time_ms == 2000

    @pytest.mark.asyncio
    async def test_evaluations_history(self, db_session):
        svc = GitOpsPipelineService(db=db_session)
        await svc.evaluate_gate(
            repo="test/repo",
            branch="main",
            commit_sha="aaa",
            changed_files=[{"path": "x.py", "content": "x = 1"}],
        )
        evals = await svc.get_evaluations(repo="test/repo")
        assert len(evals) >= 1


# ─── Data Residency Map ──────────────────────────────────────────────────


class TestResidencyMapService:
    @pytest.mark.asyncio
    async def test_get_report(self, db_session):
        svc = ResidencyMapService(db=db_session)
        report = await svc.get_residency_report()
        assert report.total_flows >= 7
        assert report.compliant > 0
        assert report.violations > 0
        assert len(report.jurisdictions_involved) > 0

    @pytest.mark.asyncio
    async def test_check_transfer_compliant(self, db_session):
        svc = ResidencyMapService(db=db_session)
        flow = await svc.check_transfer("EU", "UK", ["personal_data"])
        assert flow.status.value == "compliant"

    @pytest.mark.asyncio
    async def test_check_transfer_review_needed(self, db_session):
        svc = ResidencyMapService(db=db_session)
        flow = await svc.check_transfer("EU", "US", ["personal_data"])
        assert flow.status.value == "review_needed"
        assert len(flow.violations) > 0

    @pytest.mark.asyncio
    async def test_check_transfer_violation_china(self, db_session):
        svc = ResidencyMapService(db=db_session)
        flow = await svc.check_transfer("CN", "US", ["personal_data"])
        assert flow.status.value == "violation"
        assert any("PIPL" in v or "local" in v.lower() for v in flow.violations)

    @pytest.mark.asyncio
    async def test_check_transfer_health_data(self, db_session):
        svc = ResidencyMapService(db=db_session)
        flow = await svc.check_transfer("US", "IN", ["health_data"])
        assert flow.status.value == "review_needed"
        assert any("HIPAA" in v for v in flow.violations)

    @pytest.mark.asyncio
    async def test_check_unknown_jurisdiction(self, db_session):
        svc = ResidencyMapService(db=db_session)
        flow = await svc.check_transfer("XX", "YY", ["personal_data"])
        assert flow.status.value == "unknown"

    @pytest.mark.asyncio
    async def test_resolve_cloud_region(self, db_session):
        svc = ResidencyMapService(db=db_session)
        assert await svc.resolve_cloud_region("us-east-1") == "US"
        assert await svc.resolve_cloud_region("eu-west-1") == "EU"
        assert await svc.resolve_cloud_region("ap-southeast-1") == "SG"
        assert await svc.resolve_cloud_region("cn-north-1") == "CN"
        assert await svc.resolve_cloud_region("unknown-region") == "UNKNOWN"

    @pytest.mark.asyncio
    async def test_get_jurisdictions(self, db_session):
        svc = ResidencyMapService(db=db_session)
        jurisdictions = await svc.get_jurisdictions()
        assert len(jurisdictions) >= 11
        codes = [j.code for j in jurisdictions]
        assert "EU" in codes
        assert "US" in codes
        assert "CN" in codes


# ─── Dependency Scanner ───────────────────────────────────────────────────


class TestDependencyScannerService:
    @pytest.mark.asyncio
    async def test_scan_clean_dependencies(self, db_session):
        svc = DependencyScannerService(db=db_session)
        result = await svc.scan_requirements(
            [
                {"name": "fastapi", "version": "0.109.0", "license": "MIT"},
                {"name": "pydantic", "version": "2.6.0", "license": "MIT"},
            ]
        )
        assert result.total_dependencies == 2
        assert result.critical_risks == 0
        assert result.license_violations == 0

    @pytest.mark.asyncio
    async def test_scan_copyleft_violation(self, db_session):
        svc = DependencyScannerService(db=db_session)
        result = await svc.scan_requirements(
            [
                {"name": "some-gpl-lib", "version": "1.0", "license": "GPL-3.0"},
            ],
            proprietary_project=True,
        )
        assert result.critical_risks == 1
        assert result.license_violations == 1
        assert result.risks[0].risk_level.value == "critical"
        assert "copyleft" in result.risks[0].issues[0].lower()

    @pytest.mark.asyncio
    async def test_scan_copyleft_ok_in_oss(self, db_session):
        svc = DependencyScannerService(db=db_session)
        result = await svc.scan_requirements(
            [
                {"name": "some-gpl-lib", "version": "1.0", "license": "GPL-3.0"},
            ],
            proprietary_project=False,
        )
        assert result.critical_risks == 0

    @pytest.mark.asyncio
    async def test_scan_data_sharing_sdk(self, db_session):
        svc = DependencyScannerService(db=db_session)
        result = await svc.scan_requirements(
            [
                {"name": "mixpanel", "version": "4.0", "license": "MIT"},
            ]
        )
        assert result.data_sharing_count == 1
        assert result.high_risks >= 1
        assert result.risks[0].data_sharing is True

    @pytest.mark.asyncio
    async def test_scan_deprecated_crypto(self, db_session):
        svc = DependencyScannerService(db=db_session)
        result = await svc.scan_requirements(
            [
                {"name": "pycrypto", "version": "2.6", "license": "MIT"},
            ]
        )
        assert result.deprecated_crypto_count == 1
        assert result.risks[0].deprecated_crypto is True

    @pytest.mark.asyncio
    async def test_scan_unknown_license(self, db_session):
        svc = DependencyScannerService(db=db_session)
        result = await svc.scan_requirements(
            [
                {"name": "mystery-pkg", "version": "1.0", "license": "UNKNOWN"},
            ]
        )
        assert result.license_violations == 1

    @pytest.mark.asyncio
    async def test_scan_history(self, db_session):
        svc = DependencyScannerService(db=db_session)
        await svc.scan_requirements([{"name": "a", "version": "1", "license": "MIT"}])
        await svc.scan_requirements([{"name": "b", "version": "2", "license": "MIT"}])
        history = await svc.get_scan_history()
        assert len(history) == 2


# ─── Audit Workspace ─────────────────────────────────────────────────────


class TestAuditWorkspaceService:
    @pytest.mark.asyncio
    async def test_create_workspace(self, db_session):
        svc = AuditWorkspaceService(db=db_session)
        ws = await svc.create_workspace("test-org", AuditFramework.SOC2_TYPE_II)
        assert ws.org_id == "test-org"
        assert ws.framework == AuditFramework.SOC2_TYPE_II
        assert ws.phase == WorkspacePhase.GAP_ANALYSIS

    @pytest.mark.asyncio
    async def test_run_gap_analysis(self, db_session):
        svc = AuditWorkspaceService(db=db_session)
        ws = await svc.create_workspace("test-org", AuditFramework.SOC2_TYPE_II)
        result = await svc.run_gap_analysis(ws.id)
        assert result.total_controls >= 18
        assert result.fully_met + result.partially_met + result.not_met == result.total_controls
        assert 0 <= result.readiness_pct <= 100
        assert result.estimated_remediation_days > 0
        assert len(result.gaps) == result.total_controls

    @pytest.mark.asyncio
    async def test_gap_analysis_updates_workspace(self, db_session):
        svc = AuditWorkspaceService(db=db_session)
        ws = await svc.create_workspace("test-org", AuditFramework.SOC2_TYPE_II)
        await svc.run_gap_analysis(ws.id)
        ws = await svc.get_workspace(ws.id)
        assert ws.gap_analysis is not None
        assert ws.evidence_coverage_pct > 0

    @pytest.mark.asyncio
    async def test_advance_phase(self, db_session):
        svc = AuditWorkspaceService(db=db_session)
        ws = await svc.create_workspace("test-org", AuditFramework.SOC2_TYPE_II)
        assert ws.phase == WorkspacePhase.GAP_ANALYSIS

        ws = await svc.advance_phase(ws.id)
        assert ws.phase == WorkspacePhase.EVIDENCE_COLLECTION

        ws = await svc.advance_phase(ws.id)
        assert ws.phase == WorkspacePhase.REMEDIATION

        ws = await svc.advance_phase(ws.id)
        assert ws.phase == WorkspacePhase.REVIEW

        ws = await svc.advance_phase(ws.id)
        assert ws.phase == WorkspacePhase.AUDIT_READY

        # Can't advance past audit_ready
        ws = await svc.advance_phase(ws.id)
        assert ws.phase == WorkspacePhase.AUDIT_READY

    @pytest.mark.asyncio
    async def test_advance_nonexistent(self, db_session):
        svc = AuditWorkspaceService(db=db_session)
        result = await svc.advance_phase(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_list_workspaces(self, db_session):
        svc = AuditWorkspaceService(db=db_session)
        await svc.create_workspace("org-a", AuditFramework.SOC2_TYPE_II)
        await svc.create_workspace("org-a", AuditFramework.ISO_27001)
        await svc.create_workspace("org-b", AuditFramework.HIPAA)

        org_a = await svc.list_workspaces("org-a")
        assert len(org_a) == 2

        org_b = await svc.list_workspaces("org-b")
        assert len(org_b) == 1

    @pytest.mark.asyncio
    async def test_gap_analysis_nonexistent_workspace(self, db_session):
        svc = AuditWorkspaceService(db=db_session)
        result = await svc.run_gap_analysis(uuid4())
        assert result.total_controls == 0
