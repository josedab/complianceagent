"""API endpoints for Compliance DAO Governance."""

from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.services.dao_governance import (
    DAOGovernanceService,
    ProposalStatus,
    ProposalType,
    VoteChoice,
)

logger = structlog.get_logger()
router = APIRouter()


# --- Request Models ---

class CreateProposalRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500, description="Proposal title")
    description: str = Field(..., min_length=1, max_length=5000, description="Detailed description of the proposal")
    proposal_type: str = Field(..., min_length=1, description="Type: policy_change, framework_addition, threshold_update, member_admission, budget_allocation, emergency_action")
    affected_frameworks: list[str] = Field(default_factory=list, description="Affected compliance frameworks")
    changes_summary: str = Field("", description="Summary of proposed changes")


class CastVoteRequest(BaseModel):
    member_id: str = Field(..., min_length=1, description="Voting member ID")
    choice: str = Field(..., min_length=1, description="Vote choice: for, against, abstain")
    rationale: str = Field("", max_length=5000, description="Rationale for the vote")


# --- Response Models ---

class VoteSchema(BaseModel):
    id: str
    proposal_id: str
    member_id: str
    choice: str
    voting_power: float
    rationale: str
    cast_at: str


class ProposalSchema(BaseModel):
    id: str
    title: str
    description: str
    proposal_type: str
    status: str
    proposer_org: str
    affected_frameworks: list[str]
    changes_summary: str
    votes_for: float
    votes_against: float
    votes_abstain: float
    total_voters: int
    quorum_required: float
    approval_threshold: float
    voting_period_hours: int
    created_at: str
    voting_ends_at: str | None
    execution_hash: str


class MemberSchema(BaseModel):
    id: str
    organization: str
    display_name: str
    voting_power: float
    reputation_score: float
    proposals_created: int
    votes_cast: int


class GovernanceStatsSchema(BaseModel):
    total_proposals: int
    active_proposals: int
    passed_proposals: int
    rejected_proposals: int
    total_members: int
    total_votes_cast: int
    average_participation_rate: float
    average_approval_rate: float


# --- Endpoints ---

@router.get("/proposals", response_model=list[ProposalSchema])
async def list_proposals(
    status_filter: str | None = Query(None, alias="status"),
) -> list[dict]:
    svc = DAOGovernanceService()
    ps = None
    if status_filter:
        try:
            ps = ProposalStatus(status_filter)
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Invalid status: {status_filter}")
    proposals = await svc.list_proposals(status=ps)
    return [
        {
            "id": str(p.id), "title": p.title, "description": p.description,
            "proposal_type": p.proposal_type.value, "status": p.status.value,
            "proposer_org": p.proposer_org, "affected_frameworks": p.affected_frameworks,
            "changes_summary": p.changes_summary, "votes_for": p.votes_for,
            "votes_against": p.votes_against, "votes_abstain": p.votes_abstain,
            "total_voters": p.total_voters, "quorum_required": p.quorum_required,
            "approval_threshold": p.approval_threshold, "voting_period_hours": p.voting_period_hours,
            "created_at": p.created_at.isoformat(), "voting_ends_at": p.voting_ends_at.isoformat() if p.voting_ends_at else None,
            "execution_hash": p.execution_hash,
        }
        for p in proposals
    ]


@router.post("/proposals", response_model=ProposalSchema, status_code=status.HTTP_201_CREATED)
async def create_proposal(req: CreateProposalRequest) -> dict:
    svc = DAOGovernanceService()
    try:
        proposal_type = ProposalType(req.proposal_type)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid proposal_type: {req.proposal_type}")
    p = await svc.create_proposal(
        title=req.title, description=req.description,
        proposal_type=proposal_type,
        affected_frameworks=req.affected_frameworks,
        changes_summary=req.changes_summary,
    )
    return {
        "id": str(p.id), "title": p.title, "description": p.description,
        "proposal_type": p.proposal_type.value, "status": p.status.value,
        "proposer_org": p.proposer_org, "affected_frameworks": p.affected_frameworks,
        "changes_summary": p.changes_summary, "votes_for": p.votes_for,
        "votes_against": p.votes_against, "votes_abstain": p.votes_abstain,
        "total_voters": p.total_voters, "quorum_required": p.quorum_required,
        "approval_threshold": p.approval_threshold, "voting_period_hours": p.voting_period_hours,
        "created_at": p.created_at.isoformat(), "voting_ends_at": p.voting_ends_at.isoformat() if p.voting_ends_at else None,
        "execution_hash": p.execution_hash,
    }


@router.post("/proposals/{proposal_id}/vote", response_model=VoteSchema)
async def cast_vote(proposal_id: UUID, req: CastVoteRequest) -> dict:
    svc = DAOGovernanceService()
    try:
        choice = VoteChoice(req.choice)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid vote choice: {req.choice}")
    try:
        v = await svc.cast_vote(
            proposal_id=proposal_id, member_id=UUID(req.member_id),
            choice=choice, rationale=req.rationale,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "id": str(v.id), "proposal_id": str(v.proposal_id),
        "member_id": str(v.member_id), "choice": v.choice.value,
        "voting_power": v.voting_power, "rationale": v.rationale,
        "cast_at": v.cast_at.isoformat(),
    }


@router.get("/members", response_model=list[MemberSchema])
async def list_members() -> list[dict]:
    svc = DAOGovernanceService()
    members = await svc.get_members()
    return [
        {"id": str(m.id), "organization": m.organization, "display_name": m.display_name,
         "voting_power": m.voting_power, "reputation_score": m.reputation_score,
         "proposals_created": m.proposals_created, "votes_cast": m.votes_cast}
        for m in members
    ]


@router.get("/stats", response_model=GovernanceStatsSchema)
async def get_stats() -> dict:
    svc = DAOGovernanceService()
    s = await svc.get_stats()
    return {
        "total_proposals": s.total_proposals, "active_proposals": s.active_proposals,
        "passed_proposals": s.passed_proposals, "rejected_proposals": s.rejected_proposals,
        "total_members": s.total_members, "total_votes_cast": s.total_votes_cast,
        "average_participation_rate": s.average_participation_rate,
        "average_approval_rate": s.average_approval_rate,
    }
