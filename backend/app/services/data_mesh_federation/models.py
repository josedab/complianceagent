"""Data models for Data Mesh Federation Service."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class FederationRole(str, Enum):
    """Role of a node in the federation."""

    COORDINATOR = "coordinator"
    PARTICIPANT = "participant"
    OBSERVER = "observer"


class DataSharingPolicy(str, Enum):
    """Data sharing policy for federation nodes."""

    OPEN = "open"
    SELECTIVE = "selective"
    RESTRICTED = "restricted"


class ProofType(str, Enum):
    """Type of cryptographic proof for shared insights."""

    ZERO_KNOWLEDGE = "zero_knowledge"
    HASH_COMMITMENT = "hash_commitment"
    DIFFERENTIAL_PRIVACY = "differential_privacy"


@dataclass
class FederationNode:
    """A node participating in the data mesh federation."""

    id: UUID = field(default_factory=uuid4)
    org_name: str = ""
    role: FederationRole = FederationRole.PARTICIPANT
    endpoint_url: str = ""
    public_key: str = ""
    data_policies: list[DataSharingPolicy] = field(default_factory=list)
    joined_at: datetime | None = None


@dataclass
class SharedInsight:
    """An insight shared across the federation."""

    id: UUID = field(default_factory=uuid4)
    source_node_id: UUID = field(default_factory=uuid4)
    insight_type: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    proof_type: ProofType = ProofType.ZERO_KNOWLEDGE
    proof_hash: str = ""
    contributed_at: datetime | None = None


@dataclass
class FederationNetwork:
    """A federation network containing multiple nodes."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    nodes: list[FederationNode] = field(default_factory=list)
    insights_shared: int = 0
    created_at: datetime | None = None


@dataclass
class FederationStats:
    """Statistics for the federation network."""

    total_nodes: int = 0
    active_nodes: int = 0
    insights_shared: int = 0
    by_insight_type: dict[str, int] = field(default_factory=dict)
    proof_verifications: int = 0
