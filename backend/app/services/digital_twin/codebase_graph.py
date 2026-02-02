"""Codebase Graph Model - Dependency and data flow graph for compliance analysis."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

import structlog


logger = structlog.get_logger()


class CodeNodeType(str, Enum):
    """Types of nodes in the codebase graph."""
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    FILE = "file"
    VARIABLE = "variable"
    DATABASE_TABLE = "database_table"
    API_ENDPOINT = "api_endpoint"
    EXTERNAL_SERVICE = "external_service"
    DATA_STORE = "data_store"
    MESSAGE_QUEUE = "message_queue"
    CACHE = "cache"


class DataFlowType(str, Enum):
    """Types of data flow relationships."""
    CALLS = "calls"
    IMPORTS = "imports"
    INHERITS = "inherits"
    READS = "reads"
    WRITES = "writes"
    SENDS_TO = "sends_to"
    RECEIVES_FROM = "receives_from"
    STORES = "stores"
    RETRIEVES = "retrieves"
    TRANSFORMS = "transforms"


class DataSensitivity(str, Enum):
    """Data sensitivity classifications."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    PII = "pii"
    PHI = "phi"
    PCI = "pci"
    FINANCIAL = "financial"


@dataclass
class CodeNode:
    """A node in the codebase graph."""
    id: UUID = field(default_factory=uuid4)
    node_type: CodeNodeType = CodeNodeType.FILE
    name: str = ""
    qualified_name: str = ""
    file_path: str | None = None
    start_line: int | None = None
    end_line: int | None = None
    language: str = ""
    
    # Data handling
    data_types_handled: list[str] = field(default_factory=list)
    data_sensitivity: list[DataSensitivity] = field(default_factory=list)
    
    # Compliance annotations
    compliance_annotations: list[str] = field(default_factory=list)
    compliance_issues: list[str] = field(default_factory=list)
    
    # Metadata
    description: str = ""
    documentation: str = ""
    properties: dict[str, Any] = field(default_factory=dict)
    
    # Visualization
    x: float = 0.0
    y: float = 0.0
    size: float = 1.0
    color: str = "#4CAF50"
    group: str = ""


@dataclass
class DataFlowEdge:
    """An edge representing data flow between nodes."""
    id: UUID = field(default_factory=uuid4)
    source_id: UUID = field(default_factory=uuid4)
    target_id: UUID = field(default_factory=uuid4)
    flow_type: DataFlowType = DataFlowType.CALLS
    
    # Data characteristics
    data_types: list[str] = field(default_factory=list)
    data_sensitivity: list[DataSensitivity] = field(default_factory=list)
    is_encrypted: bool = False
    is_logged: bool = False
    
    # Compliance status
    compliance_status: str = "unknown"
    compliance_issues: list[str] = field(default_factory=list)
    
    # Metadata
    weight: float = 1.0
    label: str = ""
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class DataFlow:
    """A complete data flow path through the codebase."""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    
    # Flow path
    nodes: list[UUID] = field(default_factory=list)
    edges: list[UUID] = field(default_factory=list)
    
    # Entry/exit points
    entry_point: UUID | None = None
    exit_points: list[UUID] = field(default_factory=list)
    
    # Data characteristics
    data_types: list[str] = field(default_factory=list)
    data_sensitivity: list[DataSensitivity] = field(default_factory=list)
    
    # Compliance
    regulations_affected: list[str] = field(default_factory=list)
    compliance_status: str = "unknown"
    compliance_score: float = 0.0
    issues: list[str] = field(default_factory=list)


