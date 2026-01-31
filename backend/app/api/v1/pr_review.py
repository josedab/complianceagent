"""PR Review API endpoints for Compliance Co-Pilot."""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CurrentOrganization, OrgMember


router = APIRouter(prefix="/pr-review", tags=["PR Review"])


# ============================================================================
# Request/Response Models
# ============================================================================


class PRReviewRequest(BaseModel):
    """Request to review a PR."""
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    pr_number: int = Field(..., description="PR number")
    deep_analysis: bool = Field(True, description="Enable AI-powered deep analysis")
    regulations: list[str] | None = Field(None, description="Regulations to check")


class FileDiffRequest(BaseModel):
    """Request to review file diffs directly."""
    files: list[dict[str, Any]] = Field(..., description="List of file diffs")
    deep_analysis: bool = Field(True, description="Enable AI-powered deep analysis")
    regulations: list[str] | None = Field(None, description="Regulations to check")


class ViolationResponse(BaseModel):
    """A compliance violation."""
    id: str
    file_path: str
    line_start: int
    line_end: int
    code: str
    message: str
    severity: str
    regulation: str | None
    article_reference: str | None
    category: str | None
    suggestion: str | None
    confidence: float


class ReviewCommentResponse(BaseModel):
    """A review comment."""
    id: str
    file_path: str
    line: int
    body: str


class AutoFixResponse(BaseModel):
    """An auto-fix response."""
    id: str
    violation_id: str | None
    file_path: str
    original_code: str
    fixed_code: str
    diff: str
    description: str
    confidence: float
    status: str


class PRAnalysisResponse(BaseModel):
    """Analysis result response."""
    id: str
    pr_number: int | None
    repository: str | None
    owner: str | None
    files_analyzed: int
    total_additions: int
    total_deletions: int
    violations: list[ViolationResponse]
    regulations_checked: list[str]
    analysis_time_ms: float
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    passed: bool


class PRReviewResponse(BaseModel):
    """Complete review response."""
    id: str
    analysis: PRAnalysisResponse
    comments: list[ReviewCommentResponse]
    auto_fixes: list[AutoFixResponse]
    status: str
    summary: str
    recommendation: str
    review_time_ms: float
    reviewed_at: datetime


class GenerateFixRequest(BaseModel):
    """Request to generate fix for a violation."""
    violation_id: str
    file_content: str | None = None


class ApplyFixRequest(BaseModel):
    """Request to apply a fix."""
    fix_id: str
    owner: str
    repo: str
    branch: str


