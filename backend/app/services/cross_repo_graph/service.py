"""Cross-Repository Compliance Graph Service."""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.cross_repo_graph.models import (
    ComplianceHotspot,
    DependencyEdge,
    DependencyType,
    OrgComplianceGraph,
    RepoNode,
)


logger = structlog.get_logger()

_DEMO_REPOS = [
    RepoNode(
        name="auth-service",
        full_name="org/auth-service",
        score=82.0,
        grade="B",
        violations=5,
        frameworks=["SOC2", "GDPR"],
    ),
    RepoNode(
        name="payment-api",
        full_name="org/payment-api",
        score=71.0,
        grade="C",
        violations=14,
        frameworks=["PCI-DSS", "SOC2"],
    ),
    RepoNode(
        name="user-portal",
        full_name="org/user-portal",
        score=89.5,
        grade="A",
        violations=3,
        frameworks=["GDPR", "HIPAA"],
    ),
    RepoNode(
        name="data-pipeline",
        full_name="org/data-pipeline",
        score=65.0,
        grade="D",
        violations=22,
        frameworks=["HIPAA", "SOC2", "GDPR"],
    ),
    RepoNode(
        name="infra-config",
        full_name="org/infra-config",
        score=91.0,
        grade="A",
        violations=2,
        frameworks=["SOC2", "NIST"],
    ),
    RepoNode(
        name="ml-service",
        full_name="org/ml-service",
        score=74.0,
        grade="C",
        violations=9,
        frameworks=["EU-AI-Act", "GDPR"],
    ),
]

_DEMO_EDGES = [
    DependencyEdge(
        source_repo="org/auth-service",
        target_repo="org/user-portal",
        dependency_type=DependencyType.DIRECT,
        shared_violations=["missing-encryption-at-rest"],
    ),
    DependencyEdge(
        source_repo="org/payment-api",
        target_repo="org/auth-service",
        dependency_type=DependencyType.DIRECT,
        shared_violations=["weak-key-rotation"],
    ),
    DependencyEdge(
        source_repo="org/data-pipeline",
        target_repo="org/payment-api",
        dependency_type=DependencyType.TRANSITIVE,
        shared_violations=["pii-logging"],
    ),
    DependencyEdge(
        source_repo="org/data-pipeline",
        target_repo="org/user-portal",
        dependency_type=DependencyType.SHARED_FRAMEWORK,
        shared_violations=["consent-tracking"],
    ),
    DependencyEdge(
        source_repo="org/infra-config",
        target_repo="org/auth-service",
        dependency_type=DependencyType.SHARED_VENDOR,
        shared_violations=[],
    ),
    DependencyEdge(
        source_repo="org/ml-service",
        target_repo="org/data-pipeline",
        dependency_type=DependencyType.DIRECT,
        shared_violations=["data-retention"],
    ),
]

_DEMO_HOTSPOTS = [
    ComplianceHotspot(
        component="shared-crypto-lib",
        repos_affected=["org/auth-service", "org/payment-api", "org/data-pipeline"],
        severity="high",
        framework="SOC2",
    ),
    ComplianceHotspot(
        component="logging-middleware",
        repos_affected=["org/data-pipeline", "org/user-portal", "org/ml-service"],
        severity="medium",
        framework="GDPR",
    ),
    ComplianceHotspot(
        component="iam-module",
        repos_affected=["org/infra-config", "org/auth-service"],
        severity="high",
        framework="NIST",
    ),
]


class CrossRepoGraphService:
    """Service for building and querying cross-repository compliance graphs."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._nodes: list[RepoNode] = list(_DEMO_REPOS)
        self._edges: list[DependencyEdge] = list(_DEMO_EDGES)
        self._hotspots: list[ComplianceHotspot] = list(_DEMO_HOTSPOTS)

    async def build_org_graph(self, organization_id: str) -> OrgComplianceGraph:
        """Build the full compliance graph for an organization."""
        overall = (
            round(sum(n.score for n in self._nodes) / len(self._nodes), 1) if self._nodes else 0.0
        )
        graph = OrgComplianceGraph(
            organization_id=organization_id,
            nodes=list(self._nodes),
            edges=list(self._edges),
            overall_score=overall,
            hotspots=list(self._hotspots),
        )
        logger.info(
            "Organization graph built",
            organization_id=organization_id,
            nodes=len(self._nodes),
            edges=len(self._edges),
        )
        return graph

    async def get_repo_node(self, full_name: str) -> RepoNode | None:
        """Get a single repository node by full name."""
        return next((n for n in self._nodes if n.full_name == full_name), None)

    async def list_dependencies(self, repo_full_name: str) -> list[DependencyEdge]:
        """List all dependencies for a given repository."""
        return [e for e in self._edges if repo_full_name in (e.source_repo, e.target_repo)]

    async def find_hotspots(self, min_severity: str = "medium") -> list[ComplianceHotspot]:
        """Find compliance hotspots with at least the given severity."""
        severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        min_level = severity_order.get(min_severity, 1)
        return [h for h in self._hotspots if severity_order.get(h.severity, 0) >= min_level]

    async def get_shared_violations(self, repo_a: str, repo_b: str) -> list[str]:
        """Get violations shared between two repositories."""
        violations: list[str] = []
        for edge in self._edges:
            if (edge.source_repo == repo_a and edge.target_repo == repo_b) or (
                edge.source_repo == repo_b and edge.target_repo == repo_a
            ):
                violations.extend(edge.shared_violations)
        return violations

    async def get_aggregated_score(self, organization_id: str) -> dict:
        """Get the aggregated compliance score for the organization."""
        if not self._nodes:
            return {
                "organization_id": organization_id,
                "score": 0.0,
                "grade": "F",
                "total_repos": 0,
            }

        avg_score = round(sum(n.score for n in self._nodes) / len(self._nodes), 1)
        total_violations = sum(n.violations for n in self._nodes)

        if avg_score >= 90:
            grade = "A"
        elif avg_score >= 80:
            grade = "B"
        elif avg_score >= 70:
            grade = "C"
        elif avg_score >= 60:
            grade = "D"
        else:
            grade = "F"

        return {
            "organization_id": organization_id,
            "score": avg_score,
            "grade": grade,
            "total_repos": len(self._nodes),
            "total_violations": total_violations,
        }
