"""Tests for IDE Copilot suggestions service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.ide.copilot_suggestions import (
    CopilotComplianceSuggester,
    ComplianceSuggestion,
    QuickFix,
    RegulationTooltip,
)

pytestmark = pytest.mark.asyncio


class TestCopilotComplianceSuggester:
    """Test suite for CopilotComplianceSuggester."""

    @pytest.fixture
    def suggester(self):
        """Create CopilotComplianceSuggester instance."""
        return CopilotComplianceSuggester()

    async def test_generate_suggestion(self, suggester):
        """Test generating a compliance suggestion."""
        code = """
        def store_user_email(email: str):
            db.users.insert({"email": email})
        """
        
        with patch.object(suggester, "_call_copilot") as mock_copilot:
            mock_copilot.return_value = ComplianceSuggestion(
                suggestion_id="sugg-001",
                message="Consider encrypting PII before storage",
                severity="warning",
                regulation="GDPR",
                article="Article 32",
                code_range={"start_line": 2, "end_line": 3},
                confidence=0.88,
            )
            
            suggestion = await suggester.generate_suggestion(
                code=code,
                file_path="src/users.py",
                language="python",
                regulations=["GDPR"],
            )
            
            assert suggestion is not None
            assert suggestion.severity in ["info", "warning", "error"]

    async def test_generate_quick_fix(self, suggester):
        """Test generating a quick fix for compliance issue."""
        code = """
        user_data = {"email": email, "name": name}
        save_to_db(user_data)
        """
        
        with patch.object(suggester, "_generate_fix") as mock_fix:
            mock_fix.return_value = QuickFix(
                fix_id="fix-001",
                title="Encrypt PII fields",
                description="Add encryption for email and name fields",
                original_code=code,
                fixed_code="""
        user_data = {"email": encrypt(email), "name": encrypt(name)}
        save_to_db(user_data)
        """,
                explanation="Encrypts personal data to comply with GDPR Article 32",
            )
            
            fix = await suggester.generate_quick_fix(
                code=code,
                issue_type="unencrypted_pii",
                file_path="src/users.py",
                language="python",
            )
            
            assert fix is not None
            assert "encrypt" in fix.fixed_code

    async def test_get_regulation_tooltip(self, suggester):
        """Test getting regulation tooltip."""
        with patch.object(suggester, "_fetch_regulation_info") as mock_fetch:
            mock_fetch.return_value = RegulationTooltip(
                regulation="GDPR",
                article="17",
                title="Right to erasure",
                summary="Data subjects have the right to request deletion of their personal data.",
                key_requirements=[
                    "Delete data without undue delay",
                    "Inform third parties about deletion",
                ],
                related_articles=["Article 16", "Article 18"],
            )
            
            tooltip = await suggester.get_regulation_tooltip(
                regulation="GDPR",
                article="17",
            )
            
            assert tooltip is not None
            assert tooltip.title == "Right to erasure"
            assert len(tooltip.key_requirements) >= 1

    async def test_analyze_code_block(self, suggester):
        """Test deep analysis of code block."""
        code = """
        class UserRepository:
            def get_user(self, user_id: str):
                return db.query(User).filter(User.id == user_id).first()
            
            def delete_user(self, user_id: str):
                user = self.get_user(user_id)
                db.delete(user)
                db.commit()
        """
        
        with patch.object(suggester, "_deep_analyze") as mock_analyze:
            mock_analyze.return_value = {
                "compliance_score": 72,
                "issues": [
                    {
                        "type": "missing_audit_log",
                        "severity": "warning",
                        "message": "Delete operation should be logged for audit trail",
                        "line": 7,
                    },
                    {
                        "type": "missing_soft_delete",
                        "severity": "info",
                        "message": "Consider soft delete for data retention compliance",
                        "line": 7,
                    },
                ],
                "regulations_applicable": ["GDPR", "CCPA"],
                "recommendations": [
                    "Add audit logging for delete operations",
                    "Implement soft delete pattern",
                ],
            }
            
            analysis = await suggester.analyze_code_block(
                code=code,
                file_path="src/repositories/user.py",
                language="python",
                regulations=["GDPR", "CCPA"],
            )
            
            assert analysis["compliance_score"] <= 100
            assert len(analysis["issues"]) >= 1

    async def test_batch_suggestions(self, suggester):
        """Test getting suggestions for multiple files."""
        files = {
            "src/users.py": "def store_user(user): db.save(user)",
            "src/payments.py": "def charge(card): stripe.charge(card)",
        }
        
        with patch.object(suggester, "generate_suggestion") as mock_suggest:
            mock_suggest.side_effect = [
                ComplianceSuggestion(
                    suggestion_id="sugg-001",
                    message="PII encryption needed",
                    severity="warning",
                    regulation="GDPR",
                    confidence=0.85,
                ),
                ComplianceSuggestion(
                    suggestion_id="sugg-002",
                    message="Card data must use tokenization",
                    severity="error",
                    regulation="PCI-DSS",
                    confidence=0.92,
                ),
            ]
            
            suggestions = await suggester.batch_suggestions(
                files=files,
                regulations=["GDPR", "PCI-DSS"],
            )
            
            assert len(suggestions) == 2

    async def test_get_compliance_score(self, suggester):
        """Test getting compliance score for file."""
        code = """
        import hashlib
        
        def store_user(user):
            user['password'] = hashlib.sha256(user['password'].encode()).hexdigest()
            db.save(user)
        """
        
        with patch.object(suggester, "_calculate_score") as mock_score:
            mock_score.return_value = {
                "score": 85,
                "breakdown": {
                    "encryption": 90,
                    "access_control": 80,
                    "audit_logging": 75,
                    "data_handling": 95,
                },
                "issues_found": 2,
                "critical_issues": 0,
            }
            
            score = await suggester.get_compliance_score(
                code=code,
                file_path="src/users.py",
                language="python",
                regulations=["GDPR"],
            )
            
            assert score["score"] >= 0
            assert score["score"] <= 100


class TestComplianceSuggestion:
    """Test ComplianceSuggestion dataclass."""

    def test_suggestion_creation(self):
        """Test creating a suggestion."""
        suggestion = ComplianceSuggestion(
            suggestion_id="sugg-001",
            message="Encrypt sensitive data",
            severity="warning",
            regulation="GDPR",
            article="Article 32",
            code_range={"start_line": 10, "end_line": 15},
            confidence=0.9,
        )
        
        assert suggestion.suggestion_id == "sugg-001"
        assert suggestion.severity == "warning"

    def test_suggestion_to_dict(self):
        """Test converting suggestion to dict."""
        suggestion = ComplianceSuggestion(
            suggestion_id="sugg-002",
            message="Test",
            severity="error",
            regulation="HIPAA",
            confidence=0.8,
        )
        
        sugg_dict = suggestion.to_dict()
        
        assert sugg_dict["severity"] == "error"


class TestQuickFix:
    """Test QuickFix dataclass."""

    def test_quickfix_creation(self):
        """Test creating a quick fix."""
        fix = QuickFix(
            fix_id="fix-001",
            title="Add encryption",
            description="Encrypts PII fields",
            original_code="save(email)",
            fixed_code="save(encrypt(email))",
            explanation="Adds AES-256 encryption",
        )
        
        assert fix.fix_id == "fix-001"
        assert "encrypt" in fix.fixed_code

    def test_quickfix_to_dict(self):
        """Test converting quick fix to dict."""
        fix = QuickFix(
            fix_id="fix-002",
            title="Fix issue",
            description="Desc",
            original_code="a",
            fixed_code="b",
            explanation="Exp",
        )
        
        fix_dict = fix.to_dict()
        
        assert fix_dict["title"] == "Fix issue"


class TestRegulationTooltip:
    """Test RegulationTooltip dataclass."""

    def test_tooltip_creation(self):
        """Test creating a tooltip."""
        tooltip = RegulationTooltip(
            regulation="GDPR",
            article="17",
            title="Right to erasure",
            summary="Delete personal data on request",
            key_requirements=["Delete without delay"],
            related_articles=["Article 16"],
        )
        
        assert tooltip.regulation == "GDPR"
        assert len(tooltip.key_requirements) >= 1

    def test_tooltip_to_dict(self):
        """Test converting tooltip to dict."""
        tooltip = RegulationTooltip(
            regulation="CCPA",
            article="1798.105",
            title="Right to delete",
            summary="Consumer deletion rights",
            key_requirements=[],
            related_articles=[],
        )
        
        tooltip_dict = tooltip.to_dict()
        
        assert tooltip_dict["regulation"] == "CCPA"
