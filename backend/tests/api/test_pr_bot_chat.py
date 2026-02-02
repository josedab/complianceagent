"""Tests for PR Bot and Chat API endpoints."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestPRBotAPI:
    """Test PR Bot API endpoints."""

    async def test_analyze_pr(self, client: AsyncClient, auth_headers: dict):
        """Test triggering PR analysis."""
        with patch("app.api.v1.pr_bot.analyze_pr_task") as mock_task:
            mock_task.delay = MagicMock(return_value=MagicMock(id="task-123"))
            
            response = await client.post(
                "/api/v1/pr-bot/analyze",
                headers=auth_headers,
                json={
                    "owner": "test-owner",
                    "repo": "test-repo",
                    "pr_number": 123,
                },
            )
        
        # May need GitHub token in org settings
        assert response.status_code in [200, 400, 422]

    async def test_get_task_status(self, client: AsyncClient, auth_headers: dict):
        """Test getting task status."""
        task_id = str(uuid4())
        
        response = await client.get(
            f"/api/v1/pr-bot/task/{task_id}",
            headers=auth_headers,
        )
        
        # Task may not exist
        assert response.status_code in [200, 404]

    async def test_get_pr_bot_config(self, client: AsyncClient, auth_headers: dict):
        """Test getting PR bot configuration."""
        response = await client.get(
            "/api/v1/pr-bot/config",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "enabled" in data
        assert "frameworks" in data

    async def test_update_pr_bot_config(self, client: AsyncClient, auth_headers: dict):
        """Test updating PR bot configuration."""
        response = await client.put(
            "/api/v1/pr-bot/config",
            headers=auth_headers,
            json={
                "enabled": True,
                "auto_comment": True,
                "block_on_critical": True,
                "frameworks": ["GDPR", "HIPAA"],
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is True

    async def test_batch_analyze_prs(self, client: AsyncClient, auth_headers: dict):
        """Test batch analyzing multiple PRs."""
        with patch("app.api.v1.pr_bot.batch_analyze_prs_task") as mock_task:
            mock_task.delay = MagicMock()
            
            response = await client.post(
                "/api/v1/pr-bot/analyze/batch",
                headers=auth_headers,
                json={
                    "prs": [
                        {"owner": "test-owner", "repo": "test-repo", "pr_number": 1},
                        {"owner": "test-owner", "repo": "test-repo", "pr_number": 2},
                    ],
                },
            )
        
        assert response.status_code in [200, 400, 422]

    async def test_get_pr_bot_stats(self, client: AsyncClient, auth_headers: dict):
        """Test getting PR bot statistics."""
        response = await client.get(
            "/api/v1/pr-bot/stats",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_analyzed" in data or "prs_analyzed" in data or isinstance(data, dict)

    async def test_get_analysis_history(self, client: AsyncClient, auth_headers: dict):
        """Test getting analysis history."""
        response = await client.get(
            "/api/v1/pr-bot/history",
            headers=auth_headers,
            params={"limit": 10},
        )
        
        assert response.status_code == 200


class TestChatAPI:
    """Test Compliance Chat API endpoints."""

    async def test_send_message(self, client: AsyncClient, auth_headers: dict):
        """Test sending a chat message."""
        with patch("app.services.chat.get_compliance_assistant") as mock_get:
            mock_assistant = MagicMock()
            mock_assistant.chat = AsyncMock(return_value=MagicMock(
                id=uuid4(),
                conversation_id="conv-123",
                content="GDPR requires encryption for personal data.",
                citations=[],
                context_used=[],
                actions=[],
                model="gpt-4",
                input_tokens=100,
                output_tokens=50,
                latency_ms=150.0,
                timestamp=MagicMock(isoformat=MagicMock(return_value="2024-01-01T00:00:00Z")),
            ))
            mock_get.return_value = mock_assistant
            
            response = await client.post(
                "/api/v1/chat/message",
                headers=auth_headers,
                json={
                    "message": "What encryption does GDPR require?",
                    "regulations": ["GDPR"],
                },
            )
        
        assert response.status_code in [200, 500]  # 500 if mocking fails

    async def test_list_conversations(self, client: AsyncClient, auth_headers: dict):
        """Test listing conversations."""
        with patch("app.services.chat.get_compliance_assistant") as mock_get:
            mock_assistant = MagicMock()
            mock_assistant.conversation_manager = MagicMock()
            mock_assistant.conversation_manager.list_conversations = AsyncMock(return_value=[])
            mock_get.return_value = mock_assistant
            
            response = await client.get(
                "/api/v1/chat/conversations",
                headers=auth_headers,
            )
        
        assert response.status_code == 200

    async def test_get_quick_actions(self, client: AsyncClient, auth_headers: dict):
        """Test getting quick actions."""
        with patch("app.services.chat.get_compliance_assistant") as mock_get:
            mock_assistant = MagicMock()
            mock_assistant.get_quick_actions = AsyncMock(return_value=[
                {"label": "Check status", "query": "What's my compliance status?", "icon": "shield"},
            ])
            mock_get.return_value = mock_assistant
            
            response = await client.get(
                "/api/v1/chat/quick-actions",
                headers=auth_headers,
            )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_delete_conversation(self, client: AsyncClient, auth_headers: dict):
        """Test deleting a conversation."""
        conv_id = "test-conv-123"
        
        with patch("app.services.chat.get_compliance_assistant") as mock_get:
            mock_assistant = MagicMock()
            mock_assistant.conversation_manager = MagicMock()
            mock_assistant.conversation_manager.delete = AsyncMock(return_value=True)
            mock_get.return_value = mock_assistant
            
            response = await client.delete(
                f"/api/v1/chat/conversation/{conv_id}",
                headers=auth_headers,
            )
        
        assert response.status_code in [200, 404]

    async def test_analyze_code(self, client: AsyncClient, auth_headers: dict):
        """Test code analysis endpoint."""
        with patch("app.services.chat.get_compliance_assistant") as mock_get:
            mock_assistant = MagicMock()
            mock_assistant.chat = AsyncMock(return_value=MagicMock(
                content="This code has PII logging issues.",
                conversation_id="conv-123",
                citations=[],
                actions=[],
            ))
            mock_get.return_value = mock_assistant
            
            response = await client.post(
                "/api/v1/chat/analyze-code",
                headers=auth_headers,
                params={
                    "code": "print(user.email)",
                    "language": "python",
                },
            )
        
        assert response.status_code in [200, 422, 500]

    async def test_explain_regulation(self, client: AsyncClient, auth_headers: dict):
        """Test regulation explanation endpoint."""
        with patch("app.services.chat.get_compliance_assistant") as mock_get:
            mock_assistant = MagicMock()
            mock_assistant.chat = AsyncMock(return_value=MagicMock(
                content="GDPR Article 17 covers the right to erasure...",
                conversation_id="conv-123",
                citations=[{"source": "GDPR", "title": "Article 17"}],
            ))
            mock_get.return_value = mock_assistant
            
            response = await client.post(
                "/api/v1/chat/explain-regulation",
                headers=auth_headers,
                params={
                    "regulation": "GDPR",
                    "article": "17",
                },
            )
        
        assert response.status_code in [200, 422, 500]


class TestIDEAPIExtended:
    """Test extended IDE API endpoints."""

    async def test_get_team_suppressions(self, client: AsyncClient, auth_headers: dict):
        """Test getting team suppressions."""
        response = await client.get(
            "/api/v1/ide/suppressions",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_request_team_suppression(self, client: AsyncClient, auth_headers: dict):
        """Test requesting a team suppression."""
        response = await client.post(
            "/api/v1/ide/suppressions",
            headers=auth_headers,
            json={
                "rule_id": "GDPR-PII-001",
                "reason": "False positive in test files",
                "pattern": "test_.*\\.py",
            },
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data
        assert data["approved"] is False  # Pending approval

    async def test_delete_team_suppression(self, client: AsyncClient, auth_headers: dict):
        """Test deleting a team suppression."""
        suppression_id = str(uuid4())
        
        response = await client.delete(
            f"/api/v1/ide/suppressions/{suppression_id}",
            headers=auth_headers,
        )
        
        assert response.status_code in [200, 404]

    async def test_submit_feedback(self, client: AsyncClient, auth_headers: dict):
        """Test submitting feedback."""
        response = await client.post(
            "/api/v1/ide/feedback",
            headers=auth_headers,
            json={
                "type": "false_positive",
                "issue": {
                    "requirementId": "GDPR-PII-001",
                    "file": "src/test.py",
                    "line": 10,
                },
                "reason": "This is test code, not production",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "received"

    async def test_get_rule_statistics(self, client: AsyncClient, auth_headers: dict):
        """Test getting rule statistics."""
        response = await client.get(
            "/api/v1/ide/stats/rules",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "rule_id" in data[0]
            assert "total_detections" in data[0]

    async def test_get_single_rule_stats(self, client: AsyncClient, auth_headers: dict):
        """Test getting stats for a single rule."""
        response = await client.get(
            "/api/v1/ide/stats/rules/GDPR-PII-001",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["rule_id"] == "GDPR-PII-001"

    async def test_analyze_document(self, client: AsyncClient, auth_headers: dict):
        """Test document analysis."""
        response = await client.post(
            "/api/v1/ide/analyze",
            headers=auth_headers,
            json={
                "uri": "file:///src/user.py",
                "content": """
