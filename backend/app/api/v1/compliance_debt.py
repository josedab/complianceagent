"""API endpoints for Compliance Debt tracking."""

import structlog
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.compliance_debt import ComplianceDebtService


logger = structlog.get_logger()
router = APIRouter()


# --- Request / Response Schemas ---


class AddDebtItemRequest(BaseModel):
    title: str = Field(..., description="Debt item title")
    description: str = Field(..., description="Detailed description of the debt")
    framework: str = Field(..., description="Compliance framework")
    file_path: str = Field(..., description="File path where the debt exists")
    severity: str = Field(..., description="Severity level")
    risk_cost_usd: float = Field(..., description="Estimated risk cost in USD")
    remediation_cost_usd: float = Field(..., description="Estimated remediation cost in USD")
    repo: str = Field(..., description="Repository name")


# --- Endpoints ---


@router.post("/items")
async def add_debt_item(request: AddDebtItemRequest, db: DB) -> dict:
    """Add a new compliance debt item."""
    svc = ComplianceDebtService()
    return await svc.add_debt_item(
        db,
        title=request.title,
        description=request.description,
        framework=request.framework,
        file_path=request.file_path,
        severity=request.severity,
        risk_cost_usd=request.risk_cost_usd,
        remediation_cost_usd=request.remediation_cost_usd,
        repo=request.repo,
    )


@router.post("/items/{item_id}/resolve")
async def resolve_debt(item_id: str, db: DB) -> dict:
    """Mark a compliance debt item as resolved."""
    svc = ComplianceDebtService()
    return await svc.resolve_debt(db, item_id=item_id)


@router.post("/items/{item_id}/acknowledge")
async def acknowledge_debt(item_id: str, db: DB) -> dict:
    """Acknowledge a compliance debt item."""
    svc = ComplianceDebtService()
    return await svc.acknowledge_debt(db, item_id=item_id)


@router.get("/items")
async def list_debt(
    db: DB,
    framework: str | None = Query(None, description="Filter by compliance framework"),
    sort_by: str = Query("roi", description="Sort by: roi, risk, or age"),
) -> list[dict]:
    """List compliance debt items."""
    svc = ComplianceDebtService()
    return await svc.list_debt(db, framework=framework, sort_by=sort_by)


@router.get("/burndown")
async def get_burndown(db: DB) -> dict:
    """Get compliance debt burndown chart data."""
    svc = ComplianceDebtService()
    return await svc.get_burndown(db)


@router.get("/stats")
async def get_stats(db: DB) -> dict:
    """Get compliance debt statistics."""
    svc = ComplianceDebtService()
    return await svc.get_stats(db)
