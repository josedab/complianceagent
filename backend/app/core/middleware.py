"""Rate limiting and exception handling middleware."""

import asyncio
import hashlib
import time
import traceback
from collections import defaultdict
from collections.abc import Callable
from typing import Any

import structlog
from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.exceptions import (
    ComplianceAgentError,
    CopilotError,
    CopilotRateLimitError,
    CopilotTimeoutError,
    RepositoryAccessDeniedError,
    RepositoryNotFoundError,
    ValidationError,
)


logger = structlog.get_logger()


class GlobalExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Global exception handler that converts domain exceptions to HTTP responses.
    
    This middleware catches all unhandled exceptions and converts them to
    consistent JSON error responses, preventing stack traces from leaking
    to clients in production.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except HTTPException:
            # Let FastAPI handle HTTP exceptions normally
            raise
        except CopilotRateLimitError as e:
            logger.warning(
                "Copilot rate limit exceeded",
                retry_after=e.retry_after,
                path=request.url.path,
            )
            return JSONResponse(
                status_code=429,
                content=self._error_response(
                    "rate_limit_exceeded",
                    "AI service rate limit exceeded. Please try again later.",
                    {"retry_after": e.retry_after},
                ),
                headers={"Retry-After": str(e.retry_after or 60)},
            )
        except CopilotTimeoutError as e:
            logger.warning(
                "Copilot timeout",
                message=e.message,
                path=request.url.path,
            )
            return JSONResponse(
                status_code=504,
                content=self._error_response(
                    "ai_timeout",
                    "AI service request timed out. Please try again.",
                ),
            )
        except CopilotError as e:
            logger.error(
                "Copilot error",
                error_type=type(e).__name__,
                message=e.message,
                path=request.url.path,
            )
            return JSONResponse(
                status_code=503,
                content=self._error_response(
                    "ai_service_error",
                    "AI service temporarily unavailable.",
                    {"error_type": type(e).__name__} if settings.debug else None,
                ),
            )
        except RepositoryNotFoundError as e:
            return JSONResponse(
                status_code=404,
                content=self._error_response(
                    "repository_not_found",
                    e.message,
                ),
            )
        except RepositoryAccessDeniedError as e:
            return JSONResponse(
                status_code=403,
                content=self._error_response(
                    "repository_access_denied",
                    e.message,
                ),
            )
        except ValidationError as e:
            return JSONResponse(
                status_code=422,
                content=self._error_response(
                    "validation_error",
                    e.message,
                    e.details if settings.debug else None,
                ),
            )
        except ComplianceAgentError as e:
            logger.error(
                "Domain error",
                error_type=type(e).__name__,
                message=e.message,
                details=e.details,
                path=request.url.path,
            )
            return JSONResponse(
                status_code=500,
                content=self._error_response(
                    "compliance_error",
                    "A compliance processing error occurred.",
                    {"error_type": type(e).__name__} if settings.debug else None,
                ),
            )
        except Exception as e:
            # Log full traceback for unexpected errors
            logger.exception(
                "Unhandled exception",
                error_type=type(e).__name__,
                error=str(e),
                path=request.url.path,
            )
            # In debug mode, include more details
            details = None
            if settings.debug:
                details = {
                    "error_type": type(e).__name__,
                    "error": str(e),
                    "traceback": traceback.format_exc().split("\n")[-10:],
                }
            return JSONResponse(
                status_code=500,
                content=self._error_response(
                    "internal_server_error",
                    "An unexpected error occurred.",
                    details,
                ),
            )

    def _error_response(
        self,
        error_code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a consistent error response structure."""
        response = {
            "error": {
                "code": error_code,
                "message": message,
            }
        }
        if details:
            response["error"]["details"] = details
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiter with sliding window algorithm.
    Uses in-memory storage by default, Redis in production.
    """

    def __init__(
        self,
        app,
        calls: int = 100,
        period: int = 60,
        redis_client=None,
        key_prefix: str = "ratelimit:",
    ):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.redis = redis_client
        self.key_prefix = key_prefix
        self.requests: dict[str, list[float]] = defaultdict(list)
        self._memory_lock = asyncio.Lock()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting in development if configured
        if settings.debug and not settings.rate_limit_in_debug:
            return await call_next(request)

        # Skip health check endpoints
        if request.url.path in ["/health", "/healthz", "/api/health"]:
            return await call_next(request)

        # Get client identifier
        client_id = self._get_client_id(request)
        key = f"{self.key_prefix}{client_id}"

        try:
            # Check rate limit (Redis or in-memory)
            is_limited, remaining, reset_time = await self._check_rate_limit(key)

            if is_limited:
                logger.warning(
                    "Rate limit exceeded",
                    client_id=client_id,
                    path=request.url.path,
                )
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Please slow down.",
                    headers={
                        "Retry-After": str(self.period),
                        "X-RateLimit-Limit": str(self.calls),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(reset_time),
                    },
                )

            # Process request
            response = await call_next(request)

            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(self.calls)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_time)

            return response

        except HTTPException:
            raise
        except Exception as e:
            # Log error but don't block request
            logger.exception("Rate limiting error", error=str(e))
            return await call_next(request)

    async def _check_rate_limit(self, key: str) -> tuple[bool, int, int]:
        """Check if rate limit is exceeded. Returns (is_limited, remaining, reset_time)."""
        now = time.time()
        window_start = now - self.period
        reset_time = int(now + self.period)

        if self.redis:
            return await self._check_redis_rate_limit(key, now, window_start, reset_time)
        return await self._check_memory_rate_limit(key, now, window_start, reset_time)

    async def _check_redis_rate_limit(
        self, key: str, now: float, window_start: float, reset_time: int
    ) -> tuple[bool, int, int]:
        """Redis-backed rate limiting using sorted sets."""
        try:
            pipe = self.redis.pipeline()
            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)
            # Add current request
            pipe.zadd(key, {str(now): now})
            # Count requests in window
            pipe.zcard(key)
            # Set expiry
            pipe.expire(key, self.period + 1)
            results = await pipe.execute()

            count = results[2]
            remaining = max(0, self.calls - count)
            is_limited = count > self.calls

            return is_limited, remaining, reset_time
        except Exception as e:
            logger.exception("Redis rate limit error", error=str(e))
            # Fall back to memory
            return await self._check_memory_rate_limit(key, now, window_start, reset_time)

    async def _check_memory_rate_limit(
        self, key: str, now: float, window_start: float, reset_time: int
    ) -> tuple[bool, int, int]:
        """In-memory rate limiting using sliding window."""
        async with self._memory_lock:
            # Clean old requests
            self.requests[key] = [t for t in self.requests[key] if t > window_start]

            # Check if over limit
            count = len(self.requests[key])
            is_limited = count >= self.calls

            if not is_limited:
                # Record this request
                self.requests[key].append(now)
                count += 1

            remaining = max(0, self.calls - count)
            return is_limited, remaining, reset_time

    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier."""
        # Try to get authenticated user from token
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token_hash = hashlib.sha256(auth_header.encode()).hexdigest()[:16]
            return f"user:{token_hash}"

        # Try API key
        api_key = request.headers.get("X-API-Key", "")
        if api_key:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
            return f"apikey:{key_hash}"

        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"

        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"


class AuthRateLimitMiddleware(RateLimitMiddleware):
    """Stricter rate limiter for auth endpoints to prevent brute force attacks."""

    def __init__(self, app, redis_client=None):
        super().__init__(
            app,
            calls=5,
            period=60,
            redis_client=redis_client,
            key_prefix="ratelimit:auth:",
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only apply to auth endpoints
        if not request.url.path.startswith("/api/v1/auth"):
            return await call_next(request)

        return await super().dispatch(request, call_next)


class APIRateLimitMiddleware(RateLimitMiddleware):
    """
    Tiered rate limiting based on user plan.
    Free: 100/min, Pro: 1000/min, Enterprise: 10000/min
    """

    TIER_LIMITS = {
        "free": 100,
        "professional": 1000,
        "enterprise": 10000,
    }

    def __init__(self, app, redis_client=None):
        super().__init__(
            app,
            calls=100,  # Default for unauthenticated
            period=60,
            redis_client=redis_client,
            key_prefix="ratelimit:api:",
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip non-API endpoints
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        # Try to get user tier from request state (set by auth middleware)
        tier = getattr(request.state, "user_tier", "free") if hasattr(request, "state") else "free"
        self.calls = self.TIER_LIMITS.get(tier, 100)

        return await super().dispatch(request, call_next)
