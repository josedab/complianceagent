"""API endpoints for Regulatory Filing management."""

from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.regulatory_filing import FilingType, RegulatoryFilingService


logger = structlog.get_logger()
router = APIRouter()


class FilingGenerateRequest(BaseModel):
    filing_type: str = Field(...)
    authority_id: str = Field(...)
    data: dict = Field(default_factory=dict)


@router.post("/filings", status_code=status.HTTP_201_CREATED, summary="Generate a filing")
async def generate_filing(request: FilingGenerateRequest, db: DB) -> dict:
    """Generate a filing auto-populated from template."""
    service = RegulatoryFilingService(db=db)
    result = await service.generate_filing(
        filing_type=FilingType(request.filing_type),
        authority_id=request.authority_id,
        data=request.data,
    )
    return {
        "id": str(result.id),
        "filing_type": result.filing_type.value,
        "authority_id": result.authority_id,
        "title": result.title,
        "content": result.content,
        "status": result.status.value,
        "deadline": result.deadline.isoformat() if result.deadline else None,
    }


@router.post("/filings/{filing_id}/submit", summary="Submit a filing")
async def submit_filing(filing_id: UUID, db: DB) -> dict:
    """Submit a filing, changing status to submitted."""
    service = RegulatoryFilingService(db=db)
    try:
        result = await service.submit_filing(filing_id=filing_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return {
        "id": str(result.id),
        "status": result.status.value,
        "reference_number": result.reference_number,
        "submitted_at": result.submitted_at.isoformat() if result.submitted_at else None,
    }


@router.get("/authorities", summary="List regulatory authorities")
async def list_authorities(db: DB) -> list[dict]:
    """List all regulatory authorities."""
    service = RegulatoryFilingService(db=db)
    authorities = await service.list_authorities()
    return [
        {
            "id": a.id,
            "name": a.name,
            "authority_type": a.authority_type.value,
            "jurisdiction": a.jurisdiction,
            "accepts_electronic": a.accepts_electronic,
        }
        for a in authorities
    ]


@router.get("/templates", summary="List filing templates")
async def list_templates(db: DB) -> list[dict]:
    """List all filing templates."""
    service = RegulatoryFilingService(db=db)
    templates = await service.list_templates()
    return [
        {
            "id": t.id,
            "filing_type": t.filing_type.value,
            "authority_id": t.authority_id,
            "template_fields": t.template_fields,
            "required_attachments": t.required_attachments,
            "description": t.description,
        }
        for t in templates
    ]


@router.get("/filings", summary="List all filings")
async def list_filings(db: DB) -> list[dict]:
    """List all filings."""
    service = RegulatoryFilingService(db=db)
    filings = await service.list_filings()
    return [
        {
            "id": str(f.id),
            "filing_type": f.filing_type.value,
            "authority_id": f.authority_id,
            "title": f.title,
            "status": f.status.value,
            "deadline": f.deadline.isoformat() if f.deadline else None,
        }
        for f in filings
    ]


@router.get("/stats", summary="Get regulatory filing stats")
async def get_stats(db: DB) -> dict:
    """Get aggregate filing statistics."""
    service = RegulatoryFilingService(db=db)
    stats = await service.get_stats()
    return {
        "total_filings": stats.total_filings,
        "by_type": stats.by_type,
        "by_status": stats.by_status,
        "on_time_pct": stats.on_time_pct,
        "authorities_connected": stats.authorities_connected,
    }
