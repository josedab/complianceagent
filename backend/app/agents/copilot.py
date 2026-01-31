"""GitHub Copilot SDK integration for AI-powered compliance analysis."""

import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import Lock
from typing import Any

import httpx
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.core.exceptions import (
    CopilotAuthenticationError,
    CopilotConnectionError,
    CopilotParsingError,
    CopilotRateLimitError,
    CopilotTimeoutError,
)
from app.core.metrics import get_metrics


logger = structlog.get_logger()


@dataclass
class CopilotMessage:
    """A message in a Copilot conversation."""
    role: str  # "user" or "assistant"
    content: str


@dataclass
class CopilotResponse:
    """Response from Copilot API."""
    content: str
    model: str
    usage: dict[str, int]
    finish_reason: str


@dataclass
class CircuitBreakerState:
    """State for circuit breaker pattern."""
    failure_count: int = 0
    last_failure_time: datetime | None = None
    state: str = "closed"  # closed, open, half-open
    success_count_in_half_open: int = 0


class CircuitBreaker:
    """Circuit breaker to prevent cascading failures to external APIs.
    
    States:
    - closed: Normal operation, requests pass through
    - open: Failures exceeded threshold, requests fail fast
    - half-open: Testing if service recovered, limited requests allowed
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout_seconds: int = 60,
        half_open_max_calls: int = 3,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout_seconds
        self.half_open_max_calls = half_open_max_calls
        self._state = CircuitBreakerState()
        self._lock = Lock()

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)."""
        with self._lock:
            if self._state.state == "open":
                # Check if recovery timeout has elapsed
                if self._state.last_failure_time:
                    elapsed = (datetime.now(UTC) - self._state.last_failure_time).total_seconds()
                    if elapsed >= self.recovery_timeout:
                        self._state.state = "half-open"
                        self._state.success_count_in_half_open = 0
                        logger.info("Circuit breaker transitioning to half-open")
                        return False
                return True
            return False

    def record_success(self) -> None:
        """Record a successful call."""
        with self._lock:
            if self._state.state == "half-open":
                self._state.success_count_in_half_open += 1
                if self._state.success_count_in_half_open >= self.half_open_max_calls:
                    self._state.state = "closed"
                    self._state.failure_count = 0
                    logger.info("Circuit breaker closed after successful recovery")
            elif self._state.state == "closed":
                # Reset failure count on success
                self._state.failure_count = 0

    def record_failure(self) -> None:
        """Record a failed call."""
        with self._lock:
            self._state.failure_count += 1
            self._state.last_failure_time = datetime.now(UTC)

            if self._state.state == "half-open":
                # Any failure in half-open immediately opens the circuit
                self._state.state = "open"
                logger.warning("Circuit breaker opened after half-open failure")
            elif self._state.failure_count >= self.failure_threshold:
                self._state.state = "open"
                logger.warning(
                    "Circuit breaker opened",
                    failure_count=self._state.failure_count,
                    threshold=self.failure_threshold,
                )

    def get_state(self) -> dict[str, Any]:
        """Get current circuit breaker state for monitoring."""
        with self._lock:
            return {
                "state": self._state.state,
                "failure_count": self._state.failure_count,
                "last_failure_time": self._state.last_failure_time.isoformat() if self._state.last_failure_time else None,
            }


class CircuitBreakerOpenError(CopilotConnectionError):
    """Raised when circuit breaker is open."""

    def __init__(self, recovery_seconds: int):
        super().__init__(
            f"Circuit breaker is open. Service unavailable. Retry after {recovery_seconds}s",
            details={"retry_after": recovery_seconds},
        )
        self.retry_after = recovery_seconds


def _is_retryable_error(exception: BaseException) -> bool:
    """Determine if an exception should trigger a retry."""
    if isinstance(exception, (CopilotConnectionError, CopilotTimeoutError)):
        return True
    if isinstance(exception, CopilotRateLimitError):
        return True
    if isinstance(exception, httpx.HTTPStatusError):
        return exception.response.status_code in (429, 500, 502, 503, 504)
    return False


# Global circuit breaker instance shared across CopilotClient instances
_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout_seconds=60,
    half_open_max_calls=3,
)


