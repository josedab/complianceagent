"""API endpoints for Regulatory Change Sentiment Analyzer."""

import structlog
from fastapi import APIRouter
from pydantic import BaseModel

from app.api.v1.deps import DB, CopilotDep
from app.services.sentiment_analyzer import SentimentAnalyzerService


logger = structlog.get_logger()
router = APIRouter()


class AnalyzeRequest(BaseModel):
    regulation: str
    jurisdiction: str | None = None


class SentimentSchema(BaseModel):
    id: str
    regulation: str
    jurisdiction: str
    trend: str
    sentiment: str
    enforcement_probability: float
    avg_fine_amount: float
    enforcement_count_ytd: int
    key_topics: list[str]
    analyzed_at: str | None


class EnforcementActionSchema(BaseModel):
    id: str
    regulation: str
    jurisdiction: str
    entity_fined: str
    fine_amount: float
    violation_type: str
    date: str
    summary: str


class HeatmapCellSchema(BaseModel):
    regulation: str
    jurisdiction: str
    risk_score: float
    trend: str
    color: str


class PrioritizationSchema(BaseModel):
    regulation: str
    priority_rank: int
    risk_score: float
    effort_estimate: str
    rationale: str
    enforcement_likelihood: float


class ReportSchema(BaseModel):
    total_regulations_analyzed: int
    high_risk_count: int
    heatmap: list[HeatmapCellSchema]
    top_priorities: list[PrioritizationSchema]
    generated_at: str | None


@router.post("/analyze", response_model=SentimentSchema, summary="Analyze regulatory sentiment")
async def analyze_sentiment(req: AnalyzeRequest, db: DB, copilot: CopilotDep) -> SentimentSchema:
    service = SentimentAnalyzerService(db=db, copilot_client=copilot)
    result = await service.analyze_sentiment(req.regulation, req.jurisdiction)
    return SentimentSchema(
        id=str(result.id),
        regulation=result.regulation,
        jurisdiction=result.jurisdiction,
        trend=result.trend.value,
        sentiment=result.sentiment.value,
        enforcement_probability=result.enforcement_probability,
        avg_fine_amount=result.avg_fine_amount,
        enforcement_count_ytd=result.enforcement_count_ytd,
        key_topics=result.key_topics,
        analyzed_at=result.analyzed_at.isoformat() if result.analyzed_at else None,
    )


@router.get("/sentiments", response_model=list[SentimentSchema], summary="List analyzed sentiments")
async def list_sentiments(
    db: DB, copilot: CopilotDep, jurisdiction: str | None = None
) -> list[SentimentSchema]:
    service = SentimentAnalyzerService(db=db, copilot_client=copilot)
    sentiments = await service.list_sentiments(jurisdiction)
    return [
        SentimentSchema(
            id=str(s.id),
            regulation=s.regulation,
            jurisdiction=s.jurisdiction,
            trend=s.trend.value,
            sentiment=s.sentiment.value,
            enforcement_probability=s.enforcement_probability,
            avg_fine_amount=s.avg_fine_amount,
            enforcement_count_ytd=s.enforcement_count_ytd,
            key_topics=s.key_topics,
            analyzed_at=s.analyzed_at.isoformat() if s.analyzed_at else None,
        )
        for s in sentiments
    ]


@router.get(
    "/enforcement-actions",
    response_model=list[EnforcementActionSchema],
    summary="Get enforcement actions",
)
async def get_enforcement_actions(
    db: DB,
    copilot: CopilotDep,
    regulation: str | None = None,
    limit: int = 20,
) -> list[EnforcementActionSchema]:
    service = SentimentAnalyzerService(db=db, copilot_client=copilot)
    actions = await service.get_enforcement_actions(regulation, limit)
    return [
        EnforcementActionSchema(
            id=str(a.id),
            regulation=a.regulation,
            jurisdiction=a.jurisdiction,
            entity_fined=a.entity_fined,
            fine_amount=a.fine_amount,
            violation_type=a.violation_type,
            date=a.date,
            summary=a.summary,
        )
        for a in actions
    ]


@router.get("/heatmap", response_model=list[HeatmapCellSchema], summary="Get risk heatmap")
async def get_risk_heatmap(db: DB, copilot: CopilotDep) -> list[HeatmapCellSchema]:
    service = SentimentAnalyzerService(db=db, copilot_client=copilot)
    cells = await service.get_risk_heatmap()
    return [
        HeatmapCellSchema(
            regulation=c.regulation,
            jurisdiction=c.jurisdiction,
            risk_score=c.risk_score,
            trend=c.trend.value,
            color=c.color,
        )
        for c in cells
    ]


@router.get(
    "/prioritization",
    response_model=list[PrioritizationSchema],
    summary="Get prioritization recommendations",
)
async def get_prioritization(db: DB, copilot: CopilotDep) -> list[PrioritizationSchema]:
    service = SentimentAnalyzerService(db=db, copilot_client=copilot)
    recs = await service.get_prioritization()
    return [
        PrioritizationSchema(
            regulation=r.regulation,
            priority_rank=r.priority_rank,
            risk_score=r.risk_score,
            effort_estimate=r.effort_estimate,
            rationale=r.rationale,
            enforcement_likelihood=r.enforcement_likelihood,
        )
        for r in recs
    ]


@router.get("/report", response_model=ReportSchema, summary="Generate sentiment report")
async def generate_report(db: DB, copilot: CopilotDep) -> ReportSchema:
    service = SentimentAnalyzerService(db=db, copilot_client=copilot)
    report = await service.generate_report()
    return ReportSchema(
        total_regulations_analyzed=report.total_regulations_analyzed,
        high_risk_count=report.high_risk_count,
        heatmap=[
            HeatmapCellSchema(
                regulation=c.regulation,
                jurisdiction=c.jurisdiction,
                risk_score=c.risk_score,
                trend=c.trend.value,
                color=c.color,
            )
            for c in report.heatmap
        ],
        top_priorities=[
            PrioritizationSchema(
                regulation=p.regulation,
                priority_rank=p.priority_rank,
                risk_score=p.risk_score,
                effort_estimate=p.effort_estimate,
                rationale=p.rationale,
                enforcement_likelihood=p.enforcement_likelihood,
            )
            for p in report.top_priorities
        ],
        generated_at=report.generated_at.isoformat() if report.generated_at else None,
    )
