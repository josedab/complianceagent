"""API endpoints for Compliance MCP Server."""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.mcp_server import MCPServerService, ToolCategory


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---


class MCPToolSchema(BaseModel):
    """MCP tool definition."""

    name: str
    description: str
    category: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    requires_auth: bool
    version: str


class ExecuteToolRequest(BaseModel):
    """Request to execute an MCP tool."""

    tool_name: str = Field(..., description="Name of the tool to execute")
    params: dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    client_id: str = Field(default="api-client", description="Client identifier")


class ToolExecutionSchema(BaseModel):
    """Tool execution result."""

    id: str
    tool_name: str
    client_id: str
    input_params: dict[str, Any]
    output: dict[str, Any]
    status: str
    error_message: str
    duration_ms: float
    executed_at: str | None


class RegisterClientRequest(BaseModel):
    """Request to register an MCP client."""

    client_id: str = Field(..., description="Unique client identifier")
    client_name: str = Field(default="", description="Human-readable client name")


class ClientConnectionSchema(BaseModel):
    """Client connection response."""

    id: str
    client_id: str
    client_name: str
    status: str
    tools_accessed: list[str]
    total_executions: int
    connected_at: str | None
    last_active_at: str | None


class MCPResourceSchema(BaseModel):
    """MCP context resource."""

    uri: str
    name: str
    description: str
    mime_type: str
    content: dict[str, Any]


class MCPServerStatusSchema(BaseModel):
    """MCP server status."""

    version: str
    protocol_version: str
    tools_count: int
    resources_count: int
    active_connections: int
    total_executions: int
    uptime_seconds: float
    started_at: str | None


# --- Endpoints ---


@router.get(
    "/status",
    response_model=MCPServerStatusSchema,
    summary="Get MCP server status",
)
async def get_server_status(db: DB) -> MCPServerStatusSchema:
    """Get MCP server status and capabilities."""
    service = MCPServerService(db=db)
    s = service.get_server_status()
    return MCPServerStatusSchema(
        version=s.version,
        protocol_version=s.protocol_version,
        tools_count=s.tools_count,
        resources_count=s.resources_count,
        active_connections=s.active_connections,
        total_executions=s.total_executions,
        uptime_seconds=s.uptime_seconds,
        started_at=s.started_at.isoformat() if s.started_at else None,
    )


@router.get(
    "/tools",
    response_model=list[MCPToolSchema],
    summary="List MCP tools",
)
async def list_tools(
    db: DB,
    category: str | None = None,
) -> list[MCPToolSchema]:
    """List available MCP compliance tools."""
    service = MCPServerService(db=db)
    cat = ToolCategory(category) if category else None
    tools = service.list_tools(category=cat)
    return [
        MCPToolSchema(
            name=t.name,
            description=t.description,
            category=t.category.value,
            input_schema=t.input_schema,
            output_schema=t.output_schema,
            requires_auth=t.requires_auth,
            version=t.version,
        )
        for t in tools
    ]


@router.get(
    "/tools/{tool_name:path}",
    response_model=MCPToolSchema,
    summary="Get MCP tool details",
)
async def get_tool(tool_name: str, db: DB) -> MCPToolSchema:
    """Get details of a specific MCP tool."""
    service = MCPServerService(db=db)
    tool = service.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
    return MCPToolSchema(
        name=tool.name,
        description=tool.description,
        category=tool.category.value,
        input_schema=tool.input_schema,
        output_schema=tool.output_schema,
        requires_auth=tool.requires_auth,
        version=tool.version,
    )


@router.post(
    "/execute",
    response_model=ToolExecutionSchema,
    summary="Execute MCP tool",
)
async def execute_tool(
    request: ExecuteToolRequest,
    db: DB,
) -> ToolExecutionSchema:
    """Execute an MCP compliance tool."""
    service = MCPServerService(db=db)
    execution = await service.execute_tool(
        tool_name=request.tool_name,
        params=request.params,
        client_id=request.client_id,
    )
    return ToolExecutionSchema(
        id=str(execution.id),
        tool_name=execution.tool_name,
        client_id=execution.client_id,
        input_params=execution.input_params,
        output=execution.output,
        status=execution.status.value,
        error_message=execution.error_message,
        duration_ms=execution.duration_ms,
        executed_at=execution.executed_at.isoformat() if execution.executed_at else None,
    )


