"""Tests for domain exception edge cases."""

import pytest

from app.core.exceptions import (
    ComplianceAgentError,
    CopilotParsingError,
    CopilotRateLimitError,
    RequirementExtractionError,
)


class TestComplianceAgentError:
    def test_message_and_details(self):
        err = ComplianceAgentError("test error", {"key": "value"})
        assert str(err) == "test error"
        assert err.message == "test error"
        assert err.details == {"key": "value"}

    def test_default_empty_details(self):
        err = ComplianceAgentError("error")
        assert err.details == {}

    def test_is_exception(self):
        err = ComplianceAgentError("test")
        assert isinstance(err, Exception)


class TestCopilotParsingError:
    def test_truncates_raw_content_at_500_chars(self):
        long_content = "x" * 1000
        err = CopilotParsingError("parse failed", raw_content=long_content)
        assert err.raw_content == long_content  # raw_content preserved in full
        assert len(err.details["raw_content_preview"]) == 500

    def test_none_raw_content(self):
        err = CopilotParsingError("parse failed", raw_content=None)
        assert err.details["raw_content_preview"] is None

    def test_short_content_not_truncated(self):
        content = "short"
        err = CopilotParsingError("parse failed", raw_content=content)
        assert err.details["raw_content_preview"] == "short"

    def test_inherits_from_copilot_error(self):
        from app.core.exceptions import CopilotError
        err = CopilotParsingError("test")
        assert isinstance(err, CopilotError)


class TestCopilotRateLimitError:
    def test_retry_after_stored(self):
        err = CopilotRateLimitError("rate limited", retry_after=60)
        assert err.retry_after == 60
        assert err.details["retry_after"] == 60

    def test_retry_after_none(self):
        err = CopilotRateLimitError("rate limited")
        assert err.retry_after is None
        assert err.details["retry_after"] is None


class TestExceptionHierarchy:
    def test_requirement_extraction_error_chain(self):
        from app.core.exceptions import ComplianceProcessingError
        err = RequirementExtractionError("extraction failed")
        assert isinstance(err, ComplianceProcessingError)
        assert isinstance(err, ComplianceAgentError)
        assert isinstance(err, Exception)
