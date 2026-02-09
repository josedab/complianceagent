"""Service-level tests for Next-Gen Strategic Features (Testing & Architecture Advisor)."""


import pytest

from app.services.architecture_advisor import (
    ArchitectureAdvisorService,
    PatternType,
)
from app.services.testing import (
    ComplianceTestingService,
    TestFramework,
    TestPatternCategory,
)


class TestComplianceTestingService:
    """Tests for the ComplianceTestingService."""

    @pytest.mark.asyncio
    async def test_list_all_patterns(self, db_session):
        service = ComplianceTestingService(db=db_session)
        patterns = await service.list_patterns()
        assert len(patterns) >= 10
        assert all(p.id for p in patterns)
        assert all(p.regulation for p in patterns)

    @pytest.mark.asyncio
    async def test_list_patterns_by_regulation(self, db_session):
        service = ComplianceTestingService(db=db_session)
        gdpr_patterns = await service.list_patterns(regulation="GDPR")
        assert len(gdpr_patterns) >= 3
        assert all(p.regulation == "GDPR" for p in gdpr_patterns)

    @pytest.mark.asyncio
    async def test_list_patterns_by_category(self, db_session):
        service = ComplianceTestingService(db=db_session)
        encryption = await service.list_patterns(category=TestPatternCategory.ENCRYPTION)
        assert len(encryption) >= 1
        assert all(p.category == TestPatternCategory.ENCRYPTION for p in encryption)

    @pytest.mark.asyncio
    async def test_get_pattern_by_id(self, db_session):
        service = ComplianceTestingService(db=db_session)
        pattern = await service.get_pattern("gdpr-consent-001")
        assert pattern is not None
        assert pattern.name == "GDPR Consent Collection Verification"
        assert pattern.regulation == "GDPR"

    @pytest.mark.asyncio
    async def test_get_pattern_not_found(self, db_session):
        service = ComplianceTestingService(db=db_session)
        pattern = await service.get_pattern("nonexistent-pattern")
        assert pattern is None

    @pytest.mark.asyncio
    async def test_detect_frameworks_python(self, db_session):
        service = ComplianceTestingService(db=db_session)
        result = await service.detect_frameworks(
            repo="test/repo",
            files=["pyproject.toml", "tests/conftest.py", "src/main.py"],
        )
        assert TestFramework.PYTEST in result.detected_frameworks
        assert result.primary_language == "python"
        assert result.recommended_framework == TestFramework.PYTEST

    @pytest.mark.asyncio
    async def test_detect_frameworks_javascript(self, db_session):
        service = ComplianceTestingService(db=db_session)
        result = await service.detect_frameworks(
            repo="test/repo",
            files=["jest.config.ts", "package.json", "src/index.ts"],
        )
        assert TestFramework.JEST in result.detected_frameworks

    @pytest.mark.asyncio
    async def test_detect_frameworks_no_files(self, db_session):
        service = ComplianceTestingService(db=db_session)
        result = await service.detect_frameworks(repo="test/repo", files=[])
        assert result.recommended_framework == TestFramework.PYTEST
        assert result.primary_language == "python"

    @pytest.mark.asyncio
    async def test_generate_test_suite_gdpr(self, db_session):
        service = ComplianceTestingService(db=db_session)
        result = await service.generate_test_suite(
            regulation="GDPR",
            framework=TestFramework.PYTEST,
        )
        assert result.status.value == "completed"
        assert result.total_tests >= 3
        assert result.regulation == "GDPR"
        assert result.framework == TestFramework.PYTEST
        assert result.generation_time_ms > 0
        assert all(t.test_code for t in result.tests)
        assert all(t.test_name for t in result.tests)

    @pytest.mark.asyncio
    async def test_generate_test_suite_hipaa(self, db_session):
        service = ComplianceTestingService(db=db_session)
        result = await service.generate_test_suite(
            regulation="HIPAA",
            framework=TestFramework.JEST,
        )
        assert result.status.value == "completed"
        assert result.total_tests >= 3
        assert result.framework == TestFramework.JEST

    @pytest.mark.asyncio
    async def test_generate_test_suite_no_patterns(self, db_session):
        service = ComplianceTestingService(db=db_session)
        result = await service.generate_test_suite(
            regulation="NONEXISTENT",
        )
        assert result.status.value == "failed"
        assert result.total_tests == 0

    @pytest.mark.asyncio
    async def test_generate_with_specific_patterns(self, db_session):
        service = ComplianceTestingService(db=db_session)
        result = await service.generate_test_suite(
            regulation="GDPR",
            pattern_ids=["gdpr-consent-001"],
        )
        assert result.total_tests == 1
        assert result.patterns_used == ["gdpr-consent-001"]

    @pytest.mark.asyncio
    async def test_validate_tests(self, db_session):
        service = ComplianceTestingService(db=db_session)
        suite = await service.generate_test_suite(regulation="GDPR")
        validation = await service.validate_tests(suite.id)
        assert validation.total_tests == suite.total_tests
        assert validation.valid_tests == suite.total_tests
        assert validation.invalid_tests == 0

    @pytest.mark.asyncio
    async def test_get_result(self, db_session):
        service = ComplianceTestingService(db=db_session)
        suite = await service.generate_test_suite(regulation="PCI-DSS")
        retrieved = await service.get_result(suite.id)
        assert retrieved is not None
        assert retrieved.id == suite.id


