"""Tests for CI/CD compliance service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.cicd import (
    CICDComplianceAnalyzer,
    ComplianceScanResult,
    SARIFReport,
    GitLabCodeQualityReport,
    Finding,
    Severity,
)

pytestmark = pytest.mark.asyncio


class TestCICDComplianceAnalyzer:
    """Test suite for CICDComplianceAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create CICDComplianceAnalyzer instance."""
        return CICDComplianceAnalyzer()

    async def test_scan_repository(self, analyzer):
        """Test scanning a repository."""
        files = {
            "src/users.py": """
                def get_user(user_id):
                    return db.query(User).filter(User.id == user_id).first()
            """,
            "src/payments.py": """
                def process_payment(card_number):
                    return stripe.charge(card_number)
            """,
        }
        
        with patch.object(analyzer, "_analyze_files") as mock_analyze:
            mock_analyze.return_value = ComplianceScanResult(
                scan_id="scan-001",
                status="completed",
                total_files=2,
                files_with_issues=1,
                findings=[
                    Finding(
                        finding_id="FIND-001",
                        rule_id="PCI-DSS-3.4",
                        severity=Severity.HIGH,
                        message="Card number should be tokenized",
                        file_path="src/payments.py",
                        line_number=3,
                        regulation="PCI-DSS",
                    ),
                ],
                summary={
                    "critical": 0,
                    "high": 1,
                    "medium": 0,
                    "low": 0,
                },
            )
            
            result = await analyzer.scan(
                files=files,
                regulations=["GDPR", "PCI-DSS"],
            )
            
            assert result.status == "completed"
            assert len(result.findings) >= 1

    async def test_scan_with_config(self, analyzer):
        """Test scanning with custom configuration."""
        files = {"src/main.py": "print('hello')"}
        config = {
            "severity_threshold": "medium",
            "exclude_patterns": ["*_test.py"],
            "regulations": ["GDPR"],
        }
        
        with patch.object(analyzer, "_analyze_files") as mock_analyze:
            mock_analyze.return_value = ComplianceScanResult(
                scan_id="scan-002",
                status="completed",
                total_files=1,
                files_with_issues=0,
                findings=[],
                summary={"critical": 0, "high": 0, "medium": 0, "low": 0},
            )
            
            result = await analyzer.scan(
                files=files,
                config=config,
            )
            
            assert result.status == "completed"

    async def test_generate_sarif_report(self, analyzer):
        """Test generating SARIF report."""
        scan_result = ComplianceScanResult(
            scan_id="scan-003",
            status="completed",
            total_files=2,
            files_with_issues=1,
            findings=[
                Finding(
                    finding_id="FIND-001",
                    rule_id="GDPR-32",
                    severity=Severity.HIGH,
                    message="Unencrypted PII storage",
                    file_path="src/users.py",
                    line_number=10,
                    regulation="GDPR",
                ),
            ],
            summary={"critical": 0, "high": 1, "medium": 0, "low": 0},
        )
        
        sarif = await analyzer.to_sarif(scan_result)
        
        assert sarif is not None
        assert sarif.version == "2.1.0"
        assert len(sarif.runs) >= 1
        assert len(sarif.runs[0].results) >= 1

    async def test_generate_gitlab_report(self, analyzer):
        """Test generating GitLab Code Quality report."""
        scan_result = ComplianceScanResult(
            scan_id="scan-004",
            status="completed",
            total_files=1,
            files_with_issues=1,
            findings=[
                Finding(
                    finding_id="FIND-002",
                    rule_id="HIPAA-164.312",
                    severity=Severity.MEDIUM,
                    message="Missing access controls",
                    file_path="src/api.py",
                    line_number=25,
                    regulation="HIPAA",
                ),
            ],
            summary={"critical": 0, "high": 0, "medium": 1, "low": 0},
        )
        
        gitlab_report = await analyzer.to_gitlab_code_quality(scan_result)
        
        assert gitlab_report is not None
        assert len(gitlab_report.issues) >= 1

    async def test_incremental_scan(self, analyzer):
        """Test incremental scan (changed files only)."""
        changed_files = {
            "src/new_feature.py": "def new_function(): pass",
        }
        
        with patch.object(analyzer, "_analyze_files") as mock_analyze:
            mock_analyze.return_value = ComplianceScanResult(
                scan_id="scan-005",
                status="completed",
                total_files=1,
                files_with_issues=0,
                findings=[],
                summary={"critical": 0, "high": 0, "medium": 0, "low": 0},
            )
            
            result = await analyzer.incremental_scan(
                changed_files=changed_files,
                base_commit="abc123",
                head_commit="def456",
                regulations=["GDPR"],
            )
            
            assert result.status == "completed"
            assert result.total_files == 1

    async def test_should_block_merge(self, analyzer):
        """Test determining if PR should be blocked."""
        result_with_critical = ComplianceScanResult(
            scan_id="scan-006",
            status="completed",
            total_files=1,
            files_with_issues=1,
            findings=[
                Finding(
                    finding_id="FIND-003",
                    rule_id="CRIT-001",
                    severity=Severity.CRITICAL,
                    message="Critical compliance violation",
                    file_path="src/main.py",
                    line_number=1,
                    regulation="GDPR",
                ),
            ],
            summary={"critical": 1, "high": 0, "medium": 0, "low": 0},
        )
        
        should_block = analyzer.should_block_merge(
            result=result_with_critical,
            threshold=Severity.HIGH,
        )
        
        assert should_block is True

    async def test_should_not_block_merge(self, analyzer):
        """Test PR should not be blocked for low severity."""
        result_low_severity = ComplianceScanResult(
            scan_id="scan-007",
            status="completed",
            total_files=1,
            files_with_issues=1,
            findings=[
                Finding(
                    finding_id="FIND-004",
                    rule_id="LOW-001",
                    severity=Severity.LOW,
                    message="Minor suggestion",
                    file_path="src/main.py",
                    line_number=1,
                    regulation="GDPR",
                ),
            ],
            summary={"critical": 0, "high": 0, "medium": 0, "low": 1},
        )
        
        should_block = analyzer.should_block_merge(
            result=result_low_severity,
            threshold=Severity.HIGH,
        )
        
        assert should_block is False

    async def test_generate_pr_comment(self, analyzer):
        """Test generating PR comment."""
        result = ComplianceScanResult(
            scan_id="scan-008",
            status="completed",
            total_files=5,
            files_with_issues=2,
            findings=[
                Finding(
                    finding_id="FIND-005",
                    rule_id="GDPR-17",
                    severity=Severity.HIGH,
                    message="Missing deletion handler",
                    file_path="src/users.py",
                    line_number=50,
                    regulation="GDPR",
                ),
            ],
            summary={"critical": 0, "high": 1, "medium": 0, "low": 0},
        )
        
        comment = await analyzer.generate_pr_comment(result)
        
        assert comment is not None
        assert "compliance" in comment.lower() or "finding" in comment.lower()


class TestComplianceScanResult:
    """Test ComplianceScanResult dataclass."""

    def test_result_creation(self):
        """Test creating a scan result."""
        result = ComplianceScanResult(
            scan_id="scan-001",
            status="completed",
            total_files=10,
            files_with_issues=2,
            findings=[],
            summary={"critical": 0, "high": 0, "medium": 2, "low": 5},
        )
        
        assert result.scan_id == "scan-001"
        assert result.total_files == 10

    def test_result_to_dict(self):
        """Test converting result to dict."""
        result = ComplianceScanResult(
            scan_id="scan-002",
            status="failed",
            total_files=1,
            files_with_issues=1,
            findings=[],
            summary={},
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["status"] == "failed"


class TestFinding:
    """Test Finding dataclass."""

    def test_finding_creation(self):
        """Test creating a finding."""
        finding = Finding(
            finding_id="FIND-001",
            rule_id="GDPR-32",
            severity=Severity.HIGH,
            message="Encrypt personal data",
            file_path="src/data.py",
            line_number=25,
            regulation="GDPR",
        )
        
        assert finding.severity == Severity.HIGH
        assert finding.line_number == 25

    def test_finding_to_dict(self):
        """Test converting finding to dict."""
        finding = Finding(
            finding_id="FIND-002",
            rule_id="TEST-001",
            severity=Severity.LOW,
            message="Test",
            file_path="test.py",
            line_number=1,
            regulation="TEST",
        )
        
        finding_dict = finding.to_dict()
        
        assert finding_dict["severity"] == "low"


class TestSARIFReport:
    """Test SARIF report generation."""

    def test_sarif_structure(self):
        """Test SARIF report structure."""
        sarif = SARIFReport(
            version="2.1.0",
            schema="https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            runs=[
                {
                    "tool": {
                        "driver": {
                            "name": "ComplianceAgent",
                            "version": "1.0.0",
                        }
                    },
                    "results": [],
                }
            ],
        )
        
        assert sarif.version == "2.1.0"
        assert len(sarif.runs) == 1


class TestSeverity:
    """Test Severity enum."""

    def test_severity_values(self):
        """Test severity values."""
        assert Severity.CRITICAL.value == "critical"
        assert Severity.HIGH.value == "high"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.LOW.value == "low"

    def test_severity_comparison(self):
        """Test severity can be compared."""
        assert Severity.CRITICAL != Severity.LOW
        assert Severity.HIGH != Severity.MEDIUM
