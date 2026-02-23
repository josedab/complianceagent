"""Tests for Next-Gen v3 features (10 new capabilities)."""


import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auto_remediation.models import RemediationStatus, RiskLevel
from app.services.auto_remediation.service import AutoRemediationService
from app.services.compliance_badge.models import Grade
from app.services.compliance_badge.service import ComplianceBadgeService
from app.services.compliance_copilot.models import FixStatus
from app.services.compliance_copilot.service import ComplianceCopilotService
from app.services.compliance_export.models import ExportFormat, ExportStatus
from app.services.compliance_export.service import ComplianceExportService
from app.services.compliance_sdk.service import ComplianceSDKService
from app.services.github_app.models import AppPlan, InstallationStatus
from app.services.github_app.service import GitHubAppService
from app.services.mcp_server.models import ToolCategory, ToolExecutionStatus
from app.services.mcp_server.service import MCPServerService
from app.services.multi_scm.models import SCMConnectionStatus, SCMProvider
from app.services.multi_scm.service import MultiSCMService
from app.services.reg_change_stream.models import ChangeSeverity, ChangeStatus, RegulatoryChange
from app.services.reg_change_stream.service import RegChangeStreamService
from app.services.regulation_diff_viz.models import DiffChangeType
from app.services.regulation_diff_viz.service import RegulationDiffVizService


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def mcp_service(db_session: AsyncSession):
    return MCPServerService(db=db_session)


@pytest_asyncio.fixture
async def github_app_service(db_session: AsyncSession):
    return GitHubAppService(db=db_session)


@pytest_asyncio.fixture
async def stream_service(db_session: AsyncSession):
    return RegChangeStreamService(db=db_session)


@pytest_asyncio.fixture
async def sdk_service(db_session: AsyncSession):
    return ComplianceSDKService(db=db_session)


@pytest_asyncio.fixture
async def copilot_service(db_session: AsyncSession):
    return ComplianceCopilotService(db=db_session)


@pytest_asyncio.fixture
async def remediation_service(db_session: AsyncSession):
    return AutoRemediationService(db=db_session)


@pytest_asyncio.fixture
async def scm_service(db_session: AsyncSession):
    return MultiSCMService(db=db_session)


@pytest_asyncio.fixture
async def badge_service(db_session: AsyncSession):
    return ComplianceBadgeService(db=db_session)


@pytest_asyncio.fixture
async def diff_service(db_session: AsyncSession):
    return RegulationDiffVizService(db=db_session)


@pytest_asyncio.fixture
async def export_service(db_session: AsyncSession):
    return ComplianceExportService(db=db_session)


# ── Feature 1: MCP Server ────────────────────────────────────────────────


class TestMCPServer:
    @pytest.mark.asyncio
    async def test_list_tools_returns_builtin(self, mcp_service: MCPServerService):
        tools = mcp_service.list_tools()
        assert len(tools) >= 7
        names = [t.name for t in tools]
        assert "compliance/get_posture" in names
        assert "compliance/check_file" in names

    @pytest.mark.asyncio
    async def test_list_tools_filter_by_category(self, mcp_service: MCPServerService):
        tools = mcp_service.list_tools(category=ToolCategory.REGULATIONS)
        assert all(t.category == ToolCategory.REGULATIONS for t in tools)

    @pytest.mark.asyncio
    async def test_execute_tool_success(self, mcp_service: MCPServerService):
        execution = await mcp_service.execute_tool(
            tool_name="compliance/list_regulations",
            params={"jurisdiction": "EU"},
            client_id="test-client",
        )
        assert execution.status == ToolExecutionStatus.SUCCESS
        assert "regulations" in execution.output
        assert execution.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_execute_unknown_tool_returns_error(self, mcp_service: MCPServerService):
        execution = await mcp_service.execute_tool(
            tool_name="nonexistent/tool", params={}, client_id="test",
        )
        assert execution.status == ToolExecutionStatus.ERROR
        assert "not found" in execution.error_message

    @pytest.mark.asyncio
    async def test_register_and_disconnect_client(self, mcp_service: MCPServerService):
        conn = await mcp_service.register_client("test-client", "Test Agent")
        assert conn.client_id == "test-client"
        ok = await mcp_service.disconnect_client("test-client")
        assert ok is True

    @pytest.mark.asyncio
    async def test_server_status(self, mcp_service: MCPServerService):
        status = mcp_service.get_server_status()
        assert status.tools_count >= 7
        assert status.resources_count >= 3
        assert status.protocol_version == "2024-11-05"

    @pytest.mark.asyncio
    async def test_read_resource(self, mcp_service: MCPServerService):
        resource = await mcp_service.read_resource("compliance://frameworks/supported")
        assert resource is not None
        assert resource.content is not None


