"""API endpoints for Digital Marketplace."""

from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.digital_marketplace import DigitalMarketplaceService


logger = structlog.get_logger()
router = APIRouter()


class ListAssetRequest(BaseModel):
    title: str = Field(...)
    asset_type: str = Field(...)
    author: str = Field(...)
    pricing: str = Field(...)
    price_usd: float = Field(default=0.0)
    frameworks: list[str] = Field(default_factory=list)
    content: str = Field(default="")


class PurchaseAssetRequest(BaseModel):
    buyer_org: str = Field(...)


class RateAssetRequest(BaseModel):
    rating: float = Field(...)
    reviewer: str = Field(...)


class GenerateReportRequest(BaseModel):
    period: str = Field(...)


class AssetSchema(BaseModel):
    id: str
    title: str
    asset_type: str
    author: str
    pricing: str
    price_usd: float
    frameworks: list[str]
    rating: float
    downloads: int
    created_at: str | None


class PurchaseSchema(BaseModel):
    id: str
    asset_id: str
    buyer_org: str
    status: str
    purchased_at: str | None


class ReportSchema(BaseModel):
    id: str
    period: str
    total_revenue: float
    total_transactions: int
    top_assets: list[dict]
    generated_at: str | None


class StatsSchema(BaseModel):
    total_assets: int
    total_purchases: int
    total_revenue: float
    avg_rating: float
    active_authors: int


@router.post(
    "/assets",
    response_model=AssetSchema,
    status_code=status.HTTP_201_CREATED,
    summary="List asset",
)
async def list_asset(request: ListAssetRequest, db: DB) -> AssetSchema:
    """List a new asset on the marketplace."""
    service = DigitalMarketplaceService(db=db)
    asset = await service.list_asset(
        title=request.title,
        asset_type=request.asset_type,
        author=request.author,
        pricing=request.pricing,
        price_usd=request.price_usd,
        frameworks=request.frameworks,
        content=request.content,
    )
    return AssetSchema(
        id=str(asset.id),
        title=asset.title,
        asset_type=asset.asset_type,
        author=asset.author,
        pricing=asset.pricing,
        price_usd=asset.price_usd,
        frameworks=asset.frameworks,
        rating=asset.rating,
        downloads=asset.downloads,
        created_at=asset.created_at.isoformat() if asset.created_at else None,
    )


@router.get("/assets", response_model=list[AssetSchema], summary="Search assets")
async def search_assets(
    db: DB,
    query: str | None = None,
    asset_type: str | None = None,
    framework: str | None = None,
) -> list[AssetSchema]:
    """Search marketplace assets with optional filters."""
    service = DigitalMarketplaceService(db=db)
    assets = service.search_assets(
        query=query, asset_type=asset_type, framework=framework
    )
    return [
        AssetSchema(
            id=str(a.id),
            title=a.title,
            asset_type=a.asset_type,
            author=a.author,
            pricing=a.pricing,
            price_usd=a.price_usd,
            frameworks=a.frameworks,
            rating=a.rating,
            downloads=a.downloads,
            created_at=a.created_at.isoformat() if a.created_at else None,
        )
        for a in assets
    ]


@router.post(
    "/assets/{asset_id}/purchase",
    response_model=PurchaseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Purchase asset",
)
async def purchase_asset(
    asset_id: UUID, request: PurchaseAssetRequest, db: DB
) -> PurchaseSchema:
    """Purchase a marketplace asset."""
    service = DigitalMarketplaceService(db=db)
    purchase = await service.purchase_asset(
        asset_id=asset_id, buyer_org=request.buyer_org
    )
    if not purchase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found"
        )
    return PurchaseSchema(
        id=str(purchase.id),
        asset_id=str(purchase.asset_id),
        buyer_org=purchase.buyer_org,
        status=purchase.status,
        purchased_at=purchase.purchased_at.isoformat()
        if purchase.purchased_at
        else None,
    )


@router.post("/assets/{asset_id}/rate", summary="Rate asset")
async def rate_asset(
    asset_id: UUID, request: RateAssetRequest, db: DB
) -> dict:
    """Rate a marketplace asset."""
    service = DigitalMarketplaceService(db=db)
    ok = await service.rate_asset(
        asset_id=asset_id, rating=request.rating, reviewer=request.reviewer
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found"
        )
    return {"status": "rated", "asset_id": str(asset_id), "rating": request.rating}


@router.post(
    "/reports",
    response_model=ReportSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Generate report",
)
async def generate_report(request: GenerateReportRequest, db: DB) -> ReportSchema:
    """Generate a marketplace report for a period."""
    service = DigitalMarketplaceService(db=db)
    report = await service.generate_report(period=request.period)
    return ReportSchema(
        id=str(report.id),
        period=report.period,
        total_revenue=report.total_revenue,
        total_transactions=report.total_transactions,
        top_assets=report.top_assets,
        generated_at=report.generated_at.isoformat()
        if report.generated_at
        else None,
    )


@router.get("/stats", response_model=StatsSchema, summary="Get stats")
async def get_stats(db: DB) -> StatsSchema:
    """Get marketplace statistics."""
    service = DigitalMarketplaceService(db=db)
    stats = service.get_stats()
    return StatsSchema(
        total_assets=stats.total_assets,
        total_purchases=stats.total_purchases,
        total_revenue=stats.total_revenue,
        avg_rating=stats.avg_rating,
        active_authors=stats.active_authors,
    )
