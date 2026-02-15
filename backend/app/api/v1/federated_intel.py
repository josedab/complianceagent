"""API endpoints for Federated Compliance Intelligence Network."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CurrentOrganization, OrgMember
from app.services.federated_intel import (
    SharingLevel,
    ThreatCategory,
    get_federated_network,
)


router = APIRouter()


# Request/Response Models
class JoinNetworkRequest(BaseModel):
    industry: str
    region: str
    size_category: str = "medium"
    sharing_level: str = "industry"


class ContributeThreatRequest(BaseModel):
    title: str
    description: str
    category: str
    severity: str
    regulations: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)


class ContributePatternRequest(BaseModel):
    name: str
    description: str
    pattern_type: str  # "anti-pattern" or "best-practice"
    regulations: list[str] = Field(default_factory=list)
    code_patterns: list[str] = Field(default_factory=list)
    recommended_fix: str | None = None


class ThreatResponse(BaseModel):
    id: str
    title: str
    description: str
    category: str
    severity: str
    regulations: list[str]
    industries: list[str]
    recommended_actions: list[str]
    verified: bool
    first_seen: str


class PatternResponse(BaseModel):
    id: str
    name: str
    description: str
    pattern_type: str
    regulations: list[str]
    seen_count: int
    recommended_fix: str | None


class MemberResponse(BaseModel):
    id: str
    anonymous_id: str
    industry: str
    region: str
    reputation_score: float
    contributions_count: int


class NetworkStatsResponse(BaseModel):
    total_members: int
    active_members: int
    total_threats: int
    active_threats: int
    total_patterns: int
    industries_covered: list[str]
    regulations_covered: list[str]


# Endpoints
@router.post("/join", response_model=MemberResponse)
async def join_network(
    request: JoinNetworkRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> MemberResponse:
    """Join the federated compliance intelligence network."""
    network = get_federated_network()

    existing = await network.get_member(organization.id)
    if existing:
        raise HTTPException(status_code=400, detail="Already a network member")

    net_member = await network.join_network(
        organization_id=organization.id,
        industry=request.industry,
        region=request.region,
        size_category=request.size_category,
        sharing_level=SharingLevel(request.sharing_level),
    )

    return MemberResponse(
        id=str(net_member.id),
        anonymous_id=net_member.anonymous_id,
        industry=net_member.industry,
        region=net_member.region,
        reputation_score=net_member.reputation_score,
        contributions_count=net_member.contributions_count,
    )


@router.get("/stats", response_model=NetworkStatsResponse)
async def get_network_stats(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> NetworkStatsResponse:
    """Get network statistics."""
    network = get_federated_network()
    stats = await network.get_network_stats()

    return NetworkStatsResponse(
        total_members=stats.total_members,
        active_members=stats.active_members,
        total_threats=stats.total_threats,
        active_threats=stats.active_threats,
        total_patterns=stats.total_patterns,
        industries_covered=stats.industries_covered,
        regulations_covered=stats.regulations_covered,
    )


@router.get("/threats", response_model=list[ThreatResponse])
async def get_threats(
    category: str | None = None,
    regulation: str | None = None,
    severity: str | None = None,
    limit: int = 50,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> list[ThreatResponse]:
    """Get compliance threats from the network."""
    network = get_federated_network()
    net_member = await network.get_member(organization.id)

    if not net_member:
        raise HTTPException(status_code=403, detail="Not a network member")

    cat = ThreatCategory(category) if category else None
    from app.services.federated_intel.models import Severity
    sev = Severity(severity) if severity else None

    threats = await network.get_threats(
        member_id=net_member.id,
        category=cat,
        regulation=regulation,
        severity=sev,
        limit=limit,
    )

    return [
        ThreatResponse(
            id=str(t.id),
            title=t.title,
            description=t.description,
            category=t.category.value,
            severity=t.severity.value,
            regulations=t.regulations,
            industries=t.industries,
            recommended_actions=t.recommended_actions,
            verified=t.verified,
            first_seen=t.first_seen.isoformat(),
        )
        for t in threats
    ]


@router.post("/threats", response_model=ThreatResponse)
async def contribute_threat(
    request: ContributeThreatRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> ThreatResponse:
    """Contribute a new threat to the network."""
    network = get_federated_network()
    net_member = await network.get_member(organization.id)

    if not net_member:
        raise HTTPException(status_code=403, detail="Not a network member")

    threat = await network.contribute_threat(
        member_id=net_member.id,
        threat_data=request.model_dump(),
    )

    return ThreatResponse(
        id=str(threat.id),
        title=threat.title,
        description=threat.description,
        category=threat.category.value,
        severity=threat.severity.value,
        regulations=threat.regulations,
        industries=threat.industries,
        recommended_actions=threat.recommended_actions,
        verified=threat.verified,
        first_seen=threat.first_seen.isoformat(),
    )


@router.get("/patterns", response_model=list[PatternResponse])
async def get_patterns(
    pattern_type: str | None = None,
    regulation: str | None = None,
    limit: int = 50,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> list[PatternResponse]:
    """Get compliance patterns from the network."""
    network = get_federated_network()
    net_member = await network.get_member(organization.id)

    if not net_member:
        raise HTTPException(status_code=403, detail="Not a network member")

    patterns = await network.get_patterns(
        member_id=net_member.id,
        pattern_type=pattern_type,
        regulation=regulation,
        limit=limit,
    )

    return [
        PatternResponse(
            id=str(p.id),
            name=p.name,
            description=p.description,
            pattern_type=p.pattern_type,
            regulations=p.regulations,
            seen_count=p.seen_count,
            recommended_fix=p.recommended_fix,
        )
        for p in patterns
    ]


@router.post("/patterns", response_model=PatternResponse)
async def contribute_pattern(
    request: ContributePatternRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> PatternResponse:
    """Contribute a new pattern to the network."""
    network = get_federated_network()
    net_member = await network.get_member(organization.id)

    if not net_member:
        raise HTTPException(status_code=403, detail="Not a network member")

    pattern = await network.contribute_pattern(
        member_id=net_member.id,
        pattern_data=request.model_dump(),
    )

    return PatternResponse(
        id=str(pattern.id),
        name=pattern.name,
        description=pattern.description,
        pattern_type=pattern.pattern_type,
        regulations=pattern.regulations,
        seen_count=pattern.seen_count,
        recommended_fix=pattern.recommended_fix,
    )


@router.get("/feed")
async def get_threat_feed(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Get personalized threat feed."""
    network = get_federated_network()
    net_member = await network.get_member(organization.id)

    if not net_member:
        raise HTTPException(status_code=403, detail="Not a network member")

    threats = await network.get_threat_feed(net_member.id)

    return {
        "member_id": str(net_member.id),
        "feed_generated_at": datetime.utcnow().isoformat(),
        "threat_count": len(threats),
        "threats": [
            {
                "id": str(t.id),
                "title": t.title,
                "severity": t.severity.value,
                "category": t.category.value,
                "first_seen": t.first_seen.isoformat(),
            }
            for t in threats[:20]
        ],
    }