# ── Feature 2: GitHub App ────────────────────────────────────────────────


class TestGitHubApp:
    @pytest.mark.asyncio
    async def test_handle_installation_creates(self, github_app_service: GitHubAppService):
        inst = await github_app_service.handle_installation(
            github_installation_id=12345,
            account_login="acme-corp",
            repositories=["acme-corp/api", "acme-corp/web"],
        )
        assert inst.github_installation_id == 12345
        assert inst.status == InstallationStatus.ACTIVE
        assert inst.plan == AppPlan.FREE

    @pytest.mark.asyncio
    async def test_handle_uninstall(self, github_app_service: GitHubAppService):
        await github_app_service.handle_installation(12345, "acme-corp")
        inst = await github_app_service.handle_installation(12345, "acme-corp", action="deleted")
        assert inst.status == InstallationStatus.UNINSTALLED

    @pytest.mark.asyncio
    async def test_process_pr_webhook(self, github_app_service: GitHubAppService):
        await github_app_service.handle_installation(1, "org")
        event = await github_app_service.process_webhook(
            event_type="pull_request",
            installation_id=1,
            payload={"repository": {"full_name": "org/repo"}, "pull_request": {"number": 42}},
        )
        assert event.processed is True
        assert "check_id" in event.result

    @pytest.mark.asyncio
    async def test_marketplace_listing(self, github_app_service: GitHubAppService):
        listing = github_app_service.get_marketplace_listing()
        assert listing.name == "ComplianceAgent"
        assert len(listing.plans) == 4

    @pytest.mark.asyncio
    async def test_update_plan(self, github_app_service: GitHubAppService):
        await github_app_service.handle_installation(1, "org")
        inst = await github_app_service.update_plan(1, "business")
        assert inst is not None
        assert inst.plan == AppPlan.BUSINESS


# ── Feature 3: Regulatory Change Stream ──────────────────────────────────


class TestRegChangeStream:
    @pytest.mark.asyncio
    async def test_publish_change(self, stream_service: RegChangeStreamService):
        change = RegulatoryChange(
            regulation="GDPR", jurisdiction="EU",
            title="Mandatory data portability update", summary="New mandatory requirements",
        )
        result = await stream_service.publish_change(change)
        assert result.status == ChangeStatus.NOTIFIED
        assert result.severity == ChangeSeverity.CRITICAL  # "mandatory" keyword

    @pytest.mark.asyncio
    async def test_subscribe_and_notify(self, stream_service: RegChangeStreamService):
        sub = await stream_service.subscribe(
            subscriber_id="eng-team", channel="webhook",
            severity_threshold="medium", jurisdictions=["EU"],
        )
        assert sub.is_active is True

        change = RegulatoryChange(regulation="GDPR", jurisdiction="EU", title="Penalty enforcement update")
        await stream_service.publish_change(change)

        stats = stream_service.get_stats()
        assert stats.notifications_sent >= 1

    @pytest.mark.asyncio
    async def test_unsubscribe(self, stream_service: RegChangeStreamService):
        await stream_service.subscribe("user1", "email")
        ok = await stream_service.unsubscribe("user1")
        assert ok is True

    @pytest.mark.asyncio
    async def test_acknowledge_change(self, stream_service: RegChangeStreamService):
        change = RegulatoryChange(regulation="HIPAA", jurisdiction="US", title="PHI update")
        result = await stream_service.publish_change(change)
        acked = await stream_service.acknowledge_change(result.id)
        assert acked is not None
        assert acked.status == ChangeStatus.ACKNOWLEDGED

    @pytest.mark.asyncio
    async def test_filter_by_severity(self, stream_service: RegChangeStreamService):
        await stream_service.publish_change(
            RegulatoryChange(regulation="GDPR", jurisdiction="EU", title="Minor clarification")
        )
        await stream_service.publish_change(
            RegulatoryChange(regulation="GDPR", jurisdiction="EU", title="Mandatory penalty change")
        )
        critical = stream_service.get_changes(severity=ChangeSeverity.CRITICAL)
        assert all(c.severity == ChangeSeverity.CRITICAL for c in critical)


