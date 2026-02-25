"""API endpoints for Compliance Data Network."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB


logger = structlog.get_logger()
router = APIRouter()


def _serialize(obj: Any) -> dict[str, Any]:
    """Convert a dataclass to a JSON-serializable dict."""
    from dataclasses import fields, is_dataclass

    if not is_dataclass(obj):
        return obj

    result = {}
    for f in fields(obj):
        v = getattr(obj, f.name)
        result[f.name] = _ser_val(v)
    return result


def _ser_val(v: Any) -> Any:
    from dataclasses import is_dataclass
    from datetime import datetime
    from enum import Enum
    from uuid import UUID

    if v is None:
        return None
    if isinstance(v, Enum):
        return v.value
    if isinstance(v, UUID):
        return str(v)
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, list):
        return [_ser_val(item) for item in v]
    if isinstance(v, dict):
        return {k: _ser_val(val) for k, val in v.items()}
    if is_dataclass(v):
        return _serialize(v)
    return v


# --- Schemas ---


class JoinNetworkRequest(BaseModel):
    industry: str = Field(
        ..., description="Industry vertical (e.g. 'fintech', 'healthcare', 'saas')"
    )
    size_bucket: str = Field(
        ..., description="Organization size bucket (e.g. 'startup', 'mid-market', 'enterprise')"
    )


class NetworkMemberResponse(BaseModel):
    model_config = {"extra": "ignore"}
    id: UUID | None = None
    industry: str = ""
    size_bucket: str = ""
    joined_at: str = ""
    anonymized_id: str = ""


class BenchmarkResponse(BaseModel):
    model_config = {"extra": "ignore"}
    industry: str = ""
    avg_compliance_score: float = 0.0
    median_score: float = 0.0
    top_quartile_score: float = 0.0
    frameworks_adopted: dict[str, float] = Field(default_factory=dict)
    common_gaps: list[str] = Field(default_factory=list)
    sample_size: int = 0


class ReportThreatRequest(BaseModel):
    title: str = Field(..., description="Threat title")
    description: str = Field(..., description="Detailed threat description")
    frameworks: list[str] = Field(
        default_factory=list, description="Affected compliance frameworks"
    )
    severity: str = Field(..., description="Severity level (critical, high, medium, low)")


class ThreatResponse(BaseModel):
    model_config = {"extra": "ignore"}
    id: UUID | None = None
    title: str = ""
    description: str = ""
    frameworks: list[str] = Field(default_factory=list)
    severity: str = ""
    reported_at: str = ""
    confirmations: int = 0


class ThreatListResponse(BaseModel):
    model_config = {"extra": "ignore"}
    threats: list[ThreatResponse] = Field(default_factory=list)
    total: int = 0


class NetworkStatsResponse(BaseModel):
    model_config = {"extra": "ignore"}
    total_members: int = 0
    industries_represented: int = 0
    total_threats_reported: int = 0
    total_patterns_shared: int = 0
    avg_member_score: float = 0.0
    stats: dict[str, Any] = Field(default_factory=dict)


class IndustryComparisonResponse(BaseModel):
    model_config = {"extra": "ignore"}
    industry: str = ""
    your_score: float = 0.0
    industry_avg: float = 0.0
    percentile: float = 0.0
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class ContributePatternRequest(BaseModel):
    title: str = Field(..., description="Pattern title")
    description: str = Field(..., description="Pattern description")
    framework: str = Field(..., description="Related compliance framework")
    category: str = Field(..., description="Pattern category")
    implementation: str = Field("", description="Implementation guidance")


class PatternResponse(BaseModel):
    model_config = {"extra": "ignore"}
    id: UUID | None = None
    title: str = ""
    description: str = ""
    framework: str = ""
    category: str = ""
    contributed_at: str = ""
    adoption_count: int = 0


# --- Endpoints ---


@router.post(
    "/join",
    response_model=NetworkMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Join the compliance data network",
)
async def join_network(request: JoinNetworkRequest, db: DB) -> NetworkMemberResponse:
    """Join the anonymized compliance data network."""
    from app.services.compliance_network import (
        ComplianceNetworkService as ComplianceDataNetworkService,
    )

    service = ComplianceDataNetworkService(db=db)
    member = await service.join_network(organization_id=request.industry)
    return (
        NetworkMemberResponse(**member)
        if isinstance(member, dict)
        else NetworkMemberResponse(**_serialize(member))
    )


@router.get(
    "/benchmarks/{industry}", response_model=BenchmarkResponse, summary="Get industry benchmarks"
)
async def get_benchmarks(industry: str, db: DB) -> BenchmarkResponse:
    """Get compliance benchmarks for a specific industry."""
    from app.services.compliance_network import (
        ComplianceNetworkService as ComplianceDataNetworkService,
    )

    service = ComplianceDataNetworkService(db=db)
    benchmarks = await service.get_benchmarks(industry=industry)
    if not benchmarks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Industry not found in network"
        )
    return BenchmarkResponse(**_serialize(benchmarks))


@router.post(
    "/threats",
    response_model=ThreatResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Report a compliance threat",
)
async def report_threat(request: ReportThreatRequest, db: DB) -> ThreatResponse:
    """Report a new compliance threat to the network."""
    from app.services.compliance_network import (
        ComplianceNetworkService as ComplianceDataNetworkService,
    )

    service = ComplianceDataNetworkService(db=db)
    threat = await service.report_threat(
        title=request.title,
        description=request.description,
        frameworks=request.frameworks,
        severity=request.severity,
    )
    return ThreatResponse(**_serialize(threat))


@router.get("/threats", response_model=ThreatListResponse, summary="List recent threats")
async def list_threats(db: DB) -> ThreatListResponse:
    """List recent compliance threats reported to the network."""
    from app.services.compliance_network import (
        ComplianceNetworkService as ComplianceDataNetworkService,
    )

    service = ComplianceDataNetworkService(db=db)
    threats = await service.list_threats()
    return ThreatListResponse(
        threats=[ThreatResponse(**_serialize(t)) for t in threats],
        total=len(threats),
    )


@router.get("/stats", response_model=NetworkStatsResponse, summary="Get network statistics")
async def get_network_stats(db: DB) -> NetworkStatsResponse:
    """Get overall statistics for the compliance data network."""
    from app.services.compliance_network import (
        ComplianceNetworkService as ComplianceDataNetworkService,
    )

    service = ComplianceDataNetworkService(db=db)
    stats = await service.get_network_stats()
    return NetworkStatsResponse(**_serialize(stats))


@router.get(
    "/comparison/{industry}",
    response_model=IndustryComparisonResponse,
    summary="Get industry comparison",
)
async def get_industry_comparison(industry: str, db: DB) -> IndustryComparisonResponse:
    """Get a comparison of your compliance posture against industry peers."""
    from app.services.compliance_network import (
        ComplianceNetworkService as ComplianceDataNetworkService,
    )

    service = ComplianceDataNetworkService(db=db)
    comparison = await service.get_industry_comparison(industry=industry)
    if not comparison:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Industry not found in network"
        )
    return IndustryComparisonResponse(**_serialize(comparison))


@router.post(
    "/contribute",
    response_model=PatternResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Contribute a compliance pattern",
)
async def contribute_pattern(request: ContributePatternRequest, db: DB) -> PatternResponse:
    """Contribute a compliance pattern to the network."""
    from app.services.compliance_network import (
        ComplianceNetworkService as ComplianceDataNetworkService,
    )

    service = ComplianceDataNetworkService(db=db)
    pattern = await service.contribute_pattern(
        title=request.title,
        description=request.description,
        framework=request.framework,
        category=request.category,
        implementation=request.implementation,
    )
    return PatternResponse(**_serialize(pattern))
