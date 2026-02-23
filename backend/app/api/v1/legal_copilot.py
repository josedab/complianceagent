"""API endpoints for Legal Copilot."""

from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.legal_copilot import LegalCopilotService


logger = structlog.get_logger()
router = APIRouter()


class GenerateDPARequest(BaseModel):
    parties: list[str] = Field(...)
    frameworks: list[str] = Field(default_factory=list)
    jurisdiction: str = Field(...)


class GenerateLegalMemoRequest(BaseModel):
    topic: str = Field(...)
    framework: str = Field(...)
    jurisdiction: str = Field(...)


class ReviewContractClauseRequest(BaseModel):
    clause_text: str = Field(...)


class ApproveDocumentRequest(BaseModel):
    reviewer: str = Field(...)


class DocumentSchema(BaseModel):
    id: str
    document_type: str
    title: str
    status: str
    jurisdiction: str
    content: str
    created_at: str | None


class ClauseReviewSchema(BaseModel):
    id: str
    clause_text: str
    risk_level: str
    issues: list[dict]
    suggestions: list[str]
    compliant: bool


class StatsSchema(BaseModel):
    total_documents: int
    dpas_generated: int
    memos_generated: int
    clauses_reviewed: int
    approved_documents: int
    avg_risk_score: float


@router.post(
    "/dpa",
    response_model=DocumentSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Generate DPA",
)
async def generate_dpa(request: GenerateDPARequest, db: DB) -> DocumentSchema:
    """Generate a Data Processing Agreement."""
    service = LegalCopilotService(db=db)
    doc = await service.generate_dpa(
        parties=request.parties,
        frameworks=request.frameworks,
        jurisdiction=request.jurisdiction,
    )
    return DocumentSchema(
        id=str(doc.id),
        document_type=doc.document_type,
        title=doc.title,
        status=doc.status,
        jurisdiction=doc.jurisdiction,
        content=doc.content,
        created_at=doc.created_at.isoformat() if doc.created_at else None,
    )


@router.post(
    "/memo",
    response_model=DocumentSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Generate legal memo",
)
async def generate_legal_memo(
    request: GenerateLegalMemoRequest, db: DB
) -> DocumentSchema:
    """Generate a legal memorandum."""
    service = LegalCopilotService(db=db)
    doc = await service.generate_legal_memo(
        topic=request.topic,
        framework=request.framework,
        jurisdiction=request.jurisdiction,
    )
    return DocumentSchema(
        id=str(doc.id),
        document_type=doc.document_type,
        title=doc.title,
        status=doc.status,
        jurisdiction=doc.jurisdiction,
        content=doc.content,
        created_at=doc.created_at.isoformat() if doc.created_at else None,
    )


@router.post(
    "/review-clause",
    response_model=ClauseReviewSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Review contract clause",
)
async def review_contract_clause(
    request: ReviewContractClauseRequest, db: DB
) -> ClauseReviewSchema:
    """Review a contract clause for compliance issues."""
    service = LegalCopilotService(db=db)
    review = await service.review_contract_clause(clause_text=request.clause_text)
    return ClauseReviewSchema(
        id=str(review.id),
        clause_text=review.clause_text,
        risk_level=review.risk_level,
        issues=review.issues,
        suggestions=review.suggestions,
        compliant=review.compliant,
    )


@router.post("/documents/{document_id}/approve", summary="Approve document")
async def approve_document(
    document_id: UUID, request: ApproveDocumentRequest, db: DB
) -> dict:
    """Approve a legal document."""
    service = LegalCopilotService(db=db)
    ok = await service.approve_document(
        document_id=document_id, reviewer=request.reviewer
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    return {"status": "approved", "document_id": str(document_id)}


@router.get(
    "/documents", response_model=list[DocumentSchema], summary="List documents"
)
async def list_documents(db: DB) -> list[DocumentSchema]:
    """List all legal documents."""
    service = LegalCopilotService(db=db)
    docs = service.list_documents()
    return [
        DocumentSchema(
            id=str(d.id),
            document_type=d.document_type,
            title=d.title,
            status=d.status,
            jurisdiction=d.jurisdiction,
            content=d.content,
            created_at=d.created_at.isoformat() if d.created_at else None,
        )
        for d in docs
    ]


@router.get("/stats", response_model=StatsSchema, summary="Get stats")
async def get_stats(db: DB) -> StatsSchema:
    """Get legal copilot statistics."""
    service = LegalCopilotService(db=db)
    stats = service.get_stats()
    return StatsSchema(
        total_documents=stats.total_documents,
        dpas_generated=stats.dpas_generated,
        memos_generated=stats.memos_generated,
        clauses_reviewed=stats.clauses_reviewed,
        approved_documents=stats.approved_documents,
        avg_risk_score=stats.avg_risk_score,
    )
