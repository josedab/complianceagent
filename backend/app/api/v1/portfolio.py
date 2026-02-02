"""Multi-repo compliance portfolio API endpoints."""

from datetime import datetime
from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CurrentOrganization, OrgMember, OrgAdmin
from app.services.portfolio import PortfolioService
from app.services.portfolio.models import RiskLevel, TrendDirection


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---

class FrameworkAggregationSchema(BaseModel):
    """Framework aggregation across portfolio."""
    framework: str
    average_score: float
    min_score: float
    max_score: float
    repositories_count: int
    compliant_repos: int
    at_risk_repos: int


class PortfolioSummarySchema(BaseModel):
    """Portfolio summary statistics."""
    portfolio_id: UUID
    portfolio_name: str
    total_repositories: int
    average_compliance_score: float
    overall_risk_level: str
    repos_grade_a: int
    repos_grade_b: int
    repos_grade_c: int
    repos_grade_d: int
    repos_grade_f: int
    repos_critical_risk: int
    repos_high_risk: int
    repos_medium_risk: int
    repos_low_risk: int
    total_critical_gaps: int
    total_major_gaps: int
    total_minor_gaps: int
    framework_aggregations: list[FrameworkAggregationSchema] = Field(default_factory=list)
    repositories_needing_attention: list[UUID] = Field(default_factory=list)


class RepositoryProfileSchema(BaseModel):
    """Repository compliance profile."""
    repository_id: UUID
    repository_name: str
    repository_url: str | None = None
    compliance_score: float
    compliance_grade: str
    risk_level: str
    total_requirements: int
    compliant_requirements: int
    critical_gaps: int
    major_gaps: int
    minor_gaps: int
    framework_scores: dict[str, float] = Field(default_factory=dict)
    trend: str
    last_scanned: datetime | None = None


class PortfolioResponseSchema(BaseModel):
    """Full portfolio response."""
    id: UUID
    organization_id: UUID
    name: str
    description: str | None = None
    repository_ids: list[UUID]
    tags: list[str] = Field(default_factory=list)
    summary: PortfolioSummarySchema | None = None
    repository_profiles: list[RepositoryProfileSchema] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class PortfolioListItemSchema(BaseModel):
    """Portfolio list item (without full details)."""
    id: UUID
    name: str
    description: str | None = None
    repository_count: int
    average_score: float
    overall_risk_level: str
    tags: list[str] = Field(default_factory=list)
    created_at: datetime