# ── Feature 4: Compliance SDK ────────────────────────────────────────────


class TestComplianceSDK:
    @pytest.mark.asyncio
    async def test_create_and_validate_api_key(self, sdk_service: ComplianceSDKService):
        key, raw = await sdk_service.create_api_key("test-key", "org-1", tier="standard")
        assert key.name == "test-key"
        assert raw.startswith("ca_")
        validated = await sdk_service.validate_api_key(raw)
        assert validated is not None
        assert validated.id == key.id

    @pytest.mark.asyncio
    async def test_revoke_api_key(self, sdk_service: ComplianceSDKService):
        key, raw = await sdk_service.create_api_key("revoke-me", "org-1")
        ok = await sdk_service.revoke_api_key(key.id)
        assert ok is True
        validated = await sdk_service.validate_api_key(raw)
        assert validated is None

    @pytest.mark.asyncio
    async def test_list_sdk_packages(self, sdk_service: ComplianceSDKService):
        pkgs = sdk_service.list_sdk_packages()
        assert len(pkgs) == 3
        languages = {p.language.value for p in pkgs}
        assert "python" in languages
        assert "typescript" in languages

    @pytest.mark.asyncio
    async def test_usage_summary(self, sdk_service: ComplianceSDKService):
        await sdk_service.create_api_key("k1", "org-1", tier="free")
        await sdk_service.create_api_key("k2", "org-1", tier="professional")
        summary = sdk_service.get_usage_summary("org-1")
        assert summary.total_keys == 2
        assert summary.active_keys == 2


# ── Feature 5: AI Compliance Co-Pilot ────────────────────────────────────


class TestComplianceCopilot:
    @pytest.mark.asyncio
    async def test_start_session(self, copilot_service: ComplianceCopilotService):
        session = await copilot_service.start_session("org/repo", "user-1")
        assert session.repo == "org/repo"
        assert session.started_at is not None

    @pytest.mark.asyncio
    async def test_analyze_codebase(self, copilot_service: ComplianceCopilotService):
        analysis = await copilot_service.analyze_codebase("org/repo", frameworks=["GDPR", "HIPAA"])
        assert analysis.repo == "org/repo"
        assert len(analysis.violations) > 0
        assert analysis.score <= 100.0

    @pytest.mark.asyncio
    async def test_propose_and_accept_fix(self, copilot_service: ComplianceCopilotService):
        analysis = await copilot_service.analyze_codebase("org/repo", frameworks=["GDPR"])
        violation = analysis.violations[0]
        fix = await copilot_service.propose_fix(violation.id)
        assert fix.status == FixStatus.PROPOSED
        assert fix.confidence > 0

        accepted = await copilot_service.accept_fix(fix.id)
        assert accepted is not None
        assert accepted.status == FixStatus.ACCEPTED

    @pytest.mark.asyncio
    async def test_explain_regulation(self, copilot_service: ComplianceCopilotService):
        explanation = await copilot_service.explain_regulation("GDPR", "Art. 17")
        assert "erasure" in explanation.plain_language.lower() or "deletion" in explanation.plain_language.lower()
        assert len(explanation.technical_implications) > 0


