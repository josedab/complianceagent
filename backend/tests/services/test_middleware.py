"""Tests for rate limiting and exception handling middleware."""

import hashlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.core.exceptions import (
    ComplianceAgentError,
    CopilotRateLimitError,
)
from app.core.middleware import (
    GlobalExceptionHandlerMiddleware,
    RateLimitMiddleware,
)


# ---------------------------------------------------------------------------
# Helper: build a minimal FastAPI app with chosen middleware
# ---------------------------------------------------------------------------

def _build_app_with_rate_limit(calls: int = 3, period: int = 60) -> FastAPI:
    """Create a test FastAPI app with RateLimitMiddleware."""
    test_app = FastAPI()

    @test_app.get("/test")
    async def test_endpoint():
        return {"ok": True}

    @test_app.get("/health")
    async def health_endpoint():
        return {"status": "healthy"}

    # Add exception handler so HTTPException raised in middleware becomes a response
    from fastapi.exceptions import HTTPException as FastAPIHTTPException
    from starlette.exceptions import HTTPException as StarletteHTTPException

    @test_app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request, exc):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=getattr(exc, "headers", None),
        )

    # Patch settings so rate limiting runs even in debug mode
    with patch("app.core.middleware.settings") as mock_settings:
        mock_settings.debug = False
        mock_settings.rate_limit_in_debug = False
        test_app.add_middleware(RateLimitMiddleware, calls=calls, period=period)

    return test_app


def _build_app_with_exception_handler(raise_exc: Exception) -> FastAPI:
    """Create a test FastAPI app whose endpoint always raises *raise_exc*."""
    test_app = FastAPI()

    @test_app.get("/blow-up")
    async def blow_up():
        raise raise_exc

    with patch("app.core.middleware.settings") as mock_settings:
        mock_settings.debug = True
        test_app.add_middleware(GlobalExceptionHandlerMiddleware)

    return test_app


# ---------------------------------------------------------------------------
# RateLimitMiddleware
# ---------------------------------------------------------------------------

class TestRateLimitMiddleware:
    """In-memory sliding-window rate limiting."""

    @pytest.mark.asyncio
    async def test_requests_within_limit_succeed(self):
        """Requests under the limit should receive 200."""
        app = _build_app_with_rate_limit(calls=5, period=60)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for _ in range(5):
                resp = await client.get("/test")
                assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_request_blocked_after_limit(self):
        """The (calls+1)-th request within the window should be rejected."""
        middleware = RateLimitMiddleware(app=MagicMock(), calls=2, period=60)
        key = "ratelimit:test-client"

        # First two within limit
        is_limited, remaining, _ = await middleware._check_memory_rate_limit(
            key, __import__("time").time(), __import__("time").time() - 60, 0
        )
        assert is_limited is False
        assert remaining == 1

        is_limited, remaining, _ = await middleware._check_memory_rate_limit(
            key, __import__("time").time(), __import__("time").time() - 60, 0
        )
        assert is_limited is False
        assert remaining == 0

        # Third should be rate-limited
        is_limited, remaining, _ = await middleware._check_memory_rate_limit(
            key, __import__("time").time(), __import__("time").time() - 60, 0
        )
        assert is_limited is True
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_health_endpoint_bypasses_rate_limit(self):
        """Health check paths should never be rate-limited."""
        app = _build_app_with_rate_limit(calls=1, period=60)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Exhaust the limit on /test
            assert (await client.get("/test")).status_code == 200
            # /health should still work even though limit is exhausted
            resp = await client.get("/health")
            assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_rate_limit_headers_present(self):
        """Successful responses should include X-RateLimit-* headers."""
        app = _build_app_with_rate_limit(calls=10, period=60)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/test")
            assert resp.status_code == 200
            assert "x-ratelimit-limit" in resp.headers
            assert "x-ratelimit-remaining" in resp.headers
            assert "x-ratelimit-reset" in resp.headers

    @pytest.mark.asyncio
    async def test_sliding_window_cleans_old_requests(self):
        """Requests outside the window should be cleaned up."""
        import time as time_module

        middleware = RateLimitMiddleware(app=MagicMock(), calls=2, period=10)
        key = "ratelimit:sliding-test"

        now = time_module.time()
        # Simulate old requests outside the window
        middleware.requests[key] = [now - 20, now - 15]

        is_limited, remaining, _ = await middleware._check_memory_rate_limit(
            key, now, now - 10, 0
        )
        assert is_limited is False
        assert remaining == 1  # old ones cleaned, new one added


