"""Plugin ecosystem service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    HookPoint,
    PluginHookExecution,
    PluginInstance,
    PluginManifest,
    PluginStats,
    PluginStatus,
    PluginType,
)


logger = structlog.get_logger(__name__)


class PluginEcosystemService:
    """Service for managing the compliance plugin ecosystem."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._manifests: list[PluginManifest] = []
        self._instances: list[PluginInstance] = []
        self._executions: list[PluginHookExecution] = []
        self._seed_plugins()

    def _seed_plugins(self) -> None:
        """Seed initial plugins covering all types."""
        self._manifests = [
            PluginManifest(
                id="plugin-scanner-sast",
                name="SAST Scanner",
                plugin_type=PluginType.scanner,
                version="1.2.0",
                author="ComplianceCo",
                description="Static application security testing scanner",
                hook_points=[HookPoint.pre_scan, HookPoint.post_scan],
                config_schema={"severity_threshold": "string", "languages": "array"},
                dependencies=[],
            ),
            PluginManifest(
                id="plugin-fixer-autofix",
                name="Auto-Fix Engine",
                plugin_type=PluginType.fixer,
                version="0.9.1",
                author="ComplianceCo",
                description="Automatically fix common compliance violations",
                hook_points=[HookPoint.on_violation, HookPoint.on_fix],
                config_schema={"auto_apply": "boolean", "max_fixes": "integer"},
                dependencies=["plugin-scanner-sast"],
            ),
            PluginManifest(
                id="plugin-reporter-pdf",
                name="PDF Report Generator",
                plugin_type=PluginType.reporter,
                version="2.0.0",
                author="ReportLabs",
                description="Generate PDF compliance reports",
                hook_points=[HookPoint.on_report],
                config_schema={"template": "string", "include_charts": "boolean"},
                dependencies=[],
            ),
            PluginManifest(
                id="plugin-dashboard-metrics",
                name="Metrics Dashboard",
                plugin_type=PluginType.dashboard,
                version="1.0.0",
                author="DashCorp",
                description="Real-time compliance metrics dashboard",
                hook_points=[HookPoint.post_scan, HookPoint.on_report],
                config_schema={"refresh_interval": "integer"},
                dependencies=[],
            ),
            PluginManifest(
                id="plugin-integration-slack",
                name="Slack Integration",
                plugin_type=PluginType.integration,
                version="1.5.0",
                author="ComplianceCo",
                description="Send compliance notifications to Slack",
                hook_points=[
                    HookPoint.on_violation,
                    HookPoint.on_deploy,
                    HookPoint.on_report,
                ],
                config_schema={"webhook_url": "string", "channel": "string"},
                dependencies=[],
            ),
        ]

    async def register_plugin(
        self,
        manifest: dict,
    ) -> PluginManifest:
        """Register a new plugin from a manifest dictionary."""
        hook_points = [
            HookPoint(hp) for hp in manifest.get("hook_points", [])
        ]
        plugin = PluginManifest(
            id=manifest.get("id", f"plugin-{uuid.uuid4().hex[:8]}"),
            name=manifest.get("name", "Unknown Plugin"),
            plugin_type=PluginType(manifest.get("plugin_type", "analyzer")),
            version=manifest.get("version", "0.1.0"),
            author=manifest.get("author", "Unknown"),
            description=manifest.get("description", ""),
            hook_points=hook_points,
            config_schema=manifest.get("config_schema", {}),
            dependencies=manifest.get("dependencies", []),
        )
        self._manifests.append(plugin)

        await logger.ainfo("plugin_registered", plugin_id=plugin.id)
        return plugin

    async def install_plugin(
        self,
        plugin_id: str,
        config: dict | None = None,
    ) -> PluginInstance:
        """Install a plugin by its manifest ID."""
        manifest = next(
            (m for m in self._manifests if m.id == plugin_id), None
        )
        if not manifest:
            msg = f"Plugin {plugin_id} not found"
            raise ValueError(msg)

        instance = PluginInstance(
            id=uuid.uuid4(),
            manifest_id=plugin_id,
            status=PluginStatus.installed,
            config=config or {},
            executions=0,
            last_executed_at=None,
            installed_at=datetime.now(UTC),
        )
        self._instances.append(instance)

        await logger.ainfo(
            "plugin_installed",
            plugin_id=plugin_id,
            instance_id=str(instance.id),
        )
        return instance

    async def execute_hook(
        self,
        hook_point: str,
        input_data: dict,
    ) -> list[PluginHookExecution]:
        """Execute all plugins registered for a given hook point."""
        hp = HookPoint(hook_point)
        executions: list[PluginHookExecution] = []

        # Find all installed plugins that listen on this hook
        for instance in self._instances:
            if instance.status != PluginStatus.installed:
                continue
            manifest = next(
                (m for m in self._manifests if m.id == instance.manifest_id),
                None,
            )
            if not manifest or hp not in manifest.hook_points:
                continue

            output_data = {
                "plugin_id": manifest.id,
                "hook_point": hp.value,
                "processed": True,
                "input_keys": list(input_data.keys()),
            }

            execution = PluginHookExecution(
                id=uuid.uuid4(),
                plugin_id=manifest.id,
                hook_point=hp,
                input_data=input_data,
                output_data=output_data,
                duration_ms=1.5,
                success=True,
                executed_at=datetime.now(UTC),
            )
            executions.append(execution)

            instance.executions += 1
            instance.last_executed_at = datetime.now(UTC)

        self._executions.extend(executions)

        await logger.ainfo(
            "hook_executed",
            hook_point=hook_point,
            plugins_run=len(executions),
        )
        return executions

    async def uninstall_plugin(
        self,
        instance_id: uuid.UUID,
    ) -> bool:
        """Uninstall a plugin instance."""
        for i, inst in enumerate(self._instances):
            if inst.id == instance_id:
                self._instances.pop(i)
                await logger.ainfo(
                    "plugin_uninstalled",
                    instance_id=str(instance_id),
                )
                return True
        return False

    async def list_plugins(self) -> list[PluginManifest]:
        """List all registered plugin manifests."""
        return list(self._manifests)

    async def list_available_hooks(self) -> list[str]:
        """List all available hook points."""
        return [hp.value for hp in HookPoint]

    async def get_stats(self) -> PluginStats:
        """Get aggregate plugin ecosystem statistics."""
        by_type: dict[str, int] = {}
        for manifest in self._manifests:
            t = manifest.plugin_type.value
            by_type[t] = by_type.get(t, 0) + 1

        by_hook: dict[str, int] = {}
        durations: list[float] = []
        for execution in self._executions:
            h = execution.hook_point.value
            by_hook[h] = by_hook.get(h, 0) + 1
            durations.append(execution.duration_ms)

        avg_ms = sum(durations) / len(durations) if durations else 0.0

        return PluginStats(
            total_plugins=len(self._manifests),
            installed=len(self._instances),
            by_type=by_type,
            total_executions=len(self._executions),
            by_hook_point=by_hook,
            avg_execution_ms=avg_ms,
        )
