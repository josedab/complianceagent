"""API endpoints for Compliance API Standard."""

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.compliance_api_standard import ComplianceAPIStandardService


logger = structlog.get_logger()
router = APIRouter()


class CheckConformanceRequest(BaseModel):
    api_base_url: str = Field(...)


class SpecSchema(BaseModel):
    version: str
    title: str
    description: str
    endpoints: list[dict]
    published_at: str | None


class VersionSchema(BaseModel):
    version: str
    status: str
    published_at: str | None


class ConformanceResultSchema(BaseModel):
    api_base_url: str
    version: str
    compliant: bool
    score: float
    checks_passed: int
    checks_total: int
    issues: list[dict]


class StatsSchema(BaseModel):
    total_specs: int
    total_conformance_checks: int
    avg_compliance_score: float
    compliant_apis: int


@router.get("/spec/{version}", response_model=SpecSchema, summary="Get spec by version")
async def get_spec(version: str, db: DB) -> SpecSchema:
    """Get the compliance API specification for a given version."""
    service = ComplianceAPIStandardService(db=db)
    spec = service.get_spec(version=version)
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Spec version not found"
        )
    return SpecSchema(
        version=spec.version,
        title=spec.title,
        description=spec.description,
        endpoints=spec.endpoints,
        published_at=spec.published_at.isoformat() if spec.published_at else None,
    )


@router.get("/versions", response_model=list[VersionSchema], summary="List versions")
async def list_versions(db: DB) -> list[VersionSchema]:
    """List all available spec versions."""
    service = ComplianceAPIStandardService(db=db)
    versions = service.list_versions()
    return [
        VersionSchema(
            version=v.version,
            status=v.status,
            published_at=v.published_at.isoformat() if v.published_at else None,
        )
        for v in versions
    ]


@router.post(
    "/conformance",
    response_model=ConformanceResultSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Check conformance",
)
async def check_conformance(
    request: CheckConformanceRequest, db: DB
) -> ConformanceResultSchema:
    """Check API conformance against the compliance standard."""
    service = ComplianceAPIStandardService(db=db)
    result = await service.check_conformance(api_base_url=request.api_base_url)
    return ConformanceResultSchema(
        api_base_url=result.api_base_url,
        version=result.version,
        compliant=result.compliant,
        score=result.score,
        checks_passed=result.checks_passed,
        checks_total=result.checks_total,
        issues=result.issues,
    )


@router.get("/stats", response_model=StatsSchema, summary="Get stats")
async def get_stats(db: DB) -> StatsSchema:
    """Get compliance API standard statistics."""
    service = ComplianceAPIStandardService(db=db)
    stats = service.get_stats()
    return StatsSchema(
        total_specs=stats.total_specs,
        total_conformance_checks=stats.total_conformance_checks,
        avg_compliance_score=stats.avg_compliance_score,
        compliant_apis=stats.compliant_apis,
    )
