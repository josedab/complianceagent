"""Tests for next-gen feature implementations (Round 3).

Tests cover: PR bot GitHub API, SaaS trial flow, chat guardrails,
evidence vault auditor sessions, policy marketplace, infrastructure posture,
knowledge graph enrichment, prediction signal aggregation, and digital twin persistence.
"""

import pytest
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

pytestmark = pytest.mark.asyncio


# ============================================================================
# PR Bot GitHub API Tests
# ============================================================================


class TestPRBotGitHubAPI:
    """Test PR bot real GitHub API methods."""

    async def test_analyze_pr_returns_result(self):
        """Test that analyze_pr returns a well-structured result."""
        from app.services.pr_bot import PRBot, PRBotConfig

        config = PRBotConfig()
        bot = PRBot(config=config)

        result = await bot.analyze_pr(
            repo_owner="test-org",
            repo_name="test-repo",
            pr_number=42,
            head_sha="abc123def",
            token="test-token",
        )

        assert result["pr_number"] == 42
        assert result["repo"] == "test-org/test-repo"
        assert result["head_sha"] == "abc123def"
        assert result["status"] == "completed"
        assert "compliance_score" in result
        assert "findings" in result

    async def test_post_check_run(self):
        """Test that post_check_run makes correct HTTP call."""
        from app.services.pr_bot.checks import ChecksService

        service = ChecksService()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=MagicMock(
                status_code=201,
                json=MagicMock(return_value={"id": 1, "status": "completed"}),
                raise_for_status=MagicMock(),
            ))
            mock_client_cls.return_value = mock_client

            result = await service.post_check_run(
                repo_owner="test-org",
                repo_name="test-repo",
                head_sha="abc123",
                name="compliance-check",
                status="completed",
                conclusion="success",
                title="All clear",
                summary="No issues found",
                token="test-token",
            )

            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert "check-runs" in call_args[0][0]

    async def test_post_review_comment(self):
        """Test that post_review_comment makes correct HTTP call."""
        from app.services.pr_bot.comments import CommentService

        service = CommentService()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=MagicMock(
                status_code=201,
                json=MagicMock(return_value={"id": 1}),
                raise_for_status=MagicMock(),
            ))
            mock_client_cls.return_value = mock_client

            result = await service.post_review_comment(
                repo_owner="test-org",
                repo_name="test-repo",
                pr_number=42,
                body="GDPR issue detected",
                commit_id="abc123",
                path="src/auth.py",
                line=15,
                token="test-token",
            )

            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert "comments" in call_args[0][0]

    async def test_apply_labels_via_api(self):
        """Test that apply_labels_via_api makes correct HTTP call."""
        from app.services.pr_bot.labels import LabelService

        service = LabelService()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=MagicMock(
                status_code=200,
                json=MagicMock(return_value=[{"name": "compliance:pass"}]),
                raise_for_status=MagicMock(),
            ))
            mock_client_cls.return_value = mock_client

            result = await service.apply_labels_via_api(
                repo_owner="test-org",
                repo_name="test-repo",
                issue_number=42,
                labels=["compliance:pass"],
                token="test-token",
            )

            mock_client.post.assert_called_once()


# ============================================================================
# SaaS Platform Trial Flow Tests
# ============================================================================


class TestSaaSTrialFlow:
    """Test SaaS platform trial management."""

    @pytest.fixture
    def service(self):
        """Create SaaS platform service with mock DB."""
        from app.services.saas_platform.service import SaaSPlatformService
        mock_db = AsyncMock()
        return SaaSPlatformService(db=mock_db)

    async def test_start_trial(self, service):
        """Test starting a trial."""
        result = await service.start_trial(
            tenant_id="tenant-123",
            plan="professional",
            trial_days=14,
        )

        assert result["tenant_id"] == "tenant-123"
        assert result["status"] == "trial"
        assert result["plan"] == "professional"
        assert "trial_start" in result
        assert "trial_end" in result

    async def test_check_trial_status_active(self, service):
        """Test checking an active trial."""
        await service.start_trial(tenant_id="tenant-123", plan="professional", trial_days=14)
        result = await service.check_trial_status(tenant_id="tenant-123")

        assert result["status"] == "active"
        assert result["days_remaining"] > 0

    async def test_check_trial_status_not_found(self, service):
        """Test checking trial for non-existent tenant raises ValueError."""
        with pytest.raises(ValueError, match="No trial found"):
            await service.check_trial_status(tenant_id="nonexistent")

    async def test_convert_trial(self, service):
        """Test converting a trial to paid."""
        await service.start_trial(tenant_id="tenant-123", plan="professional")
        result = await service.convert_trial(tenant_id="tenant-123")

        assert result["status"] == "active"
        assert "converted_at" in result


