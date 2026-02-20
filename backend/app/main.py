"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

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
    except Exception as exc:
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

    # Include API router
    app.include_router(api_v1_router, prefix=settings.api_prefix)

    # OpenTelemetry distributed tracing
    _setup_opentelemetry(app)

    # Health check endpoint
    @app.get("/health")
    async def health_check() -> dict:
        return {
            "status": "healthy",
            "version": settings.app_version,
            "environment": settings.environment,
        }

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

    return app


app = create_app()
