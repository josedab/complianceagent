"""Plugin ecosystem models."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class PluginType(str, Enum):
    """Type of plugin."""

    scanner = "scanner"
    fixer = "fixer"
    reporter = "reporter"
    dashboard = "dashboard"
    integration = "integration"
    analyzer = "analyzer"


class PluginStatus(str, Enum):
    """Runtime status of a plugin instance."""

    installed = "installed"
    disabled = "disabled"
    error = "error"
    updating = "updating"


class HookPoint(str, Enum):
    """Hook point in the compliance pipeline."""

    pre_scan = "pre_scan"
    post_scan = "post_scan"
    on_violation = "on_violation"
    on_fix = "on_fix"
    on_deploy = "on_deploy"
    on_report = "on_report"


@dataclass
class PluginManifest:
    """Manifest describing a plugin."""

    id: str = ""
    name: str = ""
    plugin_type: PluginType = PluginType.scanner
    version: str = "0.1.0"
    author: str = ""
    description: str = ""
    hook_points: list[HookPoint] = field(default_factory=list)
    config_schema: dict = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)


@dataclass
class PluginInstance:
    """An installed instance of a plugin."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    manifest_id: str = ""
    status: PluginStatus = PluginStatus.installed
    config: dict = field(default_factory=dict)
    executions: int = 0
    last_executed_at: datetime | None = None
    installed_at: datetime | None = None


@dataclass
class PluginHookExecution:
    """Record of a plugin hook execution."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    plugin_id: str = ""
    hook_point: HookPoint = HookPoint.pre_scan
    input_data: dict = field(default_factory=dict)
    output_data: dict = field(default_factory=dict)
    duration_ms: float = 0.0
    success: bool = True
    executed_at: datetime | None = None


@dataclass
class PluginStats:
    """Aggregate statistics for the plugin ecosystem."""

    total_plugins: int = 0
    installed: int = 0
    by_type: dict = field(default_factory=dict)
    total_executions: int = 0
    by_hook_point: dict = field(default_factory=dict)
    avg_execution_ms: float = 0.0