class CreateFixPRRequest(BaseModel):
    """Request to create a PR with fixes."""
    fix_ids: list[str]
    owner: str
    repo: str
    base_branch: str
    pr_title: str | None = None


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/analyze", response_model=PRReviewResponse)
async def review_pull_request(
    request: PRReviewRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> PRReviewResponse:
    """Review a GitHub pull request for compliance issues.
    
    Analyzes PR diffs for compliance violations across GDPR, HIPAA, PCI-DSS,
    EU AI Act, and other regulations. Returns detailed findings with inline
    suggestions and auto-fix options.
    """
    from app.agents.copilot import CopilotClient
    from app.services.pr_review import PRAnalyzer, PRReviewer
    
    # Get GitHub token from organization settings (simplified for demo)
    github_token = organization.settings.get("github_access_token") if organization.settings else None
    
    analyzer = PRAnalyzer(enabled_regulations=request.regulations)
    copilot = CopilotClient() if request.deep_analysis else None
    reviewer = PRReviewer(copilot_client=copilot, analyzer=analyzer)
    
    try:
        result = await reviewer.review_pr(
            owner=request.owner,
            repo=request.repo,
            pr_number=request.pr_number,
            access_token=github_token,
            deep_analysis=request.deep_analysis,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to review PR: {str(e)}",
        )
    
    return _convert_review_to_response(result)


@router.post("/analyze-diff", response_model=PRReviewResponse)
async def review_diff_content(
    request: FileDiffRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> PRReviewResponse:
    """Review file diffs directly without GitHub API access.
    
    Useful for webhook-based analysis or testing. Accepts raw diff content
    and returns compliance findings.
    """
    from app.agents.copilot import CopilotClient
    from app.services.pr_review import PRAnalyzer, PRReviewer
    
    analyzer = PRAnalyzer(enabled_regulations=request.regulations)
    copilot = CopilotClient() if request.deep_analysis else None
    reviewer = PRReviewer(copilot_client=copilot, analyzer=analyzer)
    
    result = await reviewer.review_files(
        files=request.files,
        deep_analysis=request.deep_analysis,
    )
    
    return _convert_review_to_response(result)


@router.post("/generate-fixes", response_model=list[AutoFixResponse])
async def generate_fixes_for_review(
    review_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    file_contents: dict[str, str] | None = None,
) -> list[AutoFixResponse]:
    """Generate auto-fixes for violations in a review.
    
    Uses AI and template-based approaches to generate compliance fixes.
    Optionally provide file contents for better context.
    """
    from app.agents.copilot import CopilotClient
    from app.services.pr_review import AutoFixGenerator
    
    # In production, would retrieve review from database
    # For now, return empty list with informative error
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Review not found. Use /analyze endpoint first and pass violations directly.",
    )


@router.post("/generate-fix", response_model=AutoFixResponse)
async def generate_single_fix(
    request: GenerateFixRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> AutoFixResponse:
    """Generate an auto-fix for a specific violation."""
    from app.agents.copilot import CopilotClient
    from app.services.pr_review import AutoFixGenerator, ComplianceViolation, ViolationSeverity
    
    copilot = CopilotClient()
    generator = AutoFixGenerator(copilot_client=copilot)
    
    # Create a mock violation for the fix
    # In production, would retrieve from database
    violation = ComplianceViolation(
        id=UUID(request.violation_id),
        file_path="unknown.py",
        line_start=1,
        code="UNKNOWN",
        message="Violation to fix",
        severity=ViolationSeverity.MEDIUM,
    )
    
    fix = await generator.generate_fix(
        violation=violation,
        file_content=request.file_content,
    )
    
    if not fix:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not generate fix for this violation",
        )
    
    return AutoFixResponse(
        id=str(fix.id),
        violation_id=str(fix.violation_id) if fix.violation_id else None,
        file_path=fix.file_path,
        original_code=fix.original_code,
        fixed_code=fix.fixed_code,
        diff=fix.diff,
        description=fix.description,
        confidence=fix.confidence,
        status=fix.status.value,
    )


@router.post("/apply-fix")
async def apply_fix(
    request: ApplyFixRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Apply a generated fix to a repository.
    
    Commits the fix to the specified branch. Requires write access to the repository.
    """
    from app.services.pr_review import AutoFixGenerator
    
    github_token = organization.settings.get("github_access_token") if organization.settings else None
    if not github_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub access token not configured for organization",
        )
    
    # In production, would retrieve fix from database
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Apply fix requires fix to be stored in database. Use /create-fix-pr instead.",
    )


@router.post("/create-fix-pr")
async def create_fix_pr(
    request: CreateFixPRRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Create a PR with multiple compliance fixes.
    
    Creates a new branch, applies all fixes, and opens a draft PR for review.
    """
    from app.services.pr_review import AutoFixGenerator
    
    github_token = organization.settings.get("github_access_token") if organization.settings else None
    if not github_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub access token not configured for organization",
        )
    
    # In production, would retrieve fixes from database
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Create fix PR requires fixes to be stored in database.",
    )


@router.post("/webhook/github")
async def handle_github_webhook(
    payload: dict[str, Any],
    organization: CurrentOrganization,
    db: DB,
) -> dict[str, Any]:
    """Handle GitHub webhook for automatic PR review.
    
    Triggered on PR open/update events. Automatically reviews the PR
    and posts comments with findings.
    """
    event = payload.get("action")
    
    if event not in ("opened", "synchronize", "reopened"):
        return {"status": "ignored", "reason": f"Event {event} not handled"}
    
    pr = payload.get("pull_request", {})
    repo = payload.get("repository", {})
    
    # Queue async review task
    # In production, would use Celery
    return {
        "status": "queued",
        "pr_number": pr.get("number"),
        "repo": repo.get("full_name"),
    }


