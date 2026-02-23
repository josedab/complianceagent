"""API endpoints for Client SDK management."""

import structlog
from fastapi import APIRouter, Query

from app.api.v1.deps import DB
from app.services.client_sdk import ClientSDKService


logger = structlog.get_logger()
router = APIRouter()


# --- Endpoints ---


@router.get("/endpoints")
async def list_endpoints(
    db: DB,
    method: str | None = Query(None, description="Filter by HTTP method"),
) -> list[dict]:
    """List available API endpoints."""
    svc = ClientSDKService()
    return await svc.list_endpoints(db, method=method)


@router.get("/packages")
async def list_packages(
    db: DB,
    runtime: str | None = Query(None, description="Filter by runtime"),
) -> list[dict]:
    """List available SDK packages."""
    svc = ClientSDKService()
    return await svc.list_packages(db, runtime=runtime)


@router.get("/packages/{runtime}")
async def get_package(runtime: str, db: DB) -> dict:
    """Get SDK package details for a specific runtime."""
    svc = ClientSDKService()
    return await svc.get_package(db, runtime=runtime)


@router.post("/generate/{runtime}")
async def generate_client(runtime: str, db: DB) -> dict:
    """Generate a client SDK for the given runtime."""
    svc = ClientSDKService()
    return await svc.generate_client(db, runtime=runtime)


@router.get("/config")
async def get_default_config(db: DB) -> dict:
    """Get default SDK configuration."""
    svc = ClientSDKService()
    return await svc.get_default_config(db)


@router.get("/stats")
async def get_stats(db: DB) -> dict:
    """Get client SDK statistics."""
    svc = ClientSDKService()
    return await svc.get_stats(db)