class TestClientIdExtraction:
    """Test _get_client_id extracts identifiers from Bearer token, API key, or IP."""

    def _make_request(self, headers: dict | None = None, client_host: str = "127.0.0.1") -> MagicMock:
        """Build a mock Request with given headers and client IP."""
        request = MagicMock(spec=Request)
        request.headers = headers or {}
        mock_client = MagicMock()
        mock_client.host = client_host
        request.client = mock_client
        return request

    def test_bearer_token_produces_user_prefix(self):
        middleware = RateLimitMiddleware(app=MagicMock())
        token = "Bearer eyJhbGciOiJIUzI1NiJ9.test.sig"
        request = self._make_request(headers={"Authorization": token})

        client_id = middleware._get_client_id(request)

        expected_hash = hashlib.sha256(token.encode()).hexdigest()[:16]
        assert client_id == f"user:{expected_hash}"

    def test_api_key_produces_apikey_prefix(self):
        middleware = RateLimitMiddleware(app=MagicMock())
        request = self._make_request(headers={"X-API-Key": "my-secret-key"})

        client_id = middleware._get_client_id(request)

        expected_hash = hashlib.sha256("my-secret-key".encode()).hexdigest()[:16]
        assert client_id == f"apikey:{expected_hash}"

    def test_ip_fallback(self):
        middleware = RateLimitMiddleware(app=MagicMock())
        request = self._make_request(client_host="192.168.1.42")

        client_id = middleware._get_client_id(request)

        assert client_id == "ip:192.168.1.42"

    def test_x_forwarded_for_used_when_present(self):
        middleware = RateLimitMiddleware(app=MagicMock())
        request = self._make_request(
            headers={"X-Forwarded-For": "10.0.0.5, 172.16.0.1"},
            client_host="127.0.0.1",
        )

        client_id = middleware._get_client_id(request)

        assert client_id == "ip:10.0.0.5"


# ---------------------------------------------------------------------------
# GlobalExceptionHandlerMiddleware
# ---------------------------------------------------------------------------

class TestGlobalExceptionHandlerMiddleware:
    """Test that domain exceptions are mapped to correct HTTP status codes and JSON."""

    @pytest.mark.asyncio
    async def test_copilot_rate_limit_returns_429(self):
        exc = CopilotRateLimitError("rate limited", retry_after=30)
        app = _build_app_with_exception_handler(exc)
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/blow-up")

        assert resp.status_code == 429
        body = resp.json()
        assert body["error"]["code"] == "rate_limit_exceeded"
        assert "retry_after" in (body["error"].get("details") or {})

    @pytest.mark.asyncio
    async def test_compliance_agent_error_returns_500(self):
        exc = ComplianceAgentError("something broke", details={"ctx": "test"})
        app = _build_app_with_exception_handler(exc)
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/blow-up")

        assert resp.status_code == 500
        body = resp.json()
        assert body["error"]["code"] == "compliance_error"
        assert "message" in body["error"]

    @pytest.mark.asyncio
    async def test_generic_exception_returns_500_with_internal_code(self):
        exc = RuntimeError("unexpected")
        app = _build_app_with_exception_handler(exc)
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/blow-up")

        assert resp.status_code == 500
        body = resp.json()
        assert body["error"]["code"] == "internal_server_error"
