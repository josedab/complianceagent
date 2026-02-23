"""Cross-Repository Compliance Graph models."""

from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4


class DependencyType(str, Enum):
    """Types of dependencies between repositories."""

    DIRECT = "direct"
    TRANSITIVE = "transitive"
    SHARED_FRAMEWORK = "shared_framework"
    SHARED_VENDOR = "shared_vendor"


@dataclass
class RepoNode:
    """A repository node in the compliance graph."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    full_name: str = ""
    score: float = 0.0
    grade: str = "C"
    violations: int = 0
    frameworks: list[str] = field(default_factory=list)


@dataclass
class DependencyEdge:
    """An edge representing a dependency between two repositories."""

    source_repo: str = ""
    target_repo: str = ""
    dependency_type: DependencyType = DependencyType.DIRECT
    shared_violations: list[str] = field(default_factory=list)


@dataclass
class ComplianceHotspot:
    """A compliance hotspot affecting multiple repositories."""

    component: str = ""
    repos_affected: list[str] = field(default_factory=list)
    severity: str = "medium"
    framework: str = ""


@dataclass
class OrgComplianceGraph:
    """Organization-wide compliance graph."""

    organization_id: str = ""
    nodes: list[RepoNode] = field(default_factory=list)
    edges: list[DependencyEdge] = field(default_factory=list)
    overall_score: float = 0.0
    hotspots: list[ComplianceHotspot] = field(default_factory=list)
