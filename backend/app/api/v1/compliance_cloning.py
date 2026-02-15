"""API endpoints for Cross-Codebase Compliance Cloning."""

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.compliance_cloning import ComplianceCloningService

logger = structlog.get_logger()
router = APIRouter()


# --- Request/Response Models ---

class ReferenceRepoSchema(BaseModel):
    id: str
    name: str
    url: str
    description: str
    languages: list[str]
    frameworks: list[str]
    compliance_score: float
    patterns_count: int
    industry: str
    verified: bool


class RepoFingerprintSchema(BaseModel):
    repo_url: str
    languages: list[str]
    frameworks: list[str]
    cloud_providers: list[str]
    compliance_patterns: list[str]
    compliance_score: float


class ComplianceGapSchema(BaseModel):
    id: str
    category: str
    description: str
    severity: str
    reference_implementation: str
    suggested_fix: str
    estimated_effort_hours: float
    files_affected: list[str]


class MigrationPlanSchema(BaseModel):
    id: str
    source_repo: str
    target_repo: str
    status: str
    total_gaps: int
    gaps_resolved: int
    gaps: list[ComplianceGapSchema]
    estimated_total_hours: float
    compliance_score_before: float
    compliance_score_after: float


class GeneratePlanRequest(BaseModel):
    source_repo_id: str = Field(..., min_length=1, description="Reference repo ID to clone from")
    target_repo_url: str = Field(..., min_length=1, max_length=2000, description="Target repo URL")


# --- Endpoints ---

@router.get("/reference-repos", response_model=list[ReferenceRepoSchema])
async def list_reference_repos(
    industry: str | None = Query(None),
    language: str | None = Query(None),
) -> list[dict]:
    svc = ComplianceCloningService()
    repos = await svc.list_reference_repos(industry=industry, language=language)
    return [
        {"id": r.id, "name": r.name, "url": r.url, "description": r.description,
         "languages": r.languages, "frameworks": r.frameworks,
         "compliance_score": r.compliance_score, "patterns_count": r.patterns_count,
         "industry": r.industry, "verified": r.verified}
        for r in repos
    ]


@router.post("/fingerprint", response_model=RepoFingerprintSchema)
async def fingerprint_repo(repo_url: str = Query(...)) -> dict:
    svc = ComplianceCloningService()
    fp = await svc.fingerprint_repo(repo_url)
    return {
        "repo_url": fp.repo_url, "languages": fp.languages, "frameworks": fp.frameworks,
        "cloud_providers": fp.cloud_providers, "compliance_patterns": fp.compliance_patterns,
        "compliance_score": fp.compliance_score,
    }


@router.post("/similar", response_model=list[ReferenceRepoSchema])
async def find_similar_repos(repo_url: str = Query(...)) -> list[dict]:
    svc = ComplianceCloningService()
    repos = await svc.find_similar_repos(repo_url)
    return [
        {"id": r.id, "name": r.name, "url": r.url, "description": r.description,
         "languages": r.languages, "frameworks": r.frameworks,
         "compliance_score": r.compliance_score, "patterns_count": r.patterns_count,
         "industry": r.industry, "verified": r.verified}
        for r in repos
    ]


@router.post("/migration-plan", response_model=MigrationPlanSchema)
async def generate_migration_plan(req: GeneratePlanRequest) -> dict:
    svc = ComplianceCloningService()
    try:
        plan = await svc.generate_migration_plan(req.source_repo_id, req.target_repo_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "id": str(plan.id), "source_repo": plan.source_repo, "target_repo": plan.target_repo,
        "status": plan.status.value, "total_gaps": plan.total_gaps,
        "gaps_resolved": plan.gaps_resolved, "estimated_total_hours": plan.estimated_total_hours,
        "compliance_score_before": plan.compliance_score_before,
        "compliance_score_after": plan.compliance_score_after,
        "gaps": [
            {"id": g.id, "category": g.category.value, "description": g.description,
             "severity": g.severity, "reference_implementation": g.reference_implementation,
             "suggested_fix": g.suggested_fix, "estimated_effort_hours": g.estimated_effort_hours,
             "files_affected": g.files_affected}
            for g in plan.gaps
        ],
    }