@router.post(
    "/clients",
    response_model=ClientConnectionSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Register MCP client",
)
async def register_client(
    request: RegisterClientRequest,
    db: DB,
) -> ClientConnectionSchema:
    """Register a new MCP client connection."""
    service = MCPServerService(db=db)
    conn = await service.register_client(
        client_id=request.client_id,
        client_name=request.client_name,
    )
    return ClientConnectionSchema(
        id=str(conn.id),
        client_id=conn.client_id,
        client_name=conn.client_name,
        status=conn.status.value,
        tools_accessed=conn.tools_accessed,
        total_executions=conn.total_executions,
        connected_at=conn.connected_at.isoformat() if conn.connected_at else None,
        last_active_at=conn.last_active_at.isoformat() if conn.last_active_at else None,
    )


@router.get(
    "/clients",
    response_model=list[ClientConnectionSchema],
    summary="List MCP clients",
)
async def list_clients(db: DB) -> list[ClientConnectionSchema]:
    """List connected MCP clients."""
    service = MCPServerService(db=db)
    connections = service.list_connections()
    return [
        ClientConnectionSchema(
            id=str(c.id),
            client_id=c.client_id,
            client_name=c.client_name,
            status=c.status.value,
            tools_accessed=c.tools_accessed,
            total_executions=c.total_executions,
            connected_at=c.connected_at.isoformat() if c.connected_at else None,
            last_active_at=c.last_active_at.isoformat() if c.last_active_at else None,
        )
        for c in connections
    ]


@router.delete(
    "/clients/{client_id}",
    summary="Disconnect MCP client",
)
async def disconnect_client(client_id: str, db: DB) -> dict:
    """Disconnect an MCP client."""
    service = MCPServerService(db=db)
    ok = await service.disconnect_client(client_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return {"status": "disconnected", "client_id": client_id}


@router.get(
    "/resources",
    response_model=list[MCPResourceSchema],
    summary="List MCP resources",
)
async def list_resources(db: DB) -> list[MCPResourceSchema]:
    """List available MCP context resources."""
    service = MCPServerService(db=db)
    resources = service.list_resources()
    return [
        MCPResourceSchema(
            uri=r.uri,
            name=r.name,
            description=r.description,
            mime_type=r.mime_type,
            content=r.content,
        )
        for r in resources
    ]


@router.get(
    "/resources/{uri:path}",
    response_model=MCPResourceSchema,
    summary="Read MCP resource",
)
async def read_resource(uri: str, db: DB) -> MCPResourceSchema:
    """Read a specific MCP context resource."""
    service = MCPServerService(db=db)
    resource = await service.read_resource(uri)
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return MCPResourceSchema(
        uri=resource.uri,
        name=resource.name,
        description=resource.description,
        mime_type=resource.mime_type,
        content=resource.content,
    )


@router.get(
    "/executions",
    response_model=list[ToolExecutionSchema],
    summary="Get execution history",
)
async def get_execution_history(
    db: DB,
    client_id: str | None = None,
    tool_name: str | None = None,
    limit: int = 50,
) -> list[ToolExecutionSchema]:
    """Get MCP tool execution history."""
    service = MCPServerService(db=db)
    executions = service.get_execution_history(
        client_id=client_id, tool_name=tool_name, limit=limit
    )
    return [
        ToolExecutionSchema(
            id=str(e.id),
            tool_name=e.tool_name,
            client_id=e.client_id,
            input_params=e.input_params,
            output=e.output,
            status=e.status.value,
            error_message=e.error_message,
            duration_ms=e.duration_ms,
            executed_at=e.executed_at.isoformat() if e.executed_at else None,
        )
        for e in executions
    ]