# ============================================================================
# Chat Guardrails Tests
# ============================================================================


class TestChatGuardrails:
    """Test compliance chat guardrails."""

    @pytest.fixture
    def service(self):
        """Create copilot chat service with mock DB."""
        from app.services.copilot_chat.service import CopilotChatService
        mock_db = AsyncMock()
        return CopilotChatService(db=mock_db)

    async def test_guardrails_adds_disclaimer_for_regulations(self, service):
        """Test that guardrails add disclaimer when regulations mentioned."""
        response = "Under GDPR, data subjects have the right to erasure."
        result = await service.apply_guardrails(response)

        assert result["is_safe"] is True
        assert "legal advice" in result["modified"].lower()
        assert "added_legal_disclaimer" in result["guardrails_applied"]

    async def test_guardrails_no_disclaimer_for_general_text(self, service):
        """Test that guardrails don't add disclaimer for general text."""
        response = "Here is a general best practice for data handling."
        result = await service.apply_guardrails(response)

        assert result["modified"] == response
        assert len(result["guardrails_applied"]) == 0

    async def test_guardrails_detects_legal_absolutes(self, service):
        """Test that guardrails detect definitive legal claims."""
        response = "You must implement encryption. This is illegal without it."
        result = await service.apply_guardrails(response)

        assert any("softened_claim" in g for g in result["guardrails_applied"])

    async def test_extract_citations_with_matching_docs(self, service):
        """Test citation extraction with matching context docs."""
        response_text = "Under GDPR Article 17, the right to erasure applies."
        context_docs = [
            {"title": "GDPR", "reference": "Article 17", "keywords": ["gdpr", "erasure"]},
            {"title": "HIPAA", "reference": "164.312", "keywords": ["hipaa", "phi"]},
        ]
        citations = await service._extract_source_citations(response_text, context_docs)

        assert len(citations) >= 1
        assert citations[0]["source"] == "GDPR"


# ============================================================================
# Evidence Vault Auditor Portal Tests
# ============================================================================


class TestEvidenceVaultAuditor:
    """Test evidence vault auditor session management."""

    @pytest.fixture
    def service(self):
        """Create evidence vault service with mock DB."""
        from app.services.evidence_vault.service import EvidenceVaultService
        mock_db = AsyncMock()
        return EvidenceVaultService(db=mock_db)

    async def test_validate_nonexistent_session(self, service):
        """Test validating a session that doesn't exist."""
        result = await service.validate_auditor_session("nonexistent-id")
        assert result["valid"] is False

    async def test_revoke_nonexistent_session(self, service):
        """Test revoking a session that doesn't exist."""
        result = await service.revoke_auditor_session("nonexistent-id")
        assert result is False

    async def test_generate_readiness_report(self, service):
        """Test generating an audit readiness report."""
        from app.services.evidence_vault.models import ControlFramework
        report = await service.generate_readiness_report(ControlFramework.SOC2)

        assert report["framework"] == "soc2"
        assert "total_controls" in report
        assert "coverage_percentage" in report
        assert "readiness_score" in report
        assert report["readiness_score"] in ("ready", "needs_work", "not_ready")


# ============================================================================
# Policy Marketplace Tests
# ============================================================================