@dataclass
class CodebaseGraph:
    """Complete codebase graph with nodes, edges, and data flows."""
    id: UUID = field(default_factory=uuid4)
    repository_id: UUID | None = None
    organization_id: UUID | None = None
    name: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Graph components
    nodes: list[CodeNode] = field(default_factory=list)
    edges: list[DataFlowEdge] = field(default_factory=list)
    data_flows: list[DataFlow] = field(default_factory=list)
    
    # Indexes
    _nodes_by_id: dict[UUID, CodeNode] = field(default_factory=dict)
    _edges_by_source: dict[UUID, list[DataFlowEdge]] = field(default_factory=dict)
    _edges_by_target: dict[UUID, list[DataFlowEdge]] = field(default_factory=dict)
    _nodes_by_type: dict[CodeNodeType, list[CodeNode]] = field(default_factory=dict)
    
    # Statistics
    commit_sha: str | None = None
    files_analyzed: int = 0
    languages: list[str] = field(default_factory=list)
    
    def add_node(self, node: CodeNode) -> None:
        """Add a node to the graph."""
        self.nodes.append(node)
        self._nodes_by_id[node.id] = node
        
        if node.node_type not in self._nodes_by_type:
            self._nodes_by_type[node.node_type] = []
        self._nodes_by_type[node.node_type].append(node)
    
    def add_edge(self, edge: DataFlowEdge) -> None:
        """Add an edge to the graph."""
        self.edges.append(edge)
        
        if edge.source_id not in self._edges_by_source:
            self._edges_by_source[edge.source_id] = []
        self._edges_by_source[edge.source_id].append(edge)
        
        if edge.target_id not in self._edges_by_target:
            self._edges_by_target[edge.target_id] = []
        self._edges_by_target[edge.target_id].append(edge)
    
    def get_node(self, node_id: UUID) -> CodeNode | None:
        """Get a node by ID."""
        return self._nodes_by_id.get(node_id)
    
    def get_outgoing_edges(self, node_id: UUID) -> list[DataFlowEdge]:
        """Get edges originating from a node."""
        return self._edges_by_source.get(node_id, [])
    
    def get_incoming_edges(self, node_id: UUID) -> list[DataFlowEdge]:
        """Get edges targeting a node."""
        return self._edges_by_target.get(node_id, [])
    
    def get_neighbors(self, node_id: UUID) -> list[CodeNode]:
        """Get neighboring nodes."""
        neighbors = []
        for edge in self.get_outgoing_edges(node_id):
            node = self.get_node(edge.target_id)
            if node:
                neighbors.append(node)
        for edge in self.get_incoming_edges(node_id):
            node = self.get_node(edge.source_id)
            if node:
                neighbors.append(node)
        return neighbors
    
    def find_nodes_handling_data(
        self,
        sensitivity: DataSensitivity,
    ) -> list[CodeNode]:
        """Find all nodes handling data of a specific sensitivity."""
        return [
            node for node in self.nodes
            if sensitivity in node.data_sensitivity
        ]
    
    def get_data_flow_path(
        self,
        start_id: UUID,
        end_id: UUID,
        max_depth: int = 10,
    ) -> list[list[UUID]]:
        """Find paths between two nodes."""
        paths = []
        
        def dfs(current: UUID, target: UUID, path: list[UUID], depth: int):
            if depth > max_depth:
                return
            if current == target:
                paths.append(path.copy())
                return
            
            for edge in self.get_outgoing_edges(current):
                if edge.target_id not in path:
                    path.append(edge.target_id)
                    dfs(edge.target_id, target, path, depth + 1)
                    path.pop()
        
        dfs(start_id, end_id, [start_id], 0)
        return paths
    
    @property
    def node_count(self) -> int:
        return len(self.nodes)
    
    @property
    def edge_count(self) -> int:
        return len(self.edges)
    
    @property
    def sensitive_data_nodes(self) -> list[CodeNode]:
        """Get nodes handling sensitive data."""
        sensitive_types = {
            DataSensitivity.PII,
            DataSensitivity.PHI,
            DataSensitivity.PCI,
            DataSensitivity.RESTRICTED,
        }
        return [
            node for node in self.nodes
            if any(s in sensitive_types for s in node.data_sensitivity)
        ]


