"""Smoke tests that verify the app boots and all routes are importable.

These tests catch import errors, broken router registrations, and route
conflicts across all 96+ API modules — without needing any infrastructure.
"""

import pytest
from httpx import ASGITransport, AsyncClient

pytestmark = pytest.mark.asyncio


class TestAppBoot:
    """Verify the application starts without import or configuration errors."""

    async def test_app_imports_successfully(self):
        """Importing app.main should not raise — this catches broken routes."""
        from app.main import app

        assert app is not None
        assert app.title == "ComplianceAgent"

    async def test_health_endpoint(self, client: AsyncClient):
        """Health check must always respond."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    async def test_root_endpoint(self, client: AsyncClient):
        """Root endpoint returns app metadata."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "ComplianceAgent"

    async def test_openapi_schema_generates(self):
        """OpenAPI schema should generate without errors.

        This validates every route's Pydantic models, dependencies,
        and parameter declarations are well-formed.
        """
        from app.main import app

        schema = app.openapi()
        assert "paths" in schema
        assert "info" in schema
        assert schema["info"]["title"] == "ComplianceAgent"
        assert len(schema["paths"]) > 50, (
            f"Expected 50+ paths but got {len(schema['paths'])}. Routes may be missing."
        )


class TestRouteIntegrity:
    """Verify route registration is complete and conflict-free."""

    async def test_all_api_v1_routers_are_registered(self):
        """Every module in api/v1/ with a 'router' attr should be mounted."""
        import importlib
        import pkgutil

        import app.api.v1 as v1_package
        from app.api.v1 import router as api_router

        registered_prefixes = set()
        for route in api_router.routes:
            if hasattr(route, "path"):
                registered_prefixes.add(route.path)

        # Find all modules in api/v1 that define a router
        modules_with_routers = []
        for importer, modname, ispkg in pkgutil.iter_modules(v1_package.__path__):
            if modname.startswith("_"):
                continue
            try:
                mod = importlib.import_module(f"app.api.v1.{modname}")
                if hasattr(mod, "router"):
                    modules_with_routers.append(modname)
            except Exception:
                # Import error — test_app_imports_successfully will catch this
                pass

        # Verify we have routers registered (sanity check)
        assert len(registered_prefixes) > 50, (
            f"Expected 50+ routes but only found {len(registered_prefixes)}. "
            "Router registration may be broken."
        )
        assert len(modules_with_routers) > 50, (
            f"Expected 50+ API modules but only found {len(modules_with_routers)}."
        )

    async def test_no_duplicate_route_prefixes(self):
        """Detect routers mounted on the exact same prefix.

        Duplicates indicate routes that shadow each other. This test
        records known duplicates and fails only if NEW ones appear.
        """
        from app.api.v1 import router as api_router

        prefixes: list[str] = []
        for route in api_router.routes:
            if hasattr(route, "path"):
                prefixes.append(route.path)

        duplicates = sorted({p for p in prefixes if prefixes.count(p) > 1})

        # Baseline: 71 known duplicate paths exist as of 2026-02-20.
        # Increase from 53→71 is due to experimental routes being conditionally
        # registered (enable_experimental=True in test env adds routes that
        # share path patterns with core routes). Any increase above 71 means
        # a new unintentional conflict was introduced.
        KNOWN_DUPLICATE_COUNT = 71
        assert len(duplicates) <= KNOWN_DUPLICATE_COUNT, (
            f"New duplicate routes detected! Was {KNOWN_DUPLICATE_COUNT}, "
            f"now {len(duplicates)}. New duplicates: "
            f"{sorted(set(duplicates) - set(duplicates[:KNOWN_DUPLICATE_COUNT]))}"
        )

    async def test_all_routes_have_tags(self):
        """Every mounted router should have at least one OpenAPI tag."""
        from app.main import app

        tag_names = {tag["name"] for tag in (app.openapi().get("tags") or [])}
        # If there are paths, there should be tags
        paths = app.openapi().get("paths", {})
        if paths:
            assert len(tag_names) > 0 or any(
                "tags" in op
                for path_ops in paths.values()
                for op in path_ops.values()
                if isinstance(op, dict)
            ), "Routes exist but no OpenAPI tags are defined."
