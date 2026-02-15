"""API endpoints for Compliance Debt Securitization."""

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.debt import DebtPriority, DebtSecuritizationService

logger = structlog.get_logger()
router = APIRouter()


# --- Response Models ---

class DebtItemSchema(BaseModel):
    id: str
    title: str
    description: str
    priority: str
    framework: str
    control: str
    risk_score: float
    cost_of_delay_per_day: float
    accrued_interest: float
    remediation_cost: float
    days_outstanding: int
    assigned_team: str


class BondSchema(BaseModel):
    id: str
    name: str
    face_value: float
    current_value: float
    interest_rate: float
    framework: str
    debt_items_count: int
    yield_spread: float


class PortfolioSchema(BaseModel):
    total_debt_value: float
    total_items: int
    critical_items: int
    high_items: int
    medium_items: int
    low_items: int
    avg_days_outstanding: float
    daily_accrual_rate: float
    credit_rating: str
    debt_by_framework: dict[str, float]
    remediation_velocity: float
    projected_payoff_days: int


class CreditRatingSchema(BaseModel):
    rating: str
    trend: str
    total_debt: float
    daily_accrual: float
    projected_payoff_days: int


# --- Endpoints ---

@router.get("/items", response_model=list[DebtItemSchema])
async def list_debt_items(
    priority: str | None = Query(None),
    framework: str | None = Query(None),
) -> list[dict]:
    svc = DebtSecuritizationService()
    try:
        pr = DebtPriority(priority) if priority else None
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid priority: {priority}")
    items = await svc.list_debt_items(priority=pr, framework=framework)
    return [
        {"id": str(d.id), "title": d.title, "description": d.description,
         "priority": d.priority.value, "framework": d.framework, "control": d.control,
         "risk_score": d.risk_score, "cost_of_delay_per_day": d.cost_of_delay_per_day,
         "accrued_interest": d.accrued_interest, "remediation_cost": d.remediation_cost,
         "days_outstanding": d.days_outstanding, "assigned_team": d.assigned_team}
        for d in items
    ]


@router.get("/portfolio", response_model=PortfolioSchema)
async def get_portfolio() -> dict:
    svc = DebtSecuritizationService()
    p = await svc.get_portfolio()
    return {
        "total_debt_value": p.total_debt_value, "total_items": p.total_items,
        "critical_items": p.critical_items, "high_items": p.high_items,
        "medium_items": p.medium_items, "low_items": p.low_items,
        "avg_days_outstanding": p.avg_days_outstanding,
        "daily_accrual_rate": p.daily_accrual_rate,
        "credit_rating": p.credit_rating.value,
        "debt_by_framework": p.debt_by_framework,
        "remediation_velocity": p.remediation_velocity,
        "projected_payoff_days": p.projected_payoff_days,
    }


@router.get("/bonds", response_model=list[BondSchema])
async def get_bonds() -> list[dict]:
    svc = DebtSecuritizationService()
    bonds = await svc.get_bonds()
    return [
        {"id": str(b.id), "name": b.name, "face_value": b.face_value,
         "current_value": b.current_value, "interest_rate": b.interest_rate,
         "framework": b.framework, "debt_items_count": b.debt_items_count,
         "yield_spread": b.yield_spread}
        for b in bonds
    ]


@router.get("/credit-rating", response_model=CreditRatingSchema)
async def get_credit_rating() -> dict:
    svc = DebtSecuritizationService()
    return await svc.get_credit_rating()
