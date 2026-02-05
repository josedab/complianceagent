"""Tests for IDE Agent service."""

import pytest
import pytest_asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ide_agent.models import (
    AgentSession,
    AgentStatus,
    AgentTriggerType,
    AgentAction,
    AgentActionType,
    ComplianceViolation,
    ProposedFix,
    FixConfidence,
    RefactorPlan,
    AgentConfig,
    AnalysisResult,
)
from app.services.ide_agent.agent import IDEAgentService, get_ide_agent_service


pytestmark = pytest.mark.asyncio


class TestAgentModels:
    """Test IDE Agent data models."""

    def test_agent_session_creation(self):
        """Test creating an agent session."""
        session = AgentSession(
            organization_id=uuid4(),
            user_id=uuid4(),
            trigger_type=AgentTriggerType.MANUAL,
            started_at=datetime.now(UTC),
        )

        assert session.id is not None
        assert session.status == AgentStatus.IDLE
        assert session.progress == 0.0
        assert session.violations_found == 0

    def test_agent_session_to_dict(self):
        """Test converting session to dict."""
        session = AgentSession(
            organization_id=uuid4(),
            trigger_type=AgentTriggerType.FILE_SAVE,
            started_at=datetime.now(UTC),
        )

        data = session.to_dict()

        assert "id" in data
        assert data["trigger_type"] == "file_save"
        assert data["status"] == "idle"

    def test_compliance_violation_creation(self):
        """Test creating a compliance violation."""
        violation = ComplianceViolation(
            rule_id="GDPR-PII-001",
            rule_name="PII Detection",
            regulation="GDPR",
            article_reference="Article 32",
            severity="warning",
            message="Potential PII exposure detected",
            file_path="src/users.py",
            start_line=10,
            end_line=15,
            original_code="user_email = input()",
            confidence=0.85,
        )

        assert violation.id is not None
        assert violation.rule_id == "GDPR-PII-001"
        assert violation.confidence == 0.85

    def test_proposed_fix_creation(self):
        """Test creating a proposed fix."""
        fix = ProposedFix(
            fixed_code="encrypted_email = encrypt(user_email)",
            explanation="Encrypt PII before storage",
            confidence=FixConfidence.HIGH,
            confidence_score=0.92,
            imports_to_add=["from crypto import encrypt"],
            breaking_changes=False,
        )

        assert fix.id is not None
        assert fix.confidence == FixConfidence.HIGH
        assert len(fix.imports_to_add) == 1

    def test_refactor_plan_creation(self):
        """Test creating a refactor plan."""
        plan = RefactorPlan(
            total_violations=5,
            fixable_violations=4,
            manual_review_required=1,
            execution_order=["fix-1", "fix-2"],
            estimated_impact="medium",
        )

        assert plan.id is not None
        assert plan.total_violations == 5
        assert plan.fixable_violations == 4

    def test_agent_config_defaults(self):
        """Test agent configuration defaults."""
        config = AgentConfig()

        assert config.auto_fix_enabled is False
        assert config.auto_fix_confidence_threshold == 0.9
        assert config.require_approval_for_refactor is True

    def test_analysis_result_to_dict(self):
        """Test analysis result conversion."""
        result = AnalysisResult(
            violations_found=3,
            fixes_applied=1,
            issues_created=0,
            prs_created=0,
        )

        data = result.to_dict()

        assert data["violations_found"] == 3
        assert data["fixes_applied"] == 1


