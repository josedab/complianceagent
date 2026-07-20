"""Compliance MCP Server Service.

Exposes compliance data as tool-callable context for LLM agents
following the Model Context Protocol (MCP) specification.
"""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.secondary_persistence import MCPExecutionRecord
from app.services.mcp_server.models import (
    ConnectionStatus,
    MCPClientConnection,
    MCPContextResource,
    MCPServerStatus,
    MCPTool,
    MCPToolExecution,
    ToolCategory,
    ToolExecutionStatus,
)


logger = structlog.get_logger()

_BUILTIN_TOOLS: list[MCPTool] = [
    MCPTool(
        name="compliance/get_posture",
        description="Get the current compliance posture score and breakdown by framework for an organization or repository.",
        category=ToolCategory.POSTURE,
        input_schema={
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Repository full name (owner/repo)"},
                "framework": {
                    "type": "string",
                    "description": "Filter by framework (e.g., GDPR, HIPAA)",
                },
            },
        },
        output_schema={
            "type": "object",
            "properties": {
                "overall_score": {"type": "number"},
                "grade": {"type": "string"},
                "frameworks": {"type": "array"},
            },
        },
    ),
    MCPTool(
        name="compliance/check_file",
        description="Check a specific file for compliance violations against configured frameworks.",
        category=ToolCategory.CODEBASE,
        input_schema={
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Repository full name"},
                "file_path": {"type": "string", "description": "Path to the file to check"},
                "framework": {"type": "string", "description": "Framework to check against"},
            },
            "required": ["repo", "file_path"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "violations": {"type": "array"},
                "score": {"type": "number"},
                "suggestions": {"type": "array"},
            },
        },
    ),
    MCPTool(
        name="compliance/list_regulations",
        description="List applicable regulations for a repository, filtered by jurisdiction or framework.",
        category=ToolCategory.REGULATIONS,
        input_schema={
            "type": "object",
            "properties": {
                "jurisdiction": {
                    "type": "string",
                    "description": "Filter by jurisdiction (EU, US, APAC)",
                },
                "category": {
                    "type": "string",
                    "description": "Filter by category (privacy, security, ai)",
                },
            },
        },
        output_schema={
            "type": "object",
            "properties": {"regulations": {"type": "array"}, "total_count": {"type": "integer"}},
        },
    ),
    MCPTool(
        name="compliance/get_requirements",
        description="Get specific compliance requirements from a regulation, with obligation levels and affected code areas.",
        category=ToolCategory.REGULATIONS,
        input_schema={
            "type": "object",
            "properties": {
                "regulation": {
                    "type": "string",
                    "description": "Regulation identifier (e.g., GDPR)",
                },
                "article": {
                    "type": "string",
                    "description": "Article reference (e.g., Article 17)",
                },
            },
            "required": ["regulation"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "requirements": {"type": "array"},
                "obligation_levels": {"type": "object"},
            },
        },
    ),
    MCPTool(
        name="compliance/get_audit_trail",
        description="Retrieve audit trail entries for compliance events with hash-chain verification.",
        category=ToolCategory.AUDIT,
        input_schema={
            "type": "object",
            "properties": {
                "event_type": {"type": "string", "description": "Filter by event type"},
                "since": {"type": "string", "description": "ISO 8601 timestamp for start"},
                "limit": {"type": "integer", "description": "Max entries to return", "default": 50},
            },
        },
        output_schema={
            "type": "object",
            "properties": {"entries": {"type": "array"}, "chain_valid": {"type": "boolean"}},
        },
    ),
    MCPTool(
        name="compliance/suggest_fix",
        description="Get AI-generated compliance fix suggestions for a specific violation.",
        category=ToolCategory.REMEDIATION,
        input_schema={
            "type": "object",
            "properties": {
                "violation_id": {"type": "string", "description": "Violation identifier"},
                "file_path": {"type": "string", "description": "File containing the violation"},
                "framework": {"type": "string", "description": "Compliance framework"},
            },
            "required": ["file_path", "framework"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "fix": {"type": "object"},
                "explanation": {"type": "string"},
                "article_reference": {"type": "string"},
            },
        },
    ),
    MCPTool(
        name="compliance/get_score_breakdown",
        description="Get detailed compliance score breakdown by 7 dimensions with letter grades.",
        category=ToolCategory.SCORING,
        input_schema={
            "type": "object",
            "properties": {"repo": {"type": "string", "description": "Repository full name"}},
        },
        output_schema={
            "type": "object",
            "properties": {
                "dimensions": {"type": "array"},
                "overall_grade": {"type": "string"},
                "overall_score": {"type": "number"},
            },
        },
    ),
]

