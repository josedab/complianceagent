"""Domain-specific exceptions for ComplianceAgent."""

from typing import Any


class ComplianceAgentError(Exception):
    """Base exception for all ComplianceAgent errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


# AI/Copilot Errors
class CopilotError(ComplianceAgentError):
    """Base exception for Copilot SDK errors."""


class CopilotConnectionError(CopilotError):
    """Failed to connect to Copilot API."""


class CopilotRateLimitError(CopilotError):
    """Copilot API rate limit exceeded."""

    def __init__(self, message: str, retry_after: int | None = None):
        super().__init__(message, {"retry_after": retry_after})
        self.retry_after = retry_after


class CopilotTimeoutError(CopilotError):
    """Copilot API request timed out."""


class CopilotParsingError(CopilotError):
    """Failed to parse Copilot response."""

    def __init__(self, message: str, raw_content: str | None = None):
        super().__init__(message, {"raw_content_preview": raw_content[:500] if raw_content else None})
        self.raw_content = raw_content


class CopilotAuthenticationError(CopilotError):
    """Copilot API authentication failed."""


# Compliance Processing Errors
class ComplianceProcessingError(ComplianceAgentError):
    """Base exception for compliance processing errors."""


class RequirementExtractionError(ComplianceProcessingError):
    """Failed to extract requirements from regulatory text."""


class CodeMappingError(ComplianceProcessingError):
    """Failed to map requirements to codebase."""


class CodeGenerationError(ComplianceProcessingError):
    """Failed to generate compliant code."""


# Regulatory Monitoring Errors
class MonitoringError(ComplianceAgentError):
    """Base exception for regulatory monitoring errors."""


class SourceFetchError(MonitoringError):
    """Failed to fetch regulatory source."""


class SourceParseError(MonitoringError):
    """Failed to parse regulatory source content."""


# Repository Errors
class RepositoryError(ComplianceAgentError):
    """Base exception for repository operations."""


class RepositoryNotFoundError(RepositoryError):
    """Repository not found."""


class RepositoryAccessDeniedError(RepositoryError):
    """Access to repository denied."""


# Validation Errors
class ValidationError(ComplianceAgentError):
    """Base exception for validation errors."""


class InvalidRegulationError(ValidationError):
    """Invalid regulation data."""


class InvalidRequirementError(ValidationError):
    """Invalid requirement data."""