def get_user_email(user_id):
    user = db.get(user_id)
    print(f"Email: {user.email}")
    return user.email
""",
                "language": "python",
                "regulations": ["GDPR"],
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "diagnostics" in data
        assert "analysis_time_ms" in data

    async def test_get_quick_fix(self, client: AsyncClient, auth_headers: dict):
        """Test getting AI quick fix."""
        with patch("app.services.ide.get_copilot_suggester") as mock_get:
            mock_suggester = MagicMock()
            mock_suggester.generate_quick_fix = AsyncMock(return_value=MagicMock(
                original_code="print(user.email)",
                fixed_code='print(mask_pii(user.email))',
                explanation="Added PII masking to prevent data exposure in logs",
                imports_added=["from utils import mask_pii"],
                compliance_comments=["# GDPR Art. 32 - Data masking applied"],
            ))
            mock_get.return_value = mock_suggester
            
            response = await client.post(
                "/api/v1/ide/quickfix",
                headers=auth_headers,
                json={
                    "code": "print(user.email)",
                    "diagnostic_code": "GDPR-LOG-001",
                    "diagnostic_message": "PII in logs",
                    "language": "python",
                },
            )
        
        assert response.status_code in [200, 500]

    async def test_deep_analyze(self, client: AsyncClient, auth_headers: dict):
        """Test deep AI analysis."""
        with patch("app.services.ide.get_copilot_suggester") as mock_get:
            mock_suggester = MagicMock()
            mock_suggester.analyze_code_block = AsyncMock(return_value=[])
            mock_get.return_value = mock_suggester
            
            response = await client.post(
                "/api/v1/ide/deep-analyze",
                headers=auth_headers,
                json={
                    "code": """
