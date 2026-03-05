"""Tests for ComplianceOrchestrator pipeline."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.agents.orchestrator import ComplianceOrchestrator
from app.core.exceptions import CopilotError, RequirementExtractionError


def _make_regulation(**overrides) -> MagicMock:
    reg = MagicMock()
    reg.id = overrides.get("id", uuid4())
    reg.name = overrides.get("name", "GDPR 2024 Update")
    reg.framework = MagicMock()
    reg.framework.value = overrides.get("framework", "gdpr")
    reg.jurisdiction = MagicMock()
    reg.jurisdiction.value = overrides.get("jurisdiction", "eu")
    return reg


def _make_profile(**overrides) -> MagicMock:
    profile = MagicMock()
    profile.data_types_processed = overrides.get("data_types_processed", ["personal data"])
    profile.business_processes = overrides.get("business_processes", [])
    profile.processes_pii = overrides.get("processes_pii", True)
    profile.processes_health_data = overrides.get("processes_health_data", False)
    profile.uses_ai_ml = overrides.get("uses_ai_ml", False)
    return profile


def _mock_copilot(requirements=None):
    copilot = AsyncMock()
    copilot.analyze_legal_text = AsyncMock(
        return_value=requirements
        if requirements is not None
        else [
            {
                "reference_id": "REQ-GDPR-001",
                "title": "Data minimization",
                "description": "Only collect necessary data",
                "obligation_type": "must",
                "category": "data_collection",
                "data_types": ["personal data"],
                "processes": [],
                "confidence": 0.95,
            }
        ]
    )
    copilot.__aenter__ = AsyncMock(return_value=copilot)
    copilot.__aexit__ = AsyncMock(return_value=False)
    return copilot


@pytest.fixture
def db_session():
    """Mock async database session."""
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def audit_service():
    """Mock audit service."""
    svc = AsyncMock()
    svc.log_event = AsyncMock(return_value=MagicMock())
    return svc


@pytest.fixture
def org_id():
    return uuid4()


def _make_orchestrator(db_session, org_id, copilot=None, audit_service=None):
    """Create orchestrator with mocked dependencies."""
    orchestrator = ComplianceOrchestrator(
        db=db_session,
        organization_id=org_id,
        copilot=copilot,
    )
    if audit_service:
        orchestrator.audit_service = audit_service
    return orchestrator


class TestProcessRegulatoryChange:
    """Test the 3-stage pipeline: extract → filter → save."""

    @pytest.mark.asyncio
    async def test_full_pipeline_with_relevant_requirements(self, db_session, org_id, audit_service):
        copilot = _mock_copilot()
        orchestrator = _make_orchestrator(db_session, org_id, copilot, audit_service)

        regulation = _make_regulation()
        profile = _make_profile()

        result = await orchestrator.process_regulatory_change(
            regulation=regulation,
            content="Article 5: Personal data shall be collected...",
            customer_profile=profile,
        )

        assert result["status"] == "processed"
        assert result["requirements_found"] == 1
        assert result["relevant_requirements"] == 1
        assert len(result["saved_requirements"]) == 1

    @pytest.mark.asyncio
    async def test_no_relevant_requirements(self, db_session, org_id, audit_service):
        copilot = _mock_copilot(
            requirements=[
                {
                    "data_types": ["financial"],
                    "category": "banking",
                    "confidence": 0.8,
                }
            ]
        )
        orchestrator = _make_orchestrator(db_session, org_id, copilot, audit_service)

        profile = _make_profile(
            data_types_processed=[],
            processes_pii=False,
        )

        result = await orchestrator.process_regulatory_change(
            regulation=_make_regulation(),
            content="Some banking regulation text",
            customer_profile=profile,
        )

        assert result["status"] == "not_applicable"
        assert result["relevant_requirements"] == 0

    @pytest.mark.asyncio
    async def test_copilot_error_raises_extraction_error(self, db_session, org_id, audit_service):
        copilot = AsyncMock()
        copilot.analyze_legal_text = AsyncMock(side_effect=CopilotError("API down"))
        copilot.__aenter__ = AsyncMock(return_value=copilot)
        copilot.__aexit__ = AsyncMock(return_value=False)

        orchestrator = _make_orchestrator(db_session, org_id, copilot, audit_service)

        with pytest.raises(RequirementExtractionError, match="Failed to process regulation"):
            await orchestrator.process_regulatory_change(
                regulation=_make_regulation(),
                content="Regulation text",
                customer_profile=_make_profile(),
            )

    @pytest.mark.asyncio
    async def test_empty_extraction_returns_not_applicable(self, db_session, org_id, audit_service):
        copilot = _mock_copilot(requirements=[])
        orchestrator = _make_orchestrator(db_session, org_id, copilot, audit_service)

        result = await orchestrator.process_regulatory_change(
            regulation=_make_regulation(),
            content="Empty regulation",
            customer_profile=_make_profile(),
        )

        assert result["status"] == "not_applicable"
        assert result["requirements_found"] == 0


class TestSaveRequirements:
    """Test _save_requirements default value handling."""

    @pytest.mark.asyncio
    async def test_saves_with_all_fields(self, db_session, org_id, audit_service):
        orchestrator = _make_orchestrator(db_session, org_id, audit_service=audit_service)
        regulation = _make_regulation()

        reqs = [
            {
                "reference_id": "REQ-001",
                "title": "Data minimization",
                "description": "Minimize data collection",
                "obligation_type": "must",
                "category": "data_collection",
                "data_types": ["personal data"],
                "processes": ["collection"],
                "confidence": 0.95,
                "source_text": "Article 5.1(c)",
            }
        ]

        result = await orchestrator._save_requirements(regulation, reqs)
        assert len(result) == 1
        assert db_session.add.called

    @pytest.mark.asyncio
    async def test_saves_with_missing_optional_fields(self, db_session, org_id, audit_service):
        orchestrator = _make_orchestrator(db_session, org_id, audit_service=audit_service)
        regulation = _make_regulation()

        reqs = [{}]  # all fields missing — should use defaults
        result = await orchestrator._save_requirements(regulation, reqs)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_multiple_requirements_saved(self, db_session, org_id, audit_service):
        orchestrator = _make_orchestrator(db_session, org_id, audit_service=audit_service)
        regulation = _make_regulation()

        reqs = [{"title": f"Req {i}"} for i in range(5)]
        result = await orchestrator._save_requirements(regulation, reqs)
        assert len(result) == 5
        assert db_session.add.call_count == 5


class TestGenerateComplianceFix:
    """Test generate_compliance_fix edge cases."""

    @pytest.mark.asyncio
    async def test_no_gaps_returns_no_gaps_status(self, db_session, org_id, audit_service):
        copilot = _mock_copilot()
        orchestrator = _make_orchestrator(db_session, org_id, copilot, audit_service)

        mapping = MagicMock()
        mapping.id = uuid4()
        mapping.gaps = []  # no gaps

        result = await orchestrator.generate_compliance_fix(
            mapping=mapping,
            requirement=MagicMock(reference_id="REQ-001"),
            repository=MagicMock(full_name="test/repo", primary_language="python"),
        )

        assert result["status"] == "no_gaps"