class TestPolicyMarketplace:
    """Test policy marketplace operations."""

    @pytest.fixture
    def service(self):
        """Create policy marketplace service."""
        from app.services.policy_marketplace.service import PolicyMarketplaceService
        return PolicyMarketplaceService()

    async def test_publish_policy(self, service):
        """Test publishing a policy pack."""
        result = await service.publish_policy({
            "name": "Test GDPR Policy",
            "description": "GDPR compliance rules",
            "framework": "gdpr",
            "version": "1.0.0",
            "author": "test-author",
            "rules": [{"id": "r1", "name": "Consent Check"}],
        })

        assert result["name"] == "Test GDPR Policy"
        assert result["status"] == "published"
        assert result["downloads"] == 0
        assert "id" in result

    async def test_rate_policy(self, service):
        """Test rating a published policy."""
        policy = await service.publish_policy({"name": "Test Policy", "framework": "gdpr"})
        
        result = await service.rate_policy(policy["id"], 4.5, "reviewer@test.com")
        assert result["new_rating"] == 4.5

        result2 = await service.rate_policy(policy["id"], 3.5, "other@test.com")
        assert result2["new_rating"] == 4.0  # average of 4.5 and 3.5
        assert result2["total_reviews"] == 2

    async def test_rate_nonexistent_policy(self, service):
        """Test rating a policy that doesn't exist."""
        result = await service.rate_policy("nonexistent-id", 5.0)
        assert "error" in result

    async def test_search_policies(self, service):
        """Test searching marketplace policies."""
        await service.publish_policy({"name": "GDPR Pack", "framework": "gdpr", "description": "GDPR rules"})
        await service.publish_policy({"name": "HIPAA Pack", "framework": "hipaa", "description": "HIPAA rules"})

        results = await service.search_policies(query="gdpr")
        assert len(results) == 1
        assert results[0]["name"] == "GDPR Pack"

        results_all = await service.search_policies()
        assert len(results_all) == 2

    async def test_search_by_framework(self, service):
        """Test searching by framework filter."""
        await service.publish_policy({"name": "GDPR Pack", "framework": "gdpr"})
        await service.publish_policy({"name": "HIPAA Pack", "framework": "hipaa"})

        results = await service.search_policies(framework="hipaa")
        assert len(results) == 1
        assert results[0]["framework"] == "hipaa"


# ============================================================================
# Policy-as-Code Generator Tests
# ============================================================================


class TestPolicyAsCodeGenerator:
    """Test policy-as-code bundle generation."""

    @pytest.fixture
    def generator(self):
        """Create policy generator."""
        from app.services.policy_as_code.generator import PolicyGenerator
        return PolicyGenerator()

    async def test_generate_yaml_bundle(self, generator):
        """Test YAML policy bundle generation."""
        result = await generator.generate_policy_bundle("gdpr", "yaml")

        assert result["framework"] == "gdpr"
        assert result["format"] == "yaml"
        assert "version" in result["content"]

    async def test_generate_rego_bundle(self, generator):
        """Test Rego policy bundle generation."""
        result = await generator.generate_policy_bundle("hipaa", "rego")

        assert result["format"] == "rego"
        assert "package" in result["content"]

    async def test_generate_python_bundle(self, generator):
        """Test Python policy bundle generation."""
        result = await generator.generate_policy_bundle("pci-dss", "python")

        assert result["format"] == "python"
        assert "def check_compliance" in result["content"]

    async def test_generate_typescript_bundle(self, generator):
        """Test TypeScript policy bundle generation."""
        result = await generator.generate_policy_bundle("soc2", "typescript")

        assert result["format"] == "typescript"
        assert "export" in result["content"]

    async def test_unsupported_format(self, generator):
        """Test unsupported format returns error."""
        result = await generator.generate_policy_bundle("gdpr", "java")

        assert "error" in result


# ============================================================================
# Infrastructure Multi-Cloud Posture Tests
# ============================================================================


class TestInfrastructurePosture:
    """Test infrastructure multi-cloud posture."""

    @pytest.fixture
    def analyzer(self):
        """Create infrastructure analyzer."""
        from app.services.infrastructure import get_infrastructure_analyzer
        return get_infrastructure_analyzer()

    async def test_get_multi_cloud_posture(self, analyzer):
        """Test getting multi-cloud posture summary."""
        posture = await analyzer.get_multi_cloud_posture()

        assert "providers" in posture
        assert "aws" in posture["providers"]
        assert "total_scans" in posture

    async def test_persist_and_get_scan_history(self, analyzer):
        """Test persisting and retrieving scan history."""
        await analyzer.persist_scan_results({
            "providers": {"aws": {"violation_count": 3}},
            "total_violations": 3,
            "critical_count": 1,
        })

        history = await analyzer.get_scan_history()
        assert len(history) == 1
        assert history[0]["total_violations"] == 3

    async def test_scan_history_limit(self, analyzer):
        """Test scan history respects limit."""
        for i in range(5):
            await analyzer.persist_scan_results({
                "providers": {}, "total_violations": i, "critical_count": 0,
            })

        history = await analyzer.get_scan_history(limit=3)
        assert len(history) == 3


