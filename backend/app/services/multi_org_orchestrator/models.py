"""Multi-organization orchestrator models."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class OrgRelation(str, Enum):
    """Relationship type between organizations."""

    parent = "parent"
    subsidiary = "subsidiary"
    division = "division"
    joint_venture = "joint_venture"
    acquisition = "acquisition"


class PolicyInheritance(str, Enum):
    """How policies are inherited between entities."""

    inherit = "inherit"
    override = "override"
    merge = "merge"
    none = "none"


@dataclass
class OrgEntity:
    """An organization entity within a hierarchy."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = ""
    parent_id: uuid.UUID | None = None
    relation: OrgRelation = OrgRelation.subsidiary
    compliance_score: float = 0.0
    frameworks: list[str] = field(default_factory=list)
    policies: list[str] = field(default_factory=list)
    created_at: datetime | None = None


@dataclass
class OrgHierarchy:
    """A complete organizational hierarchy."""

    root_id: uuid.UUID = field(default_factory=uuid.uuid4)
    entities: list[OrgEntity] = field(default_factory=list)
    total_entities: int = 0
    avg_score: float = 0.0
    lowest_score: float = 0.0


@dataclass
class PolicyPropagation:
    """Record of a policy propagated between entities."""

    source_entity_id: uuid.UUID = field(default_factory=uuid.uuid4)
    target_entity_id: uuid.UUID = field(default_factory=uuid.uuid4)
    policy_name: str = ""
    inheritance: PolicyInheritance = PolicyInheritance.inherit
    applied: bool = True


@dataclass
class ConsolidatedReport:
    """Consolidated compliance report across entities."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    hierarchy_name: str = ""
    entities: list[dict] = field(default_factory=list)
    overall_score: float = 0.0
    gaps: list[dict] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    generated_at: datetime | None = None


@dataclass
class MultiOrgStats:
    """Aggregate statistics for multi-org orchestration."""

    total_entities: int = 0
    hierarchies: int = 0
    policies_propagated: int = 0
    avg_score: float = 0.0
    compliance_gaps: int = 0
