"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1 import router as api_v1_router
from app.core.config import settings
from app.core.metrics import MetricsMiddleware, get_metrics
from app.core.middleware import GlobalExceptionHandlerMiddleware, RateLimitMiddleware


logger = structlog.get_logger()


def _setup_opentelemetry(app: FastAPI) -> None:
    """Instrument the FastAPI app with OpenTelemetry if SDK is available."""
    try:
        from opentelemetry import trace
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider

        resource = Resource.create(
            {
                "service.name": settings.app_name,
                "service.version": settings.app_version,
                "deployment.environment": settings.environment,
            }
        )
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)

        FastAPIInstrumentor.instrument_app(
            app,
            excluded_urls="health,healthz,metrics",
        )
        logger.info("OpenTelemetry tracing enabled")
    except (ImportError, RuntimeError, ValueError) as exc:
        logger.debug("OpenTelemetry instrumentation skipped", reason=str(exc))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    yield
    # Shutdown


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Autonomous Regulatory Monitoring and Adaptation Platform",
        docs_url="/api/docs" if settings.debug else None,
        redoc_url="/api/redoc" if settings.debug else None,
        openapi_url="/api/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )

    # Global exception handler (must be first - innermost middleware)
    app.add_middleware(GlobalExceptionHandlerMiddleware)

    # Rate limiting middleware
    app.add_middleware(RateLimitMiddleware, calls=100, period=60)

    # Metrics middleware
    app.add_middleware(MetricsMiddleware)

    # CORS middleware — restrict methods/headers in non-development environments
    _cors_methods = (
        ["*"]
        if settings.environment == "development"
        else ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    )
    _cors_headers = (
        ["*"]
        if settings.environment == "development"
        else [
            "Authorization",
            "Content-Type",
            "Accept",
            "X-API-Key",
            "X-Request-ID",
        ]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=_cors_methods,
        allow_headers=_cors_headers,
    )

    # Request body size limit middleware (10 MB default)
    max_body_size = 10 * 1024 * 1024  # 10 MB

    class RequestBodySizeLimitMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > max_body_size:
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": {"code": "payload_too_large", "message": "Request body too large"}
                    },
                )
            return await call_next(request)

    app.add_middleware(RequestBodySizeLimitMiddleware)

    # Security headers middleware
    class SecurityHeadersMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; font-src 'self'; frame-ancestors 'none'"
            )
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Permissions-Policy"] = (
                "camera=(), microphone=(), geolocation=(), payment=()"
            )
            return response

    app.add_middleware(SecurityHeadersMiddleware)

    # Include API router
    app.include_router(api_v1_router, prefix=settings.api_prefix)

    # OpenTelemetry distributed tracing
    _setup_opentelemetry(app)

    # Liveness probe — always 200 if the process is running
    @app.get("/health")
    async def health_check() -> dict:
        return {
            "status": "healthy",
            "version": settings.app_version,
            "environment": settings.environment,
        }

    # Readiness probe — checks DB and Redis availability
    @app.get("/health/ready")
    async def readiness_check() -> JSONResponse:
        checks: dict[str, dict] = {}
        overall = "ready"

        # Database probe
        try:
            from app.core.database import engine

            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            checks["database"] = {"status": "up"}
        except Exception as exc:
            checks["database"] = {"status": "down", "error": str(exc)[:120]}
            overall = "degraded"

        # Redis probe
        try:
            import redis as redis_lib

            r = redis_lib.Redis.from_url(
                settings.redis_url, decode_responses=True, socket_connect_timeout=2
            )
            r.ping()
            r.close()
            checks["redis"] = {"status": "up"}
        except Exception as exc:
            checks["redis"] = {"status": "down", "error": str(exc)[:120]}
            overall = "degraded"

        status_code = 200 if overall == "ready" else 503
        return JSONResponse(
            status_code=status_code,
            content={
                "status": overall,
                "version": settings.app_version,
                "environment": settings.environment,
                "checks": checks,
            },
        )

    # Prometheus metrics endpoint
    @app.get("/metrics", response_class=PlainTextResponse)
    async def prometheus_metrics() -> str:
        """Expose Prometheus metrics."""
        return get_metrics().export_prometheus()

    # Root endpoint
    @app.get("/")
    async def root() -> dict:
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": f"{settings.api_prefix}/docs" if settings.debug else None,
        }

    # WebSocket endpoint for real-time notifications
    from fastapi import WebSocket, WebSocketDisconnect

    _ws_clients: set[WebSocket] = set()

    @app.websocket("/ws/notifications")
    async def ws_notifications(websocket: WebSocket) -> None:
        """WebSocket endpoint for pushing real-time compliance events."""
        await websocket.accept()
        _ws_clients.add(websocket)
        logger.info("ws.client_connected", total=len(_ws_clients))
        try:
            while True:
                # Keep connection alive; client can send pings
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
        except WebSocketDisconnect:
            pass
        finally:
            _ws_clients.discard(websocket)
            logger.info("ws.client_disconnected", total=len(_ws_clients))

    async def broadcast_event(event: dict) -> None:
        """Broadcast a compliance event to all connected WebSocket clients."""
        dead: list[WebSocket] = []
        for ws in _ws_clients:
            try:
                await ws.send_json(event)
            except Exception:
                dead.append(ws)
        for ws in dead:
            _ws_clients.discard(ws)

    # Attach broadcast to app state so services can access it
    app.state.broadcast_event = broadcast_event

    return app


app = create_app()
