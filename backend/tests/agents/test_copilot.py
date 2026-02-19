"""Tests for the Copilot agent: CircuitBreaker and JSON parsing."""

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from app.agents.copilot import CircuitBreaker, CopilotClient
from app.core.exceptions import CopilotParsingError


# ---------------------------------------------------------------------------
# CircuitBreaker
# ---------------------------------------------------------------------------

class TestCircuitBreakerClosedToOpen:
    """Test that the breaker opens after reaching the failure threshold."""

    @pytest.mark.asyncio
    async def test_starts_in_closed_state(self):
        cb = CircuitBreaker(failure_threshold=3)
        state = await cb.get_state()
        assert state["state"] == "closed"

    @pytest.mark.asyncio
    async def test_stays_closed_under_threshold(self):
        cb = CircuitBreaker(failure_threshold=3)
        await cb.record_failure()
        await cb.record_failure()
        state = await cb.get_state()
        assert state["state"] == "closed"
        assert state["failure_count"] == 2

    @pytest.mark.asyncio
    async def test_opens_at_threshold(self):
        cb = CircuitBreaker(failure_threshold=3)
        for _ in range(3):
            await cb.record_failure()

        state = await cb.get_state()
        assert state["state"] == "open"
        assert state["failure_count"] == 3

    @pytest.mark.asyncio
    async def test_is_open_returns_true_when_open(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout_seconds=600)
        await cb.record_failure()
        await cb.record_failure()

        assert await cb.is_open() is True


class TestCircuitBreakerRecovery:
    """Test open → half-open → closed recovery path."""

    @pytest.mark.asyncio
    async def test_transitions_to_half_open_after_timeout(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout_seconds=0)
        await cb.record_failure()
        assert (await cb.get_state())["state"] == "open"

        # With recovery_timeout=0 the next is_open() call should flip to half-open
        is_blocked = await cb.is_open()
        assert is_blocked is False
        state = await cb.get_state()
        assert state["state"] == "half-open"

    @pytest.mark.asyncio
    async def test_closes_after_enough_successes_in_half_open(self):
        cb = CircuitBreaker(
            failure_threshold=1,
            recovery_timeout_seconds=0,
            half_open_max_calls=2,
        )
        await cb.record_failure()  # → open
        await cb.is_open()  # → half-open (timeout=0 elapsed)

        await cb.record_success()
        assert (await cb.get_state())["state"] == "half-open"

        await cb.record_success()
        state = await cb.get_state()
        assert state["state"] == "closed"
        assert state["failure_count"] == 0

    @pytest.mark.asyncio
    async def test_half_open_failure_reopens_circuit(self):
        cb = CircuitBreaker(
            failure_threshold=1,
            recovery_timeout_seconds=0,
            half_open_max_calls=3,
        )
        await cb.record_failure()  # → open
        await cb.is_open()  # → half-open

        await cb.record_failure()  # any failure in half-open → open
        state = await cb.get_state()
        assert state["state"] == "open"


class TestCircuitBreakerSuccessResets:
    """Test that success in closed state resets the failure count."""

    @pytest.mark.asyncio
    async def test_success_resets_failure_count_in_closed(self):
        cb = CircuitBreaker(failure_threshold=5)
        await cb.record_failure()
        await cb.record_failure()
        await cb.record_success()

        state = await cb.get_state()
        assert state["state"] == "closed"
        assert state["failure_count"] == 0


class TestCircuitBreakerBlocksRequests:
    """Test that is_open correctly blocks when the circuit is open."""

    @pytest.mark.asyncio
    async def test_blocks_requests_before_timeout(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout_seconds=9999)
        await cb.record_failure()

        # Should remain blocked
        assert await cb.is_open() is True
        assert await cb.is_open() is True


# ---------------------------------------------------------------------------
# _parse_json_response
# ---------------------------------------------------------------------------

class TestParseJsonResponse:
    """Test the CopilotClient._parse_json_response helper."""

    def _parser(self):
        """Get a CopilotClient instance just for parsing (no network needed)."""
        return CopilotClient.__new__(CopilotClient)

    def test_plain_json_object(self):
        client = self._parser()
        result = client._parse_json_response('{"key": "value"}', "test")
        assert result == {"key": "value"}

    def test_plain_json_array(self):
        client = self._parser()
        result = client._parse_json_response('[{"a": 1}]', "test")
        assert result == [{"a": 1}]

    def test_markdown_code_block_json(self):
        content = '```json\n{"requirements": []}\n```'
        client = self._parser()
        result = client._parse_json_response(content, "test")
        assert result == {"requirements": []}

    def test_markdown_code_block_no_language(self):
        content = '```\n{"foo": "bar"}\n```'
        client = self._parser()
        result = client._parse_json_response(content, "test")
        assert result == {"foo": "bar"}

    def test_whitespace_around_json(self):
        content = '  \n {"x": 1} \n  '
        client = self._parser()
        result = client._parse_json_response(content, "test")
        assert result == {"x": 1}

    def test_invalid_json_raises_copilot_parsing_error(self):
        client = self._parser()
        with pytest.raises(CopilotParsingError) as exc_info:
            client._parse_json_response("not json at all", "analysis")

        assert "analysis" in str(exc_info.value)

    def test_empty_string_raises_copilot_parsing_error(self):
        client = self._parser()
        with pytest.raises(CopilotParsingError):
            client._parse_json_response("", "empty")

    def test_markdown_with_nested_json(self):
        content = '```json\n{"files": [{"path": "a.py", "status": "ok"}]}\n```'
        client = self._parser()
        result = client._parse_json_response(content, "mapping")
        assert result["files"][0]["path"] == "a.py"