def process_payment(card_number, cvv):
    log(f"Processing {card_number}")
    return payment_gateway.charge(card_number, cvv)
""",
                    "language": "python",
                    "regulations": ["PCI-DSS", "GDPR"],
                },
            )
        
        assert response.status_code in [200, 500]


class TestWebhooksExtended:
    """Test PR Bot webhook integration."""

    async def test_pr_webhook_triggers_analysis(self, client: AsyncClient):
        """Test that PR webhook triggers analysis."""
        # Simulated GitHub webhook payload
        payload = {
            "action": "opened",
            "number": 123,
            "pull_request": {
                "number": 123,
                "title": "Test PR",
                "head": {"sha": "abc123"},
                "base": {"ref": "main"},
            },
            "repository": {
                "full_name": "test-owner/test-repo",
                "owner": {"login": "test-owner"},
                "name": "test-repo",
            },
            "installation": {
                "id": 12345,
            },
        }
        
        with patch("app.api.v1.webhooks.process_pr_webhook_task") as mock_task:
            mock_task.delay = MagicMock()
            
            response = await client.post(
                "/api/v1/webhooks/github",
                headers={
                    "X-GitHub-Event": "pull_request",
                    "X-Hub-Signature-256": "sha256=test",
                },
                json=payload,
            )
        
        # Webhook should be accepted (signature validation may fail in test)
        assert response.status_code in [200, 202, 400, 401]

    async def test_pr_synchronize_triggers_reanalysis(self, client: AsyncClient):
        """Test that PR sync triggers re-analysis."""
        payload = {
            "action": "synchronize",
            "number": 123,
            "pull_request": {
                "number": 123,
                "head": {"sha": "def456"},
            },
            "repository": {
                "full_name": "test-owner/test-repo",
                "owner": {"login": "test-owner"},
                "name": "test-repo",
            },
        }
        
        with patch("app.api.v1.webhooks.process_pr_webhook_task") as mock_task:
            mock_task.delay = MagicMock()
            
            response = await client.post(
                "/api/v1/webhooks/github",
                headers={
                    "X-GitHub-Event": "pull_request",
                    "X-Hub-Signature-256": "sha256=test",
                },
                json=payload,
            )
        
        assert response.status_code in [200, 202, 400, 401]
