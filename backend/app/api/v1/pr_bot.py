"""PR Bot API endpoints - Manage automated compliance PR reviews."""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CurrentOrganization, OrgMember


router = APIRouter(prefix="/pr-bot", tags=["PR Bot"])


# ============================================================================
# Request/Response Models
# ============================================================================


class AnalyzePRRequest(BaseModel):
    """Request to analyze a PR."""
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    pr_number: int = Field(..., description="PR number")
    deep_analysis: bool = Field(True, description="Enable AI-powered deep analysis")
    regulations: list[str] | None = Field(None, description="Regulations to check")
    post_comments: bool = Field(True, description="Post review comments to PR")
    create_check_run: bool = Field(True, description="Create GitHub check run")
    auto_label: bool = Field(True, description="Auto-label the PR")


class BatchAnalyzeRequest(BaseModel):
    """Request to analyze multiple PRs."""
    prs: list[dict[str, Any]] = Field(..., description="List of PRs to analyze")


class CreateFixPRRequest(BaseModel):
    """Request to create a fix PR."""
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    pr_number: int = Field(..., description="Source PR number")
    fixes: list[dict[str, Any]] = Field(..., description="Fixes to apply")


class PRBotConfigUpdate(BaseModel):
    """Configuration update for PR Bot."""
    enabled_regulations: list[str] | None = None
    deep_analysis: bool | None = None
    post_review_comments: bool | None = None
    create_check_run: bool | None = None
    auto_label: bool | None = None
    block_on_critical: bool | None = None
    block_on_high: bool | None = None
    block_on_medium: bool | None = None
    min_comment_severity: str | None = None
    max_comments_per_pr: int | None = None


class PRAnalysisResponse(BaseModel):
    """Response for PR analysis."""
    task_id: str
    status: str
    pr_number: int
    repo: str
    owner: str
    queued_at: datetime


class PRBotStatsResponse(BaseModel):
    """Statistics for PR Bot."""
    total_prs_analyzed: int
    prs_passed: int
    prs_failed: int
    total_violations: int
    critical_violations: int
    high_violations: int
    fixes_generated: int
    avg_analysis_time_ms: float


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/analyze", response_model=PRAnalysisResponse)
async def analyze_pr(
    request: AnalyzePRRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> PRAnalysisResponse:
    """Queue a PR for compliance analysis.
    
    The analysis runs asynchronously. Use the task_id to check status.
    """
    from datetime import timezone
    from app.services.pr_bot.queue import PRAnalysisTask
    from app.workers.pr_bot_tasks import analyze_pr as analyze_pr_task
    
    # Get GitHub token from organization settings
    github_token = organization.settings.get("github_access_token") if organization.settings else None
    if not github_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub access token not configured for organization",
        )
    
    # Create task
    task = PRAnalysisTask(
        owner=request.owner,
        repo=request.repo,
        pr_number=request.pr_number,
        organization_id=organization.id,
        deep_analysis=request.deep_analysis,
        enabled_regulations=request.regulations or [],
        post_comments=request.post_comments,
        create_check_run=request.create_check_run,
        auto_label=request.auto_label,
    )
    
    # Queue for processing
    analyze_pr_task.delay(
        task_data=task.to_dict(),
        access_token=github_token,
        organization_id=str(organization.id),
    )
    
    return PRAnalysisResponse(
        task_id=str(task.id),
        status="queued",
        pr_number=request.pr_number,
        repo=request.repo,
        owner=request.owner,
        queued_at=datetime.now(timezone.utc),
    )


@router.post("/analyze/batch")
async def batch_analyze_prs(
    request: BatchAnalyzeRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Queue multiple PRs for analysis."""
    from app.workers.pr_bot_tasks import batch_analyze_prs as batch_task
    
    github_token = organization.settings.get("github_access_token") if organization.settings else None
    if not github_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub access token not configured",
        )
    
    result = batch_task.delay(
        pr_list=request.prs,
        access_token=github_token,
        organization_id=str(organization.id),
    )
    
    return {
        "batch_task_id": result.id,
        "prs_queued": len(request.prs),
        "status": "queued",
    }


@router.post("/reanalyze/{owner}/{repo}/{pr_number}")
async def reanalyze_pr(
    owner: str,
    repo: str,
    pr_number: int,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Re-analyze a PR (e.g., after config change or fix applied)."""
    from app.workers.pr_bot_tasks import reanalyze_pr as reanalyze_task
    
    github_token = organization.settings.get("github_access_token") if organization.settings else None
    if not github_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub access token not configured",
        )
    
    result = reanalyze_task.delay(
        owner=owner,
        repo=repo,
        pr_number=pr_number,
        access_token=github_token,
        organization_id=str(organization.id),
    )
    
    return {
        "task_id": result.id,
        "pr": f"{owner}/{repo}#{pr_number}",
        "status": "queued",
    }


