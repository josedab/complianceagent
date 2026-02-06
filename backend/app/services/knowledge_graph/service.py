"""Compliance knowledge graph explorer service."""

import re
import time
from collections import deque
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.codebase import CodebaseMapping, Repository
from app.models.regulation import Regulation
from app.models.requirement import Requirement
from app.services.knowledge_graph.models import (
    QUERY_TEMPLATES,
    GraphEdge,
    GraphNode,
    GraphQuery,
    GraphQueryResult,
    KnowledgeGraph,
    NodeType,
    RelationType,
)


logger = structlog.get_logger()


class KnowledgeGraphService:
    """Service for building and querying compliance knowledge graphs."""
    
    def __init__(self, db: AsyncSession, copilot: Any = None):
        self.db = db
        self.copilot = copilot
        self._graphs: dict[UUID, KnowledgeGraph] = {}
    
    async def build_graph(
        self,
        organization_id: UUID,
        name: str = "Compliance Knowledge Graph",
        include_regulations: bool = True,
        include_code: bool = True,
        include_vendors: bool = True,
    ) -> KnowledgeGraph:
        """Build a knowledge graph from the compliance data."""
        graph = KnowledgeGraph(
            organization_id=organization_id,
            name=name,
        )
        
        if include_regulations:
            await self._add_regulations(graph)
        
        if include_code:
            await self._add_code_mappings(graph)
        
        # Store graph
        self._graphs[graph.id] = graph
        
        # Apply layout algorithm
        self._apply_layout(graph)
        
        logger.info(
            "knowledge_graph_built",
            graph_id=str(graph.id),
            nodes=graph.node_count,
            edges=graph.edge_count,
        )
        
        return graph
    
    async def _add_regulations(self, graph: KnowledgeGraph) -> None:
        """Add regulations and requirements to the graph."""
        stmt = select(Regulation).options(selectinload(Regulation.requirements))
        result = await self.db.execute(stmt)
        regulations = result.scalars().all()
        
        for regulation in regulations:
            # Create regulation node
            reg_node = GraphNode(
                node_type=NodeType.REGULATION,
                name=regulation.name,
                description=regulation.description or "",
                external_id=str(regulation.id),
                source="database",
                properties={
                    "jurisdiction": regulation.jurisdiction,
                    "version": regulation.version,
                    "effective_date": regulation.effective_date.isoformat() if regulation.effective_date else None,
                },
                group="regulations",
                color="#4CAF50",
                size=2.0,
            )
            graph.add_node(reg_node)
            
            # Add requirement nodes
            for req in regulation.requirements:
                req_node = GraphNode(
                    node_type=NodeType.REQUIREMENT,
                    name=req.title or f"Req {req.requirement_number}",
                    description=req.description or "",
                    external_id=str(req.id),
                    source="database",
                    properties={
                        "requirement_number": req.requirement_number,
                        "category": req.category,
                        "priority": req.priority,
                    },
                    group="requirements",
                    color="#2196F3",
                    size=1.5,
                )
                graph.add_node(req_node)
                
                # Link regulation -> requirement
                edge = GraphEdge(
                    source_id=reg_node.id,
                    target_id=req_node.id,
                    relation_type=RelationType.CONTAINS,
                    weight=1.0,
                )
                graph.add_edge(edge)
    
    async def _add_code_mappings(self, graph: KnowledgeGraph) -> None:
        """Add code mappings to the graph."""
        stmt = select(CodebaseMapping).options(selectinload(CodebaseMapping.requirement))
        result = await self.db.execute(stmt)
        mappings = result.scalars().all()
        
        # Track code files to avoid duplicates
        file_nodes: dict[str, GraphNode] = {}
        
        for mapping in mappings:
            # Create or get code file node
            file_key = f"{mapping.repository_id}:{mapping.file_path}"
            
            if file_key not in file_nodes:
                file_node = GraphNode(
                    node_type=NodeType.CODE_FILE,
                    name=mapping.file_path.split("/")[-1],
                    description=f"File: {mapping.file_path}",
                    external_id=file_key,
                    properties={
                        "file_path": mapping.file_path,
                        "repository_id": str(mapping.repository_id),
                    },
                    group="code",
                    color="#FF9800",
                    size=1.0,
                )
                graph.add_node(file_node)
                file_nodes[file_key] = file_node
            else:
                file_node = file_nodes[file_key]
            
            # Find the requirement node and link
            if mapping.requirement_id:
                for node in graph.nodes_by_type.get(NodeType.REQUIREMENT, []):
                    if node.external_id == str(mapping.requirement_id):
                        edge = GraphEdge(
                            source_id=node.id,
                            target_id=file_node.id,
                            relation_type=RelationType.IMPLEMENTS,
                            weight=1.0,
                            properties={
                                "compliance_status": mapping.compliance_status.value if mapping.compliance_status else "unknown",
                                "start_line": mapping.start_line,
                                "end_line": mapping.end_line,
                            },
                        )
                        graph.add_edge(edge)
                        break
    
    def _apply_layout(self, graph: KnowledgeGraph) -> None:
        """Apply a force-directed layout to the graph nodes."""
        import math
        import random
        
        # Group nodes by type for initial positioning
        type_positions = {
            NodeType.REGULATION: (0, 0),
            NodeType.REQUIREMENT: (200, 0),
            NodeType.CODE_FILE: (400, 0),
            NodeType.FUNCTION: (500, 0),
            NodeType.DATA_ELEMENT: (300, 200),
            NodeType.VENDOR: (100, 200),
            NodeType.RISK: (200, 300),
            NodeType.CONTROL: (150, 100),
            NodeType.EVIDENCE: (350, 100),
        }
        
        for node_type, nodes in graph.nodes_by_type.items():
            base_x, base_y = type_positions.get(node_type, (250, 150))
            for i, node in enumerate(nodes):
                angle = 2 * math.pi * i / max(1, len(nodes))
                radius = 50 + 10 * i
                node.x = base_x + radius * math.cos(angle)
                node.y = base_y + radius * math.sin(angle)
    
    async def query(
        self,
        graph_id: UUID,
        query: GraphQuery,
    ) -> GraphQueryResult:
        """Execute a query on the knowledge graph."""
        start_time = time.time()
        
        graph = self._graphs.get(graph_id)
        if not graph:
            raise ValueError(f"Graph not found: {graph_id}")
        
        result = GraphQueryResult(query_id=query.id)
        
        # Natural language query processing
        if query.natural_query:
            parsed = self._parse_natural_query(query.natural_query)
            query.node_types.extend(parsed.get("node_types", []))
            query.keywords.extend(parsed.get("keywords", []))
        
        # Find matching nodes
        matched_nodes = self._find_matching_nodes(graph, query)
        
        # If start nodes specified, do traversal
        if query.start_nodes:
            result = self._traverse_from_nodes(graph, query.start_nodes, query)
        else:
            # Return matched nodes with their edges
            node_ids = {n.id for n in matched_nodes}
            result.nodes = matched_nodes
            result.edges = [
                e for e in graph.edges
                if e.source_id in node_ids and e.target_id in node_ids
            ]
        
        result.total_nodes = len(result.nodes)
        result.total_edges = len(result.edges)
        result.execution_time_ms = (time.time() - start_time) * 1000
        
        # Generate natural language answer
        if self.copilot and query.natural_query:
            result.natural_answer = await self._generate_answer(query, result)
        else:
            result.natural_answer = self._generate_simple_answer(query, result)
        
        return result
    
    def _parse_natural_query(self, query: str) -> dict:
        """Parse natural language query into structured components."""
        query_lower = query.lower()
        
        parsed = {
            "node_types": [],
            "keywords": [],
        }
        
        # Detect node types from query
        type_keywords = {
            "regulation": NodeType.REGULATION,
            "law": NodeType.REGULATION,
            "gdpr": NodeType.REGULATION,
            "hipaa": NodeType.REGULATION,
            "requirement": NodeType.REQUIREMENT,
            "control": NodeType.CONTROL,
            "code": NodeType.CODE_FILE,
            "file": NodeType.CODE_FILE,
            "function": NodeType.FUNCTION,
            "data": NodeType.DATA_ELEMENT,
            "vendor": NodeType.VENDOR,
            "risk": NodeType.RISK,
            "evidence": NodeType.EVIDENCE,
        }
        
        for keyword, node_type in type_keywords.items():
            if keyword in query_lower:
                if node_type not in parsed["node_types"]:
                    parsed["node_types"].append(node_type)
        
        # Extract other keywords
        stop_words = {"the", "a", "an", "is", "are", "how", "what", "which", "where", "show", "find", "list"}
        words = re.findall(r'\b\w+\b', query_lower)
        for word in words:
            if word not in stop_words and len(word) > 2:
                parsed["keywords"].append(word)
        
        return parsed
    
    def _find_matching_nodes(
        self,
        graph: KnowledgeGraph,
        query: GraphQuery,
    ) -> list[GraphNode]:
        """Find nodes matching the query criteria."""
        matched = []
        
        for node in graph.nodes:
            # Filter by node type
            if query.node_types and node.node_type not in query.node_types:
                continue
            
            # Keyword matching
            if query.keywords:
                text = f"{node.name} {node.description}".lower()
                if not any(kw in text for kw in query.keywords):
                    continue
            
            # Property filters
            if query.filters:
                matches_filters = True
                for key, value in query.filters.items():
                    if node.properties.get(key) != value:
                        matches_filters = False
                        break
                if not matches_filters:
                    continue
            
            matched.append(node)
            
            if len(matched) >= query.max_results:
                break
        
        return matched
    
    def _traverse_from_nodes(
        self,
        graph: KnowledgeGraph,
        start_ids: list[UUID],
        query: GraphQuery,
    ) -> GraphQueryResult:
        """Traverse graph from starting nodes using BFS."""
        result = GraphQueryResult(query_id=query.id)
        
        visited = set(start_ids)
        queue = deque([(nid, 0) for nid in start_ids])
        
        while queue:
            node_id, depth = queue.popleft()
            
            if depth > query.max_depth:
                continue
            
            node = graph.nodes_by_id.get(node_id)
            if node:
                result.nodes.append(node)
            
            # Find connected edges and nodes
            for edge in graph.edges:
                next_id = None
                if edge.source_id == node_id:
                    next_id = edge.target_id
                elif edge.target_id == node_id:
                    next_id = edge.source_id
                
                if next_id and next_id not in visited:
                    # Check relation type filter
                    if query.relation_types and edge.relation_type not in query.relation_types:
                        continue
                    
                    visited.add(next_id)
                    queue.append((next_id, depth + 1))
                    result.edges.append(edge)
        
        return result
    
    async def _generate_answer(
        self,
        query: GraphQuery,
        result: GraphQueryResult,
    ) -> str:
        """Generate natural language answer using Copilot."""
        if not self.copilot:
            return self._generate_simple_answer(query, result)
        
        context = f"""
        Query: {query.natural_query}
        
        Found {result.total_nodes} relevant nodes and {result.total_edges} relationships.
        
        Node types: {', '.join(set(n.node_type.value for n in result.nodes[:20]))}
        
        Key nodes:
        {chr(10).join(f'- {n.name} ({n.node_type.value})' for n in result.nodes[:10])}
        """
        
        try:
            response = await self.copilot.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a compliance knowledge expert. Provide a concise answer based on the graph data."},
                    {"role": "user", "content": context}
                ],
                model="gpt-4o-mini",
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("copilot_answer_failed", error=str(e))
            return self._generate_simple_answer(query, result)
    
    def _generate_simple_answer(
        self,
        query: GraphQuery,
        result: GraphQueryResult,
    ) -> str:
        """Generate a simple answer without AI."""
        if not result.nodes:
            return "No matching nodes found for your query."
        
        node_summary = {}
        for node in result.nodes:
            node_type = node.node_type.value
            node_summary[node_type] = node_summary.get(node_type, 0) + 1
        
        summary_parts = [f"{count} {ntype}(s)" for ntype, count in node_summary.items()]
        
        return f"Found {', '.join(summary_parts)} related to your query."
    
    async def get_graph(self, graph_id: UUID) -> KnowledgeGraph | None:
        """Get a graph by ID."""
        return self._graphs.get(graph_id)
    
    async def get_node_details(
        self,
        graph_id: UUID,
        node_id: UUID,
    ) -> dict | None:
        """Get detailed information about a node."""
        graph = self._graphs.get(graph_id)
        if not graph:
            return None
        
        node = graph.nodes_by_id.get(node_id)
        if not node:
            return None
        
        # Get connected nodes
        neighbors = graph.get_neighbors(node_id)
        
        # Get edges
        edges = [
            e for e in graph.edges
            if e.source_id == node_id or e.target_id == node_id
        ]
        
        return {
            "node": node,
            "neighbors": neighbors,
            "edges": edges,
            "neighbor_count": len(neighbors),
        }
    
    async def find_path(
        self,
        graph_id: UUID,
        source_id: UUID,
        target_id: UUID,
        max_depth: int = 5,
    ) -> list[list[UUID]]:
        """Find paths between two nodes."""
        graph = self._graphs.get(graph_id)
        if not graph:
            return []
        
        paths = []
        
        def dfs(current: UUID, target: UUID, path: list[UUID], depth: int):
            if depth > max_depth:
                return
            
            if current == target:
                paths.append(path.copy())
                return
            
            for edge in graph.edges:
                next_id = None
                if edge.source_id == current:
                    next_id = edge.target_id
                elif edge.target_id == current:
                    next_id = edge.source_id
                
                if next_id and next_id not in path:
                    path.append(next_id)
                    dfs(next_id, target, path, depth + 1)
                    path.pop()
        
        dfs(source_id, target_id, [source_id], 0)
        
        return paths[:10]
    
    async def get_query_templates(self) -> dict:
        """Get available query templates."""
        return QUERY_TEMPLATES
    
    async def export_for_visualization(
        self,
        graph_id: UUID,
    ) -> dict:
        """Export graph in a format suitable for visualization libraries."""
        graph = self._graphs.get(graph_id)
        if not graph:
            raise ValueError(f"Graph not found: {graph_id}")
        
        return {
            "nodes": [
                {
                    "id": str(n.id),
                    "label": n.name,
                    "type": n.node_type.value,
                    "group": n.group,
                    "x": n.x,
                    "y": n.y,
                    "size": n.size,
                    "color": n.color,
                    "properties": n.properties,
                }
                for n in graph.nodes
            ],
            "edges": [
                {
                    "id": str(e.id),
                    "source": str(e.source_id),
                    "target": str(e.target_id),
                    "type": e.relation_type.value,
                    "weight": e.weight,
                }
                for e in graph.edges
            ],
            "statistics": {
                "total_nodes": graph.node_count,
                "total_edges": graph.edge_count,
                "node_types": {
                    nt.value: len(nodes)
                    for nt, nodes in graph.nodes_by_type.items()
                },
            },
        }
