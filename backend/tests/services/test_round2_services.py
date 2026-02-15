"""Service-level tests for Round 2 Next-Gen Features."""

from uuid import uuid4

import pytest

from app.services.dao_governance import (
    DAOGovernanceService,
    ProposalStatus,
    ProposalType,
    VoteChoice,
)
from app.services.game_engine import (
    GameEngineService,
    ScenarioDifficulty,
)
from app.services.incident_remediation import (
    IncidentRemediationService,
    IncidentSeverity,
    IncidentSource,
)
from app.services.pair_programming import PairProgrammingService
from app.services.compliance_cloning import ComplianceCloningService
from app.services.api_monetization import (
    APIMonetizationService,
    PricingTier,
)
from app.services.prediction_market import (
    PredictionMarketService,
    MarketStatus,
)
from app.services.chaos_engineering import (
    ChaosEngineeringService,
    ExperimentType,
    ExperimentStatus,
)
from app.services.debt import DebtSecuritizationService
from app.services.regulation_diff import RegulationDiffService


class TestDAOGovernanceService:
    """Tests for the DAOGovernanceService."""

    @pytest.mark.asyncio
    async def test_list_proposals(self):
        svc = DAOGovernanceService()
        proposals = await svc.list_proposals()
        assert len(proposals) >= 1
        assert all(p.id for p in proposals)

    @pytest.mark.asyncio
    async def test_list_proposals_filter_by_status(self):
        svc = DAOGovernanceService()
        active = await svc.list_proposals(status=ProposalStatus.ACTIVE)
        assert all(p.status == ProposalStatus.ACTIVE for p in active)

    @pytest.mark.asyncio
    async def test_get_proposal(self):
        svc = DAOGovernanceService()
        proposals = await svc.list_proposals()
        result = await svc.get_proposal(proposals[0].id)
        assert result is not None
        assert result.id == proposals[0].id

    @pytest.mark.asyncio
    async def test_get_proposal_not_found(self):
        svc = DAOGovernanceService()
        result = await svc.get_proposal(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_create_proposal(self):
        svc = DAOGovernanceService()
        proposal = await svc.create_proposal(
            title="Test Proposal",
            description="A test proposal for unit testing",
            proposal_type=ProposalType.POLICY_CHANGE,
            affected_frameworks=["GDPR"],
            changes_summary="Test changes",
        )
        assert proposal.title == "Test Proposal"
        assert proposal.status == ProposalStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_create_proposal_empty_title_raises(self):
        svc = DAOGovernanceService()
        with pytest.raises(ValueError, match="title"):
            await svc.create_proposal(
                title="",
                description="desc",
                proposal_type=ProposalType.POLICY_CHANGE,
                affected_frameworks=[],
                changes_summary="",
            )

    @pytest.mark.asyncio
    async def test_create_proposal_empty_description_raises(self):
        svc = DAOGovernanceService()
        with pytest.raises(ValueError, match="description"):
            await svc.create_proposal(
                title="Valid Title",
                description="",
                proposal_type=ProposalType.POLICY_CHANGE,
                affected_frameworks=[],
                changes_summary="",
            )

    @pytest.mark.asyncio
    async def test_cast_vote(self):
        svc = DAOGovernanceService()
        proposals = await svc.list_proposals(status=ProposalStatus.ACTIVE)
        if not proposals:
            proposals = [
                await svc.create_proposal(
                    title="Vote Test",
                    description="Vote test desc",
                    proposal_type=ProposalType.STANDARD,
                )
            ]
        vote = await svc.cast_vote(
            proposal_id=proposals[0].id,
            member_id=uuid4(),
            choice=VoteChoice.FOR,
        )
        assert vote.choice == VoteChoice.FOR

    @pytest.mark.asyncio
    async def test_cast_vote_proposal_not_found(self):
        svc = DAOGovernanceService()
        with pytest.raises(ValueError, match="not found"):
            await svc.cast_vote(
                proposal_id=uuid4(),
                member_id=uuid4(),
                choice=VoteChoice.FOR,
            )

    @pytest.mark.asyncio
    async def test_get_members(self):
        svc = DAOGovernanceService()
        members = await svc.get_members()
        assert len(members) >= 1

    @pytest.mark.asyncio
    async def test_get_stats(self):
        svc = DAOGovernanceService()
        stats = await svc.get_stats()
        assert stats.total_proposals >= 0
        assert stats.total_members >= 0


class TestGameEngineService:
    """Tests for the GameEngineService."""

    @pytest.mark.asyncio
    async def test_list_scenarios(self):
        svc = GameEngineService()
        scenarios = await svc.list_scenarios()
        assert len(scenarios) >= 1

    @pytest.mark.asyncio
    async def test_list_scenarios_filter_difficulty(self):
        svc = GameEngineService()
        medium = await svc.list_scenarios(difficulty=ScenarioDifficulty.MEDIUM)
        assert all(s.difficulty == ScenarioDifficulty.MEDIUM for s in medium)

    @pytest.mark.asyncio
    async def test_get_scenario(self):
        svc = GameEngineService()
        scenarios = await svc.list_scenarios()
        result = await svc.get_scenario(scenarios[0].id)
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_scenario_not_found(self):
        svc = GameEngineService()
        result = await svc.get_scenario("nonexistent-scenario")
        assert result is None

    @pytest.mark.asyncio
    async def test_submit_decision(self):
        svc = GameEngineService()
        scenarios = await svc.list_scenarios()
        scenario = scenarios[0]
        decision = scenario.decisions[0]
        result = await svc.submit_decision(
            scenario_id=scenario.id,
            decision_id=decision.id,
            selected_option=0,
        )
        assert result is not None
        assert result["points_earned"] >= 0

    @pytest.mark.asyncio
    async def test_submit_decision_out_of_bounds(self):
        svc = GameEngineService()
        scenarios = await svc.list_scenarios()
        scenario = scenarios[0]
        decision = scenario.decisions[0]
        with pytest.raises(ValueError, match="out of bounds"):
            await svc.submit_decision(
                scenario_id=scenario.id,
                decision_id=decision.id,
                selected_option=999,
            )

    @pytest.mark.asyncio
    async def test_submit_decision_scenario_not_found(self):
        svc = GameEngineService()
        with pytest.raises(ValueError, match="not found"):
            await svc.submit_decision(
                scenario_id="nonexistent",
                decision_id="d1",
                selected_option=0,
            )

    @pytest.mark.asyncio
    async def test_get_leaderboard(self):
        svc = GameEngineService()
        board = await svc.get_leaderboard(limit=5)
        assert isinstance(board, list)

    @pytest.mark.asyncio
    async def test_get_leaderboard_invalid_limit(self):
        svc = GameEngineService()
        with pytest.raises(ValueError, match="limit"):
            await svc.get_leaderboard(limit=0)

    @pytest.mark.asyncio
    async def test_get_achievements(self):
        svc = GameEngineService()
        achievements = await svc.get_achievements()
        assert isinstance(achievements, list)


class TestIncidentRemediationService:
    """Tests for the IncidentRemediationService."""

    @pytest.mark.asyncio
    async def test_list_incidents(self):
        svc = IncidentRemediationService()
        incidents = await svc.list_incidents()
        assert len(incidents) >= 1

    @pytest.mark.asyncio
    async def test_list_incidents_filter_severity(self):
        svc = IncidentRemediationService()
        critical = await svc.list_incidents(severity=IncidentSeverity.CRITICAL)
        assert all(i.severity == IncidentSeverity.CRITICAL for i in critical)

    @pytest.mark.asyncio
    async def test_ingest_incident(self):
        svc = IncidentRemediationService()
        incident = await svc.ingest_incident(
            title="Test Incident",
            description="A test security incident",
            source=IncidentSource.SPLUNK,
            severity=IncidentSeverity.HIGH,
        )
        assert incident.title == "Test Incident"
        assert incident.severity == IncidentSeverity.HIGH

    @pytest.mark.asyncio
    async def test_ingest_incident_empty_title_raises(self):
        svc = IncidentRemediationService()
        with pytest.raises(ValueError, match="title"):
            await svc.ingest_incident(
                title="",
                description="desc",
                severity=IncidentSeverity.LOW,
                source=IncidentSource.MANUAL,
            )

    @pytest.mark.asyncio
    async def test_ingest_incident_empty_description_raises(self):
        svc = IncidentRemediationService()
        with pytest.raises(ValueError, match="description"):
            await svc.ingest_incident(
                title="Title",
                description="",
                severity=IncidentSeverity.LOW,
                source=IncidentSource.MANUAL,
            )

    @pytest.mark.asyncio
    async def test_get_remediation_actions(self):
        svc = IncidentRemediationService()
        incidents = await svc.list_incidents()
        actions = await svc.get_remediation_actions(incidents[0].id)
        assert isinstance(actions, list)

    @pytest.mark.asyncio
    async def test_generate_breach_notification(self):
        svc = IncidentRemediationService()
        incidents = await svc.list_incidents()
        notification = await svc.generate_breach_notification(incidents[0].id)
        assert notification is not None

    @pytest.mark.asyncio
    async def test_generate_breach_notification_not_found(self):
        svc = IncidentRemediationService()
        with pytest.raises(ValueError, match="not found"):
            await svc.generate_breach_notification(uuid4())


class TestPairProgrammingService:
    """Tests for the PairProgrammingService."""

    @pytest.mark.asyncio
    async def test_analyze_code(self):
        svc = PairProgrammingService()
        suggestions = await svc.analyze_code(
            code='email = request.form["email"]',
            file_path="test.py",
            language="python",
        )
        assert isinstance(suggestions, list)

    @pytest.mark.asyncio
    async def test_analyze_code_empty_returns_empty(self):
        svc = PairProgrammingService()
        suggestions = await svc.analyze_code(code="", file_path="test.py", language="python")
        assert suggestions == []

    @pytest.mark.asyncio
    async def test_start_session(self):
        svc = PairProgrammingService()
        session = await svc.start_session(
            user_id=uuid4(),
            repository="test/repo",
            language="python",
        )
        assert session is not None
        assert session.language == "python"

    @pytest.mark.asyncio
    async def test_get_regulation_context(self):
        svc = PairProgrammingService()
        context = await svc.get_regulation_context(language="python")
        assert isinstance(context, list)

    @pytest.mark.asyncio
    async def test_get_compliance_rules(self):
        svc = PairProgrammingService()
        rules = await svc.get_compliance_rules()
        assert len(rules) >= 1


class TestComplianceCloningService:
    """Tests for the ComplianceCloningService."""

    @pytest.mark.asyncio
    async def test_list_reference_repos(self):
        svc = ComplianceCloningService()
        repos = await svc.list_reference_repos()
        assert len(repos) >= 1

    @pytest.mark.asyncio
    async def test_fingerprint_repo(self):
        svc = ComplianceCloningService()
        fp = await svc.fingerprint_repo("https://github.com/test/repo")
        assert fp is not None
        assert fp.repo_url == "https://github.com/test/repo"

    @pytest.mark.asyncio
    async def test_find_similar_repos(self):
        svc = ComplianceCloningService()
        similar = await svc.find_similar_repos("https://github.com/test/repo")
        assert isinstance(similar, list)

    @pytest.mark.asyncio
    async def test_generate_migration_plan(self):
        svc = ComplianceCloningService()
        repos = await svc.list_reference_repos()
        plan = await svc.generate_migration_plan(
            source_repo_id=repos[0].id,
            target_repo_url="https://github.com/target/repo",
        )
        assert plan is not None

    @pytest.mark.asyncio
    async def test_generate_migration_plan_empty_url_raises(self):
        svc = ComplianceCloningService()
        repos = await svc.list_reference_repos()
        with pytest.raises(ValueError, match="target_repo_url"):
            await svc.generate_migration_plan(
                source_repo_id=repos[0].id,
                target_repo_url="",
            )


class TestAPIMonetizationService:
    """Tests for the APIMonetizationService."""

    @pytest.mark.asyncio
    async def test_list_apis(self):
        svc = APIMonetizationService()
        apis = await svc.list_apis()
        assert len(apis) >= 1

    @pytest.mark.asyncio
    async def test_list_apis_filter_regulation(self):
        svc = APIMonetizationService()
        gdpr = await svc.list_apis(regulation="GDPR")
        assert all(a.regulation == "GDPR" for a in gdpr)

    @pytest.mark.asyncio
    async def test_get_api(self):
        svc = APIMonetizationService()
        apis = await svc.list_apis()
        result = await svc.get_api(apis[0].id)
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_api_not_found(self):
        svc = APIMonetizationService()
        result = await svc.get_api("nonexistent-api")
        assert result is None

    @pytest.mark.asyncio
    async def test_create_subscription(self):
        svc = APIMonetizationService()
        apis = await svc.list_apis()
        sub = await svc.create_subscription(
            developer_id=uuid4(),
            api_id=apis[0].id,
            tier=PricingTier.PRO,
        )
        assert sub is not None
        assert sub.tier == PricingTier.PRO

    @pytest.mark.asyncio
    async def test_create_subscription_invalid_api_raises(self):
        svc = APIMonetizationService()
        with pytest.raises(ValueError, match="not found"):
            await svc.create_subscription(
                developer_id=uuid4(),
                api_id="nonexistent",
                tier=PricingTier.STARTER,
            )

    @pytest.mark.asyncio
    async def test_get_revenue_stats(self):
        svc = APIMonetizationService()
        stats = await svc.get_revenue_stats()
        assert stats.monthly_revenue >= 0


class TestPredictionMarketService:
    """Tests for the PredictionMarketService."""

    @pytest.mark.asyncio
    async def test_list_markets(self):
        svc = PredictionMarketService()
        markets = await svc.list_markets()
        assert len(markets) >= 1

    @pytest.mark.asyncio
    async def test_list_markets_filter_status(self):
        svc = PredictionMarketService()
        open_markets = await svc.list_markets(status=MarketStatus.OPEN)
        assert all(m.status == MarketStatus.OPEN for m in open_markets)

    @pytest.mark.asyncio
    async def test_get_market(self):
        svc = PredictionMarketService()
        markets = await svc.list_markets()
        result = await svc.get_market(markets[0].id)
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_market_not_found(self):
        svc = PredictionMarketService()
        result = await svc.get_market(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_place_prediction(self):
        svc = PredictionMarketService()
        open_markets = await svc.list_markets(status=MarketStatus.OPEN)
        if not open_markets:
            pytest.skip("No open markets in seed data")
        pred = await svc.place_prediction(
            market_id=open_markets[0].id,
            participant_id=uuid4(),
            position="yes",
            shares=10,
        )
        assert pred is not None
        assert pred.position == "yes"

    @pytest.mark.asyncio
    async def test_place_prediction_invalid_position(self):
        svc = PredictionMarketService()
        open_markets = await svc.list_markets(status=MarketStatus.OPEN)
        if not open_markets:
            pytest.skip("No open markets in seed data")
        with pytest.raises(ValueError, match="Position"):
            await svc.place_prediction(
                market_id=open_markets[0].id,
                participant_id=uuid4(),
                position="maybe",
                shares=5,
            )

    @pytest.mark.asyncio
    async def test_place_prediction_zero_shares(self):
        svc = PredictionMarketService()
        open_markets = await svc.list_markets(status=MarketStatus.OPEN)
        if not open_markets:
            pytest.skip("No open markets in seed data")
        with pytest.raises(ValueError, match="Shares"):
            await svc.place_prediction(
                market_id=open_markets[0].id,
                participant_id=uuid4(),
                position="yes",
                shares=0,
            )

    @pytest.mark.asyncio
    async def test_place_prediction_market_not_found(self):
        svc = PredictionMarketService()
        with pytest.raises(ValueError, match="not found"):
            await svc.place_prediction(
                market_id=uuid4(),
                participant_id=uuid4(),
                position="yes",
                shares=5,
            )

    @pytest.mark.asyncio
    async def test_get_leaderboard(self):
        svc = PredictionMarketService()
        board = await svc.get_leaderboard()
        assert isinstance(board, list)

    @pytest.mark.asyncio
    async def test_get_stats(self):
        svc = PredictionMarketService()
        stats = await svc.get_stats()
        assert stats.total_markets >= 0


class TestChaosEngineeringService:
    """Tests for the ChaosEngineeringService."""

    @pytest.mark.asyncio
    async def test_list_experiments(self):
        svc = ChaosEngineeringService()
        experiments = await svc.list_experiments()
        assert len(experiments) >= 1

    @pytest.mark.asyncio
    async def test_get_experiment(self):
        svc = ChaosEngineeringService()
        experiments = await svc.list_experiments()
        result = await svc.get_experiment(experiments[0].id)
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_experiment_not_found(self):
        svc = ChaosEngineeringService()
        result = await svc.get_experiment(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_create_experiment(self):
        svc = ChaosEngineeringService()
        exp = await svc.create_experiment(
            name="Test Experiment",
            description="A test chaos experiment",
            experiment_type=ExperimentType.REMOVE_ENCRYPTION,
            target_service="compliance-api",
            target_environment="staging",
        )
        assert exp.name == "Test Experiment"
        assert exp.status == ExperimentStatus.SCHEDULED

    @pytest.mark.asyncio
    async def test_create_experiment_production_blocked(self):
        svc = ChaosEngineeringService()
        with pytest.raises(ValueError, match="production"):
            await svc.create_experiment(
                name="Prod Test",
                description="Test prod blocking",
                experiment_type=ExperimentType.REMOVE_ENCRYPTION,
                target_service="compliance-api",
                target_environment="production",
            )

    @pytest.mark.asyncio
    async def test_run_experiment(self):
        svc = ChaosEngineeringService()
        exp = await svc.create_experiment(
            name="Run Test",
            description="Test run experiment",
            experiment_type=ExperimentType.DISABLE_AUDIT_LOGS,
            target_service="audit-service",
            target_environment="staging",
        )
        result = await svc.run_experiment(exp.id)
        assert result.status in (ExperimentStatus.RUNNING, ExperimentStatus.COMPLETED)

    @pytest.mark.asyncio
    async def test_run_experiment_not_found(self):
        svc = ChaosEngineeringService()
        with pytest.raises(ValueError, match="not found"):
            await svc.run_experiment(uuid4())

    @pytest.mark.asyncio
    async def test_list_game_days(self):
        svc = ChaosEngineeringService()
        game_days = await svc.list_game_days()
        assert isinstance(game_days, list)

    @pytest.mark.asyncio
    async def test_get_stats(self):
        svc = ChaosEngineeringService()
        stats = await svc.get_stats()
        assert stats.total_experiments >= 0


class TestDebtSecuritizationService:
    """Tests for the DebtSecuritizationService."""

    @pytest.mark.asyncio
    async def test_list_debt_items(self):
        svc = DebtSecuritizationService()
        items = await svc.list_debt_items()
        assert len(items) >= 1

    @pytest.mark.asyncio
    async def test_get_portfolio(self):
        svc = DebtSecuritizationService()
        portfolio = await svc.get_portfolio()
        assert portfolio is not None
        assert portfolio.total_debt_value >= 0

    @pytest.mark.asyncio
    async def test_get_bonds(self):
        svc = DebtSecuritizationService()
        bonds = await svc.get_bonds()
        assert isinstance(bonds, list)

    @pytest.mark.asyncio
    async def test_get_credit_rating(self):
        svc = DebtSecuritizationService()
        rating = await svc.get_credit_rating()
        assert "rating" in rating
        assert "total_debt" in rating


class TestRegulationDiffService:
    """Tests for the RegulationDiffService."""

    @pytest.mark.asyncio
    async def test_list_versions(self):
        svc = RegulationDiffService()
        versions = await svc.list_versions()
        assert len(versions) >= 1

    @pytest.mark.asyncio
    async def test_list_versions_filter_regulation(self):
        svc = RegulationDiffService()
        gdpr = await svc.list_versions(regulation="GDPR")
        assert all("GDPR" in v.regulation for v in gdpr)

    @pytest.mark.asyncio
    async def test_get_version(self):
        svc = RegulationDiffService()
        versions = await svc.list_versions()
        result = await svc.get_version(versions[0].id)
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_version_not_found(self):
        svc = RegulationDiffService()
        result = await svc.get_version("nonexistent-version")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_diffs(self):
        svc = RegulationDiffService()
        diffs = await svc.list_diffs()
        assert isinstance(diffs, list)

    @pytest.mark.asyncio
    async def test_get_diff(self):
        svc = RegulationDiffService()
        diffs = await svc.list_diffs()
        if diffs:
            result = await svc.get_diff(diffs[0].id)
            assert result is not None

    @pytest.mark.asyncio
    async def test_compare_versions(self):
        svc = RegulationDiffService()
        versions = await svc.list_versions()
        if len(versions) >= 2:
            result = await svc.compare_versions(versions[0].id, versions[1].id)
            # May return None if no diff exists between these versions
            assert result is None or result.from_version is not None