# ── Feature 6: Auto-Remediation ──────────────────────────────────────────


class TestAutoRemediation:
    @pytest.mark.asyncio
    async def test_trigger_low_risk_pipeline(self, remediation_service: AutoRemediationService):
        pipeline = await remediation_service.trigger_pipeline(
            repo="org/api",
            violations=[{"file_path": "src/app.py", "severity": "low", "rule_id": "test", "framework": "GDPR", "message": "test"}],
        )
        assert pipeline.risk_level == RiskLevel.LOW
        assert pipeline.fixes_generated >= 1
        # Low risk auto-merges
        assert pipeline.status in (RemediationStatus.PR_CREATED, RemediationStatus.APPROVED)

    @pytest.mark.asyncio
    async def test_high_risk_requires_approval(self, remediation_service: AutoRemediationService):
        pipeline = await remediation_service.trigger_pipeline(
            repo="org/api",
            violations=[{"severity": "high", "file_path": "x.py", "rule_id": "r", "framework": "HIPAA", "message": "m"}],
        )
        assert pipeline.risk_level == RiskLevel.HIGH
        assert pipeline.status == RemediationStatus.AWAITING_APPROVAL

    @pytest.mark.asyncio
    async def test_approve_pipeline(self, remediation_service: AutoRemediationService):
        pipeline = await remediation_service.trigger_pipeline(
            repo="org/api",
            violations=[{"severity": "high", "file_path": "x.py", "rule_id": "r", "framework": "GDPR", "message": "m"}],
        )
        approved = await remediation_service.approve_pipeline(pipeline.id, "admin@org.com", "LGTM")
        assert approved is not None
        assert approved.status == RemediationStatus.PR_CREATED
        assert approved.pr_url != ""

    @pytest.mark.asyncio
    async def test_rollback_pipeline(self, remediation_service: AutoRemediationService):
        pipeline = await remediation_service.trigger_pipeline(repo="org/api", violations=[])
        rolled = await remediation_service.rollback_pipeline(pipeline.id)
        assert rolled is not None
        assert rolled.status == RemediationStatus.ROLLED_BACK


# ── Feature 7: Multi-SCM ─────────────────────────────────────────────────


class TestMultiSCM:
    @pytest.mark.asyncio
    async def test_connect_github(self, scm_service: MultiSCMService):
        conn = await scm_service.connect_provider("github", "acme-corp")
        assert conn.provider == SCMProvider.GITHUB
        assert conn.status == SCMConnectionStatus.CONNECTED

    @pytest.mark.asyncio
    async def test_connect_gitlab(self, scm_service: MultiSCMService):
        conn = await scm_service.connect_provider("gitlab", "acme-corp")
        assert conn.provider == SCMProvider.GITLAB

    @pytest.mark.asyncio
    async def test_sync_repositories(self, scm_service: MultiSCMService):
        await scm_service.connect_provider("github", "org")
        repos = await scm_service.sync_repositories("github", "org")
        assert len(repos) > 0
        assert all(r.provider == SCMProvider.GITHUB for r in repos)

    @pytest.mark.asyncio
    async def test_create_compliance_pr(self, scm_service: MultiSCMService):
        pr = await scm_service.create_compliance_pr(
            provider="github", repo_full_name="org/repo",
            title="fix: GDPR compliance", source_branch="compliance-fix",
        )
        assert pr.number >= 1
        assert pr.url != ""

    @pytest.mark.asyncio
    async def test_process_webhook(self, scm_service: MultiSCMService):
        wh = await scm_service.process_webhook(
            "github", "push", {"repository": {"full_name": "org/repo"}}
        )
        assert wh.processed is True


# ── Feature 8: Compliance Badge ──────────────────────────────────────────


