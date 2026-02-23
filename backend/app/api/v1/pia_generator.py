"""API endpoints for Privacy Impact Assessment (PIA) Generator."""


import structlog
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.pia_generator import PIAGeneratorService


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---


class GeneratePIARequest(BaseModel):
    repo: str = Field(..., description="Repository to assess")
    title: str = Field(..., description="Assessment title")


class ApprovePIARequest(BaseModel):
    approver: str = Field(..., description="Approver name or identifier")


class ExportPIARequest(BaseModel):
    format: str = Field(default="pdf", description="Export format (pdf, html, markdown)")


class PIAFindingSchema(BaseModel):
    category: str
    description: str
    severity: str
    recommendation: str


class PIASchema(BaseModel):
    id: str
    repo: str
    title: str
    status: str
    findings: list[PIAFindingSchema]
    risk_score: float
    approved_by: str | None
    approved_at: str | None
    created_at: str | None


class PIAStatsSchema(BaseModel):
    total_assessments: int
    pending_approval: int
    approved: int
    average_risk_score: float


# --- Endpoints ---


@router.post("/assessments", response_model=PIASchema, status_code=status.HTTP_201_CREATED, summary="Generate PIA")
async def generate_pia(request: GeneratePIARequest, db: DB) -> PIASchema:
    service = PIAGeneratorService(db=db)
    pia = await service.generate_pia(repo=request.repo, title=request.title)
    logger.info("pia_generated", repo=request.repo, title=request.title)
    return PIASchema(
        id=str(pia.id), repo=pia.repo, title=pia.title, status=pia.status,
        findings=[
            PIAFindingSchema(category=f.category, description=f.description, severity=f.severity, recommendation=f.recommendation)
            for f in pia.findings
        ],
        risk_score=pia.risk_score, approved_by=pia.approved_by,
        approved_at=pia.approved_at.isoformat() if pia.approved_at else None,
        created_at=pia.created_at.isoformat() if pia.created_at else None,
    )


@router.post("/assessments/{assessment_id}/approve", summary="Approve PIA")
async def approve_pia(assessment_id: str, request: ApprovePIARequest, db: DB) -> dict:
    service = PIAGeneratorService(db=db)
    result = await service.approve_pia(assessment_id=assessment_id, approver=request.approver)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    logger.info("pia_approved", assessment_id=assessment_id, approver=request.approver)
    return {"assessment_id": assessment_id, "status": "approved", "approver": request.approver}


@router.post("/assessments/{assessment_id}/export", summary="Export PIA")
async def export_pia(assessment_id: str, request: ExportPIARequest, db: DB) -> dict:
    service = PIAGeneratorService(db=db)
    export = await service.export_pia(assessment_id=assessment_id, format=request.format)
    if not export:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    logger.info("pia_exported", assessment_id=assessment_id, format=request.format)
    return {"assessment_id": assessment_id, "format": request.format, "download_url": export}


@router.get("/assessments", response_model=list[PIASchema], summary="List PIAs")
async def list_pias(db: DB, status_filter: str | None = Query(None, alias="status")) -> list[PIASchema]:
    service = PIAGeneratorService(db=db)
    pias = await service.list_pias(status_filter=status_filter)
    return [
        PIASchema(
            id=str(p.id), repo=p.repo, title=p.title, status=p.status,
            findings=[
                PIAFindingSchema(category=f.category, description=f.description, severity=f.severity, recommendation=f.recommendation)
                for f in p.findings
            ],
            risk_score=p.risk_score, approved_by=p.approved_by,
            approved_at=p.approved_at.isoformat() if p.approved_at else None,
            created_at=p.created_at.isoformat() if p.created_at else None,
        )
        for p in pias
    ]


@router.get("/stats", response_model=PIAStatsSchema, summary="Get PIA stats")
async def get_stats(db: DB) -> PIAStatsSchema:
    service = PIAGeneratorService(db=db)
    s = await service.get_stats()
    return PIAStatsSchema(
        total_assessments=s.total_assessments,
        pending_approval=s.pending_approval,
        approved=s.approved,
        average_risk_score=s.average_risk_score,
    )