class CopilotClient:
    """Client for GitHub Copilot SDK with retry logic, error handling, and circuit breaker."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.githubcopilot.com",
        default_model: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
    ):
        self.api_key = api_key or settings.copilot_api_key
        self.base_url = base_url
        self.default_model = default_model or settings.copilot_default_model
        self.timeout = timeout or settings.copilot_timeout_seconds
        self.max_retries = max_retries or settings.copilot_max_retries
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(self.timeout, connect=30.0),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    def _create_retry_decorator(self):
        """Create a retry decorator with current settings."""
        return retry(
            retry=retry_if_exception_type((
                CopilotConnectionError,
                CopilotTimeoutError,
                CopilotRateLimitError,
                httpx.ConnectError,
                httpx.ReadTimeout,
            )),
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(
                multiplier=1,
                min=settings.copilot_retry_min_wait,
                max=settings.copilot_retry_max_wait,
            ),
            before_sleep=lambda retry_state: logger.warning(
                "Retrying Copilot request",
                attempt=retry_state.attempt_number,
                wait=retry_state.next_action.sleep if retry_state.next_action else 0,
            ),
        )

    async def _make_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Make HTTP request to Copilot API with error handling and circuit breaker."""
        if not self._client:
            msg = "Client not initialized. Use async with."
            raise RuntimeError(msg)

        # Check circuit breaker before making request
        if _circuit_breaker.is_open:
            raise CircuitBreakerOpenError(recovery_seconds=60)

        metrics = get_metrics()
        metrics.inc_copilot_request()
        start_time = time.perf_counter()

        try:
            response = await self._client.post("/v1/chat/completions", json=payload)
        except httpx.ConnectError as e:
            metrics.inc_copilot_error()
            _circuit_breaker.record_failure()
            raise CopilotConnectionError(f"Failed to connect to Copilot API: {e}") from e
        except httpx.ReadTimeout as e:
            metrics.inc_copilot_error()
            _circuit_breaker.record_failure()
            raise CopilotTimeoutError(
                f"Copilot API request timed out after {self.timeout}s"
            ) from e
        except httpx.TimeoutException as e:
            metrics.inc_copilot_error()
            _circuit_breaker.record_failure()
            raise CopilotTimeoutError(f"Copilot API timeout: {e}") from e

        # Handle HTTP errors
        if response.status_code == 401:
            metrics.inc_copilot_error()
            # Auth errors don't trip circuit breaker (not a service issue)
            raise CopilotAuthenticationError("Invalid or expired Copilot API key")
        if response.status_code == 429:
            metrics.inc_copilot_error()
            _circuit_breaker.record_failure()
            retry_after = response.headers.get("Retry-After")
            raise CopilotRateLimitError(
                "Copilot API rate limit exceeded",
                retry_after=int(retry_after) if retry_after else None,
            )
        if response.status_code >= 500:
            metrics.inc_copilot_error()
            _circuit_breaker.record_failure()
            raise CopilotConnectionError(
                f"Copilot API server error: {response.status_code}",
                details={"status_code": response.status_code, "body": response.text[:500]},
            )

        response.raise_for_status()

        # Record success for circuit breaker
        _circuit_breaker.record_success()

        # Record successful request latency
        latency = time.perf_counter() - start_time
        metrics.observe_copilot_latency(latency)

        return response.json()

    async def chat(
        self,
        messages: list[CopilotMessage],
        model: str | None = None,
        system_message: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
    ) -> CopilotResponse:
        """Send a chat completion request with automatic retries."""
        formatted_messages = []
        if system_message:
            formatted_messages.append({"role": "system", "content": system_message})

        for msg in messages:
            formatted_messages.append({"role": msg.role, "content": msg.content})

        payload = {
            "model": model or self.default_model,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if tools:
            payload["tools"] = tools

        logger.debug("Sending Copilot request", model=payload["model"])

        # Apply retry decorator
        retry_decorator = self._create_retry_decorator()
        make_request_with_retry = retry_decorator(self._make_request)

        data = await make_request_with_retry(payload)

        return CopilotResponse(
            content=data["choices"][0]["message"]["content"],
            model=data["model"],
            usage=data.get("usage", {}),
            finish_reason=data["choices"][0]["finish_reason"],
        )

    def _parse_json_response(
        self,
        content: str,
        context: str,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Parse JSON from AI response with improved error handling."""
        original_content = content
        content = content.strip()

        # Remove markdown code blocks
        if content.startswith("```"):
            lines = content.split("\n")
            # Remove first line (```json or ```)
            if lines:
                lines = lines[1:]
            # Remove last line if it's just ``
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines)

        content = content.strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse JSON response",
                context=context,
                error=str(e),
                content_preview=original_content[:200],
            )
            raise CopilotParsingError(
                f"Failed to parse {context} response: {e}",
                raw_content=original_content,
            ) from e

    async def analyze_legal_text(
        self,
        text: str,
        regulation_name: str,
        jurisdiction: str,
        framework: str,
    ) -> list[dict[str, Any]]:
        """Extract requirements from legal text."""
        system_prompt = """You are an expert regulatory compliance analyst.
Extract specific, actionable requirements from legal text.

For each requirement, provide a JSON object with:
- reference_id: Unique ID like "REQ-{framework}-001"
- title: Brief title
- description: Clear description of what must be done
- obligation_type: MUST, MUST_NOT, SHOULD, SHOULD_NOT, or MAY
- category: data_collection, data_storage, data_processing, data_transfer, data_deletion, data_access, consent, notification, documentation, security, audit, breach_response, risk_assessment, vendor_management, ai_transparency, ai_testing, ai_documentation, human_oversight, other
- subject: Who must comply
- action: What action is required
- object: What it applies to (optional)
- data_types: Array of affected data types
- processes: Array of affected processes
- timeframe: Deadline/timeframe mentioned
- source_text: Exact source text
- citations: Array of {article, section, paragraph}
- confidence: 0.0 to 1.0

Return a JSON array of requirements. If none found, return []."""

        user_prompt = f"""Extract compliance requirements from:

**Regulation**: {regulation_name}
**Jurisdiction**: {jurisdiction}
**Framework**: {framework}

**Text**:
{text[:30000]}

Return JSON array only, no explanation."""

        response = await self.chat(
            messages=[CopilotMessage(role="user", content=user_prompt)],
            system_message=system_prompt,
            temperature=0.3,
            max_tokens=8192,
        )

        try:
            result = self._parse_json_response(response.content, "legal analysis")
            if isinstance(result, list):
                return result
            logger.warning("Legal analysis returned non-array, wrapping in array")
            return [result] if result else []
        except CopilotParsingError:
            # Return empty list but log the error (already logged in _parse_json_response)
            return []

    async def map_requirement_to_code(
        self,
        requirement: dict[str, Any],
        codebase_structure: str,
        sample_files: dict[str, str],
        languages: list[str],
    ) -> dict[str, Any]:
        """Map a requirement to code locations."""
        system_prompt = """You are an expert compliance engineer mapping regulatory requirements to code.

Analyze the codebase and identify:
1. Files handling regulated data/processes
2. Existing compliance implementations
3. Gaps where requirements are not met

Return JSON with:
- affected_files: [{path, relevance (0-1), functions, classes, status}]
- existing_implementations: [{path, description, coverage}]
- gaps: [{severity (critical/major/minor), description, file_path, suggestion}]
- data_flows: [{name, entry_point, data_touched, compliance_status}]
- estimated_effort_hours: number
- estimated_effort_description: string
- risk_level: high/medium/low
- confidence: 0.0 to 1.0"""

        sample_content = "\n\n".join(
            f"### {path}\n```\n{content[:2000]}\n```"
            for path, content in list(sample_files.items())[:10]
        )

        user_prompt = f"""Map this requirement to the codebase:

**Requirement**:
- ID: {requirement.get('reference_id')}
- Title: {requirement.get('title')}
- Description: {requirement.get('description')}
- Category: {requirement.get('category')}
- Data Types: {requirement.get('data_types', [])}
- Processes: {requirement.get('processes', [])}

**Languages**: {', '.join(languages)}

**Codebase Structure**:
{codebase_structure[:5000]}

**Sample Files**:
{sample_content}

Return JSON only."""

        response = await self.chat(
            messages=[CopilotMessage(role="user", content=user_prompt)],
            system_message=system_prompt,
            temperature=0.3,
            max_tokens=4096,
        )

        default_response = {
            "affected_files": [],
            "existing_implementations": [],
            "gaps": [],
            "data_flows": [],
            "estimated_effort_hours": 8.0,
            "estimated_effort_description": "Manual analysis required",
            "risk_level": "medium",
            "confidence": 0.0,
        }

        try:
            result = self._parse_json_response(response.content, "code mapping")
            if isinstance(result, dict):
                return result
            logger.warning("Code mapping returned non-dict, using default response")
            return default_response
        except CopilotParsingError:
            return default_response

    async def generate_compliant_code(
        self,
        requirement: dict[str, Any],
        gaps: list[dict[str, Any]],
        existing_code: dict[str, str],
        language: str,
        style_guide: str | None = None,
    ) -> dict[str, Any]:
        """Generate compliant code to address gaps."""
        system_prompt = f"""You are an expert {language} developer generating compliance code.

Generate production-quality code that:
1. Follows existing codebase patterns
2. Includes compliance comments with regulation citations
3. Includes comprehensive tests
4. Is minimally invasive
5. Documents all changes

Return JSON with:
- files: [{{path, operation (create/modify), content, diff, language}}]
- tests: [{{path, test_type (unit/integration/compliance), content, description}}]
- documentation: markdown string
- compliance_comments: [{{file, line, comment}}]
- pr_title: string
- pr_body: markdown string
- confidence: 0.0 to 1.0
- warnings: [string]"""

        gaps_text = "\n".join(
            f"- [{g.get('severity', 'unknown').upper()}] {g.get('description')}"
            for g in gaps
        )

        existing_text = "\n\n".join(
            f"### {path}\n```{language}\n{content[:3000]}\n```"
            for path, content in list(existing_code.items())[:5]
        )

        user_prompt = f"""Generate compliant code for:

**Requirement**: {requirement.get('title')}
**Description**: {requirement.get('description')}
**Regulation**: {requirement.get('regulation_name', 'Unknown')}

**Gaps to Address**:
{gaps_text}

**Existing Code**:
{existing_text}

**Style Guide**: {style_guide or 'Follow existing patterns'}

Return JSON only."""

        response = await self.chat(
            messages=[CopilotMessage(role="user", content=user_prompt)],
            system_message=system_prompt,
            temperature=0.4,
            max_tokens=8192,
        )

        default_response = {
            "files": [],
            "tests": [],
            "documentation": None,
            "compliance_comments": [],
            "pr_title": f"Compliance: {requirement.get('title', 'Unknown')}",
            "pr_body": "Code generation failed - manual implementation required.",
            "confidence": 0.0,
            "warnings": ["Code generation failed - manual implementation required"],
        }

        try:
            result = self._parse_json_response(response.content, "code generation")
            if isinstance(result, dict):
                return result
            logger.warning("Code generation returned non-dict, using default response")
            return default_response
        except CopilotParsingError:
            return default_response


def create_copilot_client() -> CopilotClient:
    """Factory function to create a new CopilotClient instance.
    
    Prefer using this factory over direct instantiation to allow
    for configuration changes and testing.
    """
    return CopilotClient()


async def get_copilot_client() -> CopilotClient:
    """Get a Copilot client instance for dependency injection.
    
    Creates a new instance per request to avoid global mutable state.
    The CopilotClient is lightweight and safe to create per-request.
    """
    return create_copilot_client()


def get_circuit_breaker_state() -> dict[str, Any]:
    """Get circuit breaker state for monitoring and health checks."""
    return _circuit_breaker.get_state()


def reset_circuit_breaker() -> None:
    """Reset circuit breaker to closed state. For testing and recovery."""
    global _circuit_breaker
    _circuit_breaker = CircuitBreaker(
        failure_threshold=5,
        recovery_timeout_seconds=60,
        half_open_max_calls=3,
    )
