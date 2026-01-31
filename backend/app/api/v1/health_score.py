"""API endpoints for Compliance Health Score API."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Response
from pydantic import BaseModel, Field

from app.services.health_score import (
    BadgeConfig,
    BadgeStyle,
    ScoreCategory,
    get_badge_generator,
    get_cicd_service,
    get_score_calculator,
)


router = APIRouter(prefix="/health-score", tags=["health-score"])


# Request/Response Models
class CalculateScoreRequest(BaseModel):
    """Request to calculate health score."""
    
    repository_id: UUID
    regulations: list[str] = []
    force_refresh: bool = False


class BadgeConfigRequest(BaseModel):
    """Request to configure badge."""
    
    style: str = "flat"
    show_grade: bool = True
    show_score: bool = True
    label: str = "compliance"
    include_regulations: list[str] | None = None


class CreateCICDIntegrationRequest(BaseModel):
    """Request to create CI/CD integration."""
    
    repository_id: UUID
    platform: str = Field(..., description="Platform: github_actions, gitlab_ci, jenkins, circleci, azure_devops, bitbucket_pipelines")
    fail_threshold: float = Field(70.0, ge=0, le=100)
    warn_threshold: float = Field(85.0, ge=0, le=100)
    block_on_failure: bool = False
    regulations_required: list[str] = []


class RunCheckRequest(BaseModel):
    """Request to run CI/CD compliance check."""
    
    commit_sha: str
    branch: str
    pr_number: int | None = None


class UpdateCICDIntegrationRequest(BaseModel):
    """Request to update CI/CD integration."""
    
    fail_threshold: float | None = Field(None, ge=0, le=100)
    warn_threshold: float | None = Field(None, ge=0, le=100)
    block_on_failure: bool | None = None
    regulations_required: list[str] | None = None


class UpdateWeightsRequest(BaseModel):
    """Request to update category weights."""
    
    weights: dict[str, float]


def _parse_badge_style(value: str) -> BadgeStyle:
    """Parse badge style string."""
    try:
        return BadgeStyle(value.lower().replace("-", "_").replace(" ", "_"))
    except ValueError:
        return BadgeStyle.FLAT


# Score Endpoints
@router.post("/calculate")
async def calculate_health_score(request: CalculateScoreRequest):
    """Calculate comprehensive health score for a repository.
    
    Returns detailed breakdown by category with recommendations.
    """
    calculator = get_score_calculator()
    
    score = await calculator.calculate_score(
        repository_id=request.repository_id,
        regulations=request.regulations,
        force_refresh=request.force_refresh,
    )
    
    return {
        "id": str(score.id),
        "repository_id": str(score.repository_id),
        "overall": {
            "score": round(score.overall_score, 2),
            "grade": score.grade.value,
        },
        "trend": {
            "direction": score.trend.value,
            "delta": round(score.trend_delta, 2),
            "previous_score": round(score.previous_score, 2) if score.previous_score else None,
        },
        "categories": {
            k: {
                "score": round(v.score, 2),
                "weight": v.weight,
                "weighted_score": round(v.weighted_score, 2),
                "details": v.details,
                "recommendations": v.recommendations,
            }
            for k, v in score.category_scores.items()
        },
        "controls": {
            "total": score.total_controls,
            "passing": score.passing_controls,
            "failing": score.failing_controls,
            "not_applicable": score.not_applicable_controls,
        },
        "regulations_checked": score.regulations_checked,
        "recommendations": score.recommendations,
        "calculated_at": score.calculated_at.isoformat(),
    }


@router.get("/{repository_id}")
async def get_health_score(
    repository_id: UUID,
    regulations: str | None = None,
):
    """Get current health score for a repository.
    
    Use ?regulations=SOC2,HIPAA to filter by specific regulations.
    """
    calculator = get_score_calculator()
    
    regulation_list = regulations.split(",") if regulations else []
    
    score = await calculator.calculate_score(
        repository_id=repository_id,
        regulations=regulation_list,
        force_refresh=False,
    )
    
    return {
        "repository_id": str(score.repository_id),
        "score": round(score.overall_score, 2),
        "grade": score.grade.value,
        "trend": score.trend.value,
        "categories": {
            k: round(v.score, 2) for k, v in score.category_scores.items()
        },
        "calculated_at": score.calculated_at.isoformat(),
    }


@router.get("/{repository_id}/history")
async def get_score_history(
    repository_id: UUID,
    days: int = 30,
):
    """Get historical health scores for a repository."""
    calculator = get_score_calculator()
    
    history = await calculator.get_history(repository_id, days=days)
    
    return {
        "repository_id": str(repository_id),
        "period_days": days,
        "count": len(history),
        "history": [
            {
                "score": round(h.score, 2),
                "grade": h.grade.value,
                "recorded_at": h.recorded_at.isoformat(),
            }
            for h in history
        ],
    }


# Badge Endpoints
@router.get("/{repository_id}/badge.svg")
async def get_badge_svg(
    repository_id: UUID,
    style: str = "flat",
    grade: bool = True,
    score: bool = True,
    label: str = "compliance",
    regulations: str | None = None,
):
    """Get SVG badge for embedding in README or documentation.
    
    Parameters:
    - style: flat, flat-square, plastic, for-the-badge, social
    - grade: Show letter grade (A+, B, etc.)
    - score: Show percentage score
    - label: Custom label text
    - regulations: Comma-separated regulations to check
    """
    calculator = get_score_calculator()
    badge_gen = get_badge_generator()
    
    regulation_list = regulations.split(",") if regulations else []
    
    health_score = await calculator.calculate_score(
        repository_id=repository_id,
        regulations=regulation_list,
        force_refresh=False,
    )
    
    config = BadgeConfig(
        repository_id=repository_id,
        style=_parse_badge_style(style),
        show_grade=grade,
        show_score=score,
        label=label,
        include_regulations=regulation_list if regulation_list else None,
    )
    
    badge = badge_gen.generate_badge(health_score, config)
    
    return Response(
        content=badge.svg_content,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": f"max-age={config.cache_seconds}",
        },
    )


@router.get("/{repository_id}/badge")
async def get_badge_metadata(
    repository_id: UUID,
    style: str = "flat",
    grade: bool = True,
    score_display: bool = True,
    label: str = "compliance",
):
    """Get badge metadata including URLs and embed codes."""
    calculator = get_score_calculator()
    badge_gen = get_badge_generator()
    
    health_score = await calculator.calculate_score(
        repository_id=repository_id,
        force_refresh=False,
    )
    
    config = BadgeConfig(
        repository_id=repository_id,
        style=_parse_badge_style(style),
        show_grade=grade,
        show_score=score_display,
        label=label,
    )
    
    badge = badge_gen.generate_badge(health_score, config)
    
    return {
        "repository_id": str(badge.repository_id),
        "score": round(badge.score, 2),
        "grade": badge.grade.value,
        "url": badge.url,
        "markdown": badge.markdown,
        "html": badge.html,
        "generated_at": badge.generated_at.isoformat(),
    }


# CI/CD Integration Endpoints
@router.post("/cicd/integrations")
async def create_cicd_integration(request: CreateCICDIntegrationRequest):
    """Create a new CI/CD integration.
    
    Returns the integration details and a one-time API token.
    Store the token securely as it won't be shown again.
    """
    cicd = get_cicd_service()
    
    try:
        integration, token = await cicd.create_integration(
            repository_id=request.repository_id,
            platform=request.platform,
            fail_threshold=request.fail_threshold,
            warn_threshold=request.warn_threshold,
            block_on_failure=request.block_on_failure,
            regulations_required=request.regulations_required,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Generate workflow snippet
    snippet = cicd.generate_workflow_snippet(integration)
    
    return {
        "integration": {
            "id": str(integration.id),
            "repository_id": str(integration.repository_id),
            "platform": integration.platform,
            "fail_threshold": integration.fail_threshold,
            "warn_threshold": integration.warn_threshold,
            "block_on_failure": integration.block_on_failure,
            "regulations_required": integration.regulations_required,
            "created_at": integration.created_at.isoformat(),
        },
        "api_token": token,
        "workflow_snippet": snippet,
        "note": "Store the API token securely. It will not be shown again.",
    }


@router.get("/cicd/integrations/{integration_id}")
async def get_cicd_integration(integration_id: UUID):
    """Get CI/CD integration details."""
    cicd = get_cicd_service()
    integration = await cicd.get_integration(integration_id)
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    return {
        "id": str(integration.id),
        "repository_id": str(integration.repository_id),
        "platform": integration.platform,
        "fail_threshold": integration.fail_threshold,
        "warn_threshold": integration.warn_threshold,
        "block_on_failure": integration.block_on_failure,
        "regulations_required": integration.regulations_required,
        "created_at": integration.created_at.isoformat(),
        "updated_at": integration.updated_at.isoformat(),
    }


@router.get("/repositories/{repository_id}/cicd/integrations")
async def list_repository_integrations(repository_id: UUID):
    """List CI/CD integrations for a repository."""
    cicd = get_cicd_service()
    integrations = await cicd.get_integrations_for_repo(repository_id)
    
    return {
        "repository_id": str(repository_id),
        "count": len(integrations),
        "integrations": [
            {
                "id": str(i.id),
                "platform": i.platform,
                "fail_threshold": i.fail_threshold,
                "block_on_failure": i.block_on_failure,
            }
            for i in integrations
        ],
    }


@router.patch("/cicd/integrations/{integration_id}")
async def update_cicd_integration(
    integration_id: UUID,
    request: UpdateCICDIntegrationRequest,
):
    """Update CI/CD integration settings."""
    cicd = get_cicd_service()
    
    integration = await cicd.update_integration(
        integration_id=integration_id,
        fail_threshold=request.fail_threshold,
        warn_threshold=request.warn_threshold,
        block_on_failure=request.block_on_failure,
        regulations_required=request.regulations_required,
    )
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    return {
        "id": str(integration.id),
        "updated": True,
        "fail_threshold": integration.fail_threshold,
        "warn_threshold": integration.warn_threshold,
        "block_on_failure": integration.block_on_failure,
        "regulations_required": integration.regulations_required,
    }


@router.delete("/cicd/integrations/{integration_id}")
async def delete_cicd_integration(integration_id: UUID):
    """Delete a CI/CD integration."""
    cicd = get_cicd_service()
    deleted = await cicd.delete_integration(integration_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    return {"deleted": True, "id": str(integration_id)}


@router.post("/check")
async def run_compliance_check(
    request: RunCheckRequest,
    authorization: str = Header(..., description="Bearer token from CI/CD integration"),
):
    """Run a compliance check from CI/CD pipeline.
    
    Called by CI/CD systems with integration API token.
    Returns pass/fail status based on configured thresholds.
    """
    cicd = get_cicd_service()
    calculator = get_score_calculator()
    
    # Validate token
    token = authorization.replace("Bearer ", "").strip()
    integration = await cicd.validate_token(token)
    
    if not integration:
        raise HTTPException(status_code=401, detail="Invalid API token")
    
    # Calculate score
    score = await calculator.calculate_score(
        repository_id=integration.repository_id,
        regulations=integration.regulations_required,
        force_refresh=True,
    )
    
    # Run check
    result = await cicd.run_check(
        integration_id=integration.id,
        score=score,
        commit_sha=request.commit_sha,
        branch=request.branch,
        pr_number=request.pr_number,
    )
    
    status_code = 200 if result.passed else 422
    
    return Response(
        status_code=status_code,
        content={
            "passed": result.passed,
            "score": round(result.score, 2),
            "grade": result.grade.value,
            "summary": result.summary,
            "details": result.details,
            "commit_sha": result.commit_sha,
            "branch": result.branch,
        }.__str__(),
        media_type="application/json",
    )


@router.get("/cicd/integrations/{integration_id}/results")
async def get_check_results(
    integration_id: UUID,
    limit: int = 50,
):
    """Get recent compliance check results."""
    cicd = get_cicd_service()
    
    integration = await cicd.get_integration(integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    results = await cicd.get_results(integration_id, limit=limit)
    
    return {
        "integration_id": str(integration_id),
        "count": len(results),
        "results": [
            {
                "id": str(r.id),
                "passed": r.passed,
                "score": round(r.score, 2),
                "grade": r.grade.value,
                "commit_sha": r.commit_sha,
                "branch": r.branch,
                "pr_number": r.pr_number,
                "summary": r.summary,
                "created_at": r.created_at.isoformat(),
            }
            for r in results
        ],
    }


@router.get("/cicd/integrations/{integration_id}/snippet")
async def get_workflow_snippet(integration_id: UUID):
    """Get CI/CD workflow snippet for the integration."""
    cicd = get_cicd_service()
    
    integration = await cicd.get_integration(integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    snippet = cicd.generate_workflow_snippet(integration)
    
    return {
        "platform": integration.platform,
        "snippet": snippet,
    }


# Category Configuration
@router.put("/weights")
async def update_category_weights(request: UpdateWeightsRequest):
    """Update scoring weights for categories.
    
    Weights are automatically normalized to sum to 1.0.
    """
    calculator = get_score_calculator()
    
    for category_str, weight in request.weights.items():
        try:
            category = ScoreCategory(category_str)
            calculator.set_category_weight(category, weight)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category: {category_str}. Valid: {[c.value for c in ScoreCategory]}",
            )
    
    return {
        "updated": True,
        "weights": {c.value: w for c, w in calculator._weights.items()},
    }


@router.get("/categories")
async def list_categories():
    """List scoring categories with default weights."""
    from app.services.health_score.models import DEFAULT_WEIGHTS
    
    return {
        "categories": [
            {
                "value": c.value,
                "name": c.value.replace("_", " ").title(),
                "default_weight": DEFAULT_WEIGHTS[c],
            }
            for c in ScoreCategory
        ]
    }


@router.get("/grades")
async def list_grades():
    """List grade thresholds."""
    from app.services.health_score.models import GRADE_THRESHOLDS
    
    return {
        "grades": [
            {"grade": g.value, "minimum_score": t}
            for t, g in GRADE_THRESHOLDS
        ]
    }


@router.get("/cicd/platforms")
async def list_cicd_platforms():
    """List supported CI/CD platforms."""
    cicd = get_cicd_service()
    
    return {
        "platforms": [
            {"value": p, "name": p.replace("_", " ").title()}
            for p in cicd.SUPPORTED_PLATFORMS
        ]
    }
