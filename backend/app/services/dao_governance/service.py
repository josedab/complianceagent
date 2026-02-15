"""Compliance DAO Governance service."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from uuid import UUID, uuid4

import structlog

from app.services.dao_governance.models import (
    GovernanceMember,
    GovernanceProposal,
    GovernanceStats,
    ProposalStatus,
    ProposalType,
    Vote,
    VoteChoice,
)

logger = structlog.get_logger()

_proposals: list[GovernanceProposal] = []
_members: list[GovernanceMember] = []


def _seed_data() -> None:
    """Seed initial governance data."""
    if _proposals:
        return

    m1 = GovernanceMember(
        id=uuid4(), organization="Acme Corp", display_name="Alice Chen",
        voting_power=2.0, reputation_score=85.0, proposals_created=3, votes_cast=12,
    )
    m2 = GovernanceMember(
        id=uuid4(), organization="TechStartup Inc", display_name="Bob Martinez",
        voting_power=1.5, reputation_score=72.0, proposals_created=1, votes_cast=8,
    )
    m3 = GovernanceMember(
        id=uuid4(), organization="FinanceHQ", display_name="Carol Wang",
        voting_power=1.8, reputation_score=90.0, proposals_created=2, votes_cast=15,
    )
    _members.extend([m1, m2, m3])

    p1_id = uuid4()
    _proposals.append(GovernanceProposal(
        id=p1_id, title="Add EU AI Act Framework Support",
        description="Proposal to add comprehensive EU AI Act compliance framework including risk classification, transparency requirements, and conformity assessment procedures.",
        proposal_type=ProposalType.FRAMEWORK_ADDITION,
        status=ProposalStatus.ACTIVE,
        proposer_id=m1.id, proposer_org="Acme Corp",
        affected_frameworks=["EU AI Act", "GDPR"],
        changes_summary="Add 47 new controls for AI system compliance across risk categories.",
        votes_for=3.5, votes_against=0.5, votes_abstain=0.3, total_voters=3,
        voting_period_hours=48,
        voting_ends_at=datetime.utcnow() + timedelta(hours=36),
    ))
    _proposals.append(GovernanceProposal(
        id=uuid4(), title="Increase PCI-DSS Violation Threshold",
        description="Raise the minimum confidence threshold for PCI-DSS violation detection from 70% to 85% to reduce false positives in payment processing code.",
        proposal_type=ProposalType.THRESHOLD_UPDATE,
        status=ProposalStatus.PASSED,
        proposer_id=m3.id, proposer_org="FinanceHQ",
        affected_frameworks=["PCI-DSS"],
        changes_summary="Update confidence threshold from 0.70 to 0.85 for PCI-DSS rules.",
        votes_for=4.8, votes_against=0.5, total_voters=4,
        executed_at=datetime.utcnow() - timedelta(days=3),
        execution_hash=hashlib.sha256(b"pci-threshold-update").hexdigest()[:16],
    ))
    _proposals.append(GovernanceProposal(
        id=uuid4(), title="Emergency: Disable Flawed HIPAA Rule",
        description="Emergency proposal to disable HIPAA-PHI-017 rule that generates false positives on anonymized research data sets.",
        proposal_type=ProposalType.EMERGENCY_ACTION,
        status=ProposalStatus.ACTIVE,
        proposer_id=m2.id, proposer_org="TechStartup Inc",
        affected_frameworks=["HIPAA"],
        changes_summary="Temporarily disable HIPAA-PHI-017 pending investigation.",
        votes_for=1.5, votes_against=2.0, total_voters=2,
        voting_period_hours=24,
        voting_ends_at=datetime.utcnow() + timedelta(hours=12),
    ))


class DAOGovernanceService:
    """Service for compliance DAO governance."""

    def __init__(self) -> None:
        _seed_data()

    async def list_proposals(
        self, status: ProposalStatus | None = None,
    ) -> list[GovernanceProposal]:
        if status:
            return [p for p in _proposals if p.status == status]
        return list(_proposals)

    async def get_proposal(self, proposal_id: UUID) -> GovernanceProposal | None:
        return next((p for p in _proposals if p.id == proposal_id), None)

    async def create_proposal(
        self, title: str, description: str,
        proposal_type: ProposalType,
        affected_frameworks: list[str],
        changes_summary: str,
    ) -> GovernanceProposal:
        if not title or not title.strip():
            raise ValueError("Proposal title must not be empty")
        if not description or not description.strip():
            raise ValueError("Proposal description must not be empty")
        proposal = GovernanceProposal(
            id=uuid4(), title=title, description=description,
            proposal_type=proposal_type,
            status=ProposalStatus.ACTIVE,
            affected_frameworks=affected_frameworks,
            changes_summary=changes_summary,
            voting_ends_at=datetime.utcnow() + timedelta(hours=48),
        )
        _proposals.append(proposal)
        logger.info("dao.proposal_created", proposal_id=str(proposal.id), title=title)
        return proposal

    async def cast_vote(
        self, proposal_id: UUID, member_id: UUID,
        choice: VoteChoice, rationale: str = "",
    ) -> Vote:
        proposal = await self.get_proposal(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")
        if proposal.status != ProposalStatus.ACTIVE:
            raise ValueError(f"Proposal {proposal_id} is not active (status: {proposal.status.value})")

        existing_vote = next((v for v in proposal.votes if v.member_id == member_id), None)
        if existing_vote:
            raise ValueError(f"Member {member_id} has already voted on proposal {proposal_id}")

        member = next((m for m in _members if m.id == member_id), None)
        if not member:
            logger.warning("dao.unknown_member", member_id=str(member_id), default_power=1.0)
        power = member.voting_power if member else 1.0

        vote = Vote(
            id=uuid4(), proposal_id=proposal_id, member_id=member_id,
            choice=choice, voting_power=power, rationale=rationale,
        )
        proposal.votes.append(vote)
        proposal.total_voters += 1
        if choice == VoteChoice.FOR:
            proposal.votes_for += power
        elif choice == VoteChoice.AGAINST:
            proposal.votes_against += power
        else:
            proposal.votes_abstain += power

        total = proposal.votes_for + proposal.votes_against + proposal.votes_abstain
        if proposal.votes_for / max(total, 1) >= proposal.approval_threshold:
            proposal.status = ProposalStatus.PASSED

        logger.info("dao.vote_cast", proposal_id=str(proposal_id), choice=choice.value)
        return vote

    async def get_members(self) -> list[GovernanceMember]:
        return list(_members)

    async def get_stats(self) -> GovernanceStats:
        active = sum(1 for p in _proposals if p.status == ProposalStatus.ACTIVE)
        passed = sum(1 for p in _proposals if p.status in (ProposalStatus.PASSED, ProposalStatus.EXECUTED))
        rejected = sum(1 for p in _proposals if p.status == ProposalStatus.REJECTED)
        total_votes = sum(p.total_voters for p in _proposals)
        return GovernanceStats(
            total_proposals=len(_proposals),
            active_proposals=active,
            passed_proposals=passed,
            rejected_proposals=rejected,
            total_members=len(_members),
            total_votes_cast=total_votes,
            average_participation_rate=0.78,
            average_approval_rate=passed / max(len(_proposals), 1),
        )
