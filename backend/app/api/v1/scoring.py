"""Real-time compliance scoring API endpoints."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field, HttpUrl

from app.api.v1.deps import DB, CurrentOrganization, OrgMember
from app.services.scoring import ComplianceScoringService, ComplianceGrade


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---

class GapDetailSchema(BaseModel):
    """Details of a compliance gap."""
    framework: str
    requirement_id: str
    title: str
    severity: str
    description: str
    affected_files: list[str] = Field(default_factory=list)
    remediation_hint: str | None = None


class FrameworkScoreSchema(BaseModel):
    """Score for a single regulatory framework."""
    framework: str
    score: float
    grade: str
    total_requirements: int
    compliant_requirements: int
    critical_gaps: int
    major_gaps: int
    minor_gaps: int
    gaps: list[GapDetailSchema] = Field(default_factory=list)


class ScoringResponseSchema(BaseModel):
    """Complete scoring result response."""
    overall_score: float = Field(..., ge=0, le=100, description="Overall compliance score (0-100)")
    overall_grade: str = Field(..., description="Letter grade (A-F)")
    framework_scores: list[FrameworkScoreSchema]
    total_requirements: int
    compliant_requirements: int
    total_gaps: int
    critical_gaps: int
    major_gaps: int
    minor_gaps: int
    top_gaps: list[GapDetailSchema] = Field(default_factory=list)
    badge_url: str | None = Field(None, description="URL to embeddable badge image")
    badge_markdown: str | None = Field(None, description="Markdown snippet for badge")
    scored_at: datetime
    scan_duration_seconds: float
    confidence: float = Field(..., ge=0, le=1, description="AI confidence score")
    metadata: dict[str, Any] = Field(default_factory=dict)


class QuickScoreRequest(BaseModel):
    """Request for quick scoring of external repository."""
    repository_url: str = Field(..., description="URL of repository to score")
    frameworks: list[str] | None = Field(
        None, 
        description="List of frameworks to score against (e.g., ['GDPR', 'HIPAA'])"
    )


class BadgeFormat(str, Enum):
    """Supported badge formats."""
    SVG = "svg"
    PNG = "png"
    JSON = "json"


# --- Helper Functions ---

def _result_to_schema(result) -> ScoringResponseSchema:
    """Convert ScoringResult dataclass to Pydantic schema."""
    return ScoringResponseSchema(
        overall_score=result.overall_score,
        overall_grade=result.overall_grade.value,
        framework_scores=[
            FrameworkScoreSchema(
                framework=fs.framework,
                score=fs.score,
                grade=fs.grade.value,
                total_requirements=fs.total_requirements,
                compliant_requirements=fs.compliant_requirements,
                critical_gaps=fs.critical_gaps,
                major_gaps=fs.major_gaps,
                minor_gaps=fs.minor_gaps,
                gaps=[
                    GapDetailSchema(
                        framework=g.framework,
                        requirement_id=g.requirement_id,
                        title=g.title,
                        severity=g.severity,
                        description=g.description,
                        affected_files=g.affected_files,
                        remediation_hint=g.remediation_hint,
                    ) for g in fs.gaps
                ],
            ) for fs in result.framework_scores
        ],
        total_requirements=result.total_requirements,
        compliant_requirements=result.compliant_requirements,
        total_gaps=result.total_gaps,
        critical_gaps=result.critical_gaps,
        major_gaps=result.major_gaps,
        minor_gaps=result.minor_gaps,
        top_gaps=[
            GapDetailSchema(
                framework=g.framework,
                requirement_id=g.requirement_id,
                title=g.title,
                severity=g.severity,
                description=g.description,
                affected_files=g.affected_files,
                remediation_hint=g.remediation_hint,
            ) for g in result.top_gaps
        ],
        badge_url=result.badge_url,
        badge_markdown=result.badge_markdown,
        scored_at=result.scored_at,
        scan_duration_seconds=result.scan_duration_seconds,
        confidence=result.confidence,
        metadata=result.metadata,
    )


# --- Endpoints ---

@router.get(
    "/repository/{repository_id}",
    response_model=ScoringResponseSchema,
    summary="Score repository compliance",
    description="Get real-time compliance score for a registered repository",
)
async def score_repository(
    repository_id: UUID,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    frameworks: list[str] | None = Query(None, description="Filter by frameworks"),
    include_gaps: bool = Query(True, description="Include detailed gap information"),
    max_gaps: int = Query(10, ge=1, le=50, description="Maximum gaps to return"),
) -> ScoringResponseSchema:
    """
    Score a repository's compliance status across regulatory frameworks.
    
    Returns a letter grade (A-F) with detailed breakdown by framework
    and top compliance gaps that need attention.
    """
    try:
        service = ComplianceScoringService(db=db)
        result = await service.score_repository(
            repository_id=repository_id,
            frameworks=frameworks,
            include_gaps=include_gaps,
            max_gaps=max_gaps,
        )
        return _result_to_schema(result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.exception("Scoring failed", repository_id=str(repository_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Scoring failed. Please try again.",
        )


@router.post(
    "/quick",
    response_model=ScoringResponseSchema,
    summary="Quick score external repository",
    description="Perform a quick compliance scan on any public repository URL",
)
async def quick_score(
    request: QuickScoreRequest,
    db: DB,
) -> ScoringResponseSchema:
    """
    Quick compliance score for any repository URL.
    
    This endpoint performs a lightweight analysis without requiring
    the repository to be registered. Useful for due diligence,
    procurement, and discovery.
    
    Note: Quick scores have lower confidence than full repository scans.
    """
    try:
        service = ComplianceScoringService(db=db)
        result = await service.quick_score(
            repository_url=request.repository_url,
            frameworks=request.frameworks,
        )
        return _result_to_schema(result)
    except Exception as e:
        logger.exception("Quick scoring failed", url=request.repository_url, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Quick scoring failed. Please try again.",
        )


@router.get(
    "/badge/{repository_id}",
    summary="Get compliance badge",
    description="Get an embeddable compliance badge for your repository",
)
async def get_badge(
    repository_id: UUID,
    db: DB,
    format: BadgeFormat = Query(BadgeFormat.SVG, description="Badge format"),
    framework: str | None = Query(None, description="Specific framework to show"),
) -> dict:
    """
    Get an embeddable compliance badge for a repository.
    
    Badges can be embedded in README files, websites, and documentation
    to show compliance status at a glance.
    """
    try:
        service = ComplianceScoringService(db=db)
        result = await service.score_repository(
            repository_id=repository_id,
            frameworks=[framework] if framework else None,
            include_gaps=False,
        )
        
        grade = result.overall_grade.value
        colors = {
            "A": "#4c1",      # bright green
            "B": "#97ca00",   # green
            "C": "#dfb317",   # yellow
            "D": "#fe7d37",   # orange
            "F": "#e05d44",   # red
        }
        color = colors.get(grade, "#9f9f9f")
        
        if format == BadgeFormat.JSON:
            return {
                "schemaVersion": 1,
                "label": "compliance",
                "message": grade,
                "color": color,
                "logoSvg": None,
            }
        
        # Return badge URLs for SVG/PNG
        label = f"compliance-{framework}" if framework else "compliance"
        shields_url = f"https://img.shields.io/badge/{label}-{grade}-{color.replace('#', '')}"
        
        return {
            "badge_url": shields_url,
            "markdown": f"[![Compliance {grade}]({shields_url})](https://complianceagent.ai/score/{repository_id})",
            "html": f'<a href="https://complianceagent.ai/score/{repository_id}"><img src="{shields_url}" alt="Compliance {grade}"></a>',
            "grade": grade,
            "score": result.overall_score,
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/compare",
    summary="Compare repository scores",
    description="Compare compliance scores across multiple repositories",
)
async def compare_scores(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    repository_ids: list[UUID] = Query(..., description="Repository IDs to compare"),
    framework: str | None = Query(None, description="Filter to specific framework"),
) -> dict:
    """
    Compare compliance scores across multiple repositories.
    
    Useful for portfolio analysis and identifying which repositories
    need the most attention.
    """
    if len(repository_ids) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 repositories can be compared at once",
        )
    
    service = ComplianceScoringService(db=db)
    comparisons = []
    
    for repo_id in repository_ids:
        try:
            result = await service.score_repository(
                repository_id=repo_id,
                frameworks=[framework] if framework else None,
                include_gaps=False,
            )
            comparisons.append({
                "repository_id": str(repo_id),
                "overall_score": result.overall_score,
                "overall_grade": result.overall_grade.value,
                "total_requirements": result.total_requirements,
                "compliant_requirements": result.compliant_requirements,
                "critical_gaps": result.critical_gaps,
            })
        except ValueError:
            comparisons.append({
                "repository_id": str(repo_id),
                "error": "Repository not found",
            })
    
    # Sort by score descending
    comparisons.sort(
        key=lambda x: x.get("overall_score", -1),
        reverse=True,
    )
    
    return {
        "comparisons": comparisons,
        "framework_filter": framework,
        "total_repositories": len(repository_ids),
        "compared_at": datetime.utcnow().isoformat(),
    }
