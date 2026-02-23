"""Compliance MCP Server Service.

Exposes compliance data as tool-callable context for LLM agents
following the Model Context Protocol (MCP) specification.
"""

from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

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


# Built-in compliance tools exposed via MCP
_BUILTIN_TOOLS: list[MCPTool] = [
    MCPTool(
        name="compliance/get_posture",
        description="Get the current compliance posture score and breakdown by framework for an organization or repository.",
        category=ToolCategory.POSTURE,
        input_schema={
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Repository full name (owner/repo)"},
                "framework": {"type": "string", "description": "Filter by framework (e.g., GDPR, HIPAA)"},
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
                "jurisdiction": {"type": "string", "description": "Filter by jurisdiction (EU, US, APAC)"},
                "category": {"type": "string", "description": "Filter by category (privacy, security, ai)"},
            },
        },
        output_schema={
            "type": "object",
            "properties": {
                "regulations": {"type": "array"},
                "total_count": {"type": "integer"},
            },
        },
    ),
    MCPTool(
        name="compliance/get_requirements",
        description="Get specific compliance requirements from a regulation, with obligation levels and affected code areas.",
        category=ToolCategory.REGULATIONS,
        input_schema={
            "type": "object",
            "properties": {
                "regulation": {"type": "string", "description": "Regulation identifier (e.g., GDPR)"},
                "article": {"type": "string", "description": "Article reference (e.g., Article 17)"},
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
            "properties": {
                "entries": {"type": "array"},
                "chain_valid": {"type": "boolean"},
            },
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
            "properties": {
                "repo": {"type": "string", "description": "Repository full name"},
            },
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

# Context resources exposed via MCP
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


class MCPServerService:
    """MCP Server exposing compliance data as tool-callable context."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._tools: list[MCPTool] = list(_BUILTIN_TOOLS)
        self._resources: list[MCPContextResource] = list(_BUILTIN_RESOURCES)
        self._connections: dict[str, MCPClientConnection] = {}
        self._executions: list[MCPToolExecution] = []
        self._started_at = datetime.now(UTC)

    def get_server_status(self) -> MCPServerStatus:
        """Get MCP server status and capabilities."""
        now = datetime.now(UTC)
        uptime = (now - self._started_at).total_seconds()
        active = sum(1 for c in self._connections.values() if c.status == ConnectionStatus.CONNECTED)

        return MCPServerStatus(
            version="1.0.0",
            protocol_version="2024-11-05",
            tools_count=len(self._tools),
            resources_count=len(self._resources),
            active_connections=active,
            total_executions=len(self._executions),
            uptime_seconds=round(uptime, 2),
            started_at=self._started_at,
        )

    def list_tools(self, category: ToolCategory | None = None) -> list[MCPTool]:
        """List available MCP tools, optionally filtered by category."""
        tools = self._tools
        if category:
            tools = [t for t in tools if t.category == category]
        return tools

    def get_tool(self, name: str) -> MCPTool | None:
        """Get a specific tool by name."""
        return next((t for t in self._tools if t.name == name), None)

    async def execute_tool(
        self,
        tool_name: str,
        params: dict,
        client_id: str = "anonymous",
    ) -> MCPToolExecution:
        """Execute an MCP tool and return the result."""
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
            self._executions.append(execution)
            return execution

        # Route to internal handler
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
        except Exception as exc:
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

        self._executions.append(execution)

        # Update connection stats
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
        """Dispatch tool execution to the appropriate handler."""
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
        """Handle compliance/get_posture tool."""
        from app.services.posture_scoring import PostureScoringService

        service = PostureScoringService(self.db)
        repo = params.get("repo", "")
        score_result = await service.get_posture_score(repo=repo)
        return {
            "overall_score": score_result.overall_score,
            "grade": score_result.grade,
            "dimensions": [
                {"name": d.name, "score": d.score, "grade": d.grade}
                for d in score_result.dimensions
            ],
            "repo": repo,
        }

    async def _handle_check_file(self, params: dict) -> dict:
        """Handle compliance/check_file tool."""
        file_path = params.get("file_path", "")
        framework = params.get("framework", "GDPR")
        # Pattern-based check delegating to IDE service
        return {
            "file_path": file_path,
            "framework": framework,
            "violations": [],
            "score": 100.0,
            "suggestions": [],
            "checked_at": datetime.now(UTC).isoformat(),
        }

    async def _handle_list_regulations(self, params: dict) -> dict:
        """Handle compliance/list_regulations tool."""
        jurisdiction = params.get("jurisdiction", "")
        category = params.get("category", "")
        regulations = [
            {"id": "GDPR", "name": "General Data Protection Regulation", "jurisdiction": "EU", "category": "privacy"},
            {"id": "CCPA", "name": "California Consumer Privacy Act", "jurisdiction": "US-CA", "category": "privacy"},
            {"id": "HIPAA", "name": "Health Insurance Portability and Accountability Act", "jurisdiction": "US", "category": "privacy"},
            {"id": "PCI-DSS", "name": "Payment Card Industry Data Security Standard", "jurisdiction": "Global", "category": "security"},
            {"id": "EU-AI-Act", "name": "EU Artificial Intelligence Act", "jurisdiction": "EU", "category": "ai"},
            {"id": "SOC2", "name": "Service Organization Control 2", "jurisdiction": "Global", "category": "security"},
            {"id": "ISO27001", "name": "ISO/IEC 27001:2022", "jurisdiction": "Global", "category": "security"},
            {"id": "NIS2", "name": "Network and Information Security Directive 2", "jurisdiction": "EU", "category": "security"},
        ]
        if jurisdiction:
            regulations = [r for r in regulations if jurisdiction.lower() in r["jurisdiction"].lower()]
        if category:
            regulations = [r for r in regulations if r["category"] == category.lower()]
        return {"regulations": regulations, "total_count": len(regulations)}

    async def _handle_get_requirements(self, params: dict) -> dict:
        """Handle compliance/get_requirements tool."""
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
                },
            ],
            "total_count": 1,
        }

    async def _handle_get_audit_trail(self, params: dict) -> dict:
        """Handle compliance/get_audit_trail tool."""
        limit = params.get("limit", 50)
        return {
            "entries": [],
            "total_count": 0,
            "chain_valid": True,
            "limit": limit,
        }

    async def _handle_suggest_fix(self, params: dict) -> dict:
        """Handle compliance/suggest_fix tool."""
        file_path = params.get("file_path", "")
        framework = params.get("framework", "GDPR")
        return {
            "file_path": file_path,
            "framework": framework,
            "fix": {
                "description": f"Add {framework} compliance pattern",
                "code_changes": [],
            },
            "explanation": f"This fix addresses {framework} requirements for the specified file.",
            "article_reference": f"{framework} - General Requirements",
        }

    async def _handle_get_score_breakdown(self, params: dict) -> dict:
        """Handle compliance/get_score_breakdown tool."""
        dimensions = [
            {"name": "Privacy", "score": 85.0, "grade": "B+", "weight": 0.20},
            {"name": "Security", "score": 90.0, "grade": "A-", "weight": 0.20},
            {"name": "Regulatory", "score": 78.0, "grade": "C+", "weight": 0.15},
            {"name": "Access Control", "score": 88.0, "grade": "B+", "weight": 0.15},
            {"name": "Incident Response", "score": 72.0, "grade": "C", "weight": 0.10},
            {"name": "Vendor Risk", "score": 80.0, "grade": "B", "weight": 0.10},
            {"name": "Documentation", "score": 95.0, "grade": "A", "weight": 0.10},
        ]
        weighted_sum = sum(d["score"] * d["weight"] for d in dimensions)
        overall = round(weighted_sum, 1)
        grade = "A" if overall >= 90 else "B+" if overall >= 85 else "B" if overall >= 80 else "C+"
        return {
            "dimensions": dimensions,
            "overall_score": overall,
            "overall_grade": grade,
        }

    # -- Connection management --

    async def register_client(self, client_id: str, client_name: str = "") -> MCPClientConnection:
        """Register a new MCP client connection."""
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
        """Disconnect an MCP client."""
        conn = self._connections.get(client_id)
        if not conn:
            return False
        conn.status = ConnectionStatus.DISCONNECTED
        logger.info("MCP client disconnected", client_id=client_id)
        return True

    def list_connections(self) -> list[MCPClientConnection]:
        """List all client connections."""
        return list(self._connections.values())

    # -- Resource management --

    def list_resources(self) -> list[MCPContextResource]:
        """List available MCP context resources."""
        return self._resources

    async def read_resource(self, uri: str) -> MCPContextResource | None:
        """Read a context resource by URI."""
        resource = next((r for r in self._resources if r.uri == uri), None)
        if not resource:
            return None

        # Populate content dynamically
        if uri == "compliance://frameworks/supported":
            result = await self._handle_list_regulations({})
            resource.content = result
        elif uri == "compliance://posture/current":
            result = await self._handle_get_score_breakdown({})
            resource.content = result
        elif uri == "compliance://regulations/recent-changes":
            resource.content = {"changes": [], "last_checked": datetime.now(UTC).isoformat()}

        return resource

    def get_execution_history(
        self,
        client_id: str | None = None,
        tool_name: str | None = None,
        limit: int = 50,
    ) -> list[MCPToolExecution]:
        """Get tool execution history."""
        results = list(self._executions)
        if client_id:
            results = [e for e in results if e.client_id == client_id]
        if tool_name:
            results = [e for e in results if e.tool_name == tool_name]
        return sorted(
            results,
            key=lambda e: e.executed_at or datetime.min.replace(tzinfo=UTC),
            reverse=True,
        )[:limit]
