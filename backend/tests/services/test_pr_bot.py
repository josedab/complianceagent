"""Tests for PR Bot service."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.pr_bot import PRBot, PRBotConfig, PRBotResult
from app.services.pr_bot.queue import PRAnalysisQueue, PRAnalysisTask, TaskStatus
from app.services.pr_bot.checks import ChecksService, CheckConclusion
from app.services.pr_bot.comments import CommentGenerator
from app.services.pr_bot.labels import LabelService, ComplianceLabel

pytestmark = pytest.mark.asyncio


class TestPRBotConfig:
    """Test PRBotConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = PRBotConfig()
        
        assert config.enabled is True
        assert config.auto_comment is True
        assert config.auto_label is True
        assert config.create_check_run is True
        assert config.block_on_critical is True
        assert config.min_severity == "medium"
        assert "GDPR" in config.frameworks

    def test_custom_config(self):
        """Test custom configuration."""
        config = PRBotConfig(
            enabled=True,
            auto_comment=False,
            block_on_critical=False,
            min_severity="high",
            frameworks=["HIPAA", "SOC2"],
        )
        
        assert config.auto_comment is False
        assert config.block_on_critical is False
        assert config.min_severity == "high"
        assert "HIPAA" in config.frameworks


class TestPRAnalysisQueue:
    """Test PRAnalysisQueue."""

    @pytest.fixture
    def queue(self):
        """Create queue instance."""
        return PRAnalysisQueue()

    async def test_enqueue_task(self, queue):
        """Test enqueueing a task."""
        task = PRAnalysisTask(
            id=uuid4(),
            owner="test-owner",
            repo="test-repo",
            pr_number=123,
            organization_id=uuid4(),
            access_token="test-token",
        )
        
        await queue.enqueue(task)
        
        # Task should be trackable
        retrieved = await queue.get_task(task.id)
        assert retrieved is not None
        assert retrieved.pr_number == 123

    async def test_update_task_status(self, queue):
        """Test updating task status."""
        task = PRAnalysisTask(
            id=uuid4(),
            owner="test-owner",
            repo="test-repo",
            pr_number=123,
            organization_id=uuid4(),
            access_token="test-token",
        )
        
        await queue.enqueue(task)
        await queue.update_status(task.id, TaskStatus.PROCESSING)
        
        retrieved = await queue.get_task(task.id)
        assert retrieved.status == TaskStatus.PROCESSING

    async def test_complete_task(self, queue):
        """Test completing a task with result."""
        task = PRAnalysisTask(
            id=uuid4(),
            owner="test-owner",
            repo="test-repo",
            pr_number=123,
            organization_id=uuid4(),
            access_token="test-token",
        )
        
        result = PRBotResult(
            pr_number=123,
            owner="test-owner",
            repo="test-repo",
            violations_found=5,
            critical_count=1,
            high_count=2,
            medium_count=2,
            low_count=0,
        )
        
        await queue.enqueue(task)
        await queue.complete(task.id, result)
        
        retrieved = await queue.get_task(task.id)
        assert retrieved.status == TaskStatus.COMPLETED
        assert retrieved.result is not None
        assert retrieved.result.violations_found == 5

    async def test_fail_task(self, queue):
        """Test failing a task."""
        task = PRAnalysisTask(
            id=uuid4(),
            owner="test-owner",
            repo="test-repo",
            pr_number=123,
            organization_id=uuid4(),
            access_token="test-token",
        )
        
        await queue.enqueue(task)
        await queue.fail(task.id, "API rate limit exceeded")
        
        retrieved = await queue.get_task(task.id)
        assert retrieved.status == TaskStatus.FAILED
        assert "rate limit" in retrieved.error.lower()