class CreatePortfolioRequest(BaseModel):
    """Request to create a portfolio."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    repository_ids: list[UUID] = Field(..., min_length=1, max_length=100)
    tags: list[str] = Field(default_factory=list)


class UpdatePortfolioRequest(BaseModel):
    """Request to update a portfolio."""
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    tags: list[str] | None = None


class ModifyRepositoriesRequest(BaseModel):
    """Request to add/remove repositories."""
    repository_ids: list[UUID] = Field(..., min_length=1)


class CrossRepoAnalysisSchema(BaseModel):
    """Cross-repository analysis results."""
    portfolio_id: UUID
    common_gaps: list[dict] = Field(default_factory=list)
    shared_risky_dependencies: list[dict] = Field(default_factory=list)
    framework_coverage: dict[str, dict] = Field(default_factory=dict)
    portfolio_recommendations: list[str] = Field(default_factory=list)
    analyzed_at: datetime


# --- Helper Functions ---

def _portfolio_to_schema(portfolio) -> PortfolioResponseSchema:
    """Convert Portfolio to response schema."""
    summary_schema = None
    if portfolio.summary:
        summary_schema = PortfolioSummarySchema(
            portfolio_id=portfolio.summary.portfolio_id,
            portfolio_name=portfolio.summary.portfolio_name,
            total_repositories=portfolio.summary.total_repositories,
            average_compliance_score=portfolio.summary.average_compliance_score,
            overall_risk_level=portfolio.summary.overall_risk_level.value,
            repos_grade_a=portfolio.summary.repos_grade_a,
            repos_grade_b=portfolio.summary.repos_grade_b,
            repos_grade_c=portfolio.summary.repos_grade_c,
            repos_grade_d=portfolio.summary.repos_grade_d,
            repos_grade_f=portfolio.summary.repos_grade_f,
            repos_critical_risk=portfolio.summary.repos_critical_risk,
            repos_high_risk=portfolio.summary.repos_high_risk,
            repos_medium_risk=portfolio.summary.repos_medium_risk,
            repos_low_risk=portfolio.summary.repos_low_risk,
            total_critical_gaps=portfolio.summary.total_critical_gaps,
            total_major_gaps=portfolio.summary.total_major_gaps,
            total_minor_gaps=portfolio.summary.total_minor_gaps,
            framework_aggregations=[
                FrameworkAggregationSchema(
                    framework=fa.framework,
                    average_score=fa.average_score,
                    min_score=fa.min_score,
                    max_score=fa.max_score,
                    repositories_count=fa.repositories_count,
                    compliant_repos=fa.compliant_repos,
                    at_risk_repos=fa.at_risk_repos,
                ) for fa in portfolio.summary.framework_aggregations
            ],
            repositories_needing_attention=portfolio.summary.repositories_needing_attention,
        )
    
    profile_schemas = [
        RepositoryProfileSchema(
            repository_id=p.repository_id,
            repository_name=p.repository_name,
            repository_url=p.repository_url,
            compliance_score=p.compliance_score,
            compliance_grade=p.compliance_grade,
            risk_level=p.risk_level.value,
            total_requirements=p.total_requirements,
            compliant_requirements=p.compliant_requirements,
            critical_gaps=p.critical_gaps,
            major_gaps=p.major_gaps,
            minor_gaps=p.minor_gaps,
            framework_scores=p.framework_scores,
            trend=p.trend.value,
            last_scanned=p.last_scanned,
        ) for p in portfolio.repository_profiles
    ]
    
    return PortfolioResponseSchema(
        id=portfolio.id,
        organization_id=portfolio.organization_id,
        name=portfolio.name,
        description=portfolio.description,
        repository_ids=portfolio.repository_ids,
        tags=portfolio.tags,
        summary=summary_schema,
        repository_profiles=profile_schemas,
        created_at=portfolio.created_at,
        updated_at=portfolio.updated_at,
    )


# --- Endpoints ---

@router.post(
    "/",
    response_model=PortfolioResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create portfolio",
    description="Create a new compliance portfolio with multiple repositories",
)
async def create_portfolio(
    request: CreatePortfolioRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> PortfolioResponseSchema:
    """
    Create a new compliance portfolio.
    
    A portfolio groups multiple repositories for unified compliance
    tracking and reporting.
    """
    service = PortfolioService(db=db)
    
    portfolio = await service.create_portfolio(
        organization_id=organization.id,
        name=request.name,
        description=request.description,
        repository_ids=request.repository_ids,
        created_by=member.user_id,
        tags=request.tags,
    )
    
    return _portfolio_to_schema(portfolio)


@router.get(
    "/",
    response_model=list[PortfolioListItemSchema],
    summary="List portfolios",
    description="Get all portfolios for the organization",
)
async def list_portfolios(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> list[PortfolioListItemSchema]:
    """List all compliance portfolios for the organization."""
    service = PortfolioService(db=db)
    
    portfolios = await service.list_portfolios(
        organization_id=organization.id,
        include_summaries=True,
    )
    
    return [
        PortfolioListItemSchema(
            id=p.id,
            name=p.name,
            description=p.description,
            repository_count=len(p.repository_ids),
            average_score=p.summary.average_compliance_score if p.summary else 0,
            overall_risk_level=p.summary.overall_risk_level.value if p.summary else "unknown",
            tags=p.tags,
            created_at=p.created_at,
        ) for p in portfolios
    ]


@router.get(
    "/{portfolio_id}",
    response_model=PortfolioResponseSchema,
    summary="Get portfolio",
    description="Get portfolio details with repository profiles",
)
async def get_portfolio(
    portfolio_id: UUID,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    include_trends: bool = Query(False, description="Include historical trends"),
) -> PortfolioResponseSchema:
    """Get a specific portfolio with full details."""
    service = PortfolioService(db=db)
    
    portfolio = await service.get_portfolio(
        portfolio_id=portfolio_id,
        include_profiles=True,
        include_trends=include_trends,
    )
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found",
        )
    
    if portfolio.organization_id != organization.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Portfolio not accessible",
        )
    
    return _portfolio_to_schema(portfolio)


@router.patch(
    "/{portfolio_id}",
    response_model=PortfolioResponseSchema,
    summary="Update portfolio",
    description="Update portfolio metadata",
)
async def update_portfolio(
    portfolio_id: UUID,
    request: UpdatePortfolioRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> PortfolioResponseSchema:
    """Update portfolio name, description, or tags."""
    service = PortfolioService(db=db)
    
    # Get existing to check ownership
    existing = await service.get_portfolio(portfolio_id, include_profiles=False)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found",
        )
    
    if existing.organization_id != organization.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Portfolio not accessible",
        )
    
    portfolio = await service.update_portfolio(
        portfolio_id=portfolio_id,
        name=request.name,
        description=request.description,
        tags=request.tags,
    )
    
    return _portfolio_to_schema(portfolio)


@router.delete(
    "/{portfolio_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete portfolio",
    description="Delete a portfolio (does not delete repositories)",
)
async def delete_portfolio(
    portfolio_id: UUID,
    organization: CurrentOrganization,
    admin: OrgAdmin,
    db: DB,
) -> None:
    """Delete a portfolio. Requires admin access."""
    service = PortfolioService(db=db)
    
    # Check ownership
    existing = await service.get_portfolio(portfolio_id, include_profiles=False)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found",
        )
    
    if existing.organization_id != organization.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Portfolio not accessible",
        )
    
    await service.delete_portfolio(portfolio_id)


@router.post(
    "/{portfolio_id}/repositories",
    response_model=PortfolioResponseSchema,
    summary="Add repositories",
    description="Add repositories to a portfolio",
)
async def add_repositories(
    portfolio_id: UUID,
    request: ModifyRepositoriesRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> PortfolioResponseSchema:
    """Add repositories to an existing portfolio."""
    service = PortfolioService(db=db)
    
    portfolio = await service.add_repositories(
        portfolio_id=portfolio_id,
        repository_ids=request.repository_ids,
    )
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found",
        )
    
    return _portfolio_to_schema(portfolio)


@router.delete(
    "/{portfolio_id}/repositories",
    response_model=PortfolioResponseSchema,
    summary="Remove repositories",
    description="Remove repositories from a portfolio",
)
async def remove_repositories(
    portfolio_id: UUID,
    request: ModifyRepositoriesRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> PortfolioResponseSchema:
    """Remove repositories from a portfolio."""
    service = PortfolioService(db=db)
    
    portfolio = await service.remove_repositories(
        portfolio_id=portfolio_id,
        repository_ids=request.repository_ids,
    )
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found",
        )
    
    return _portfolio_to_schema(portfolio)


@router.get(
    "/{portfolio_id}/analysis",
    response_model=CrossRepoAnalysisSchema,
    summary="Cross-repo analysis",
    description="Get cross-repository analysis for the portfolio",
)
async def get_cross_repo_analysis(
    portfolio_id: UUID,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> CrossRepoAnalysisSchema:
    """
    Analyze patterns across all repositories in the portfolio.
    
    Identifies common compliance gaps, shared risky dependencies,
    and provides portfolio-level recommendations.
    """
    service = PortfolioService(db=db)
    
    analysis = await service.get_cross_repo_analysis(portfolio_id)
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found",
        )
    
    return CrossRepoAnalysisSchema(
        portfolio_id=analysis.portfolio_id,
        common_gaps=analysis.common_gaps,
        shared_risky_dependencies=analysis.shared_risky_dependencies,
        framework_coverage=analysis.framework_coverage,
        portfolio_recommendations=analysis.portfolio_recommendations,
        analyzed_at=analysis.analyzed_at,
    )


@router.get(
    "/{portfolio_id}/heat-map",
    summary="Get compliance heat map",
    description="Get heat map data for portfolio visualization",
)
async def get_heat_map(
    portfolio_id: UUID,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict:
    """
    Get heat map data showing compliance status across
    repositories and frameworks.
    """
    service = PortfolioService(db=db)
    
    portfolio = await service.get_portfolio(
        portfolio_id=portfolio_id,
        include_profiles=True,
    )
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found",
        )
    
    # Build heat map data
    heat_map = {
        "repositories": [],
        "frameworks": set(),
    }
    
    for profile in portfolio.repository_profiles:
        repo_data = {
            "id": str(profile.repository_id),
            "name": profile.repository_name,
            "scores": profile.framework_scores,
        }
        heat_map["repositories"].append(repo_data)
        heat_map["frameworks"].update(profile.framework_scores.keys())
    
    heat_map["frameworks"] = sorted(list(heat_map["frameworks"]))
    
    return heat_map


@router.get(
    "/{portfolio_id}/export",
    summary="Export portfolio report",
    description="Export portfolio compliance report",
)
async def export_report(
    portfolio_id: UUID,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    format: str = Query("json", enum=["json", "csv"]),
) -> dict:
    """Export portfolio compliance data for reporting."""
    service = PortfolioService(db=db)
    
    portfolio = await service.get_portfolio(
        portfolio_id=portfolio_id,
        include_profiles=True,
    )
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found",
        )
    
    if format == "csv":
        # Build CSV data
        rows = [
            ["Repository", "Score", "Grade", "Risk Level", "Critical Gaps", "Major Gaps"]
        ]
        for p in portfolio.repository_profiles:
            rows.append([
                p.repository_name,
                str(p.compliance_score),
                p.compliance_grade,
                p.risk_level.value,
                str(p.critical_gaps),
                str(p.major_gaps),
            ])
        
        csv_content = "\n".join([",".join(row) for row in rows])
        
        return {
            "format": "csv",
            "content": csv_content,
            "filename": f"portfolio_{portfolio_id}_report.csv",
        }
    
    # JSON format
    return {
        "format": "json",
        "portfolio": _portfolio_to_schema(portfolio).model_dump(),
        "exported_at": datetime.utcnow().isoformat(),
    }
