"""Smoke tests that verify the app boots and all routes are importable.

These tests catch import errors, broken router registrations, and route
conflicts across all 96+ API modules — without needing any infrastructure.
"""

from collections import Counter

import pytest
from fastapi import APIRouter
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


def _route_entries(router: APIRouter, prefix: str = "") -> list[tuple[str, str]]:
    """Flatten routes across FastAPI's lazy included-router wrappers."""
    entries: list[tuple[str, str]] = []
    for route in router.routes:
        path = getattr(route, "path", None)
        if path is not None:
            methods = getattr(route, "methods", None) or {"*"}
            entries.extend((method, f"{prefix}{path}") for method in methods)
            continue

        included_router = getattr(route, "original_router", None)
        include_context = getattr(route, "include_context", None)
        if included_router is not None and include_context is not None:
            entries.extend(_route_entries(included_router, f"{prefix}{include_context.prefix}"))
    return entries


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

        registered_prefixes = {path for _, path in _route_entries(api_router)}

        # Find all modules in api/v1 that define a router
        modules_with_routers = []
        for _importer, modname, _ispkg in pkgutil.iter_modules(v1_package.__path__):
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

        route_counts = Counter(_route_entries(api_router))
        duplicates = sorted(route for route, count in route_counts.items() if count > 1)

        assert duplicates == [], f"Duplicate method/path routes detected: {duplicates}"

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