class TestChecksService:
    """Test ChecksService."""

    @pytest.fixture
    def checks_service(self):
        """Create checks service instance."""
        return ChecksService()

    def test_build_output_from_analysis(self, checks_service):
        """Test building check output from analysis result."""
        result = PRBotResult(
            pr_number=123,
            owner="test-owner",
            repo="test-repo",
            violations_found=3,
            critical_count=1,
            high_count=1,
            medium_count=1,
            low_count=0,
            violations=[
                {
                    "rule_id": "GDPR-001",
                    "severity": "critical",
                    "message": "PII logged without masking",
                    "file": "src/user.py",
                    "line": 45,
                },
                {
                    "rule_id": "SOC2-002",
                    "severity": "high",
                    "message": "Hardcoded credential",
                    "file": "src/config.py",
                    "line": 12,
                },
            ],
        )
        
        output = checks_service.build_output_from_analysis(result)
        
        assert output["title"] is not None
        assert "3" in output["summary"] or "violations" in output["summary"].lower()
        assert len(output["annotations"]) == 2

    def test_determine_conclusion_critical(self, checks_service):
        """Test conclusion determination with critical issues."""
        result = PRBotResult(
            pr_number=123,
            owner="test-owner",
            repo="test-repo",
            violations_found=1,
            critical_count=1,
            high_count=0,
            medium_count=0,
            low_count=0,
        )
        
        conclusion = checks_service.determine_conclusion(result, block_on_critical=True)
        assert conclusion == CheckConclusion.FAILURE

    def test_determine_conclusion_no_critical(self, checks_service):
        """Test conclusion determination without critical issues."""
        result = PRBotResult(
            pr_number=123,
            owner="test-owner",
            repo="test-repo",
            violations_found=2,
            critical_count=0,
            high_count=2,
            medium_count=0,
            low_count=0,
        )
        
        conclusion = checks_service.determine_conclusion(result, block_on_critical=True)
        assert conclusion in [CheckConclusion.NEUTRAL, CheckConclusion.SUCCESS]

    def test_determine_conclusion_clean(self, checks_service):
        """Test conclusion for clean PR."""
        result = PRBotResult(
            pr_number=123,
            owner="test-owner",
            repo="test-repo",
            violations_found=0,
            critical_count=0,
            high_count=0,
            medium_count=0,
            low_count=0,
        )
        
        conclusion = checks_service.determine_conclusion(result, block_on_critical=True)
        assert conclusion == CheckConclusion.SUCCESS


class TestCommentGenerator:
    """Test CommentGenerator."""

    @pytest.fixture
    def comment_gen(self):
        """Create comment generator instance."""
        return CommentGenerator()

    def test_generate_summary_comment(self, comment_gen):
        """Test generating summary comment."""
        result = PRBotResult(
            pr_number=123,
            owner="test-owner",
            repo="test-repo",
            violations_found=5,
            critical_count=1,
            high_count=2,
            medium_count=2,
            low_count=0,
            violations=[],
        )
        
        comment = comment_gen.generate_summary_comment(result)
        
        assert "## 🛡️ ComplianceAgent Analysis" in comment
        assert "5" in comment  # Total violations
        assert "Critical" in comment

    def test_generate_inline_comment(self, comment_gen):
        """Test generating inline comment."""
        violation = {
            "rule_id": "GDPR-PII-001",
            "severity": "critical",
            "message": "Personal data logged without encryption",
            "framework": "GDPR",
            "article": "Article 32",
            "quick_fix": "Encrypt or mask PII before logging",
        }
        
        comment = comment_gen.generate_inline_comment(violation)
        
        assert "GDPR" in comment
        assert "critical" in comment.lower() or "🔴" in comment
        assert "encrypt" in comment.lower() or "mask" in comment.lower()

    def test_generate_clean_pr_comment(self, comment_gen):
        """Test generating comment for clean PR."""
        result = PRBotResult(
            pr_number=123,
            owner="test-owner",
            repo="test-repo",
            violations_found=0,
            critical_count=0,
            high_count=0,
            medium_count=0,
            low_count=0,
        )
        
        comment = comment_gen.generate_summary_comment(result)
        
        assert "✅" in comment or "clean" in comment.lower() or "no" in comment.lower()


class TestLabelService:
    """Test LabelService."""

    @pytest.fixture
    def label_service(self):
        """Create label service instance."""
        return LabelService()

    def test_determine_labels_critical(self, label_service):
        """Test label determination for critical violations."""
        result = PRBotResult(
            pr_number=123,
            owner="test-owner",
            repo="test-repo",
            violations_found=1,
            critical_count=1,
            high_count=0,
            medium_count=0,
            low_count=0,
        )
        
        labels = label_service.determine_labels(result)
        
        assert ComplianceLabel.COMPLIANCE_CRITICAL in labels

    def test_determine_labels_needs_review(self, label_service):
        """Test label determination for review-needed."""
        result = PRBotResult(
            pr_number=123,
            owner="test-owner",
            repo="test-repo",
            violations_found=3,
            critical_count=0,
            high_count=2,
            medium_count=1,
            low_count=0,
        )
        
        labels = label_service.determine_labels(result)
        
        assert ComplianceLabel.NEEDS_COMPLIANCE_REVIEW in labels

    def test_determine_labels_compliant(self, label_service):
        """Test label determination for compliant PR."""
        result = PRBotResult(
            pr_number=123,
            owner="test-owner",
            repo="test-repo",
            violations_found=0,
            critical_count=0,
            high_count=0,
            medium_count=0,
            low_count=0,
        )
        
        labels = label_service.determine_labels(result)
        
        assert ComplianceLabel.COMPLIANCE_PASSED in labels

    def test_get_label_definitions(self, label_service):
        """Test getting label definitions."""
        definitions = label_service.get_label_definitions()
        
        assert len(definitions) > 0
        for label, defn in definitions.items():
            assert "color" in defn
            assert "description" in defn