class TestIDEAgentService:
    """Test IDE Agent service."""

    @pytest.fixture
    def service(self, db_session: AsyncSession):
        """Create IDE Agent service instance."""
        return IDEAgentService(db=db_session, organization_id=uuid4())

    async def test_start_session(self, service):
        """Test starting a new agent session."""
        session = await service.start_session(
            trigger_type=AgentTriggerType.MANUAL,
            trigger_context={"file": "test.py"},
        )

        assert session is not None
        assert session.status == AgentStatus.IDLE
        assert session.trigger_type == AgentTriggerType.MANUAL

    async def test_analyze_code_detects_violations(self, service):
        """Test code analysis detects violations."""
        session = await service.start_session(
            trigger_type=AgentTriggerType.MANUAL,
        )

        code = """
def store_user_data(user):
    # Store PII directly without encryption
    db.users.insert({
        "email": user.email,
        "ssn": user.ssn,
        "credit_card": user.credit_card
    })
"""

        violations = await service.analyze_code(
            session=session,
            code=code,
            file_path="src/users.py",
            language="python",
        )

        assert len(violations) > 0
        assert session.violations_found > 0

    async def test_generate_fixes_for_violations(self, service):
        """Test generating fixes for violations."""
        session = await service.start_session(
            trigger_type=AgentTriggerType.MANUAL,
        )

        code = "user_email = get_email()"
        violations = [
            ComplianceViolation(
                rule_id="GDPR-PII-001",
                rule_name="PII Detection",
                regulation="GDPR",
                message="PII should be encrypted",
                original_code=code,
                confidence=0.9,
            )
        ]

        fixes = await service.generate_fixes(
            session=session,
            violations=violations,
            code=code,
            language="python",
        )

        assert len(fixes) > 0
        for fix in fixes:
            assert fix.fixed_code is not None
            assert fix.explanation is not None

    async def test_create_refactor_plan(self, service):
        """Test creating a refactor plan."""
        session = await service.start_session(
            trigger_type=AgentTriggerType.MANUAL,
        )

        violations = [
            ComplianceViolation(
                rule_id="GDPR-PII-001",
                rule_name="PII Detection",
                regulation="GDPR",
                message="Test violation 1",
                file_path="src/users.py",
                start_line=10,
                original_code="test",
                confidence=0.9,
            ),
            ComplianceViolation(
                rule_id="GDPR-PII-002",
                rule_name="Encryption",
                regulation="GDPR",
                message="Test violation 2",
                file_path="src/api.py",
                start_line=20,
                original_code="test2",
                confidence=0.8,
            ),
        ]

        fixes = [
            ProposedFix(
                fixed_code="fixed1",
                explanation="Fix 1",
                confidence=FixConfidence.HIGH,
                confidence_score=0.9,
            ),
            ProposedFix(
                fixed_code="fixed2",
                explanation="Fix 2",
                confidence=FixConfidence.MEDIUM,
                confidence_score=0.7,
            ),
        ]

        plan = await service.create_refactor_plan(
            session=session,
            violations=violations,
            fixes=fixes,
        )

        assert plan is not None
        assert plan.total_violations == 2
        assert plan.fixable_violations >= 0

    async def test_apply_fixes(self, service):
        """Test applying fixes."""
        session = await service.start_session(
            trigger_type=AgentTriggerType.MANUAL,
        )

        fixes = [
            ProposedFix(
                fixed_code="encrypted_email = encrypt(email)",
                explanation="Encrypt PII",
                confidence=FixConfidence.HIGH,
                confidence_score=0.95,
            )
        ]

        result = await service.apply_fixes(
            session=session,
            fixes=fixes,
            dry_run=True,
        )

        assert "applied" in result or "dry_run" in result

    async def test_run_full_analysis(self, service):
        """Test running full analysis pipeline."""
        code = """
def get_user(user_id):
    return db.query("SELECT * FROM users WHERE id = " + user_id)
"""

        session = await service.run_full_analysis(
            code=code,
            file_path="src/db.py",
            language="python",
        )

        assert session is not None
        assert session.status in [AgentStatus.COMPLETED, AgentStatus.WAITING_APPROVAL]

    async def test_get_config(self, service):
        """Test getting configuration."""
        org_id = uuid4()
        config = service.get_config(org_id)

        assert config is not None
        assert isinstance(config.enabled_triggers, list)

    async def test_update_config(self, service):
        """Test updating configuration."""
        org_id = uuid4()
        updates = {
            "auto_fix_enabled": True,
            "auto_fix_confidence_threshold": 0.95,
        }

        config = service.update_config(org_id, updates)

        assert config.auto_fix_enabled is True
        assert config.auto_fix_confidence_threshold == 0.95

    async def test_list_sessions(self, service):
        """Test listing sessions."""
        # Create some sessions
        await service.start_session(trigger_type=AgentTriggerType.MANUAL)
        await service.start_session(trigger_type=AgentTriggerType.FILE_SAVE)

        sessions = service.list_sessions(limit=10)

        assert len(sessions) >= 2

    async def test_get_session(self, service):
        """Test getting a specific session."""
        session = await service.start_session(
            trigger_type=AgentTriggerType.MANUAL,
        )

        retrieved = service.get_session(session.id)

        assert retrieved is not None
        assert retrieved.id == session.id

    async def test_cancel_session(self, service):
        """Test cancelling a session."""
        session = await service.start_session(
            trigger_type=AgentTriggerType.MANUAL,
        )

        cancelled = service.cancel_session(session.id)

        assert cancelled is not None
        assert cancelled.status == AgentStatus.CANCELLED


class TestAgentActions:
    """Test agent action handling."""

    @pytest.fixture
    def service(self, db_session: AsyncSession):
        """Create service instance."""
        return IDEAgentService(db=db_session, organization_id=uuid4())

    async def test_approve_action(self, service):
        """Test approving an action."""
        session = await service.start_session(
            trigger_type=AgentTriggerType.MANUAL,
        )

        # Create an action
        action = AgentAction(
            session_id=session.id,
            action_type=AgentActionType.REFACTOR,
            description="Refactor code",
            requires_approval=True,
        )
        session.actions.append(action)

        approved = await service.approve_action(session.id, action.id)

        assert approved is not None
        assert approved.approved is True

    async def test_reject_action(self, service):
        """Test rejecting an action."""
        session = await service.start_session(
            trigger_type=AgentTriggerType.MANUAL,
        )

        action = AgentAction(
            session_id=session.id,
            action_type=AgentActionType.CREATE_PR,
            description="Create PR",
            requires_approval=True,
        )
        session.actions.append(action)

        rejected = await service.reject_action(
            session.id,
            action.id,
            reason="Not ready for PR",
        )

        assert rejected is not None
        assert rejected.approved is False
        assert rejected.rejection_reason == "Not ready for PR"


class TestGetIDEAgentService:
    """Test the factory function."""

    def test_creates_service(self, db_session: AsyncSession):
        """Test factory creates service instance."""
        org_id = uuid4()
        service = get_ide_agent_service(db=db_session, organization_id=org_id)

        assert isinstance(service, IDEAgentService)
        assert service.organization_id == org_id
