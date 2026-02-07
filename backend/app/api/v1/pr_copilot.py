"""API endpoints for Compliance Co-Pilot for PRs."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep

from app.services.pr_copilot import PRCopilotService, SuggestionAction, SuggestionFeedback


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---


class AnalyzePRRequest(BaseModel):
    """Request to analyze a PR."""

    repo: str = Field(..., description="Repository full name (owner/repo)")
    pr_number: int = Field(..., description="PR number")
    diff: str = Field(..., description="PR diff content")
    files_changed: list[str] = Field(default_factory=list)
    base_branch: str = Field(default="main")


class FindingSchema(BaseModel):
    """Compliance finding response."""

    id: str
    file_path: str
    line_start: int
    line_end: int
    severity: str
    regulation: str
    article_ref: str
    title: str
    description: str
    suggestion: str
    suggested_code: str
    confidence: float


class PRReviewResponse(BaseModel):
    """PR review result response."""

    id: str
    pr_number: int
    repo: str
    status: str
    findings: list[FindingSchema]
    summary: str
    risk_level: str
    labels: list[str]
    should_block_merge: bool
    analysis_time_ms: float


class FeedbackRequest(BaseModel):
    """Feedback on a suggestion."""

    finding_id: str = Field(..., description="Finding UUID")
    action: str = Field(..., description="accepted, dismissed, or deferred")
    reason: str = Field(default="")


class LearningStatsResponse(BaseModel):
    """Learning statistics response."""

    total_suggestions: int
    accepted: int
    dismissed: int
    deferred: int
    acceptance_rate: float


# --- Endpoints ---


@router.post(
    "/analyze",
    response_model=PRReviewResponse,
    summary="Analyze PR for compliance",
    description="Run comprehensive compliance analysis on a pull request",
)
async def analyze_pr(
    request: AnalyzePRRequest,
    db: DB,
    copilot: CopilotDep,
) -> PRReviewResponse:
    """Analyze a PR for compliance issues."""
    service = PRCopilotService(db=db, copilot_client=copilot)
    result = await service.analyze_pr(
        repo=request.repo,
        pr_number=request.pr_number,
        diff=request.diff,
        files_changed=request.files_changed,
        base_branch=request.base_branch,
    )

    return PRReviewResponse(
        id=str(result.id),
        pr_number=result.pr_number,
        repo=result.repo,
        status=result.status.value,
        findings=[
            FindingSchema(
                id=str(f.id),
                file_path=f.file_path,
                line_start=f.line_start,
                line_end=f.line_end,
                severity=f.severity.value,
                regulation=f.regulation,
                article_ref=f.article_ref,
                title=f.title,
                description=f.description,
                suggestion=f.suggestion,
                suggested_code=f.suggested_code,
                confidence=f.confidence,
            )
            for f in result.findings
        ],
        summary=result.summary,
        risk_level=result.risk_level,
        labels=result.labels,
        should_block_merge=result.should_block_merge,
        analysis_time_ms=result.analysis_time_ms,
    )


@router.get(
    "/reviews",
    response_model=list[PRReviewResponse],
    summary="List PR reviews",
)
async def list_reviews(
    db: DB,
    copilot: CopilotDep,
    repo: str | None = None,
) -> list[PRReviewResponse]:
    """List PR compliance reviews."""
    service = PRCopilotService(db=db, copilot_client=copilot)
    results = await service.list_reviews(repo=repo)
    return [
        PRReviewResponse(
            id=str(r.id),
            pr_number=r.pr_number,
            repo=r.repo,
            status=r.status.value,
            findings=[],
            summary=r.summary,
            risk_level=r.risk_level,
            labels=r.labels,
            should_block_merge=r.should_block_merge,
            analysis_time_ms=r.analysis_time_ms,
        )
        for r in results
    ]


@router.get(
    "/reviews/{review_id}/comments",
    summary="Get inline comments",
    description="Get inline review comments for GitHub/GitLab",
)
async def get_inline_comments(
    review_id: UUID,
    db: DB,
    copilot: CopilotDep,
) -> list[dict]:
    """Get inline review comments for a PR review."""
    service = PRCopilotService(db=db, copilot_client=copilot)
    return await service.get_inline_comments(review_id)


@router.post(
    "/feedback",
    summary="Submit suggestion feedback",
    description="Provide feedback on a compliance suggestion to improve future accuracy",
)
async def submit_feedback(
    request: FeedbackRequest,
    db: DB,
    copilot: CopilotDep,
) -> dict:
    """Submit feedback on a compliance suggestion."""
    service = PRCopilotService(db=db, copilot_client=copilot)
    feedback = SuggestionFeedback(
        finding_id=UUID(request.finding_id),
        action=SuggestionAction(request.action),
        reason=request.reason,
    )
    result = await service.submit_feedback(feedback)
    return {"status": "recorded", "action": result.action.value}


@router.get(
    "/learning-stats",
    response_model=LearningStatsResponse,
    summary="Get learning statistics",
)
async def get_learning_stats(
    db: DB,
    copilot: CopilotDep,
) -> LearningStatsResponse:
    """Get suggestion learning statistics."""
    service = PRCopilotService(db=db, copilot_client=copilot)
    stats = await service.get_learning_stats()
    return LearningStatsResponse(
        total_suggestions=stats.total_suggestions,
        accepted=stats.accepted,
        dismissed=stats.dismissed,
        deferred=stats.deferred,
        acceptance_rate=stats.acceptance_rate,
    )