class TestComplianceBadge:
    @pytest.mark.asyncio
    async def test_generate_badge_svg(self, badge_service: ComplianceBadgeService):
        badge = await badge_service.generate_badge("org/repo")
        assert badge.svg.startswith("<svg")
        assert badge.grade is not None
        assert badge.color != ""

    @pytest.mark.asyncio
    async def test_get_public_scorecard(self, badge_service: ComplianceBadgeService):
        sc = await badge_service.get_public_scorecard("org/repo")
        assert sc.overall_score > 0
        assert sc.overall_grade in Grade
        assert len(sc.frameworks) > 0

    @pytest.mark.asyncio
    async def test_embed_snippets(self, badge_service: ComplianceBadgeService):
        snippets = badge_service.get_embed_snippets("org/repo")
        assert len(snippets) == 3
        formats = {s.format for s in snippets}
        assert "markdown" in formats
        assert "html" in formats


# ── Feature 9: Regulation Diff Visualizer ─────────────────────────────────


class TestRegulationDiffViz:
    @pytest.mark.asyncio
    async def test_list_available_regulations(self, diff_service: RegulationDiffVizService):
        regs = diff_service.list_available_regulations()
        assert "GDPR" in regs
        assert "HIPAA" in regs

    @pytest.mark.asyncio
    async def test_list_versions(self, diff_service: RegulationDiffVizService):
        versions = diff_service.list_regulation_versions("GDPR")
        assert len(versions) >= 2

    @pytest.mark.asyncio
    async def test_compute_diff(self, diff_service: RegulationDiffVizService):
        result = await diff_service.compute_diff("GDPR")
        assert result.regulation == "GDPR"
        assert result.changed_sections > 0
        changed = [s for s in result.sections if s.change_type != DiffChangeType.UNCHANGED]
        assert len(changed) > 0

    @pytest.mark.asyncio
    async def test_diff_has_added_section(self, diff_service: RegulationDiffVizService):
        result = await diff_service.compute_diff("GDPR")
        added = [s for s in result.sections if s.change_type == DiffChangeType.ADDED]
        assert len(added) > 0
        assert added[0].section_id == "art-22a"

    @pytest.mark.asyncio
    async def test_add_annotation(self, diff_service: RegulationDiffVizService):
        result = await diff_service.compute_diff("GDPR")
        ann = await diff_service.add_annotation(
            diff_id=result.id, section_id="art-5",
            author="compliance-lead", comment="Need to update data processing docs",
            action_required=True,
        )
        assert ann.action_required is True
        anns = diff_service.get_annotations(result.id)
        assert len(anns) == 1


# ── Feature 10: Compliance Export ─────────────────────────────────────────


class TestComplianceExport:
    @pytest.mark.asyncio
    async def test_create_export(self, export_service: ComplianceExportService):
        job = await export_service.create_export(data_type="posture_scores", format="json")
        assert job.status == ExportStatus.COMPLETED
        assert job.row_count > 0
        assert job.download_url != ""

    @pytest.mark.asyncio
    async def test_create_csv_export(self, export_service: ComplianceExportService):
        job = await export_service.create_export(data_type="violations", format="csv")
        assert job.format == ExportFormat.CSV
        assert job.status == ExportStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_create_schedule(self, export_service: ComplianceExportService):
        sched = await export_service.create_schedule(
            name="Weekly Report", data_type="full_report", schedule_cron="0 0 * * 1",
        )
        assert sched.is_active is True
        assert sched.schedule_cron == "0 0 * * 1"

    @pytest.mark.asyncio
    async def test_configure_connector(self, export_service: ComplianceExportService):
        config = await export_service.configure_connector(
            connector="snowflake", database="compliance_db", schema="compliance",
        )
        assert config.status == "configured"
        connectors = export_service.list_connectors()
        assert len(connectors) == 1

    @pytest.mark.asyncio
    async def test_export_summary(self, export_service: ComplianceExportService):
        await export_service.create_export("posture_scores")
        await export_service.create_export("violations")
        summary = export_service.get_summary()
        assert summary.total_exports == 2
        assert summary.total_rows_exported > 0
