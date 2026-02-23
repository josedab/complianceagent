"""Compliance MCP Server models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class ToolCategory(str, Enum):
    """MCP tool category."""

    POSTURE = "posture"
    REGULATIONS = "regulations"
    AUDIT = "audit"
    CODEBASE = "codebase"
    SCORING = "scoring"
    REMEDIATION = "remediation"


class ToolExecutionStatus(str, Enum):
    """Status of a tool execution."""

    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"
    TIMEOUT = "timeout"


class ConnectionStatus(str, Enum):
    """MCP client connection status."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    AUTHENTICATING = "authenticating"


@dataclass
class MCPTool:
    """Definition of an MCP-exposed compliance tool."""

    name: str = ""
    description: str = ""
    category: ToolCategory = ToolCategory.POSTURE
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    requires_auth: bool = True
    version: str = "1.0.0"


@dataclass
class MCPToolExecution:
    """Record of a single tool execution."""

    id: UUID = field(default_factory=uuid4)
    tool_name: str = ""
    client_id: str = ""
    input_params: dict[str, Any] = field(default_factory=dict)
    output: dict[str, Any] = field(default_factory=dict)
    status: ToolExecutionStatus = ToolExecutionStatus.SUCCESS
    error_message: str = ""
    duration_ms: float = 0.0
    executed_at: datetime | None = None


@dataclass
class MCPClientConnection:
    """An MCP client connection."""

    id: UUID = field(default_factory=uuid4)
    client_id: str = ""
    client_name: str = ""
    status: ConnectionStatus = ConnectionStatus.CONNECTED
    tools_accessed: list[str] = field(default_factory=list)
    total_executions: int = 0
    connected_at: datetime | None = None
    last_active_at: datetime | None = None


@dataclass
class MCPContextResource:
    """A compliance context resource exposed via MCP."""

    uri: str = ""
    name: str = ""
    description: str = ""
    mime_type: str = "application/json"
    content: dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPServerStatus:
    """Overall MCP server status."""

    version: str = "1.0.0"
    protocol_version: str = "2024-11-05"
    tools_count: int = 0
    resources_count: int = 0
    active_connections: int = 0
    total_executions: int = 0
    uptime_seconds: float = 0.0
    started_at: datetime | None = None
