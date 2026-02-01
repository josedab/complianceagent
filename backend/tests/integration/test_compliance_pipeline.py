"""Integration tests for the compliance pipeline."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.copilot import CopilotClient, CopilotMessage, CopilotResponse
from app.agents.orchestrator import ComplianceOrchestrator
from app.models import Organization, Regulation, Requirement, Repository
from app.models.regulation import RegulationStatus


@pytest_asyncio.fixture
async def test_regulation(
    db_session: AsyncSession, test_organization: Organization
) -> Regulation:
    """Create a test regulation."""
    regulation = Regulation(
        id=uuid4(),
        organization_id=test_organization.id,
        name="Test Data Protection Regulation",
        description="Test regulation for data protection compliance",
        source_url="https://example.com/regulation",
        jurisdiction="US",
        industry="Technology",
        status=RegulationStatus.ACTIVE,
        version="1.0",
        full_text="Organizations must ensure data protection...",
    )
    db_session.add(regulation)
    await db_session.commit()
    await db_session.refresh(regulation)
    return regulation


@pytest_asyncio.fixture
async def test_requirement(
    db_session: AsyncSession,
    test_regulation: Regulation,
) -> Requirement:
    """Create a test requirement."""
    requirement = Requirement(
        id=uuid4(),
        regulation_id=test_regulation.id,
        title="Data Encryption Requirement",
        description="All personal data must be encrypted at rest",
        obligation_type="must",
        priority="high",
        section_reference="Section 4.2",
        full_text="Personal data must be encrypted using AES-256 or equivalent.",
    )
    db_session.add(requirement)
    await db_session.commit()
    await db_session.refresh(requirement)
    return requirement


@pytest_asyncio.fixture
async def test_repository(
    db_session: AsyncSession,
    test_organization: Organization,
) -> Repository:
    """Create a test repository."""
    repository = Repository(
        id=uuid4(),
        organization_id=test_organization.id,
        name="test-app",
        url="https://github.com/testorg/test-app",
        default_branch="main",
        scan_patterns=["**/*.py", "**/*.js"],
        is_active=True,
    )
    db_session.add(repository)
    await db_session.commit()
    await db_session.refresh(repository)
    return repository


class TestCompliancePipeline:
    """Integration tests for the compliance processing pipeline."""

    @pytest.mark.asyncio
    async def test_orchestrator_initialization(
        self, mock_copilot_client: MagicMock
    ):
        """Test orchestrator can be initialized."""
        with patch("app.agents.orchestrator.CopilotClient") as MockClient:
            MockClient.return_value = mock_copilot_client
            orchestrator = ComplianceOrchestrator()
            assert orchestrator is not None

    @pytest.mark.asyncio
    async def test_regulation_text_analysis(
        self, mock_copilot_client: MagicMock
    ):
        """Test that regulations can be analyzed for requirements."""
        mock_copilot_client.analyze_legal_text = AsyncMock(
            return_value={
                "requirements": [
                    {
                        "title": "Data Encryption",
                        "description": "All personal data must be encrypted",
                        "obligation_type": "must",
                        "subject": "data controller",
                        "action": "encrypt data",
                        "priority": "high",
                        "confidence": 0.95,
                    },
                    {
                        "title": "Access Logging",
                        "description": "All data access must be logged",
                        "obligation_type": "must",
                        "subject": "system",
                        "action": "log access",
                        "priority": "medium",
                        "confidence": 0.88,
                    },
                ]
            }
        )

        result = await mock_copilot_client.analyze_legal_text(
            "Personal data must be encrypted. All access must be logged."
        )

        assert "requirements" in result
        assert len(result["requirements"]) == 2
        assert result["requirements"][0]["title"] == "Data Encryption"
        assert result["requirements"][0]["obligation_type"] == "must"

    @pytest.mark.asyncio
    async def test_code_mapping(
        self, mock_copilot_client: MagicMock
    ):
        """Test that requirements can be mapped to code."""
        mock_copilot_client.map_requirement_to_code = AsyncMock(
            return_value={
                "mappings": [
                    {
                        "file_path": "src/api/users.py",
                        "function_name": "create_user",
                        "line_start": 45,
                        "line_end": 78,
                        "compliance_status": "partial",
                        "confidence": 0.85,
                        "gaps": ["Missing encryption for email field"],
                    }
                ]
            }
        )

        result = await mock_copilot_client.map_requirement_to_code(
            requirement_text="All personal data must be encrypted",
            code_files={
                "src/api/users.py": "def create_user(email: str): ..."
            }
        )

        assert "mappings" in result
        assert len(result["mappings"]) == 1
        assert result["mappings"][0]["compliance_status"] == "partial"
        assert "gaps" in result["mappings"][0]

    @pytest.mark.asyncio
    async def test_fix_generation(
        self, mock_copilot_client: MagicMock
    ):
        """Test that compliance fixes can be generated."""
        mock_copilot_client.generate_compliant_code = AsyncMock(
            return_value={
                "original_code": "def create_user(email: str):\n    db.save(email)",
                "fixed_code": "def create_user(email: str):\n    encrypted = encrypt(email)\n    db.save(encrypted)",
                "explanation": "Added encryption for email field to comply with data protection requirement",
                "changes": [
                    {
                        "type": "addition",
                        "line": 2,
                        "description": "Added encryption call",
                    }
                ],
            }
        )

        result = await mock_copilot_client.generate_compliant_code(
            code="def create_user(email: str):\n    db.save(email)",
            requirement="All personal data must be encrypted",
            context={"gap": "Missing encryption for email field"},
        )

        assert "fixed_code" in result
        assert "encrypt" in result["fixed_code"]
        assert "explanation" in result


class TestPipelineErrorHandling:
    """Test error handling in the compliance pipeline."""

    @pytest.mark.asyncio
    async def test_handles_copilot_timeout(self):
        """Test that Copilot timeouts are handled gracefully."""
        from app.core.exceptions import CopilotTimeoutError

        mock_client = MagicMock()
        mock_client.chat = AsyncMock(
            side_effect=CopilotTimeoutError("Request timed out")
        )

        with pytest.raises(CopilotTimeoutError):
            await mock_client.chat([CopilotMessage(role="user", content="test")])

    @pytest.mark.asyncio
    async def test_handles_parsing_errors(self):
        """Test that JSON parsing errors are handled."""
        from app.core.exceptions import CopilotParsingError

        mock_client = MagicMock()
        mock_client.analyze_legal_text = AsyncMock(
            side_effect=CopilotParsingError(
                "Failed to parse response",
                raw_response="invalid json {{"
            )
        )

        with pytest.raises(CopilotParsingError) as exc_info:
            await mock_client.analyze_legal_text("test regulation text")

        assert "Failed to parse" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handles_rate_limiting(self):
        """Test that rate limiting is handled with retry info."""
        from app.core.exceptions import CopilotRateLimitError

        mock_client = MagicMock()
        mock_client.chat = AsyncMock(
            side_effect=CopilotRateLimitError(
                "Rate limit exceeded",
                retry_after=30
            )
        )

        with pytest.raises(CopilotRateLimitError) as exc_info:
            await mock_client.chat([CopilotMessage(role="user", content="test")])

        assert exc_info.value.retry_after == 30


class TestComplianceFixtures:
    """Tests using compliance-specific fixtures."""

    @pytest.mark.asyncio
    async def test_regulation_with_requirements(
        self,
        db_session: AsyncSession,
        test_regulation: Regulation,
        test_requirement: Requirement,
    ):
        """Test that regulations and requirements are properly linked."""
        assert test_requirement.regulation_id == test_regulation.id
        assert test_requirement.obligation_type == "must"
        assert test_requirement.priority == "high"

    @pytest.mark.asyncio
    async def test_repository_scanning_setup(
        self,
        test_repository: Repository,
        test_organization: Organization,
    ):
        """Test that repository is properly configured for scanning."""
        assert test_repository.organization_id == test_organization.id
        assert test_repository.is_active is True
        assert "**/*.py" in test_repository.scan_patterns

    @pytest.mark.asyncio
    async def test_full_pipeline_mock(
        self,
        db_session: AsyncSession,
        test_organization: Organization,
        test_regulation: Regulation,
        test_requirement: Requirement,
        test_repository: Repository,
        mock_copilot_client: MagicMock,
    ):
        """Test a complete compliance pipeline with mocked AI."""
        # Setup mock responses for the full pipeline
        mock_copilot_client.map_requirement_to_code = AsyncMock(
            return_value={
                "mappings": [{
                    "file_path": "src/main.py",
                    "compliance_status": "non_compliant",
                    "confidence": 0.9,
                    "gaps": ["Missing encryption"],
                }]
            }
        )

        mock_copilot_client.generate_compliant_code = AsyncMock(
            return_value={
                "fixed_code": "# Fixed code with encryption",
                "explanation": "Added encryption",
            }
        )

        # Simulate pipeline steps
        # Step 1: Map requirement to code
        mapping_result = await mock_copilot_client.map_requirement_to_code(
            requirement_text=test_requirement.full_text,
            code_files={"src/main.py": "# Original code"}
        )

        assert mapping_result["mappings"][0]["compliance_status"] == "non_compliant"

        # Step 2: Generate fix for non-compliant mapping
        fix_result = await mock_copilot_client.generate_compliant_code(
            code="# Original code",
            requirement=test_requirement.full_text,
            context={"gaps": mapping_result["mappings"][0]["gaps"]}
        )

        assert "fixed_code" in fix_result
        assert "encryption" in fix_result["fixed_code"].lower() or "explanation" in fix_result


class TestEndToEndCompliance:
    """End-to-end integration tests for compliance workflows."""

    @pytest.mark.asyncio
    async def test_regulation_import_workflow(
        self,
        db_session: AsyncSession,
        test_organization: Organization,
        mock_copilot_client: MagicMock,
    ):
        """Test importing and processing a new regulation."""
        # Mock the regulation parsing
        mock_copilot_client.analyze_legal_text = AsyncMock(
            return_value={
                "requirements": [
                    {
                        "title": "Data Retention Policy",
                        "description": "Personal data must not be retained longer than necessary",
                        "obligation_type": "must_not",
                        "priority": "high",
                        "confidence": 0.92,
                    }
                ]
            }
        )

        # Simulate regulation import
        regulation_text = """
        Article 5 - Data Retention
        Personal data must not be retained for periods longer than necessary
        for the purposes for which the personal data are processed.
        """

        result = await mock_copilot_client.analyze_legal_text(regulation_text)

        assert len(result["requirements"]) == 1
        req = result["requirements"][0]
        assert req["obligation_type"] == "must_not"
        assert req["priority"] == "high"
        assert req["confidence"] > 0.9

    @pytest.mark.asyncio
    async def test_repository_scan_workflow(
        self,
        test_repository: Repository,
        test_requirement: Requirement,
        mock_copilot_client: MagicMock,
        mock_github_client: MagicMock,
    ):
        """Test scanning a repository for compliance."""
        # Mock file listing
        mock_github_client.list_files = AsyncMock(
            return_value=[
                {"path": "src/user_service.py", "type": "file"},
                {"path": "src/data_handler.py", "type": "file"},
            ]
        )

        # Mock file content
        mock_github_client.get_file_content = AsyncMock(
            side_effect=[
                "class UserService:\n    def save_user(self, data):\n        db.insert(data)",
                "def handle_data(raw):\n    return process(raw)",
            ]
        )

        # Mock compliance mapping
        mock_copilot_client.map_requirement_to_code = AsyncMock(
            return_value={
                "mappings": [
                    {
                        "file_path": "src/user_service.py",
                        "function_name": "save_user",
                        "compliance_status": "non_compliant",
                        "confidence": 0.87,
                        "gaps": ["Data not encrypted before storage"],
                    },
                    {
                        "file_path": "src/data_handler.py",
                        "function_name": "handle_data",
                        "compliance_status": "compliant",
                        "confidence": 0.82,
                        "gaps": [],
                    },
                ]
            }
        )

        # Get files
        files = await mock_github_client.list_files(
            repo=test_repository.url,
            path="src",
            patterns=test_repository.scan_patterns,
        )
        assert len(files) == 2

        # Map to compliance
        mapping_result = await mock_copilot_client.map_requirement_to_code(
            requirement_text=test_requirement.full_text,
            code_files={f["path"]: "code" for f in files}
        )

        non_compliant = [
            m for m in mapping_result["mappings"]
            if m["compliance_status"] == "non_compliant"
        ]
        assert len(non_compliant) == 1
        assert non_compliant[0]["file_path"] == "src/user_service.py"
