"""API endpoints for Marketplace Revenue."""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.marketplace_revenue import MarketplaceRevenueService


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---


class CreateListingRequest(BaseModel):
    agent_slug: str = Field(..., description="Unique agent slug")
    author: str = Field(..., description="Author or publisher name")
    revenue_model: str = Field(..., description="Revenue model (subscription, usage, one-time)")
    price_usd: float = Field(..., description="Price in USD")


class RecordTransactionRequest(BaseModel):
    listing_id: str = Field(..., description="Listing identifier")
    amount: float = Field(..., description="Transaction amount in USD")


class GeneratePayoutRequest(BaseModel):
    author: str = Field(..., description="Author to generate payout for")
    period: str = Field(..., description="Payout period (e.g. 2024-01)")


class GenerateRevenueReportRequest(BaseModel):
    period: str = Field(..., description="Report period (e.g. 2024-Q1)")


class ListingSchema(BaseModel):
    id: str
    agent_slug: str
    author: str
    revenue_model: str
    price_usd: float
    total_revenue: float
    transactions_count: int
    created_at: str | None


class TransactionSchema(BaseModel):
    id: str
    listing_id: str
    amount: float
    created_at: str | None


class PayoutSchema(BaseModel):
    id: str
    author: str
    period: str
    amount: float
    status: str
    created_at: str | None


class RevenueReportSchema(BaseModel):
    period: str
    total_revenue: float
    total_transactions: int
    top_listings: list[dict[str, Any]]
    by_revenue_model: dict[str, float]


class MarketplaceStatsSchema(BaseModel):
    total_listings: int
    total_revenue: float
    total_transactions: int
    total_payouts: float


# --- Endpoints ---


@router.post("/listings", response_model=ListingSchema, status_code=status.HTTP_201_CREATED, summary="Create listing")
async def create_listing(request: CreateListingRequest, db: DB) -> ListingSchema:
    service = MarketplaceRevenueService(db=db)
    listing = await service.create_listing(
        agent_slug=request.agent_slug,
        author=request.author,
        revenue_model=request.revenue_model,
        price_usd=request.price_usd,
    )
    logger.info("listing_created", agent_slug=request.agent_slug, author=request.author)
    return ListingSchema(
        id=str(listing.id), agent_slug=listing.agent_slug, author=listing.author,
        revenue_model=listing.revenue_model, price_usd=listing.price_usd,
        total_revenue=listing.total_revenue, transactions_count=listing.transactions_count,
        created_at=listing.created_at.isoformat() if listing.created_at else None,
    )


@router.post("/transactions", response_model=TransactionSchema, status_code=status.HTTP_201_CREATED, summary="Record transaction")
async def record_transaction(request: RecordTransactionRequest, db: DB) -> TransactionSchema:
    service = MarketplaceRevenueService(db=db)
    txn = await service.record_transaction(
        listing_id=request.listing_id,
        amount=request.amount,
    )
    if not txn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    logger.info("transaction_recorded", listing_id=request.listing_id, amount=request.amount)
    return TransactionSchema(
        id=str(txn.id), listing_id=txn.listing_id, amount=txn.amount,
        created_at=txn.created_at.isoformat() if txn.created_at else None,
    )


@router.post("/payouts", response_model=PayoutSchema, status_code=status.HTTP_201_CREATED, summary="Generate payout")
async def generate_payout(request: GeneratePayoutRequest, db: DB) -> PayoutSchema:
    service = MarketplaceRevenueService(db=db)
    payout = await service.generate_payout(
        author=request.author,
        period=request.period,
    )
    logger.info("payout_generated", author=request.author, period=request.period)
    return PayoutSchema(
        id=str(payout.id), author=payout.author, period=payout.period,
        amount=payout.amount, status=payout.status,
        created_at=payout.created_at.isoformat() if payout.created_at else None,
    )


@router.post("/reports", response_model=RevenueReportSchema, summary="Generate revenue report")
async def generate_revenue_report(request: GenerateRevenueReportRequest, db: DB) -> RevenueReportSchema:
    service = MarketplaceRevenueService(db=db)
    report = await service.generate_revenue_report(period=request.period)
    logger.info("revenue_report_generated", period=request.period)
    return RevenueReportSchema(
        period=report.period,
        total_revenue=report.total_revenue,
        total_transactions=report.total_transactions,
        top_listings=report.top_listings,
        by_revenue_model=report.by_revenue_model,
    )


@router.get("/listings", response_model=list[ListingSchema], summary="List listings")
async def list_listings(db: DB) -> list[ListingSchema]:
    service = MarketplaceRevenueService(db=db)
    listings = await service.list_listings()
    return [
        ListingSchema(
            id=str(l.id), agent_slug=l.agent_slug, author=l.author,
            revenue_model=l.revenue_model, price_usd=l.price_usd,
            total_revenue=l.total_revenue, transactions_count=l.transactions_count,
            created_at=l.created_at.isoformat() if l.created_at else None,
        )
        for l in listings
    ]


@router.get("/stats", response_model=MarketplaceStatsSchema, summary="Get marketplace stats")
async def get_stats(db: DB) -> MarketplaceStatsSchema:
    service = MarketplaceRevenueService(db=db)
    s = await service.get_stats()
    return MarketplaceStatsSchema(
        total_listings=s.total_listings,
        total_revenue=s.total_revenue,
        total_transactions=s.total_transactions,
        total_payouts=s.total_payouts,
    )
