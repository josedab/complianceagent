"""API endpoints for Compliance-Aware Code Review Agent."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.code_review_agent import CodeReviewAgentService


logger = structlog.get_logger()
router = APIRouter()


class AnalyzePRRequest(BaseModel):
    repo: str = Field(...)
    pr_number: int = Field(...)
    commit_sha: str = Field(default="")
    diff_content: str = Field(default="")
    changed_files: list[dict[str, Any]] = Field(default_factory=list)


class SuggestionSchema(BaseModel):
    id: str
    file_path: str
    line_number: int
    rule_id: str
    framework: str
    article_ref: str
    message: str
    suggested_code: str
    risk_level: str
    status: str


class ReviewSchema(BaseModel):
    id: str
    repo: str
    pr_number: int
    commit_sha: str
    overall_risk: str
    decision: str
    suggestions: list[SuggestionSchema]
    files_analyzed: int
    hunks_analyzed: int
    compliance_score_before: float
    compliance_score_after: float
    auto_approve_eligible: bool
    review_time_ms: float
    created_at: str | None


class StatsSchema(BaseModel):
    total_reviews: int
    auto_approved: int
    suggestions_made: int
    suggestions_accepted: int
    acceptance_rate: float
    avg_review_time_ms: float
    by_risk_level: dict[str, int]


def _suggestion_to_schema(s: Any) -> SuggestionSchema:
    return SuggestionSchema(
        id=str(s.id),
        file_path=s.file_path,
        line_number=s.line_number,
        rule_id=s.rule_id,
        framework=s.framework,
        article_ref=s.article_ref,
        message=s.message,
        suggested_code=s.suggested_code,
        risk_level=s.risk_level.value,
        status=s.status.value,
    )


def _review_to_schema(r: Any) -> ReviewSchema:
    return ReviewSchema(
        id=str(r.id),
        repo=r.repo,
        pr_number=r.pr_number,
        commit_sha=r.commit_sha,
        overall_risk=r.overall_risk.value,
        decision=r.decision.value,
        suggestions=[_suggestion_to_schema(s) for s in r.suggestions],
        files_analyzed=r.files_analyzed,
        hunks_analyzed=r.hunks_analyzed,
        compliance_score_before=r.compliance_score_before,
        compliance_score_after=r.compliance_score_after,
        auto_approve_eligible=r.auto_approve_eligible,
        review_time_ms=r.review_time_ms,
        created_at=r.created_at.isoformat() if r.created_at else None,
    )


@router.post("/analyze", response_model=ReviewSchema, summary="Analyze PR for compliance")
async def analyze_pr(request: AnalyzePRRequest, db: DB) -> ReviewSchema:
    service = CodeReviewAgentService(db=db)
    r = await service.analyze_pr(
        repo=request.repo,
        pr_number=request.pr_number,
        commit_sha=request.commit_sha,
        diff_content=request.diff_content,
        changed_files=request.changed_files,
    )
    return _review_to_schema(r)


@router.post("/suggestions/{suggestion_id}/accept", summary="Accept suggestion")
async def accept_suggestion(suggestion_id: UUID, db: DB) -> dict:
    service = CodeReviewAgentService(db=db)
    ok = await service.accept_suggestion(suggestion_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suggestion not found")
    return {"status": "accepted"}


@router.post("/suggestions/{suggestion_id}/reject", summary="Reject suggestion")
async def reject_suggestion(suggestion_id: UUID, db: DB) -> dict:
    service = CodeReviewAgentService(db=db)
    ok = await service.reject_suggestion(suggestion_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suggestion not found")
    return {"status": "rejected"}


@router.get("/reviews", response_model=list[ReviewSchema], summary="List reviews")
async def list_reviews(db: DB, repo: str | None = None, limit: int = 50) -> list[ReviewSchema]:
    service = CodeReviewAgentService(db=db)
    reviews = service.list_reviews(repo=repo, limit=limit)
    return [_review_to_schema(r) for r in reviews]


@router.get("/stats", response_model=StatsSchema, summary="Get review stats")
async def get_stats(db: DB) -> StatsSchema:
    service = CodeReviewAgentService(db=db)
    s = service.get_stats()
    return StatsSchema(
        total_reviews=s.total_reviews,
        auto_approved=s.auto_approved,
        suggestions_made=s.suggestions_made,
        suggestions_accepted=s.suggestions_accepted,
        acceptance_rate=s.acceptance_rate,
        avg_review_time_ms=s.avg_review_time_ms,
        by_risk_level=s.by_risk_level,
    )