class CodebaseGraphBuilder:
    """Builds codebase graphs from source analysis."""

    def __init__(self):
        self._graphs: dict[UUID, CodebaseGraph] = {}

    async def build_graph(
        self,
        repository_id: UUID,
        organization_id: UUID,
        files: dict[str, str],
        commit_sha: str | None = None,
    ) -> CodebaseGraph:
        """Build a codebase graph from source files."""
        graph = CodebaseGraph(
            repository_id=repository_id,
            organization_id=organization_id,
            name=f"Codebase Graph - {datetime.utcnow().strftime('%Y-%m-%d')}",
            commit_sha=commit_sha,
        )
        
        # Analyze each file
        for file_path, content in files.items():
            await self._analyze_file(graph, file_path, content)
        
        # Detect data flows
        await self._detect_data_flows(graph)
        
        # Apply compliance analysis
        await self._analyze_compliance(graph)
        
        # Calculate layout
        self._apply_layout(graph)
        
        # Update statistics
        graph.files_analyzed = len(files)
        graph.languages = list(set(n.language for n in graph.nodes if n.language))
        graph.updated_at = datetime.utcnow()
        
        # Store graph
        self._graphs[graph.id] = graph
        
        logger.info(
            "codebase_graph_built",
            graph_id=str(graph.id),
            nodes=graph.node_count,
            edges=graph.edge_count,
            data_flows=len(graph.data_flows),
        )
        
        return graph

    async def _analyze_file(
        self,
        graph: CodebaseGraph,
        file_path: str,
        content: str,
    ) -> None:
        """Analyze a single file and add nodes/edges."""
        # Detect language
        language = self._detect_language(file_path)
        
        # Create file node
        file_node = CodeNode(
            node_type=CodeNodeType.FILE,
            name=file_path.split("/")[-1],
            qualified_name=file_path,
            file_path=file_path,
            language=language,
        )
        
        # Analyze content for data handling patterns
        self._detect_data_handling(file_node, content)
        
        graph.add_node(file_node)
        
        # Extract functions/classes (simplified pattern matching)
        if language == "python":
            await self._analyze_python_file(graph, file_node, content)
        elif language in ("typescript", "javascript"):
            await self._analyze_js_file(graph, file_node, content)

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext_map = {
            ".py": "python",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".js": "javascript",
            ".jsx": "javascript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".sql": "sql",
        }
        for ext, lang in ext_map.items():
            if file_path.endswith(ext):
                return lang
        return "unknown"

    def _detect_data_handling(self, node: CodeNode, content: str) -> None:
        """Detect what types of data a file handles."""
        content_lower = content.lower()
        
        # PII indicators
        pii_patterns = [
            "email", "phone", "address", "ssn", "social_security",
            "name", "user_name", "first_name", "last_name", "dob",
            "date_of_birth", "password", "credentials",
        ]
        if any(p in content_lower for p in pii_patterns):
            node.data_sensitivity.append(DataSensitivity.PII)
            node.data_types_handled.append("pii")
        
        # PHI indicators (HIPAA)
        phi_patterns = [
            "patient", "medical", "health", "diagnosis", "treatment",
            "prescription", "insurance", "hipaa", "phi",
        ]
        if any(p in content_lower for p in phi_patterns):
            node.data_sensitivity.append(DataSensitivity.PHI)
            node.data_types_handled.append("phi")
        
        # PCI indicators
        pci_patterns = [
            "credit_card", "card_number", "cvv", "expiry", "payment",
            "stripe", "billing", "pan", "cardholder",
        ]
        if any(p in content_lower for p in pci_patterns):
            node.data_sensitivity.append(DataSensitivity.PCI)
            node.data_types_handled.append("pci")
        
        # Financial data
        financial_patterns = [
            "account_number", "balance", "transaction", "bank",
            "routing_number", "wire", "ach",
        ]
        if any(p in content_lower for p in financial_patterns):
            node.data_sensitivity.append(DataSensitivity.FINANCIAL)
            node.data_types_handled.append("financial")

    async def _analyze_python_file(
        self,
        graph: CodebaseGraph,
        file_node: CodeNode,
        content: str,
    ) -> None:
        """Analyze Python file for functions and classes."""
        import re
        
        # Find class definitions
        class_pattern = r'class\s+(\w+)(?:\([^)]*\))?:'
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            class_node = CodeNode(
                node_type=CodeNodeType.CLASS,
                name=class_name,
                qualified_name=f"{file_node.qualified_name}:{class_name}",
                file_path=file_node.file_path,
                start_line=content[:match.start()].count('\n') + 1,
                language="python",
            )
            self._detect_data_handling(class_node, content[match.start():])
            graph.add_node(class_node)
            
            # Link file -> class
            edge = DataFlowEdge(
                source_id=file_node.id,
                target_id=class_node.id,
                flow_type=DataFlowType.CALLS,
                label="contains",
            )
            graph.add_edge(edge)
        
        # Find function definitions
        func_pattern = r'def\s+(\w+)\s*\([^)]*\):'
        for match in re.finditer(func_pattern, content):
            func_name = match.group(1)
            if func_name.startswith('_'):
                continue  # Skip private methods
            
            func_node = CodeNode(
                node_type=CodeNodeType.FUNCTION,
                name=func_name,
                qualified_name=f"{file_node.qualified_name}:{func_name}",
                file_path=file_node.file_path,
                start_line=content[:match.start()].count('\n') + 1,
                language="python",
            )
            self._detect_data_handling(func_node, content[match.start():match.start()+500])
            graph.add_node(func_node)

    async def _analyze_js_file(
        self,
        graph: CodebaseGraph,
        file_node: CodeNode,
        content: str,
    ) -> None:
        """Analyze JavaScript/TypeScript file."""
        import re
        
        # Find function definitions
        func_patterns = [
            r'function\s+(\w+)\s*\(',
            r'const\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>',
            r'const\s+(\w+)\s*=\s*(?:async\s*)?function',
        ]
        
        for pattern in func_patterns:
            for match in re.finditer(pattern, content):
                func_name = match.group(1)
                func_node = CodeNode(
                    node_type=CodeNodeType.FUNCTION,
                    name=func_name,
                    qualified_name=f"{file_node.qualified_name}:{func_name}",
                    file_path=file_node.file_path,
                    start_line=content[:match.start()].count('\n') + 1,
                    language=file_node.language,
                )
                self._detect_data_handling(func_node, content[match.start():match.start()+500])
                graph.add_node(func_node)

    async def _detect_data_flows(self, graph: CodebaseGraph) -> None:
        """Detect data flow patterns in the graph."""
        # Find API endpoints that handle data
        api_nodes = [
            n for n in graph.nodes
            if n.node_type == CodeNodeType.FUNCTION and
            any(d in n.name.lower() for d in ["get", "post", "put", "delete", "create", "update"])
        ]
        
        # Find database-related nodes
        db_nodes = [
            n for n in graph.nodes
            if any(d in n.name.lower() for d in ["query", "insert", "update", "delete", "select", "save"])
        ]
        
        # Create data flows between API and DB nodes
        for api_node in api_nodes:
            for db_node in db_nodes:
                if api_node.file_path == db_node.file_path:
                    # Create edge
                    edge = DataFlowEdge(
                        source_id=api_node.id,
                        target_id=db_node.id,
                        flow_type=DataFlowType.CALLS,
                        data_types=list(set(api_node.data_types_handled + db_node.data_types_handled)),
                        data_sensitivity=list(set(api_node.data_sensitivity + db_node.data_sensitivity)),
                    )
                    graph.add_edge(edge)
        
        # Identify complete data flows
        sensitive_nodes = graph.sensitive_data_nodes
        for node in sensitive_nodes:
            flow = DataFlow(
                name=f"Data flow: {node.name}",
                description=f"Data flow through {node.qualified_name}",
                entry_point=node.id,
                nodes=[node.id],
                data_types=node.data_types_handled,
                data_sensitivity=node.data_sensitivity,
            )
            
            # Trace downstream
            visited = {node.id}
            queue = [node.id]
            while queue:
                current = queue.pop(0)
                for edge in graph.get_outgoing_edges(current):
                    if edge.target_id not in visited:
                        visited.add(edge.target_id)
                        flow.nodes.append(edge.target_id)
                        flow.edges.append(edge.id)
                        queue.append(edge.target_id)
            
            if len(flow.nodes) > 1:
                graph.data_flows.append(flow)

    async def _analyze_compliance(self, graph: CodebaseGraph) -> None:
        """Analyze compliance status of nodes and data flows."""
        for node in graph.nodes:
            issues = []
            
            # Check for unencrypted sensitive data
            if node.data_sensitivity and DataSensitivity.PII in node.data_sensitivity:
                # Check for encryption patterns
                if not any(
                    ann in node.compliance_annotations
                    for ann in ["encrypted", "secure", "protected"]
                ):
                    issues.append("PII may not be encrypted")
            
            if DataSensitivity.PHI in node.data_sensitivity:
                issues.append("PHI handling requires HIPAA compliance review")
            
            if DataSensitivity.PCI in node.data_sensitivity:
                issues.append("PCI data handling requires PCI-DSS compliance review")
            
            node.compliance_issues = issues
        
        # Analyze data flows
        for flow in graph.data_flows:
            if DataSensitivity.PII in flow.data_sensitivity:
                flow.regulations_affected.append("GDPR")
                flow.regulations_affected.append("CCPA")
            
            if DataSensitivity.PHI in flow.data_sensitivity:
                flow.regulations_affected.append("HIPAA")
            
            if DataSensitivity.PCI in flow.data_sensitivity:
                flow.regulations_affected.append("PCI-DSS")
            
            # Calculate compliance score
            total_nodes = len(flow.nodes)
            nodes_with_issues = sum(
                1 for nid in flow.nodes
                if (n := graph.get_node(nid)) and n.compliance_issues
            )
            
            if total_nodes > 0:
                flow.compliance_score = 1.0 - (nodes_with_issues / total_nodes)
                flow.compliance_status = (
                    "compliant" if flow.compliance_score >= 0.9
                    else "partial" if flow.compliance_score >= 0.5
                    else "non_compliant"
                )

    def _apply_layout(self, graph: CodebaseGraph) -> None:
        """Apply layout algorithm to graph nodes."""
        import math
        
        # Group by node type
        type_positions = {
            CodeNodeType.API_ENDPOINT: (0, 0),
            CodeNodeType.FUNCTION: (200, 0),
            CodeNodeType.CLASS: (200, 100),
            CodeNodeType.FILE: (400, 0),
            CodeNodeType.DATABASE_TABLE: (600, 0),
            CodeNodeType.EXTERNAL_SERVICE: (800, 0),
        }
        
        for node_type, nodes in graph._nodes_by_type.items():
            base_x, base_y = type_positions.get(node_type, (300, 200))
            for i, node in enumerate(nodes):
                angle = 2 * math.pi * i / max(1, len(nodes))
                radius = 50 + 10 * (i % 5)
                node.x = base_x + radius * math.cos(angle)
                node.y = base_y + radius * math.sin(angle)

    async def get_graph(self, graph_id: UUID) -> CodebaseGraph | None:
        """Get a graph by ID."""
        return self._graphs.get(graph_id)

    async def export_for_visualization(
        self,
        graph_id: UUID,
    ) -> dict[str, Any]:
        """Export graph for visualization."""
        graph = self._graphs.get(graph_id)
        if not graph:
            raise ValueError(f"Graph not found: {graph_id}")
        
        return {
            "id": str(graph.id),
            "name": graph.name,
            "nodes": [
                {
                    "id": str(n.id),
                    "type": n.node_type.value,
                    "name": n.name,
                    "qualified_name": n.qualified_name,
                    "file_path": n.file_path,
                    "language": n.language,
                    "data_sensitivity": [s.value for s in n.data_sensitivity],
                    "compliance_issues": n.compliance_issues,
                    "x": n.x,
                    "y": n.y,
                    "size": n.size,
                    "color": n.color,
                }
                for n in graph.nodes
            ],
            "edges": [
                {
                    "id": str(e.id),
                    "source": str(e.source_id),
                    "target": str(e.target_id),
                    "type": e.flow_type.value,
                    "data_types": e.data_types,
                    "compliance_status": e.compliance_status,
                }
                for e in graph.edges
            ],
            "data_flows": [
                {
                    "id": str(f.id),
                    "name": f.name,
                    "node_count": len(f.nodes),
                    "data_sensitivity": [s.value for s in f.data_sensitivity],
                    "regulations": f.regulations_affected,
                    "compliance_score": f.compliance_score,
                    "compliance_status": f.compliance_status,
                }
                for f in graph.data_flows
            ],
            "statistics": {
                "node_count": graph.node_count,
                "edge_count": graph.edge_count,
                "data_flow_count": len(graph.data_flows),
                "files_analyzed": graph.files_analyzed,
                "languages": graph.languages,
                "sensitive_nodes": len(graph.sensitive_data_nodes),
            },
        }


# Global instance
_graph_builder: CodebaseGraphBuilder | None = None


def get_codebase_graph_builder() -> CodebaseGraphBuilder:
    """Get or create the codebase graph builder."""
    global _graph_builder
    if _graph_builder is None:
        _graph_builder = CodebaseGraphBuilder()
    return _graph_builder
