"""Compliance DAO Governance models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID


class ProposalStatus(str, Enum):
    """Status of a governance proposal."""

    DRAFT = "draft"
    ACTIVE = "active"
    PASSED = "passed"
    REJECTED = "rejected"
    EXECUTED = "executed"
    EXPIRED = "expired"


class ProposalType(str, Enum):
    """Type of governance proposal."""

    POLICY_CHANGE = "policy_change"
    FRAMEWORK_ADDITION = "framework_addition"
    THRESHOLD_UPDATE = "threshold_update"
    MEMBER_ADMISSION = "member_admission"
    BUDGET_ALLOCATION = "budget_allocation"
    EMERGENCY_ACTION = "emergency_action"


class VoteChoice(str, Enum):
    """Voting options."""

    FOR = "for"
    AGAINST = "against"
    ABSTAIN = "abstain"


@dataclass
class GovernanceMember:
    """A member of the compliance DAO."""

    id: UUID
    organization: str
    display_name: str
    voting_power: float = 1.0
    reputation_score: float = 50.0
    proposals_created: int = 0
    votes_cast: int = 0
    joined_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Vote:
    """A single vote on a proposal."""

    id: UUID
    proposal_id: UUID
    member_id: UUID
    choice: VoteChoice
    voting_power: float
    rationale: str = ""
    cast_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class GovernanceProposal:
    """A governance proposal for compliance policy changes."""

    id: UUID
    title: str
    description: str
    proposal_type: ProposalType
    status: ProposalStatus = ProposalStatus.DRAFT
    proposer_id: UUID | None = None
    proposer_org: str = ""
    affected_frameworks: list[str] = field(default_factory=list)
    changes_summary: str = ""
    votes_for: float = 0.0
    votes_against: float = 0.0
    votes_abstain: float = 0.0
    total_voters: int = 0
    quorum_required: float = 0.6
    approval_threshold: float = 0.66
    voting_period_hours: int = 48
    created_at: datetime = field(default_factory=datetime.utcnow)
    voting_ends_at: datetime | None = None
    executed_at: datetime | None = None
    execution_hash: str = ""
    votes: list[Vote] = field(default_factory=list)


@dataclass
class GovernanceStats:
    """Aggregate governance statistics."""

    total_proposals: int = 0
    active_proposals: int = 0
    passed_proposals: int = 0
    rejected_proposals: int = 0
    total_members: int = 0
    total_votes_cast: int = 0
    average_participation_rate: float = 0.0
    average_approval_rate: float = 0.0
