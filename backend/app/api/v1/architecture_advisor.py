"""API endpoints for Regulation-to-Architecture Advisor."""


import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep
from app.services.architecture_advisor import (
    ArchitectureAdvisorService,
)


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---


class AnalyzeRequest(BaseModel):
    """Request to analyze architecture for compliance."""

    repo: str = Field(..., min_length=1, description="Repository name")
    files: list[str] = Field(default_factory=list, description="File paths to analyze")
    regulations: list[str] = Field(default_factory=list, description="Regulations to check against")


class PatternSchema(BaseModel):
    """Detected architecture pattern."""

    pattern_type: str
    confidence: float
    evidence: list[str]
    description: str


class RiskSchema(BaseModel):
    """Compliance risk in architecture."""

    id: str
    pattern: str
    regulation: str
    severity: str
    title: str
    description: str
    affected_components: list[str]
    recommendation: str


class RecommendationSchema(BaseModel):
    """Architecture recommendation."""

    id: str
    title: str
    description: str
    regulation: str
    current_pattern: str
    recommended_pattern: str
    effort_estimate_days: int
    impact: str
    trade_offs: list[str]


class ScoreSchema(BaseModel):
    """Architecture compliance score."""

    overall_score: int
    data_isolation_score: int
    encryption_score: int
    audit_trail_score: int
    access_control_score: int
    data_flow_score: int
    max_score: int
    grade: str
    risks_found: int
    recommendations_count: int


class DesignReviewSchema(BaseModel):
    """Design review result."""

    id: str
    repo: str
    detected_patterns: list[PatternSchema]
    risks: list[RiskSchema]
    recommendations: list[RecommendationSchema]
    score: ScoreSchema
    regulations_analyzed: list[str]


class PatternInfoSchema(BaseModel):
    """Pattern info with compliance notes."""

    type: str
    name: str
    compliance_notes: str


# --- Endpoints ---


@router.post(
    "/analyze",
    response_model=DesignReviewSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Analyze architecture for compliance",
    description="Analyze repository architecture and identify compliance risks",
)
async def analyze_architecture(
    request: AnalyzeRequest,
    db: DB,
    copilot: CopilotDep,
) -> DesignReviewSchema:
    """Analyze architecture for compliance risks and recommendations."""
    service = ArchitectureAdvisorService(db=db, copilot_client=copilot)
    result = await service.analyze_architecture(
        repo=request.repo,
        files=request.files or None,
        regulations=request.regulations or None,
    )

    return DesignReviewSchema(
        id=str(result.id),
        repo=result.repo,
        detected_patterns=[
            PatternSchema(
                pattern_type=p.pattern_type.value, confidence=p.confidence,
                evidence=p.evidence, description=p.description,
            )
            for p in result.detected_patterns
        ],
        risks=[
            RiskSchema(
                id=str(r.id), pattern=r.pattern.value, regulation=r.regulation,
                severity=r.severity.value, title=r.title, description=r.description,
                affected_components=r.affected_components, recommendation=r.recommendation,
            )
            for r in result.risks
        ],
        recommendations=[
            RecommendationSchema(
                id=str(r.id), title=r.title, description=r.description,
                regulation=r.regulation, current_pattern=r.current_pattern.value,
                recommended_pattern=r.recommended_pattern,
                effort_estimate_days=r.effort_estimate_days,
                impact=r.impact.value, trade_offs=r.trade_offs,
            )
            for r in result.recommendations
        ],
        score=ScoreSchema(
            overall_score=result.score.overall_score,
            data_isolation_score=result.score.data_isolation_score,
            encryption_score=result.score.encryption_score,
            audit_trail_score=result.score.audit_trail_score,
            access_control_score=result.score.access_control_score,
            data_flow_score=result.score.data_flow_score,
            max_score=result.score.max_score,
            grade=result.score.grade,
            risks_found=result.score.risks_found,
            recommendations_count=result.score.recommendations_count,
        ),
        regulations_analyzed=result.regulations_analyzed,
    )


@router.get(
    "/patterns",
    response_model=list[PatternInfoSchema],
    summary="List architecture patterns",
)
async def list_patterns(
    db: DB,
    copilot: CopilotDep,
) -> list[PatternInfoSchema]:
    """List known architectural patterns with compliance notes."""
    service = ArchitectureAdvisorService(db=db, copilot_client=copilot)
    patterns = await service.list_patterns()
    return [
        PatternInfoSchema(type=p["type"], name=p["name"], compliance_notes=p["compliance_notes"])
        for p in patterns
    ]


@router.get(
    "/score/{repo:path}",
    response_model=ScoreSchema,
    summary="Get architecture compliance score",
)
async def get_score(
    repo: str,
    db: DB,
    copilot: CopilotDep,
) -> ScoreSchema:
    """Get the latest architecture compliance score for a repository."""
    service = ArchitectureAdvisorService(db=db, copilot_client=copilot)
    score = await service.get_score(repo)
    if not score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No architecture review found for {repo}",
        )
    return ScoreSchema(
        overall_score=score.overall_score,
        data_isolation_score=score.data_isolation_score,
        encryption_score=score.encryption_score,
        audit_trail_score=score.audit_trail_score,
        access_control_score=score.access_control_score,
        data_flow_score=score.data_flow_score,
        max_score=score.max_score,
        grade=score.grade,
        risks_found=score.risks_found,
        recommendations_count=score.recommendations_count,
    )