@router.get("/report")
async def generate_report(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Generate an intelligence report."""
    network = get_federated_network()
    net_member = await network.get_member(organization.id)

    if not net_member:
        raise HTTPException(status_code=403, detail="Not a network member")

    report = await network.generate_intelligence_report(net_member.id)

    return {
        "id": str(report.id),
        "title": report.title,
        "period": report.period,
        "summary": report.summary,
        "key_findings": report.key_findings,
        "active_threats": report.active_threats,
        "new_threats": report.new_threats,
        "top_threats": report.top_threats,
        "recommendations": report.recommendations,
        "priority_actions": report.priority_actions,
    }


@router.get("/benchmarks/{industry}")
async def get_benchmarks(
    industry: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Get industry compliance benchmarks."""
    network = get_federated_network()
    return await network.get_industry_benchmarks(industry)


class PrivacyConfigRequest(BaseModel):
    """Request to update privacy configuration."""

    epsilon: float | None = Field(default=None, ge=0.01, le=10.0)
    delta: float | None = Field(default=None, ge=0.0, le=0.1)
    noise_mechanism: str | None = None
    k_anonymity: int | None = Field(default=None, ge=2, le=100)
    suppress_small_groups: bool | None = None
    generalize_locations: bool | None = None
    hash_contributor_ids: bool | None = None
    retention_days: int | None = Field(default=None, ge=30, le=3650)
    auto_expire_threats: bool | None = None
    require_explicit_consent: bool | None = None
    allow_opt_out: bool | None = None
    data_minimization: bool | None = None


@router.get("/privacy")
async def get_privacy_config(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Get current privacy and anonymization settings."""
    network = get_federated_network()
    config = await network.get_privacy_config()
    return config.model_dump()


@router.put("/privacy")
async def update_privacy_config(
    request: PrivacyConfigRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Update privacy and anonymization settings."""
    network = get_federated_network()
    config = await network.update_privacy_config(**request.model_dump(exclude_none=True))
    return config.model_dump()


@router.get("/anonymization-summary")
async def get_anonymization_summary(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Get anonymization status summary for the network."""
    network = get_federated_network()
    return await network.get_anonymization_summary()


# Request/Response Models for new endpoints
class VerificationVoteRequest(BaseModel):
    voter_id: str
    vote: bool
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


class ContributorScoreResponse(BaseModel):
    member_id: str
    organization_name: str
    total_contributions: int
    verified_contributions: int
    accuracy_score: float
    reputation_tier: str
    first_contribution: str
    last_contribution: str


class ComparativeInsightResponse(BaseModel):
    insight_id: str
    metric_name: str
    your_value: float
    peer_average: float
    peer_median: float
    percentile: float
    sample_size: int
    industry: str
    description: str


class NetworkHealthResponse(BaseModel):
    total_members: int
    active_members_30d: int
    total_threats_shared: int
    total_patterns_shared: int
    avg_verification_rate: float
    avg_contribution_quality: float
    network_coverage_industries: int
    network_coverage_regulations: int
    top_contributors: list[ContributorScoreResponse]
    measured_at: str


@router.get("/contributors", response_model=list[ContributorScoreResponse])
async def get_contributor_scores(
    top_n: int = 20,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> list[ContributorScoreResponse]:
    """Get top contributor reputation scores."""
    network = get_federated_network()
    scores = await network.get_contributor_scores(top_n=top_n)
    return [
        ContributorScoreResponse(
            member_id=str(s.member_id),
            organization_name=s.organization_name,
            total_contributions=s.total_contributions,
            verified_contributions=s.verified_contributions,
            accuracy_score=s.accuracy_score,
            reputation_tier=s.reputation_tier,
            first_contribution=s.first_contribution.isoformat(),
            last_contribution=s.last_contribution.isoformat(),
        )
        for s in scores
    ]


@router.get("/insights/{industry}", response_model=list[ComparativeInsightResponse])
async def get_comparative_insights(
    industry: str,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> list[ComparativeInsightResponse]:
    """Get 'companies like yours' comparative insights for an organization."""
    network = get_federated_network()
    insights = await network.get_comparative_insights(
        organization_id=organization.id,
        industry=industry,
    )
    return [
        ComparativeInsightResponse(
            insight_id=str(i.insight_id),
            metric_name=i.metric_name,
            your_value=i.your_value,
            peer_average=i.peer_average,
            peer_median=i.peer_median,
            percentile=i.percentile,
            sample_size=i.sample_size,
            industry=i.industry,
            description=i.description,
        )
        for i in insights
    ]


@router.get("/health", response_model=NetworkHealthResponse)
async def get_network_health(
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> NetworkHealthResponse:
    """Get network health metrics."""
    network = get_federated_network()
    health = await network.get_network_health()
    return NetworkHealthResponse(
        total_members=health.total_members,
        active_members_30d=health.active_members_30d,
        total_threats_shared=health.total_threats_shared,
        total_patterns_shared=health.total_patterns_shared,
        avg_verification_rate=health.avg_verification_rate,
        avg_contribution_quality=health.avg_contribution_quality,
        network_coverage_industries=health.network_coverage_industries,
        network_coverage_regulations=health.network_coverage_regulations,
        top_contributors=[
            ContributorScoreResponse(
                member_id=str(s.member_id),
                organization_name=s.organization_name,
                total_contributions=s.total_contributions,
                verified_contributions=s.verified_contributions,
                accuracy_score=s.accuracy_score,
                reputation_tier=s.reputation_tier,
                first_contribution=s.first_contribution.isoformat(),
                last_contribution=s.last_contribution.isoformat(),
            )
            for s in health.top_contributors
        ],
        measured_at=health.measured_at.isoformat(),
    )


@router.post("/threats/{threat_id}/vote")
async def cast_verification_vote(
    threat_id: str,
    request: VerificationVoteRequest,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> dict[str, Any]:
    """Cast a verification vote on a shared threat."""
    network = get_federated_network()
    from uuid import UUID as _UUID
    try:
        result = await network.cast_verification_vote(
            threat_id=_UUID(threat_id),
            voter_id=_UUID(request.voter_id),
            vote=request.vote,
            confidence=request.confidence,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return result