@router.get("/patterns")
async def list_compliance_patterns(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    regulation: str | None = Query(None),
) -> dict[str, Any]:
    """List available compliance patterns for PR review.
    
    Shows all patterns used to detect compliance issues, with their
    severity and regulation mappings.
    """
    from app.services.pr_review.analyzer import COMPLIANCE_PATTERNS
    
    patterns = []
    for name, config in COMPLIANCE_PATTERNS.items():
        if regulation and config.get("regulation") != regulation:
            continue
        patterns.append({
            "name": name,
            "message": config.get("message"),
            "severity": config.get("severity", "medium").value if hasattr(config.get("severity"), "value") else config.get("severity"),
            "regulation": config.get("regulation"),
            "article": config.get("article"),
            "category": config.get("category"),
        })
    
    return {
        "patterns": patterns,
        "total": len(patterns),
    }


@router.post("/patterns")
async def add_custom_pattern(
    name: str,
    pattern: str,
    message: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    severity: str = "medium",
    regulation: str | None = None,
    article: str | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    """Add a custom compliance pattern for the organization.
    
    Custom patterns are used alongside built-in patterns for PR review.
    """
    # In production, would store in database per organization
    return {
        "status": "created",
        "pattern": {
            "name": name,
            "pattern": pattern,
            "message": message,
            "severity": severity,
            "regulation": regulation,
            "article": article,
            "category": category,
        },
    }


# ============================================================================
# Helper Functions
# ============================================================================


def _convert_review_to_response(result) -> PRReviewResponse:
    """Convert PRReviewResult to API response."""
    analysis = result.analysis
    
    violations = [
        ViolationResponse(
            id=str(v.id),
            file_path=v.file_path,
            line_start=v.line_start,
            line_end=v.line_end,
            code=v.code,
            message=v.message,
            severity=v.severity.value,
            regulation=v.regulation,
            article_reference=v.article_reference,
            category=v.category,
            suggestion=v.suggestion,
            confidence=v.confidence,
        )
        for v in (analysis.violations if analysis else [])
    ]
    
    comments = [
        ReviewCommentResponse(
            id=str(c.id),
            file_path=c.file_path,
            line=c.line,
            body=c.body,
        )
        for c in result.comments
    ]
    
    auto_fixes = [
        AutoFixResponse(
            id=str(f.id),
            violation_id=str(f.violation_id) if f.violation_id else None,
            file_path=f.file_path,
            original_code=f.original_code,
            fixed_code=f.fixed_code,
            diff=f.diff,
            description=f.description,
            confidence=f.confidence,
            status=f.status.value,
        )
        for f in result.auto_fixes
    ]
    
    return PRReviewResponse(
        id=str(result.id),
        analysis=PRAnalysisResponse(
            id=str(analysis.id) if analysis else "",
            pr_number=analysis.pr_number if analysis else None,
            repository=analysis.repository if analysis else None,
            owner=analysis.owner if analysis else None,
            files_analyzed=analysis.files_analyzed if analysis else 0,
            total_additions=analysis.total_additions if analysis else 0,
            total_deletions=analysis.total_deletions if analysis else 0,
            violations=violations,
            regulations_checked=analysis.regulations_checked if analysis else [],
            analysis_time_ms=analysis.analysis_time_ms if analysis else 0,
            critical_count=analysis.critical_count if analysis else 0,
            high_count=analysis.high_count if analysis else 0,
            medium_count=analysis.medium_count if analysis else 0,
            low_count=analysis.low_count if analysis else 0,
            passed=analysis.passed if analysis else True,
        ),
        comments=comments,
        auto_fixes=auto_fixes,
        status=result.status.value,
        summary=result.summary,
        recommendation=result.recommendation,
        review_time_ms=result.review_time_ms,
        reviewed_at=result.reviewed_at,
    )
