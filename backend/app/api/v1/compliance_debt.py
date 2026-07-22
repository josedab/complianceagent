"""API endpoints for Compliance Debt tracking."""

import structlog
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.compliance_debt import (
    ComplianceDebtItem,
    ComplianceDebtService,
    DebtStats,
    SprintBurndown,
)


logger = structlog.get_logger()
router = APIRouter()


# --- Request / Response Schemas ---


class AddDebtItemRequest(BaseModel):
    title: str = Field(..., description="Debt item title")
    description: str = Field(..., description="Detailed description of the debt")
    framework: str = Field(..., description="Compliance framework")
    rule_id: str = Field(..., description="Compliance rule identifier")
    file_path: str = Field(..., description="File path where the debt exists")
    severity: str = Field(..., description="Severity level")
    risk_cost_usd: float = Field(..., description="Estimated risk cost in USD")
    remediation_cost_usd: float = Field(..., description="Estimated remediation cost in USD")
    repo: str = Field(..., description="Repository name")


# --- Endpoints ---


@router.post("/items")
async def add_debt_item(request: AddDebtItemRequest, db: DB) -> ComplianceDebtItem:
    """Add a new compliance debt item."""
    svc = ComplianceDebtService(db)
    return await svc.add_debt_item(
        title=request.title,
        description=request.description,
        framework=request.framework,
        rule_id=request.rule_id,
        file_path=request.file_path,
        severity=request.severity,
        risk_cost_usd=request.risk_cost_usd,
        remediation_cost_usd=request.remediation_cost_usd,
        repo=request.repo,
    )


@router.post("/items/{item_id}/resolve")
async def resolve_debt(item_id: str, db: DB) -> ComplianceDebtItem:
    """Mark a compliance debt item as resolved."""
    svc = ComplianceDebtService(db)
    return await svc.resolve_debt(item_id=item_id)


@router.post("/items/{item_id}/acknowledge")
async def acknowledge_debt(item_id: str, db: DB) -> ComplianceDebtItem:
    """Acknowledge a compliance debt item."""
    svc = ComplianceDebtService(db)
    return await svc.acknowledge_debt(item_id=item_id)


@router.get("/items")
async def list_debt(
    db: DB,
    framework: str | None = Query(None, description="Filter by compliance framework"),
    sort_by_roi: bool = Query(True, description="Sort items by ROI, descending"),
) -> list[ComplianceDebtItem]:
    """List compliance debt items."""
    svc = ComplianceDebtService(db)
    return await svc.list_debt(framework=framework, sort_by_roi=sort_by_roi)


@router.get("/burndown")
async def get_burndown(db: DB) -> list[SprintBurndown]:
    """Get compliance debt burndown chart data."""
    svc = ComplianceDebtService(db)
    return svc.get_burndown()


@router.get("/stats")
async def get_stats(db: DB) -> DebtStats:
    """Get compliance debt statistics."""
    svc = ComplianceDebtService(db)
    return svc.get_stats()
