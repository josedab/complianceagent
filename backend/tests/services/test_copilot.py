"""Integration tests for the Copilot SDK client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from app.agents.copilot import CopilotClient, CopilotMessage, CopilotResponse
from app.core.exceptions import (
    CopilotAuthenticationError,
    CopilotConnectionError,
    CopilotParsingError,
    CopilotRateLimitError,
    CopilotTimeoutError,
)

pytestmark = pytest.mark.asyncio


class TestCopilotClient:
    """Test suite for CopilotClient."""

    @pytest.fixture
    def mock_httpx_response(self):
        """Create mock httpx response."""
        response = MagicMock()
        response.json.return_value = {
            "choices": [
                {
                    "message": {"content": "Test response"},
                    "finish_reason": "stop",
                }
            ],
            "model": "test-model",
            "usage": {"prompt_tokens": 10, "completion_tokens": 20},
        }
        response.status_code = 200
        return response

    @pytest.fixture
    def copilot_client(self):
        """Create CopilotClient instance."""
        return CopilotClient(
            api_key="test-api-key",
            default_model="test-model",
            timeout=30.0,
            max_retries=2,
        )

    async def test_chat_completion(self, copilot_client, mock_httpx_response):
        """Test basic chat completion."""
        with patch.object(copilot_client, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_httpx_response)
            copilot_client._client = mock_client

            messages = [CopilotMessage(role="user", content="Hello")]
            response = await copilot_client.chat(messages)

            assert isinstance(response, CopilotResponse)
            assert response.content == "Test response"
            assert response.model == "test-model"
            assert response.finish_reason == "stop"

    async def test_chat_with_system_message(self, copilot_client, mock_httpx_response):
        """Test chat with system message."""
        with patch.object(copilot_client, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_httpx_response)
            copilot_client._client = mock_client

            messages = [CopilotMessage(role="user", content="Test")]
            await copilot_client.chat(messages, system_message="You are helpful")

            # Verify system message was included
            call_args = mock_client.post.call_args
            payload = call_args[1]["json"]
            assert payload["messages"][0]["role"] == "system"
            assert payload["messages"][0]["content"] == "You are helpful"

    async def test_analyze_legal_text(self, copilot_client, mock_httpx_response):
        """Test legal text analysis."""
        # Mock response with JSON requirements
        mock_httpx_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": """[
                            {
                                "reference_id": "REQ-GDPR-001",
                                "title": "Data Processing Consent",
                                "obligation_type": "MUST",
                                "category": "consent",
                                "confidence": 0.95
                            }
                        ]"""
                    },
                    "finish_reason": "stop",
                }
            ],
            "model": "test-model",
            "usage": {},
        }

        with patch.object(copilot_client, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_httpx_response)
            copilot_client._client = mock_client

            requirements = await copilot_client.analyze_legal_text(
                text="Data controllers shall obtain consent...",
                regulation_name="GDPR",
                jurisdiction="EU",
                framework="gdpr",
            )

            assert isinstance(requirements, list)
            assert len(requirements) == 1
            assert requirements[0]["reference_id"] == "REQ-GDPR-001"
            assert requirements[0]["obligation_type"] == "MUST"

    async def test_analyze_legal_text_handles_markdown_json(
        self, copilot_client, mock_httpx_response
    ):
        """Test legal text analysis handles JSON wrapped in markdown."""
        # Mock response with JSON in markdown code block
        mock_httpx_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": """```json
                        [{"reference_id": "REQ-001", "title": "Test"}]
                        ```"""
                    },
                    "finish_reason": "stop",
                }
            ],
            "model": "test-model",
            "usage": {},
        }

        with patch.object(copilot_client, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_httpx_response)
            copilot_client._client = mock_client

            requirements = await copilot_client.analyze_legal_text(
                text="Test text",
                regulation_name="Test",
                jurisdiction="Test",
                framework="test",
            )

            assert len(requirements) == 1
            assert requirements[0]["reference_id"] == "REQ-001"

    async def test_analyze_legal_text_handles_invalid_json(
        self, copilot_client, mock_httpx_response
    ):
        """Test legal text analysis handles invalid JSON gracefully."""
        mock_httpx_response.json.return_value = {
            "choices": [
                {"message": {"content": "Not valid JSON"}, "finish_reason": "stop"}
            ],
            "model": "test-model",
            "usage": {},
        }

        with patch.object(copilot_client, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_httpx_response)
            copilot_client._client = mock_client

            requirements = await copilot_client.analyze_legal_text(
                text="Test", regulation_name="Test", jurisdiction="Test", framework="test"
            )

            # Should return empty list on parse error
            assert requirements == []

    async def test_map_requirement_to_code(self, copilot_client, mock_httpx_response):
        """Test requirement to code mapping."""
        mock_httpx_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": """{
                            "affected_files": [
                                {"path": "src/users.py", "relevance": 0.9}
                            ],
                            "gaps": [
                                {"severity": "major", "description": "Missing consent check"}
                            ],
                            "estimated_effort_hours": 4,
                            "risk_level": "medium",
                            "confidence": 0.85
                        }"""
                    },
                    "finish_reason": "stop",
                }
            ],
            "model": "test-model",
            "usage": {},
        }

        with patch.object(copilot_client, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_httpx_response)
            copilot_client._client = mock_client

            mapping = await copilot_client.map_requirement_to_code(
                requirement={"reference_id": "REQ-001", "title": "Test"},
                codebase_structure="src/\n  users.py\n  api/",
                sample_files={"src/users.py": "def get_user(): pass"},
                languages=["python"],
            )

            assert "affected_files" in mapping
            assert len(mapping["affected_files"]) == 1
            assert mapping["risk_level"] == "medium"

    async def test_generate_compliant_code(self, copilot_client, mock_httpx_response):
        """Test code generation."""
        mock_httpx_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": """{
                            "files": [
                                {
                                    "path": "src/consent.py",
                                    "operation": "create",
                                    "content": "def check_consent(): pass",
                                    "language": "python"
                                }
                            ],
                            "tests": [
                                {
                                    "path": "tests/test_consent.py",
                                    "content": "def test_consent(): assert True",
                                    "test_type": "unit"
                                }
                            ],
                            "pr_title": "Add consent handling",
                            "pr_body": "Implements GDPR consent requirement",
                            "confidence": 0.88,
                            "warnings": []
                        }"""
                    },
                    "finish_reason": "stop",
                }
            ],
            "model": "test-model",
            "usage": {},
        }

        with patch.object(copilot_client, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_httpx_response)
            copilot_client._client = mock_client

            result = await copilot_client.generate_compliant_code(
                requirement={"reference_id": "REQ-001", "title": "Consent"},
                gaps=[{"severity": "major", "description": "Missing consent"}],
                existing_code={"src/users.py": "def get_user(): pass"},
                language="python",
            )

            assert "files" in result
            assert len(result["files"]) == 1
            assert result["files"][0]["path"] == "src/consent.py"
            assert "tests" in result
            assert result["pr_title"] == "Add consent handling"


class TestCopilotClientErrorHandling:
    """Test error handling and retry logic."""

    @pytest.fixture
    def copilot_client(self):
        """Create CopilotClient with short retry settings for testing."""
        return CopilotClient(
            api_key="test-api-key",
            default_model="test-model",
            timeout=5.0,
            max_retries=2,
        )

    async def test_authentication_error_on_401(self, copilot_client):
        """Test 401 response raises CopilotAuthenticationError."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch.object(copilot_client, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_response)
            copilot_client._client = mock_client

            with pytest.raises(CopilotAuthenticationError) as exc_info:
                await copilot_client._make_request({"model": "test"})

            assert "Invalid or expired" in str(exc_info.value)

    async def test_rate_limit_error_on_429(self, copilot_client):
        """Test 429 response raises CopilotRateLimitError."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}

        with patch.object(copilot_client, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_response)
            copilot_client._client = mock_client

            with pytest.raises(CopilotRateLimitError) as exc_info:
                await copilot_client._make_request({"model": "test"})

            assert exc_info.value.retry_after == 60

    async def test_connection_error_on_5xx(self, copilot_client):
        """Test 5xx response raises CopilotConnectionError."""
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.text = "Service Unavailable"

        with patch.object(copilot_client, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_response)
            copilot_client._client = mock_client

            with pytest.raises(CopilotConnectionError) as exc_info:
                await copilot_client._make_request({"model": "test"})

            assert "server error" in str(exc_info.value).lower()

    async def test_timeout_error_on_read_timeout(self, copilot_client):
        """Test httpx.ReadTimeout raises CopilotTimeoutError."""
        with patch.object(copilot_client, "_client") as mock_client:
            mock_client.post = AsyncMock(side_effect=httpx.ReadTimeout("timeout"))
            copilot_client._client = mock_client

            with pytest.raises(CopilotTimeoutError) as exc_info:
                await copilot_client._make_request({"model": "test"})

            assert "timed out" in str(exc_info.value).lower()

    async def test_connection_error_on_connect_error(self, copilot_client):
        """Test httpx.ConnectError raises CopilotConnectionError."""
        with patch.object(copilot_client, "_client") as mock_client:
            mock_client.post = AsyncMock(side_effect=httpx.ConnectError("connection failed"))
            copilot_client._client = mock_client

            with pytest.raises(CopilotConnectionError) as exc_info:
                await copilot_client._make_request({"model": "test"})

            assert "connect" in str(exc_info.value).lower()


class TestCopilotClientJsonParsing:
    """Test JSON parsing edge cases."""

    @pytest.fixture
    def copilot_client(self):
        return CopilotClient(api_key="test-key")

    def test_parse_json_removes_markdown_wrapper(self, copilot_client):
        """Test _parse_json_response strips markdown code blocks."""
        content = """```json
        {"key": "value"}
        ```"""
        result = copilot_client._parse_json_response(content, "test")
        assert result == {"key": "value"}

    def test_parse_json_handles_bare_json(self, copilot_client):
        """Test _parse_json_response handles bare JSON."""
        content = '{"key": "value"}'
        result = copilot_client._parse_json_response(content, "test")
        assert result == {"key": "value"}

    def test_parse_json_handles_array(self, copilot_client):
        """Test _parse_json_response handles JSON arrays."""
        content = '[{"id": 1}, {"id": 2}]'
        result = copilot_client._parse_json_response(content, "test")
        assert result == [{"id": 1}, {"id": 2}]

    def test_parse_json_raises_on_invalid(self, copilot_client):
        """Test _parse_json_response raises CopilotParsingError on invalid JSON."""
        with pytest.raises(CopilotParsingError) as exc_info:
            copilot_client._parse_json_response("not json", "test context")

        assert "test context" in str(exc_info.value)
        assert exc_info.value.raw_content == "not json"


class TestCopilotClientContextManager:
    """Test async context manager functionality."""

    async def test_context_manager_lifecycle(self):
        """Test client properly initializes and closes in context manager."""
        with patch("app.agents.copilot.httpx.AsyncClient") as mock_async_client:
            mock_client_instance = AsyncMock()
            mock_async_client.return_value = mock_client_instance

            client = CopilotClient(api_key="test-key")

            async with client:
                assert client._client is not None

            mock_client_instance.aclose.assert_called_once()

    async def test_configurable_timeout(self):
        """Test that timeout is configurable."""
        with patch("app.agents.copilot.httpx.AsyncClient") as mock_async_client:
            mock_async_client.return_value = AsyncMock()

            client = CopilotClient(api_key="test-key", timeout=300.0)

            async with client:
                call_kwargs = mock_async_client.call_args[1]
                assert call_kwargs["timeout"].read == 300.0


class TestCopilotMessage:
    """Test CopilotMessage dataclass."""

    def test_message_creation(self):
        """Test message creation."""
        msg = CopilotMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_assistant_message(self):
        """Test assistant message."""
        msg = CopilotMessage(role="assistant", content="Hi there")
        assert msg.role == "assistant"


class TestCopilotResponse:
    """Test CopilotResponse dataclass."""

    def test_response_creation(self):
        """Test response creation."""
        response = CopilotResponse(
            content="Test",
            model="claude-sonnet",
            usage={"prompt_tokens": 10},
            finish_reason="stop",
        )
        assert response.content == "Test"
        assert response.model == "claude-sonnet"
        assert response.finish_reason == "stop"
