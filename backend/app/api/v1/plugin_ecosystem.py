"""API endpoints for Plugin Ecosystem."""

from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.plugin_ecosystem import PluginEcosystemService


logger = structlog.get_logger()
router = APIRouter()


class PluginRegisterRequest(BaseModel):
    manifest: dict = Field(...)


class PluginInstallRequest(BaseModel):
    config: dict | None = Field(default=None)


class HookExecuteRequest(BaseModel):
    input_data: dict = Field(...)


@router.post("/plugins", status_code=status.HTTP_201_CREATED, summary="Register plugin")
async def register_plugin(request: PluginRegisterRequest, db: DB) -> dict:
    """Register a new plugin from a manifest."""
    service = PluginEcosystemService(db=db)
    result = await service.register_plugin(manifest=request.manifest)
    return {
        "id": result.id,
        "name": result.name,
        "plugin_type": result.plugin_type.value,
        "version": result.version,
        "author": result.author,
        "description": result.description,
        "hook_points": [hp.value for hp in result.hook_points],
    }


@router.post("/plugins/{plugin_id}/install", status_code=status.HTTP_201_CREATED, summary="Install plugin")
async def install_plugin(plugin_id: str, request: PluginInstallRequest, db: DB) -> dict:
    """Install a plugin by its manifest ID."""
    service = PluginEcosystemService(db=db)
    try:
        result = await service.install_plugin(
            plugin_id=plugin_id,
            config=request.config,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    return {
        "id": str(result.id),
        "manifest_id": result.manifest_id,
        "status": result.status.value,
        "config": result.config,
        "installed_at": result.installed_at.isoformat() if result.installed_at else None,
    }


@router.post("/hooks/{hook_point}/execute", summary="Execute hook")
async def execute_hook(hook_point: str, request: HookExecuteRequest, db: DB) -> list[dict]:
    """Execute all plugins registered for a given hook point."""
    service = PluginEcosystemService(db=db)
    executions = await service.execute_hook(
        hook_point=hook_point,
        input_data=request.input_data,
    )
    return [
        {
            "id": str(e.id),
            "plugin_id": e.plugin_id,
            "hook_point": e.hook_point.value,
            "output_data": e.output_data,
            "duration_ms": e.duration_ms,
            "success": e.success,
            "executed_at": e.executed_at.isoformat() if e.executed_at else None,
        }
        for e in executions
    ]


@router.delete("/plugins/{instance_id}", summary="Uninstall plugin")
async def uninstall_plugin(instance_id: UUID, db: DB) -> dict:
    """Uninstall a plugin instance."""
    service = PluginEcosystemService(db=db)
    removed = await service.uninstall_plugin(instance_id=instance_id)
    return {"instance_id": str(instance_id), "uninstalled": removed}


@router.get("/plugins", summary="List plugins")
async def list_plugins(db: DB) -> list[dict]:
    """List all registered plugin manifests."""
    service = PluginEcosystemService(db=db)
    plugins = await service.list_plugins()
    return [
        {
            "id": p.id,
            "name": p.name,
            "plugin_type": p.plugin_type.value,
            "version": p.version,
            "author": p.author,
            "description": p.description,
            "hook_points": [hp.value for hp in p.hook_points],
        }
        for p in plugins
    ]


@router.get("/hooks", summary="List hooks")
async def list_hooks(db: DB) -> list[str]:
    """List all available hook points."""
    service = PluginEcosystemService(db=db)
    return await service.list_available_hooks()


@router.get("/stats", summary="Get stats")
async def get_stats(db: DB) -> dict:
    """Get plugin ecosystem statistics."""
    service = PluginEcosystemService(db=db)
    stats = await service.get_stats()
    return {
        "total_plugins": stats.total_plugins,
        "installed": stats.installed,
        "by_type": stats.by_type,
        "total_executions": stats.total_executions,
        "by_hook_point": stats.by_hook_point,
        "avg_execution_ms": stats.avg_execution_ms,
    }