@router.post("/create-fix-pr")
async def create_fix_pr(
    request: CreateFixPRRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Create a PR with compliance fixes."""
    from app.workers.pr_bot_tasks import create_fix_pr as create_fix_task
    
    github_token = organization.settings.get("github_access_token") if organization.settings else None
    if not github_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub access token not configured",
        )
    
    if not request.fixes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fixes provided",
        )
    
    result = create_fix_task.delay(
        owner=request.owner,
        repo=request.repo,
        pr_number=request.pr_number,
        fixes=request.fixes,
        access_token=github_token,
        organization_id=str(organization.id),
    )
    
    return {
        "task_id": result.id,
        "source_pr": request.pr_number,
        "fixes_count": len(request.fixes),
        "status": "queued",
    }


@router.get("/task/{task_id}")
async def get_task_status(
    task_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Get the status of an analysis task."""
    from celery.result import AsyncResult
    from app.workers import celery_app
    
    result = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "status": result.status,
        "ready": result.ready(),
    }
    
    if result.ready():
        if result.successful():
            response["result"] = result.result
        else:
            response["error"] = str(result.result) if result.result else "Unknown error"
    
    return response


@router.get("/config")
async def get_pr_bot_config(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Get PR Bot configuration for the organization."""
    from app.services.pr_bot import PRBotConfig
    
    # Default config
    default_config = PRBotConfig()
    
    # Override with organization settings
    settings = organization.settings or {}
    pr_bot_settings = settings.get("pr_bot", {})
    
    return {
        "enabled_regulations": pr_bot_settings.get(
            "enabled_regulations", default_config.enabled_regulations
        ),
        "deep_analysis": pr_bot_settings.get(
            "deep_analysis", default_config.deep_analysis
        ),
        "post_review_comments": pr_bot_settings.get(
            "post_review_comments", default_config.post_review_comments
        ),
        "create_check_run": pr_bot_settings.get(
            "create_check_run", default_config.create_check_run
        ),
        "auto_label": pr_bot_settings.get(
            "auto_label", default_config.auto_label
        ),
        "block_on_critical": pr_bot_settings.get(
            "block_on_critical", default_config.block_on_critical
        ),
        "block_on_high": pr_bot_settings.get(
            "block_on_high", default_config.block_on_high
        ),
        "block_on_medium": pr_bot_settings.get(
            "block_on_medium", default_config.block_on_medium
        ),
        "min_comment_severity": pr_bot_settings.get(
            "min_comment_severity", default_config.min_comment_severity.value
        ),
        "max_comments_per_pr": pr_bot_settings.get(
            "max_comments_per_pr", default_config.max_comments_per_pr
        ),
    }


@router.patch("/config")
async def update_pr_bot_config(
    config: PRBotConfigUpdate,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Update PR Bot configuration for the organization."""
    from sqlalchemy import select
    from app.models.organization import Organization
    
    # Get organization and update settings
    result = await db.execute(
        select(Organization).where(Organization.id == organization.id)
    )
    org = result.scalar_one()
    
    settings = org.settings or {}
    pr_bot_settings = settings.get("pr_bot", {})
    
    # Update only provided fields
    update_dict = config.model_dump(exclude_none=True)
    pr_bot_settings.update(update_dict)
    settings["pr_bot"] = pr_bot_settings
    
    org.settings = settings
    await db.commit()
    
    return {"status": "updated", "config": pr_bot_settings}


@router.get("/stats", response_model=PRBotStatsResponse)
async def get_pr_bot_stats(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    days: int = Query(30, description="Number of days to include in stats"),
) -> PRBotStatsResponse:
    """Get PR Bot statistics for the organization."""
    from datetime import timedelta
    from sqlalchemy import func, select
    from app.models.audit import AuditEventType, AuditTrail
    
    cutoff = datetime.now() - timedelta(days=days)
    
    # Query audit events for PR analysis
    result = await db.execute(
        select(AuditTrail.event_data)
        .where(
            AuditTrail.organization_id == organization.id,
            AuditTrail.event_type == AuditEventType.PR_ANALYZED,
            AuditTrail.created_at >= cutoff,
        )
    )
    events = list(result.scalars().all())
    
    total = len(events)
    passed = sum(1 for e in events if e and e.get("passed", False))
    failed = total - passed
    
    violations = sum(e.get("violations", 0) for e in events if e)
    critical = sum(e.get("critical", 0) for e in events if e)
    high = sum(e.get("high", 0) for e in events if e)
    
    return PRBotStatsResponse(
        total_prs_analyzed=total,
        prs_passed=passed,
        prs_failed=failed,
        total_violations=violations,
        critical_violations=critical,
        high_violations=high,
        fixes_generated=0,  # Would come from separate tracking
        avg_analysis_time_ms=0.0,  # Would calculate from event data
    )


@router.get("/history")
async def get_pr_analysis_history(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    repo: str | None = Query(None, description="Filter by repository"),
) -> dict[str, Any]:
    """Get history of PR analyses."""
    from sqlalchemy import select
    from app.models.audit import AuditEventType, AuditTrail
    
    query = (
        select(AuditTrail)
        .where(
            AuditTrail.organization_id == organization.id,
            AuditTrail.event_type == AuditEventType.PR_ANALYZED,
        )
        .order_by(AuditTrail.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    
    result = await db.execute(query)
    events = list(result.scalars().all())
    
    history = []
    for event in events:
        data = event.event_data or {}
        history.append({
            "id": str(event.id),
            "timestamp": event.created_at.isoformat(),
            "pr_number": data.get("pr_number"),
            "repo": f"{data.get('owner', 'unknown')}/{data.get('repo', 'unknown')}" if 'owner' in data else None,
            "passed": data.get("passed"),
            "violations": data.get("violations", 0),
            "critical": data.get("critical", 0),
            "high": data.get("high", 0),
        })
    
    return {
        "history": history,
        "limit": limit,
        "offset": offset,
        "total": len(history),
    }