# ============================================================================
# Knowledge Graph Enrichment Tests
# ============================================================================


class TestKnowledgeGraphEnrichment:
    """Test knowledge graph evidence and risk node enrichment."""

    @pytest.fixture
    def service(self):
        """Create knowledge graph service with mock DB."""
        from app.services.knowledge_graph.service import KnowledgeGraphService
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        ))
        return KnowledgeGraphService(db=mock_db)

    async def test_build_graph_includes_controls(self, service):
        """Test that build_graph adds control nodes."""
        graph = await service.build_graph(organization_id=uuid4())

        from app.services.knowledge_graph.models import NodeType
        control_nodes = graph.nodes_by_type.get(NodeType.CONTROL, [])
        assert len(control_nodes) > 0

    async def test_build_graph_includes_risks(self, service):
        """Test that build_graph adds risk nodes."""
        graph = await service.build_graph(organization_id=uuid4())

        from app.services.knowledge_graph.models import NodeType
        risk_nodes = graph.nodes_by_type.get(NodeType.RISK, [])
        assert len(risk_nodes) == 4  # 4 risk categories

    async def test_risk_node_names(self, service):
        """Test risk node names are correct."""
        graph = await service.build_graph(organization_id=uuid4())

        from app.services.knowledge_graph.models import NodeType
        risk_names = {n.name for n in graph.nodes_by_type.get(NodeType.RISK, [])}
        assert "Data Breach Risk" in risk_names
        assert "Regulatory Fine Risk" in risk_names
        assert "Audit Failure Risk" in risk_names
        assert "Vendor Exposure Risk" in risk_names


# ============================================================================
# Prediction Signal Aggregator Tests
# ============================================================================


class TestSignalAggregator:
    """Test regulatory signal aggregation."""

    @pytest.fixture
    def aggregator(self):
        """Create signal aggregator."""
        from app.services.prediction.sources import SignalAggregator
        return SignalAggregator()

    def test_register_source(self, aggregator):
        """Test registering a regulatory source."""
        aggregator.register_source("EUR-Lex", "legislative", "https://eur-lex.europa.eu")

        assert aggregator.source_count == 1

    def test_register_multiple_sources(self, aggregator):
        """Test registering multiple sources."""
        aggregator.register_source("EUR-Lex", "legislative")
        aggregator.register_source("Congress.gov", "legislative")
        aggregator.register_source("FTC", "enforcement")

        assert aggregator.source_count == 3

    async def test_aggregate_signals_empty(self, aggregator):
        """Test aggregating with no signals."""
        result = await aggregator.aggregate_signals()

        assert result["signals_found"] == 0
        assert "aggregated_at" in result

    async def test_aggregate_with_filters(self, aggregator):
        """Test aggregating with jurisdiction filters."""
        result = await aggregator.aggregate_signals(
            jurisdictions=["EU", "US"],
            frameworks=["GDPR", "HIPAA"],
        )

        assert result["jurisdictions"] == ["EU", "US"]
        assert result["frameworks"] == ["GDPR", "HIPAA"]


# ============================================================================
# Digital Twin Persistence Tests
# ============================================================================


class TestDigitalTwinPersistence:
    """Test digital twin DB persistence."""

    async def test_snapshot_manager_with_db(self):
        """Test SnapshotManager accepts DB session."""
        from app.services.digital_twin.snapshot import SnapshotManager
        mock_db = AsyncMock()

        manager = SnapshotManager(db=mock_db)
        assert manager.db is mock_db

    async def test_snapshot_manager_without_db(self):
        """Test SnapshotManager works without DB (backward compat)."""
        from app.services.digital_twin.snapshot import SnapshotManager

        manager = SnapshotManager()
        assert manager.db is None

    async def test_simulator_with_db(self):
        """Test ComplianceSimulator accepts DB session."""
        from app.services.digital_twin.simulator import ComplianceSimulator
        mock_db = AsyncMock()

        simulator = ComplianceSimulator(db=mock_db)
        assert simulator.db is mock_db

    async def test_simulator_without_db(self):
        """Test ComplianceSimulator works without DB (backward compat)."""
        from app.services.digital_twin.simulator import ComplianceSimulator

        simulator = ComplianceSimulator()
        assert simulator.db is None
