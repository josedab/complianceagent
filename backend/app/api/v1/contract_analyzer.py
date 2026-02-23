"""API endpoints for Contract Analyzer."""


import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.contract_analyzer import ContractAnalyzerService


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---


class AnalyzeContractRequest(BaseModel):
    contract_name: str = Field(..., description="Name of the contract")
    contract_type: str = Field(..., description="Type of contract")
    vendor: str = Field(..., description="Vendor or counterparty name")
    contract_text: str = Field(..., description="Full contract text to analyze")


class ClauseSchema(BaseModel):
    id: str
    clause_type: str
    text: str
    risk_level: str
    recommendation: str


class AnalysisSchema(BaseModel):
    id: str
    contract_name: str
    contract_type: str
    vendor: str
    risk_score: float
    clauses: list[ClauseSchema]
    summary: str
    status: str
    created_at: str | None


class ContractStatsSchema(BaseModel):
    total_analyses: int
    high_risk_contracts: int
    average_risk_score: float
    clauses_flagged: int


# --- Endpoints ---


@router.post("/analyze", response_model=AnalysisSchema, status_code=status.HTTP_201_CREATED, summary="Analyze contract")
async def analyze_contract(request: AnalyzeContractRequest, db: DB) -> AnalysisSchema:
    service = ContractAnalyzerService(db=db)
    analysis = await service.analyze_contract(
        contract_name=request.contract_name,
        contract_type=request.contract_type,
        vendor=request.vendor,
        contract_text=request.contract_text,
    )
    logger.info("contract_analyzed", contract_name=request.contract_name, vendor=request.vendor)
    return AnalysisSchema(
        id=str(analysis.id), contract_name=analysis.contract_name,
        contract_type=analysis.contract_type, vendor=analysis.vendor,
        risk_score=analysis.risk_score,
        clauses=[
            ClauseSchema(
                id=str(c.id), clause_type=c.clause_type, text=c.text,
                risk_level=c.risk_level, recommendation=c.recommendation,
            )
            for c in analysis.clauses
        ],
        summary=analysis.summary, status=analysis.status,
        created_at=analysis.created_at.isoformat() if analysis.created_at else None,
    )


@router.get("/analyses", response_model=list[AnalysisSchema], summary="List analyses")
async def list_analyses(db: DB) -> list[AnalysisSchema]:
    service = ContractAnalyzerService(db=db)
    analyses = await service.list_analyses()
    return [
        AnalysisSchema(
            id=str(a.id), contract_name=a.contract_name,
            contract_type=a.contract_type, vendor=a.vendor,
            risk_score=a.risk_score,
            clauses=[
                ClauseSchema(
                    id=str(c.id), clause_type=c.clause_type, text=c.text,
                    risk_level=c.risk_level, recommendation=c.recommendation,
                )
                for c in a.clauses
            ],
            summary=a.summary, status=a.status,
            created_at=a.created_at.isoformat() if a.created_at else None,
        )
        for a in analyses
    ]


@router.get("/analyses/{analysis_id}", response_model=AnalysisSchema, summary="Get analysis")
async def get_analysis(analysis_id: str, db: DB) -> AnalysisSchema:
    service = ContractAnalyzerService(db=db)
    analysis = await service.get_analysis(analysis_id=analysis_id)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return AnalysisSchema(
        id=str(analysis.id), contract_name=analysis.contract_name,
        contract_type=analysis.contract_type, vendor=analysis.vendor,
        risk_score=analysis.risk_score,
        clauses=[
            ClauseSchema(
                id=str(c.id), clause_type=c.clause_type, text=c.text,
                risk_level=c.risk_level, recommendation=c.recommendation,
            )
            for c in analysis.clauses
        ],
        summary=analysis.summary, status=analysis.status,
        created_at=analysis.created_at.isoformat() if analysis.created_at else None,
    )


@router.get("/stats", response_model=ContractStatsSchema, summary="Get contract stats")
async def get_stats(db: DB) -> ContractStatsSchema:
    service = ContractAnalyzerService(db=db)
    s = await service.get_stats()
    return ContractStatsSchema(
        total_analyses=s.total_analyses,
        high_risk_contracts=s.high_risk_contracts,
        average_risk_score=s.average_risk_score,
        clauses_flagged=s.clauses_flagged,
    )