class TestArchitectureAdvisorService:
    """Tests for the ArchitectureAdvisorService."""

    @pytest.mark.asyncio
    async def test_analyze_monolith(self, db_session):
        service = ArchitectureAdvisorService(db=db_session)
        result = await service.analyze_architecture(
            repo="test/monolith-app",
            files=["src/main.py", "src/api.py", "src/models.py"],
            regulations=["GDPR"],
        )
        assert result.repo == "test/monolith-app"
        assert len(result.detected_patterns) >= 1
        assert result.detected_patterns[0].pattern_type == PatternType.MONOLITH
        assert result.score.overall_score > 0
        assert result.score.grade in ("A", "B", "C", "D", "F")

    @pytest.mark.asyncio
    async def test_analyze_microservices(self, db_session):
        service = ArchitectureAdvisorService(db=db_session)
        result = await service.analyze_architecture(
            repo="test/microservices-app",
            files=["docker-compose.yml", "k8s/deployment.yaml", "services/api/main.py"],
            regulations=["PCI-DSS"],
        )
        detected_types = {p.pattern_type for p in result.detected_patterns}
        assert PatternType.MICROSERVICES in detected_types

    @pytest.mark.asyncio
    async def test_analyze_event_driven(self, db_session):
        service = ArchitectureAdvisorService(db=db_session)
        result = await service.analyze_architecture(
            repo="test/event-app",
            files=["celery/tasks.py", "events/consumer.py", "docker-compose.yml"],
            regulations=["HIPAA"],
        )
        detected_types = {p.pattern_type for p in result.detected_patterns}
        assert PatternType.EVENT_DRIVEN in detected_types
        # Event-driven + HIPAA should generate risks
        assert len(result.risks) >= 1

    @pytest.mark.asyncio
    async def test_analyze_detects_data_lake_risk(self, db_session):
        service = ArchitectureAdvisorService(db=db_session)
        result = await service.analyze_architecture(
            repo="test/data-lake",
            files=["datalake/ingestion.py", "spark/jobs.py"],
            regulations=["GDPR"],
        )
        detected_types = {p.pattern_type for p in result.detected_patterns}
        assert PatternType.DATA_LAKE in detected_types
        # Data lake + GDPR should produce critical risk
        gdpr_risks = [r for r in result.risks if r.regulation == "GDPR"]
        assert len(gdpr_risks) >= 1

    @pytest.mark.asyncio
    async def test_analyze_default_regulations(self, db_session):
        service = ArchitectureAdvisorService(db=db_session)
        result = await service.analyze_architecture(
            repo="test/repo",
            files=["src/main.py"],
        )
        assert len(result.regulations_analyzed) == 3
        assert "GDPR" in result.regulations_analyzed

    @pytest.mark.asyncio
    async def test_recommendations_generated(self, db_session):
        service = ArchitectureAdvisorService(db=db_session)
        result = await service.analyze_architecture(
            repo="test/repo",
            regulations=["GDPR", "HIPAA"],
        )
        assert len(result.recommendations) >= 2
        assert all(r.effort_estimate_days > 0 for r in result.recommendations)

    @pytest.mark.asyncio
    async def test_list_patterns(self, db_session):
        service = ArchitectureAdvisorService(db=db_session)
        patterns = await service.list_patterns()
        assert len(patterns) == len(PatternType)
        assert all("type" in p and "name" in p and "compliance_notes" in p for p in patterns)

    @pytest.mark.asyncio
    async def test_get_score_after_review(self, db_session):
        service = ArchitectureAdvisorService(db=db_session)
        await service.analyze_architecture(repo="test/repo", files=["src/main.py"])
        score = await service.get_score("test/repo")
        assert score is not None
        assert 0 <= score.overall_score <= 100
        assert score.grade in ("A", "B", "C", "D", "F")

    @pytest.mark.asyncio
    async def test_get_score_not_found(self, db_session):
        service = ArchitectureAdvisorService(db=db_session)
        score = await service.get_score("nonexistent/repo")
        assert score is None

    @pytest.mark.asyncio
    async def test_score_penalized_by_risks(self, db_session):
        service = ArchitectureAdvisorService(db=db_session)
        # Data lake + GDPR produces critical risk → lower score
        risky = await service.analyze_architecture(
            repo="test/risky",
            files=["datalake/main.py", "spark/jobs.py"],
            regulations=["GDPR"],
        )
        # Monolith without data lake → fewer risks
        clean = await service.analyze_architecture(
            repo="test/clean",
            files=["src/main.py"],
            regulations=["GDPR"],
        )
        assert risky.score.overall_score <= clean.score.overall_score

    @pytest.mark.asyncio
    async def test_review_cached(self, db_session):
        service = ArchitectureAdvisorService(db=db_session)
        result = await service.analyze_architecture(repo="test/cached")
        retrieved = await service.get_review(result.id)
        assert retrieved is not None
        assert retrieved.id == result.id
