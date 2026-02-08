"""API endpoints for Federated Compliance Intelligence Network."""

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from uuid import UUID

from app.api.v1.deps import DB, CopilotDep
from app.services.compliance_intel import ComplianceIntelService, PrivacyLevel

logger = structlog.get_logger()
router = APIRouter()


class JoinNetworkRequest(BaseModel):
    organization_name: str = Field(..., min_length=1)
    industry: str = Field(...)
    size_category: str = Field(default="medium")
    privacy_level: str = Field(default="standard")


class ContributePatternRequest(BaseModel):
    participant_id: str = Field(...)
    framework: str = Field(...)
    control_id: str = Field(...)
    pattern_description: str = Field(...)
    effectiveness_score: float = Field(..., ge=0, le=100)


class ParticipantSchema(BaseModel):
    id: str
    organization_name: str
    industry: str
    status: str
    privacy_level: str
    contributed_patterns: int


class PatternSchema(BaseModel):
    id: str
    framework: str
    control_id: str
    pattern_description: str
    adoption_rate: float
    effectiveness_score: float
    industry: str
    noise_applied: bool


class InsightSchema(BaseModel):
    id: str
    insight_type: str
    title: str
    description: str
    framework: str
    industry: str
    relevance_score: float
    recommendations: list[str]


@router.post("/join", response_model=ParticipantSchema, status_code=status.HTTP_201_CREATED,
             summary="Join the federated network")
async def join_network(request: JoinNetworkRequest, db: DB, copilot: CopilotDep) -> ParticipantSchema:
    service = ComplianceIntelService(db=db, copilot_client=copilot)
    pl = PrivacyLevel(request.privacy_level) if request.privacy_level in [p.value for p in PrivacyLevel] else PrivacyLevel.STANDARD
    participant = await service.join_network(
        organization_name=request.organization_name, industry=request.industry,
        size_category=request.size_category, privacy_level=pl,
    )
    return ParticipantSchema(
        id=str(participant.id), organization_name=participant.organization_name,
        industry=participant.industry, status=participant.status.value,
        privacy_level=participant.privacy_level.value, contributed_patterns=participant.contributed_patterns,
    )


@router.post("/patterns", response_model=PatternSchema, status_code=status.HTTP_201_CREATED,
             summary="Contribute anonymized pattern")
async def contribute_pattern(request: ContributePatternRequest, db: DB, copilot: CopilotDep) -> PatternSchema:
    service = ComplianceIntelService(db=db, copilot_client=copilot)
    pattern = await service.contribute_pattern(
        participant_id=UUID(request.participant_id), framework=request.framework,
        control_id=request.control_id, pattern_description=request.pattern_description,
        effectiveness_score=request.effectiveness_score,
    )
    if not pattern:
        raise HTTPException(status_code=400, detail="Invalid participant or not active")
    return PatternSchema(
        id=str(pattern.id), framework=pattern.framework, control_id=pattern.control_id,
        pattern_description=pattern.pattern_description, adoption_rate=pattern.adoption_rate,
        effectiveness_score=pattern.effectiveness_score, industry=pattern.industry,
        noise_applied=pattern.noise_applied,
    )


@router.get("/patterns", response_model=list[PatternSchema], summary="Get compliance patterns")
async def get_patterns(db: DB, copilot: CopilotDep, framework: str | None = None,
                       industry: str | None = None) -> list[PatternSchema]:
    service = ComplianceIntelService(db=db, copilot_client=copilot)
    patterns = await service.get_patterns(framework=framework, industry=industry)
    return [PatternSchema(
        id=str(p.id), framework=p.framework, control_id=p.control_id,
        pattern_description=p.pattern_description, adoption_rate=p.adoption_rate,
        effectiveness_score=p.effectiveness_score, industry=p.industry, noise_applied=p.noise_applied,
    ) for p in patterns]


@router.get("/insights", response_model=list[InsightSchema], summary="Get federated insights")
async def get_insights(db: DB, copilot: CopilotDep, industry: str | None = None,
                       framework: str | None = None, limit: int = 10) -> list[InsightSchema]:
    service = ComplianceIntelService(db=db, copilot_client=copilot)
    insights = await service.get_insights(industry=industry, framework=framework, limit=limit)
    return [InsightSchema(
        id=str(i.id), insight_type=i.insight_type.value, title=i.title, description=i.description,
        framework=i.framework, industry=i.industry, relevance_score=i.relevance_score,
        recommendations=i.recommendations,
    ) for i in insights]


@router.get("/similar-orgs", summary="Get 'companies like you' insights")
async def similar_orgs(db: DB, copilot: CopilotDep, industry: str = "saas",
                       size_category: str = "medium") -> list[dict]:
    service = ComplianceIntelService(db=db, copilot_client=copilot)
    return await service.get_similar_orgs_insights(industry=industry, size_category=size_category)


@router.get("/stats", summary="Get network statistics")
async def get_stats(db: DB, copilot: CopilotDep) -> dict:
    service = ComplianceIntelService(db=db, copilot_client=copilot)
    stats = await service.get_network_stats()
    return {
        "total_participants": stats.total_participants, "active_participants": stats.active_participants,
        "total_patterns": stats.total_patterns, "total_insights": stats.total_insights,
        "industries": stats.industries_represented, "frameworks": stats.frameworks_covered,
    }
