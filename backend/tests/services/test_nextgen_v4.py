"""Tests for Next-Gen v4 features (10 new capabilities)."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agents_marketplace.models import AgentStatus
from app.services.agents_marketplace.service import AgentsMarketplaceService
from app.services.code_review_agent.models import ReviewDecision, ReviewRiskLevel
from app.services.code_review_agent.service import CodeReviewAgentService
from app.services.compliance_observability.models import AlertSeverity
from app.services.compliance_observability.service import ComplianceObservabilityService
from app.services.cost_benefit_analyzer.service import CostBenefitAnalyzerService
from app.services.cross_org_benchmark.service import CrossOrgBenchmarkService
from app.services.evidence_generation.models import ControlStatus, EvidenceFramework
from app.services.evidence_generation.service import EvidenceGenerationService
from app.services.nl_compliance_query.service import NLComplianceQueryService
from app.services.reg_prediction.models import PredictionConfidence
from app.services.reg_prediction.service import RegPredictionService
from app.services.saas_onboarding.models import SaaSPlan, TenantStatus
from app.services.saas_onboarding.service import SaaSOnboardingService
from app.services.twin_simulation.models import SimulationStatus
from app.services.twin_simulation.service import TwinSimulationService


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def marketplace_service(db_session: AsyncSession):
    return AgentsMarketplaceService(db=db_session)


@pytest_asyncio.fixture
async def saas_service(db_session: AsyncSession):
    return SaaSOnboardingService(db=db_session)


@pytest_asyncio.fixture
async def review_service(db_session: AsyncSession):
    return CodeReviewAgentService(db=db_session)


@pytest_asyncio.fixture
async def prediction_service(db_session: AsyncSession):
    return RegPredictionService(db=db_session)


@pytest_asyncio.fixture
async def observability_service(db_session: AsyncSession):
    return ComplianceObservabilityService(db=db_session)


@pytest_asyncio.fixture
async def nl_query_service(db_session: AsyncSession):
    return NLComplianceQueryService(db=db_session)


@pytest_asyncio.fixture
async def twin_service(db_session: AsyncSession):
    return TwinSimulationService(db=db_session)


@pytest_asyncio.fixture
async def benchmark_service(db_session: AsyncSession):
    return CrossOrgBenchmarkService(db=db_session)


@pytest_asyncio.fixture
async def evidence_service(db_session: AsyncSession):
    return EvidenceGenerationService(db=db_session)


@pytest_asyncio.fixture
async def cost_service(db_session: AsyncSession):
    return CostBenefitAnalyzerService(db=db_session)


# ── Feature 1: Agents Marketplace ────────────────────────────────────────


class TestAgentsMarketplace:
    @pytest.mark.asyncio
    async def test_search_returns_seed_agents(self, marketplace_service: AgentsMarketplaceService):
        agents = marketplace_service.search_agents()
        assert len(agents) >= 5
        assert all(a.status == AgentStatus.PUBLISHED for a in agents)

    @pytest.mark.asyncio
    async def test_search_by_framework(self, marketplace_service: AgentsMarketplaceService):
        agents = marketplace_service.search_agents(framework="GDPR")
        assert len(agents) >= 1
        assert all("GDPR" in a.frameworks for a in agents)

    @pytest.mark.asyncio
    async def test_publish_and_approve_agent(self, marketplace_service: AgentsMarketplaceService):
        agent = await marketplace_service.publish_agent(
            name="Test Agent", slug="test-agent", description="A test",
            category="checker", author="tester",
        )
        assert agent.status == AgentStatus.IN_REVIEW
        approved = await marketplace_service.approve_agent("test-agent")
        assert approved is not None
        assert approved.status == AgentStatus.PUBLISHED

    @pytest.mark.asyncio
    async def test_install_agent(self, marketplace_service: AgentsMarketplaceService):
        inst = await marketplace_service.install_agent("gdpr-data-flow-scanner", "org-1")
        assert inst is not None
        assert inst.organization_id == "org-1"

    @pytest.mark.asyncio
    async def test_rate_agent(self, marketplace_service: AgentsMarketplaceService):
        review = await marketplace_service.rate_agent("hipaa-phi-detector", "user1", 5, "Great!")
        assert review is not None
        assert review.rating == 5

    @pytest.mark.asyncio
    async def test_stats(self, marketplace_service: AgentsMarketplaceService):
        stats = marketplace_service.get_stats()
        assert stats.published_agents >= 5
        assert len(stats.by_category) > 0


# ── Feature 2: Zero-Config SaaS ─────────────────────────────────────────


class TestSaaSOnboarding:
    @pytest.mark.asyncio
    async def test_create_tenant(self, saas_service: SaaSOnboardingService):
        tenant = await saas_service.create_tenant("Acme Corp", "admin@acme.com")
        assert tenant.status == TenantStatus.ACTIVE
        assert tenant.plan == SaaSPlan.FREE
        assert tenant.repo_limit == 3

    @pytest.mark.asyncio
    async def test_onboarding_flow(self, saas_service: SaaSOnboardingService):
        await saas_service.create_tenant("Test Co", "test@test.com")
        progress = await saas_service.advance_onboarding("test-co", "connect_scm", {"provider": "github", "organization": "test-co"})
        assert progress is not None
        assert "connect_scm" in progress.steps_completed
        progress = await saas_service.advance_onboarding("test-co", "completed")
        assert progress.completed_at is not None

    @pytest.mark.asyncio
    async def test_upgrade_plan(self, saas_service: SaaSOnboardingService):
        await saas_service.create_tenant("Upgrade Co", "up@test.com")
        tenant = await saas_service.upgrade_plan("upgrade-co", "business")
        assert tenant is not None
        assert tenant.plan == SaaSPlan.BUSINESS
        assert tenant.repo_limit == 100

    @pytest.mark.asyncio
    async def test_plan_limits(self, saas_service: SaaSOnboardingService):
        limits = saas_service.get_usage_limits("enterprise")
        assert limits.max_repos == -1
        assert limits.sso_enabled is True
        assert limits.ai_features_enabled is True


# ── Feature 3: Code Review Agent ─────────────────────────────────────────


class TestCodeReviewAgent:
    @pytest.mark.asyncio
    async def test_analyze_clean_pr(self, review_service: CodeReviewAgentService):
        review = await review_service.analyze_pr(
            repo="org/repo", pr_number=1,
            changed_files=[{"path": "README.md", "start_line": 1, "end_line": 5, "added_lines": ["# Documentation update"]}],
        )
        assert review.overall_risk == ReviewRiskLevel.NONE
        assert review.decision in (ReviewDecision.AUTO_APPROVED, ReviewDecision.APPROVE)

    @pytest.mark.asyncio
    async def test_analyze_pr_with_violations(self, review_service: CodeReviewAgentService):
        review = await review_service.analyze_pr(
            repo="org/repo", pr_number=2,
            changed_files=[{"path": "src/users.py", "start_line": 10, "end_line": 20, "added_lines": ["user_email = request.form['email']", "store_forever(personal_data)"]}],
        )
        assert len(review.suggestions) > 0
        assert review.overall_risk != ReviewRiskLevel.NONE

    @pytest.mark.asyncio
    async def test_analyze_pr_detects_pci(self, review_service: CodeReviewAgentService):
        review = await review_service.analyze_pr(
            repo="org/payments", pr_number=3,
            changed_files=[{"path": "src/checkout.py", "start_line": 1, "end_line": 10, "added_lines": ["card_number = request.json['card']"]}],
        )
        pci_suggestions = [s for s in review.suggestions if s.framework == "PCI-DSS"]
        assert len(pci_suggestions) > 0

    @pytest.mark.asyncio
    async def test_accept_suggestion(self, review_service: CodeReviewAgentService):
        review = await review_service.analyze_pr(
            repo="org/repo", pr_number=4,
            changed_files=[{"path": "src/health.py", "start_line": 1, "end_line": 5, "added_lines": ["patient_id = get_patient()"]}],
        )
        if review.suggestions:
            ok = await review_service.accept_suggestion(review.suggestions[0].id)
            assert ok is True

    @pytest.mark.asyncio
    async def test_stats(self, review_service: CodeReviewAgentService):
        await review_service.analyze_pr("org/repo", 10, changed_files=[{"path": "x.py", "start_line": 1, "end_line": 1, "added_lines": ["x = 1"]}])
        stats = review_service.get_stats()
        assert stats.total_reviews >= 1


# ── Feature 4: Regulatory Prediction ─────────────────────────────────────


class TestRegPrediction:
    @pytest.mark.asyncio
    async def test_list_predictions(self, prediction_service: RegPredictionService):
        preds = prediction_service.list_predictions()
        assert len(preds) >= 5

    @pytest.mark.asyncio
    async def test_filter_by_jurisdiction(self, prediction_service: RegPredictionService):
        eu_preds = prediction_service.list_predictions(jurisdiction="EU")
        assert all(p.jurisdiction == "EU" for p in eu_preds)

    @pytest.mark.asyncio
    async def test_filter_by_confidence(self, prediction_service: RegPredictionService):
        high = prediction_service.list_predictions(confidence=PredictionConfidence.HIGH)
        assert all(p.confidence == PredictionConfidence.HIGH for p in high)
        assert all(p.confidence_score >= 0.7 for p in high)

    @pytest.mark.asyncio
    async def test_generate_early_warnings(self, prediction_service: RegPredictionService):
        warnings = await prediction_service.generate_early_warnings()
        assert len(warnings) >= 1
        assert all(len(w.recommended_actions) > 0 for w in warnings)

    @pytest.mark.asyncio
    async def test_add_signal(self, prediction_service: RegPredictionService):
        signal = await prediction_service.add_signal("legislative", "Congress", "US", "New privacy bill", 0.8)
        assert signal.relevance_score == 0.8
        signals = prediction_service.list_signals(jurisdiction="US")
        assert len(signals) >= 1


# ── Feature 5: Compliance Observability ──────────────────────────────────


class TestComplianceObservability:
    @pytest.mark.asyncio
    async def test_emit_metric(self, observability_service: ComplianceObservabilityService):
        m = await observability_service.emit_metric("compliance.test.score", 92.0, "gauge")
        assert m.name == "compliance.test.score"
        assert m.value == 92.0

    @pytest.mark.asyncio
    async def test_low_score_triggers_alert(self, observability_service: ComplianceObservabilityService):
        await observability_service.emit_metric("compliance.posture.score", 55.0, "gauge")
        alerts = observability_service.list_alerts()
        critical = [a for a in alerts if a.severity == AlertSeverity.CRITICAL]
        assert len(critical) >= 1

    @pytest.mark.asyncio
    async def test_configure_exporter(self, observability_service: ComplianceObservabilityService):
        e = await observability_service.configure_exporter("datadog", "https://api.datadoghq.com", "dd-api-key")
        assert e.exporter_type.value == "datadog"
        exporters = observability_service.list_exporters()
        assert len(exporters) == 1

    @pytest.mark.asyncio
    async def test_list_builtin_metrics(self, observability_service: ComplianceObservabilityService):
        metrics = observability_service.list_metrics(name_prefix="compliance.")
        assert len(metrics) >= 7

    @pytest.mark.asyncio
    async def test_get_dashboard(self, observability_service: ComplianceObservabilityService):
        dash = observability_service.get_dashboard("grafana")
        assert dash is not None
        assert len(dash.panels) >= 3


# ── Feature 6: Natural Language Queries ──────────────────────────────────


class TestNLComplianceQuery:
    @pytest.mark.asyncio
    async def test_violation_query(self, nl_query_service: NLComplianceQueryService):
        result = await nl_query_service.query("Show me all GDPR violations in the payments service")
        assert "violation" in result.answer.lower() or "finding" in result.answer.lower()
        assert len(result.follow_up_suggestions) > 0

    @pytest.mark.asyncio
    async def test_posture_query(self, nl_query_service: NLComplianceQueryService):
        result = await nl_query_service.query("What is our compliance posture status?")
        assert "score" in result.answer.lower() or "%" in result.answer
        assert result.execution_time_ms >= 0

    @pytest.mark.asyncio
    async def test_recommendation_query(self, nl_query_service: NLComplianceQueryService):
        result = await nl_query_service.query("Recommend how to improve our compliance posture")
        assert "recommend" in result.answer.lower() or "improve" in result.answer.lower()

    @pytest.mark.asyncio
    async def test_feedback(self, nl_query_service: NLComplianceQueryService):
        result = await nl_query_service.query("What regulations apply to us?")
        fb = await nl_query_service.submit_feedback(result.query_id, True, "Helpful!")
        assert fb.helpful is True

    @pytest.mark.asyncio
    async def test_query_history(self, nl_query_service: NLComplianceQueryService):
        await nl_query_service.query("Test query")
        history = nl_query_service.get_query_history()
        assert len(history) >= 1


# ── Feature 7: Digital Twin Simulation ────────────────────────────────────


class TestTwinSimulation:
    @pytest.mark.asyncio
    async def test_capture_snapshot(self, twin_service: TwinSimulationService):
        snapshot = await twin_service.capture_snapshot("org/repo", "baseline")
        assert snapshot.score > 0
        assert len(snapshot.frameworks) > 0

    @pytest.mark.asyncio
    async def test_simulate_code_change(self, twin_service: TwinSimulationService):
        await twin_service.capture_snapshot("org/repo")
        result = await twin_service.simulate("org/repo", [
            {"change_type": "code_change", "description": "Add user data processing", "target": "src/users.py"},
        ])
        assert result.status == SimulationStatus.COMPLETED
        assert result.score_delta < 0  # Code change should decrease score
        assert len(result.recommendations) > 0

    @pytest.mark.asyncio
    async def test_simulate_vendor_change(self, twin_service: TwinSimulationService):
        await twin_service.capture_snapshot("org/repo")
        result = await twin_service.simulate("org/repo", [
            {"change_type": "vendor_change", "description": "Switch to new cloud provider", "target": "infrastructure"},
        ])
        assert result.risk_assessment in ("medium", "high")
        assert result.score_delta < -3

    @pytest.mark.asyncio
    async def test_simulation_history(self, twin_service: TwinSimulationService):
        await twin_service.capture_snapshot("org/repo")
        await twin_service.simulate("org/repo", [{"change_type": "code_change"}])
        await twin_service.simulate("org/repo", [{"change_type": "dependency_add"}])
        history = twin_service.get_history()
        assert history.total_simulations == 2


# ── Feature 8: Cross-Org Benchmarking ────────────────────────────────────


class TestCrossOrgBenchmark:
    @pytest.mark.asyncio
    async def test_get_benchmark(self, benchmark_service: CrossOrgBenchmarkService):
        result = await benchmark_service.get_benchmark(85.0, "fintech")
        assert result.percentile > 0
        assert result.industry_avg > 0
        assert result.peer_count > 0

    @pytest.mark.asyncio
    async def test_high_score_percentile(self, benchmark_service: CrossOrgBenchmarkService):
        result = await benchmark_service.get_benchmark(95.0, "fintech")
        assert result.percentile > 80  # Top scorer should be high percentile

    @pytest.mark.asyncio
    async def test_low_score_gets_suggestions(self, benchmark_service: CrossOrgBenchmarkService):
        result = await benchmark_service.get_benchmark(60.0, "saas")
        assert len(result.improvement_suggestions) > 0

    @pytest.mark.asyncio
    async def test_contribute_data(self, benchmark_service: CrossOrgBenchmarkService):
        profile = await benchmark_service.contribute_data("fintech", "medium", 82.0, {"GDPR": 85.0})
        assert profile.industry.value == "fintech"

    @pytest.mark.asyncio
    async def test_list_industries(self, benchmark_service: CrossOrgBenchmarkService):
        industries = benchmark_service.list_industries()
        assert len(industries) >= 8


# ── Feature 9: Evidence Generation ────────────────────────────────────────


class TestEvidenceGeneration:
    @pytest.mark.asyncio
    async def test_generate_soc2_package(self, evidence_service: EvidenceGenerationService):
        pkg = await evidence_service.generate_evidence_package("soc2")
        assert pkg.framework == EvidenceFramework.SOC2
        assert pkg.controls_total >= 13
        assert pkg.coverage_pct > 0
        assert len(pkg.items) > 0

    @pytest.mark.asyncio
    async def test_generate_iso27001_package(self, evidence_service: EvidenceGenerationService):
        pkg = await evidence_service.generate_evidence_package("iso27001")
        assert pkg.framework == EvidenceFramework.ISO27001
        assert pkg.controls_total >= 12

    @pytest.mark.asyncio
    async def test_coverage_above_threshold(self, evidence_service: EvidenceGenerationService):
        pkg = await evidence_service.generate_evidence_package("soc2")
        assert pkg.coverage_pct >= 70  # At least 70% auto-generated

    @pytest.mark.asyncio
    async def test_control_mapping_status(self, evidence_service: EvidenceGenerationService):
        pkg = await evidence_service.generate_evidence_package("soc2")
        met = [m for m in pkg.control_mappings if m.status == ControlStatus.MET]
        assert len(met) > 0
        assert all(m.evidence_count > 0 for m in met)

    @pytest.mark.asyncio
    async def test_list_frameworks(self, evidence_service: EvidenceGenerationService):
        fws = evidence_service.list_frameworks()
        assert len(fws) >= 4
        names = [f["framework"] for f in fws]
        assert "soc2" in names


# ── Feature 10: Cost-Benefit Analyzer ─────────────────────────────────────


class TestCostBenefitAnalyzer:
    @pytest.mark.asyncio
    async def test_add_investment(self, cost_service: CostBenefitAnalyzerService):
        inv = await cost_service.add_investment(
            name="GDPR Consent Management", framework="GDPR",
            cost_usd=15000, engineering_hours=120, score_impact=8.0,
        )
        assert inv.name == "GDPR Consent Management"
        assert inv.risk_reduction_usd > 0

    @pytest.mark.asyncio
    async def test_calculate_roi(self, cost_service: CostBenefitAnalyzerService):
        inv = await cost_service.add_investment(
            name="HIPAA Encryption", framework="HIPAA",
            cost_usd=10000, engineering_hours=80, score_impact=12.0,
        )
        roi = await cost_service.calculate_roi(inv.id)
        assert roi is not None
        assert roi.total_cost == 10000
        assert roi.risk_reduction > 0

    @pytest.mark.asyncio
    async def test_cost_breakdown(self, cost_service: CostBenefitAnalyzerService):
        await cost_service.add_investment("A", "GDPR", cost_usd=5000, score_impact=3.0)
        await cost_service.add_investment("B", "GDPR", category="tooling", cost_usd=2000, score_impact=2.0)
        breakdowns = cost_service.get_cost_breakdown("GDPR")
        assert len(breakdowns) == 1
        assert breakdowns[0].total_cost == 7000

    @pytest.mark.asyncio
    async def test_executive_report(self, cost_service: CostBenefitAnalyzerService):
        await cost_service.add_investment("Test", "GDPR", cost_usd=10000, score_impact=5.0)
        report = await cost_service.generate_executive_report("Q1 2026")
        assert report.total_investment == 10000
        assert len(report.highlights) > 0

    @pytest.mark.asyncio
    async def test_stats(self, cost_service: CostBenefitAnalyzerService):
        await cost_service.add_investment("X", "HIPAA", cost_usd=8000, score_impact=4.0)
        stats = cost_service.get_stats()
        assert stats.total_investments == 1
        assert stats.total_spend == 8000
