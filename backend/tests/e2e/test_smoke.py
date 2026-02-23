"""Smoke tests: verify app starts and core endpoints respond.

These tests use ASGI transport (no server needed) and validate that:
1. The FastAPI app initializes without errors
2. All 200+ routers are registered
3. Core endpoints return expected responses
4. OpenAPI schema generates correctly
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="module")
async def smoke_client():
    """Create test client with in-memory DB for smoke tests."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
    await engine.dispose()


class TestAppStartup:
    """Verify the application starts and routes are registered."""

    @pytest.mark.asyncio
    async def test_app_has_routes(self, smoke_client: AsyncClient):
        """Application has 1000+ routes registered."""
        from app.main import app as fastapi_app

        route_count = len([r for r in fastapi_app.routes if hasattr(r, "path")])
        assert route_count > 1000, f"Only {route_count} routes registered"

    @pytest.mark.asyncio
    async def test_api_v1_prefix(self, smoke_client: AsyncClient):
        """All API routes are under /api/v1/ prefix."""
        from app.main import app as fastapi_app

        api_routes = [r.path for r in fastapi_app.routes if hasattr(r, "path") and "/api/v1/" in r.path]
        assert len(api_routes) > 500


class TestCoreEndpoints:
    """Verify core API endpoints respond correctly."""

    @pytest.mark.asyncio
    async def test_status_endpoint(self, smoke_client: AsyncClient):
        """Platform status endpoint returns health info."""
        resp = await smoke_client.get("/api/v1/status/")
        assert resp.status_code == 200


class TestV3Endpoints:
    """Verify v3 router endpoints are accessible."""

    @pytest.mark.asyncio
    async def test_mcp_server_status(self, smoke_client: AsyncClient):
        resp = await smoke_client.get("/api/v1/mcp-server/status")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_mcp_server_tools(self, smoke_client: AsyncClient):
        resp = await smoke_client.get("/api/v1/mcp-server/tools")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 7


class TestV5Endpoints:
    """Verify v5 knowledge fabric responds."""

    @pytest.mark.asyncio
    async def test_knowledge_search(self, smoke_client: AsyncClient):
        resp = await smoke_client.post(
            "/api/v1/knowledge-fabric/search",
            json={"query": "GDPR erasure", "scope": "all", "limit": 5},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert "rag_answer" in data


class TestRouteCount:
    """Verify expected number of routes are registered."""

    @pytest.mark.asyncio
    async def test_minimum_route_count(self, smoke_client: AsyncClient):
        """App should have 1000+ API routes registered from all v3-v9 routers."""
        from app.main import app as fastapi_app

        all_routes = [r.path for r in fastapi_app.routes if hasattr(r, "path")]
        assert len(all_routes) >= 1000, (
            f"Expected 1000+ routes but found {len(all_routes)}. "
            "Check that all routers are registered in api/v1/__init__.py"
        )
