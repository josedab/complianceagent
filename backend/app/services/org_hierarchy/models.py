"""Multi-Tenant Organization Hierarchy models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class OrgNodeType(str, Enum):
    ROOT = "root"
    BUSINESS_UNIT = "business_unit"
    DEPARTMENT = "department"
    TEAM = "team"
    PROJECT = "project"


class OrgRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    COMPLIANCE_OFFICER = "compliance_officer"
    DEVELOPER = "developer"
    AUDITOR = "auditor"
    VIEWER = "viewer"


class PolicyInheritance(str, Enum):
    INHERIT = "inherit"
    OVERRIDE = "override"
    MERGE = "merge"


@dataclass
class OrgNode:
    """A node in the organization hierarchy."""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    slug: str = ""
    node_type: OrgNodeType = OrgNodeType.TEAM
    parent_id: UUID | None = None
    depth: int = 0
    policy_inheritance: PolicyInheritance = PolicyInheritance.INHERIT
    policies: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    created_at: datetime | None = None


@dataclass
class OrgMembership:
    """A user's membership in an org node."""
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    user_email: str = ""
    org_node_id: UUID = field(default_factory=uuid4)
    role: OrgRole = OrgRole.VIEWER
    inherited_roles: list[OrgRole] = field(default_factory=list)
    created_at: datetime | None = None


@dataclass
class OrgTree:
    """Flattened organization tree for display."""
    root: OrgNode | None = None
    nodes: list[OrgNode] = field(default_factory=list)
    total_members: int = 0
    total_repositories: int = 0
    max_depth: int = 0


@dataclass
class AggregatedCompliance:
    """Aggregated compliance stats across org nodes."""
    org_node_id: UUID = field(default_factory=uuid4)
    org_node_name: str = ""
    overall_score: float = 0.0
    children_scores: dict[str, float] = field(default_factory=dict)
    violation_count: int = 0
    repository_count: int = 0
    computed_at: datetime | None = None
