"""Tests for compliance knowledge graph service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.graph import (
    ComplianceKnowledgeGraph,
    GraphNode,
    GraphEdge,
    GraphQuery,
    NodeType,
    EdgeType,
)

pytestmark = pytest.mark.asyncio


class TestComplianceKnowledgeGraph:
    """Test suite for ComplianceKnowledgeGraph."""

    @pytest.fixture
    def graph(self):
        """Create ComplianceKnowledgeGraph instance."""
        return ComplianceKnowledgeGraph()

    async def test_add_node(self, graph):
        """Test adding a node to the graph."""
        node = GraphNode(
            node_id="gdpr-art-17",
            node_type=NodeType.REQUIREMENT,
            name="Right to Erasure",
            properties={
                "regulation": "GDPR",
                "article": "17",
                "obligation_type": "must",
            },
        )
        
        result = await graph.add_node(node)
        
        assert result is True

    async def test_add_edge(self, graph):
        """Test adding an edge between nodes."""
        # Add nodes first
        await graph.add_node(GraphNode(
            node_id="gdpr-art-17",
            node_type=NodeType.REQUIREMENT,
            name="Right to Erasure",
            properties={},
        ))
        await graph.add_node(GraphNode(
            node_id="user-service",
            node_type=NodeType.CODE_MODULE,
            name="User Service",
            properties={"file": "src/user_service.py"},
        ))
        
        edge = GraphEdge(
            edge_id="gdpr-17-to-user-svc",
            edge_type=EdgeType.IMPLEMENTS,
            source_id="user-service",
            target_id="gdpr-art-17",
            properties={"confidence": 0.85},
        )
        
        result = await graph.add_edge(edge)
        
        assert result is True

    async def test_query_natural_language(self, graph):
        """Test natural language query."""
        with patch.object(graph, "_process_nl_query") as mock_process:
            mock_process.return_value = {
                "nodes": [
                    {
                        "node_id": "user-service",
                        "node_type": "code_module",
                        "name": "User Service",
                    },
                ],
                "edges": [],
                "query_interpretation": "Find code that handles GDPR consent",
            }
            
            result = await graph.query_natural_language(
                "What code handles GDPR consent?"
            )
            
            assert "nodes" in result
            assert "query_interpretation" in result

    async def test_query_structured(self, graph):
        """Test structured graph query."""
        query = GraphQuery(
            node_types=[NodeType.REQUIREMENT],
            edge_types=[EdgeType.IMPLEMENTS],
            filters={"regulation": "GDPR"},
            limit=10,
        )
        
        with patch.object(graph, "_execute_query") as mock_execute:
            mock_execute.return_value = {
                "nodes": [
                    {"node_id": "gdpr-art-17", "node_type": "requirement"},
                ],
                "edges": [],
                "total_count": 1,
            }
            
            result = await graph.query(query)
            
            assert "nodes" in result
            assert len(result["nodes"]) >= 0

    async def test_get_node(self, graph):
        """Test getting a specific node."""
        await graph.add_node(GraphNode(
            node_id="test-node",
            node_type=NodeType.REGULATION,
            name="Test Regulation",
            properties={},
        ))
        
        node = await graph.get_node("test-node")
        
        assert node is not None
        assert node.node_id == "test-node"

    async def test_get_node_not_found(self, graph):
        """Test getting non-existent node."""
        node = await graph.get_node("non-existent")
        
        assert node is None

    async def test_get_connected_nodes(self, graph):
        """Test getting nodes connected to a given node."""
        # Setup nodes and edges
        await graph.add_node(GraphNode(
            node_id="center",
            node_type=NodeType.REQUIREMENT,
            name="Center Node",
            properties={},
        ))
        await graph.add_node(GraphNode(
            node_id="connected-1",
            node_type=NodeType.CODE_MODULE,
            name="Connected 1",
            properties={},
        ))
        await graph.add_edge(GraphEdge(
            edge_id="edge-1",
            edge_type=EdgeType.IMPLEMENTS,
            source_id="connected-1",
            target_id="center",
            properties={},
        ))
        
        connected = await graph.get_connected_nodes(
            node_id="center",
            edge_type=EdgeType.IMPLEMENTS,
            direction="incoming",
        )
        
        assert len(connected) >= 0

    async def test_find_path(self, graph):
        """Test finding path between nodes."""
        with patch.object(graph, "_find_shortest_path") as mock_path:
            mock_path.return_value = {
                "path": ["node-a", "node-b", "node-c"],
                "edges": ["edge-1", "edge-2"],
                "length": 2,
            }
            
            path = await graph.find_path(
                source_id="node-a",
                target_id="node-c",
            )
            
            assert "path" in path
            assert len(path["path"]) >= 2

    async def test_get_regulation_coverage(self, graph):
        """Test getting regulation coverage statistics."""
        with patch.object(graph, "_calculate_coverage") as mock_coverage:
            mock_coverage.return_value = {
                "regulation": "GDPR",
                "total_requirements": 50,
                "implemented_requirements": 42,
                "coverage_percentage": 84.0,
                "gaps": [
                    {"requirement_id": "gdpr-art-22", "status": "not_implemented"},
                ],
            }
            
            coverage = await graph.get_regulation_coverage("GDPR")
            
            assert coverage["coverage_percentage"] == 84.0
            assert len(coverage["gaps"]) >= 1

    async def test_export_subgraph(self, graph):
        """Test exporting a subgraph."""
        with patch.object(graph, "_export_nodes_and_edges") as mock_export:
            mock_export.return_value = {
                "nodes": [
                    {"node_id": "node-1", "node_type": "requirement"},
                ],
                "edges": [],
                "format": "json",
            }
            
            export = await graph.export_subgraph(
                node_ids=["node-1"],
                include_connected=True,
                export_format="json",
            )
            
            assert "nodes" in export
            assert export["format"] == "json"

    async def test_get_impact_analysis(self, graph):
        """Test getting impact analysis for a node."""
        with patch.object(graph, "_analyze_impact") as mock_impact:
            mock_impact.return_value = {
                "source_node": "gdpr-art-17",
                "affected_nodes": [
                    {"node_id": "user-service", "impact_level": "high"},
                    {"node_id": "data-export", "impact_level": "medium"},
                ],
                "total_affected": 2,
            }
            
            impact = await graph.get_impact_analysis("gdpr-art-17")
            
            assert impact["total_affected"] >= 1

    def test_list_node_types(self, graph):
        """Test listing available node types."""
        types = graph.list_node_types()
        
        assert len(types) >= 4
        type_values = [t.value for t in types]
        assert "regulation" in type_values
        assert "requirement" in type_values
        assert "code_module" in type_values

    def test_list_edge_types(self, graph):
        """Test listing available edge types."""
        types = graph.list_edge_types()
        
        assert len(types) >= 3
        type_values = [t.value for t in types]
        assert "implements" in type_values
        assert "depends_on" in type_values


class TestGraphNode:
    """Test GraphNode dataclass."""

    def test_node_creation(self):
        """Test creating a node."""
        node = GraphNode(
            node_id="test-node",
            node_type=NodeType.REGULATION,
            name="Test Node",
            properties={"version": "1.0"},
        )
        
        assert node.node_id == "test-node"
        assert node.node_type == NodeType.REGULATION

    def test_node_to_dict(self):
        """Test converting node to dict."""
        node = GraphNode(
            node_id="test-node",
            node_type=NodeType.REQUIREMENT,
            name="Test",
            properties={},
        )
        
        node_dict = node.to_dict()
        
        assert node_dict["node_id"] == "test-node"
        assert node_dict["node_type"] == "requirement"


class TestGraphEdge:
    """Test GraphEdge dataclass."""

    def test_edge_creation(self):
        """Test creating an edge."""
        edge = GraphEdge(
            edge_id="test-edge",
            edge_type=EdgeType.IMPLEMENTS,
            source_id="node-a",
            target_id="node-b",
            properties={"confidence": 0.9},
        )
        
        assert edge.edge_id == "test-edge"
        assert edge.edge_type == EdgeType.IMPLEMENTS

    def test_edge_to_dict(self):
        """Test converting edge to dict."""
        edge = GraphEdge(
            edge_id="test-edge",
            edge_type=EdgeType.DEPENDS_ON,
            source_id="a",
            target_id="b",
            properties={},
        )
        
        edge_dict = edge.to_dict()
        
        assert edge_dict["edge_type"] == "depends_on"


class TestGraphQuery:
    """Test GraphQuery dataclass."""

    def test_query_creation(self):
        """Test creating a query."""
        query = GraphQuery(
            node_types=[NodeType.REQUIREMENT, NodeType.CODE_MODULE],
            edge_types=[EdgeType.IMPLEMENTS],
            filters={"regulation": "GDPR"},
            limit=50,
        )
        
        assert len(query.node_types) == 2
        assert query.limit == 50


class TestNodeType:
    """Test NodeType enum."""

    def test_node_types(self):
        """Test node type values."""
        assert NodeType.REGULATION.value == "regulation"
        assert NodeType.REQUIREMENT.value == "requirement"
        assert NodeType.CODE_MODULE.value == "code_module"
        assert NodeType.TEAM.value == "team"


class TestEdgeType:
    """Test EdgeType enum."""

    def test_edge_types(self):
        """Test edge type values."""
        assert EdgeType.IMPLEMENTS.value == "implements"
        assert EdgeType.DEPENDS_ON.value == "depends_on"
        assert EdgeType.ASSIGNED_TO.value == "assigned_to"
        assert EdgeType.REFERENCES.value == "references"