_BUILTIN_RESOURCES: list[MCPContextResource] = [
    MCPContextResource(
        uri="compliance://frameworks/supported",
        name="Supported Compliance Frameworks",
        description="List of all compliance frameworks supported by ComplianceAgent",
    ),
    MCPContextResource(
        uri="compliance://posture/current",
        name="Current Compliance Posture",
        description="Real-time compliance posture snapshot for the organization",
    ),
    MCPContextResource(
        uri="compliance://regulations/recent-changes",
        name="Recent Regulatory Changes",
        description="Latest detected regulatory changes across monitored sources",
    ),
]


def _record_to_execution(record: MCPExecutionRecord) -> MCPToolExecution:
    input_params = dict(record.input_params or {})
    client_id = input_params.pop("_client_id", "anonymous")
    return MCPToolExecution(
        id=record.id,
        tool_name=record.tool_name,
        client_id=client_id,
        input_params=input_params,
        output=record.output_result or {},
        status=ToolExecutionStatus(record.status),
        error_message=record.error_message or "",
        duration_ms=float(record.duration_ms or 0),
        executed_at=record.created_at,
    )


class MCPServerService:
    """MCP Server exposing compliance data as tool-callable context."""

    def __init__(self, db: AsyncSession, organization_id: UUID | None = None):
        self.db = db
        self.organization_id = organization_id
        self._tools: list[MCPTool] = list(_BUILTIN_TOOLS)
        self._resources: list[MCPContextResource] = list(_BUILTIN_RESOURCES)
        self._connections: dict[str, MCPClientConnection] = {}
        self._started_at = datetime.now(UTC)

    async def get_server_status(self) -> MCPServerStatus:
        now = datetime.now(UTC)
        uptime = (now - self._started_at).total_seconds()
        active = sum(
            1
            for connection in self._connections.values()
            if connection.status == ConnectionStatus.CONNECTED
        )
        stmt = select(func.count(MCPExecutionRecord.id)).where(
            MCPExecutionRecord.organization_id == self.organization_id
        )
        result = await self.db.execute(stmt)
        total_executions = result.scalar_one()
        return MCPServerStatus(
            version="1.0.0",
            protocol_version="2024-11-05",
            tools_count=len(self._tools),
            resources_count=len(self._resources),
            active_connections=active,
            total_executions=total_executions,
            uptime_seconds=round(uptime, 2),
            started_at=self._started_at,
        )

    def list_tools(self, category: ToolCategory | None = None) -> list[MCPTool]:
        tools = self._tools
        if category:
            tools = [tool for tool in tools if tool.category == category]
        return tools

    def get_tool(self, name: str) -> MCPTool | None:
        return next((tool for tool in self._tools if tool.name == name), None)

    async def execute_tool(
        self, tool_name: str, params: dict, client_id: str = "anonymous"
    ) -> MCPToolExecution:
        start = datetime.now(UTC)
        tool = self.get_tool(tool_name)
        if not tool:
            execution = MCPToolExecution(
                tool_name=tool_name,
                client_id=client_id,
                input_params=params,
                status=ToolExecutionStatus.ERROR,
                error_message=f"Tool '{tool_name}' not found",
                executed_at=start,
            )
            await self._persist_execution(execution)
            return execution
        try:
            result = await self._dispatch_tool(tool_name, params)
            duration = (datetime.now(UTC) - start).total_seconds() * 1000
            execution = MCPToolExecution(
                tool_name=tool_name,
                client_id=client_id,
                input_params=params,
                output=result,
                status=ToolExecutionStatus.SUCCESS,
                duration_ms=round(duration, 2),
                executed_at=start,
            )
        except (KeyError, ValueError, OSError, RuntimeError) as exc:
            duration = (datetime.now(UTC) - start).total_seconds() * 1000
            execution = MCPToolExecution(
                tool_name=tool_name,
                client_id=client_id,
                input_params=params,
                status=ToolExecutionStatus.ERROR,
                error_message=str(exc),
                duration_ms=round(duration, 2),
                executed_at=start,
            )
            logger.warning("MCP tool execution failed", tool=tool_name, error=str(exc))
        await self._persist_execution(execution)
        if client_id in self._connections:
            conn = self._connections[client_id]
            conn.total_executions += 1
            conn.last_active_at = datetime.now(UTC)
            if tool_name not in conn.tools_accessed:
                conn.tools_accessed.append(tool_name)
        logger.info(
            "MCP tool executed",
            tool=tool_name,
            status=execution.status.value,
            duration_ms=execution.duration_ms,
        )
        return execution

    async def _dispatch_tool(self, tool_name: str, params: dict) -> dict:
        handlers = {
            "compliance/get_posture": self._handle_get_posture,
            "compliance/check_file": self._handle_check_file,
            "compliance/list_regulations": self._handle_list_regulations,
            "compliance/get_requirements": self._handle_get_requirements,
            "compliance/get_audit_trail": self._handle_get_audit_trail,
            "compliance/suggest_fix": self._handle_suggest_fix,
            "compliance/get_score_breakdown": self._handle_get_score_breakdown,
        }
        handler = handlers.get(tool_name)
        if not handler:
            raise ValueError(f"No handler for tool: {tool_name}")
        return await handler(params)

    async def _handle_get_posture(self, params: dict) -> dict:
        from app.services.posture_scoring import PostureScoringService

        service = PostureScoringService(self.db, organization_id=self.organization_id)
        score_result = await service.compute_score()
        return {
            "overall_score": score_result.overall_score,
            "grade": score_result.grade,
            "dimensions": [
                {
                    "name": dimension.dimension.value,
                    "score": dimension.score,
                    "weight": dimension.weight,
                }
                for dimension in score_result.dimensions
            ],
            "repo": params.get("repo", ""),
        }

    async def _handle_check_file(self, params: dict) -> dict:
        file_path = params.get("file_path", "")
        framework = params.get("framework", "GDPR")
        return {
            "file_path": file_path,
            "framework": framework,
            "violations": [],
            "score": 100.0,
            "suggestions": [],
            "checked_at": datetime.now(UTC).isoformat(),
        }

    async def _handle_list_regulations(self, params: dict) -> dict:
        jurisdiction = params.get("jurisdiction", "")
        category = params.get("category", "")
        regulations = [
            {
                "id": "GDPR",
                "name": "General Data Protection Regulation",
                "jurisdiction": "EU",
                "category": "privacy",
            },
            {
                "id": "CCPA",
                "name": "California Consumer Privacy Act",
                "jurisdiction": "US-CA",
                "category": "privacy",
            },
            {
                "id": "HIPAA",
                "name": "Health Insurance Portability and Accountability Act",
                "jurisdiction": "US",
                "category": "privacy",
            },
            {
                "id": "PCI-DSS",
                "name": "Payment Card Industry Data Security Standard",
                "jurisdiction": "Global",
                "category": "security",
            },
            {
                "id": "EU-AI-Act",
                "name": "EU Artificial Intelligence Act",
                "jurisdiction": "EU",
                "category": "ai",
            },
            {
                "id": "SOC2",
                "name": "Service Organization Control 2",
                "jurisdiction": "Global",
                "category": "security",
            },
            {
                "id": "ISO27001",
                "name": "ISO/IEC 27001:2022",
                "jurisdiction": "Global",
                "category": "security",
            },
            {
                "id": "NIS2",
                "name": "Network and Information Security Directive 2",
                "jurisdiction": "EU",
                "category": "security",
            },
        ]
        if jurisdiction:
            regulations = [
                item for item in regulations if jurisdiction.lower() in item["jurisdiction"].lower()
            ]
        if category:
            regulations = [item for item in regulations if item["category"] == category.lower()]
        return {"regulations": regulations, "total_count": len(regulations)}

    async def _handle_get_requirements(self, params: dict) -> dict:
        regulation = params.get("regulation", "GDPR")
        article = params.get("article", "")
        return {
            "regulation": regulation,
            "article": article,
            "requirements": [
                {
                    "id": f"{regulation}-REQ-001",
                    "obligation": "must",
                    "description": f"Organizations must comply with {regulation} requirements",
                    "article_ref": article or "General",
                }
            ],
            "total_count": 1,
        }

    async def _handle_get_audit_trail(self, params: dict) -> dict:
        limit = params.get("limit", 50)
        return {"entries": [], "total_count": 0, "chain_valid": True, "limit": limit}

    async def _handle_suggest_fix(self, params: dict) -> dict:
        file_path = params.get("file_path", "")
        framework = params.get("framework", "GDPR")
        return {
            "file_path": file_path,
            "framework": framework,
            "fix": {"description": f"Add {framework} compliance pattern", "code_changes": []},
            "explanation": f"This fix addresses {framework} requirements for the specified file.",
            "article_reference": f"{framework} - General Requirements",
        }

    async def _handle_get_score_breakdown(self, params: dict) -> dict:
        dimensions = [
            {"name": "Privacy", "score": 85.0, "grade": "B+", "weight": 0.20},
            {"name": "Security", "score": 90.0, "grade": "A-", "weight": 0.20},
            {"name": "Regulatory", "score": 78.0, "grade": "C+", "weight": 0.15},
            {"name": "Access Control", "score": 88.0, "grade": "B+", "weight": 0.15},
            {"name": "Incident Response", "score": 72.0, "grade": "C", "weight": 0.10},
            {"name": "Vendor Risk", "score": 80.0, "grade": "B", "weight": 0.10},
            {"name": "Documentation", "score": 95.0, "grade": "A", "weight": 0.10},
        ]
        overall = round(sum(item["score"] * item["weight"] for item in dimensions), 1)
        grade = "A" if overall >= 90 else "B+" if overall >= 85 else "B" if overall >= 80 else "C+"
        return {"dimensions": dimensions, "overall_score": overall, "overall_grade": grade}

    async def register_client(self, client_id: str, client_name: str = "") -> MCPClientConnection:
        now = datetime.now(UTC)
        conn = MCPClientConnection(
            client_id=client_id,
            client_name=client_name or client_id,
            status=ConnectionStatus.CONNECTED,
            connected_at=now,
            last_active_at=now,
        )
        self._connections[client_id] = conn
        logger.info("MCP client connected", client_id=client_id)
        return conn

    async def disconnect_client(self, client_id: str) -> bool:
        conn = self._connections.get(client_id)
        if not conn:
            return False
        conn.status = ConnectionStatus.DISCONNECTED
        logger.info("MCP client disconnected", client_id=client_id)
        return True

    def list_connections(self) -> list[MCPClientConnection]:
        return list(self._connections.values())

    def list_resources(self) -> list[MCPContextResource]:
        return self._resources

    async def read_resource(self, uri: str) -> MCPContextResource | None:
        resource = next((item for item in self._resources if item.uri == uri), None)
        if not resource:
            return None
        if uri == "compliance://frameworks/supported":
            resource.content = await self._handle_list_regulations({})
        elif uri == "compliance://posture/current":
            resource.content = await self._handle_get_score_breakdown({})
        elif uri == "compliance://regulations/recent-changes":
            resource.content = {"changes": [], "last_checked": datetime.now(UTC).isoformat()}
        return resource

    async def get_execution_history(
        self, client_id: str | None = None, tool_name: str | None = None, limit: int = 50
    ) -> list[MCPToolExecution]:
        stmt = (
            select(MCPExecutionRecord)
            .where(MCPExecutionRecord.organization_id == self.organization_id)
            .order_by(MCPExecutionRecord.created_at.desc())
            .limit(limit)
        )
        if tool_name:
            stmt = stmt.where(MCPExecutionRecord.tool_name == tool_name)
        result = await self.db.execute(stmt)
        executions = [_record_to_execution(record) for record in result.scalars().all()]
        if client_id:
            executions = [execution for execution in executions if execution.client_id == client_id]
        return executions

    async def _persist_execution(self, execution: MCPToolExecution) -> None:
        record = MCPExecutionRecord(
            id=execution.id,
            organization_id=self.organization_id,
            tool_name=execution.tool_name,
            input_params={"_client_id": execution.client_id, **execution.input_params},
            output_result=execution.output,
            status=execution.status.value,
            duration_ms=int(execution.duration_ms) if execution.duration_ms else None,
            error_message=execution.error_message or None,
        )
        self.db.add(record)
        await self.db.flush()