class TestPRBot:
    """Test PRBot main class."""

    @pytest.fixture
    def mock_github_client(self):
        """Create mock GitHub client."""
        client = MagicMock()
        client.get_pull_request = AsyncMock(return_value={
            "number": 123,
            "title": "Test PR",
            "head": {"sha": "abc123"},
            "base": {"ref": "main"},
        })
        client.get_pull_request_files = AsyncMock(return_value=[
            {"filename": "src/user.py", "status": "modified", "patch": "@@ -1,5 +1,10 @@\n+def get_user():\n+    log(user.email)"},
        ])
        client.create_check_run = AsyncMock(return_value={"id": 456})
        client.update_check_run = AsyncMock(return_value={"id": 456})
        client.create_review_comment = AsyncMock(return_value={"id": 789})
        client.create_issue_comment = AsyncMock(return_value={"id": 101})
        client.add_labels = AsyncMock(return_value=[])
        return client

    @pytest.fixture
    def mock_analyzer(self):
        """Create mock PR analyzer."""
        analyzer = MagicMock()
        analyzer.analyze_diff = AsyncMock(return_value=[
            {
                "rule_id": "GDPR-LOG-001",
                "severity": "critical",
                "message": "PII in logs",
                "file": "src/user.py",
                "line": 2,
                "framework": "GDPR",
            },
        ])
        return analyzer

    @pytest.fixture
    def pr_bot(self, mock_github_client, mock_analyzer):
        """Create PRBot instance with mocks."""
        config = PRBotConfig()
        bot = PRBot(config=config)
        bot._github_client = mock_github_client
        bot._analyzer = mock_analyzer
        return bot

    async def test_analyze_pr(self, pr_bot, mock_github_client, mock_analyzer):
        """Test analyzing a PR."""
        with patch.object(pr_bot, '_get_github_client', return_value=mock_github_client):
            with patch.object(pr_bot, '_get_analyzer', return_value=mock_analyzer):
                result = await pr_bot.analyze_pr(
                    owner="test-owner",
                    repo="test-repo",
                    pr_number=123,
                    access_token="test-token",
                )
        
        assert result is not None
        assert result.pr_number == 123
        assert result.violations_found >= 0

    async def test_process_task(self, pr_bot, mock_github_client, mock_analyzer):
        """Test processing a queued task."""
        task = PRAnalysisTask(
            id=uuid4(),
            owner="test-owner",
            repo="test-repo",
            pr_number=123,
            organization_id=uuid4(),
            access_token="test-token",
        )
        
        with patch.object(pr_bot, '_get_github_client', return_value=mock_github_client):
            with patch.object(pr_bot, '_get_analyzer', return_value=mock_analyzer):
                result = await pr_bot.process_task(task)
        
        assert result is not None

    async def test_create_check_run(self, pr_bot, mock_github_client):
        """Test creating GitHub check run."""
        result = PRBotResult(
            pr_number=123,
            owner="test-owner",
            repo="test-repo",
            violations_found=1,
            critical_count=1,
            high_count=0,
            medium_count=0,
            low_count=0,
        )
        
        with patch.object(pr_bot, '_get_github_client', return_value=mock_github_client):
            check_id = await pr_bot._create_check_run(
                owner="test-owner",
                repo="test-repo",
                head_sha="abc123",
                result=result,
                access_token="test-token",
            )
        
        assert check_id is not None
        mock_github_client.create_check_run.assert_called()


class TestPRBotResult:
    """Test PRBotResult dataclass."""

    def test_result_creation(self):
        """Test creating a result."""
        result = PRBotResult(
            pr_number=123,
            owner="test-owner",
            repo="test-repo",
            violations_found=5,
            critical_count=1,
            high_count=2,
            medium_count=2,
            low_count=0,
        )
        
        assert result.pr_number == 123
        assert result.total_violations == 5

    def test_result_has_blocking_issues(self):
        """Test checking for blocking issues."""
        result_blocking = PRBotResult(
            pr_number=123,
            owner="test-owner",
            repo="test-repo",
            violations_found=1,
            critical_count=1,
            high_count=0,
            medium_count=0,
            low_count=0,
        )
        
        result_non_blocking = PRBotResult(
            pr_number=124,
            owner="test-owner",
            repo="test-repo",
            violations_found=2,
            critical_count=0,
            high_count=2,
            medium_count=0,
            low_count=0,
        )
        
        assert result_blocking.has_blocking_issues is True
        assert result_non_blocking.has_blocking_issues is False

    def test_result_to_dict(self):
        """Test converting result to dict."""
        result = PRBotResult(
            pr_number=123,
            owner="test-owner",
            repo="test-repo",
            violations_found=3,
            critical_count=1,
            high_count=1,
            medium_count=1,
            low_count=0,
        )
        
        data = result.to_dict()
        
        assert data["pr_number"] == 123
        assert data["violations_found"] == 3
        assert "critical_count" in data
