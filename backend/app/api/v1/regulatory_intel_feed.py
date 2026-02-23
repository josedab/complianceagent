"""API endpoints for Regulatory Intel Feed."""

import structlog
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.regulatory_intel_feed import RegulatoryIntelFeedService


logger = structlog.get_logger()
router = APIRouter()


class SubscribeRequest(BaseModel):
    user_id: str = Field(...)
    preferences: dict = Field(default_factory=dict)


class GenerateDigestRequest(BaseModel):
    user_id: str = Field(...)
    period: str = Field(default="weekly")


class FeedItemSchema(BaseModel):
    id: str
    title: str
    summary: str
    source: str
    regulation: str
    jurisdiction: str
    impact_level: str
    published_at: str | None


class SubscriptionSchema(BaseModel):
    id: str
    user_id: str
    preferences: dict
    status: str
    created_at: str | None


class DigestSchema(BaseModel):
    id: str
    user_id: str
    period: str
    items_count: int
    highlights: list[dict]
    generated_at: str | None


class ArticleSchema(BaseModel):
    id: str
    title: str
    content: str
    source: str
    regulation: str
    jurisdiction: str
    tags: list[str]
    published_at: str | None


class StatsSchema(BaseModel):
    total_feed_items: int
    total_subscribers: int
    total_digests: int
    jurisdictions_covered: int
    avg_items_per_day: float


@router.get("/feed", response_model=list[FeedItemSchema], summary="Get feed")
async def get_feed(db: DB) -> list[FeedItemSchema]:
    """Get the latest regulatory intel feed."""
    service = RegulatoryIntelFeedService(db=db)
    items = service.get_feed()
    return [
        FeedItemSchema(
            id=str(i.id),
            title=i.title,
            summary=i.summary,
            source=i.source,
            regulation=i.regulation,
            jurisdiction=i.jurisdiction,
            impact_level=i.impact_level,
            published_at=i.published_at.isoformat() if i.published_at else None,
        )
        for i in items
    ]


@router.post(
    "/subscribe",
    response_model=SubscriptionSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Subscribe to feed",
)
async def subscribe(request: SubscribeRequest, db: DB) -> SubscriptionSchema:
    """Subscribe a user to the regulatory intel feed."""
    service = RegulatoryIntelFeedService(db=db)
    sub = await service.subscribe(
        user_id=request.user_id, preferences=request.preferences
    )
    return SubscriptionSchema(
        id=str(sub.id),
        user_id=sub.user_id,
        preferences=sub.preferences,
        status=sub.status,
        created_at=sub.created_at.isoformat() if sub.created_at else None,
    )


@router.post(
    "/digest",
    response_model=DigestSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Generate digest",
)
async def generate_digest(request: GenerateDigestRequest, db: DB) -> DigestSchema:
    """Generate a personalized regulatory digest."""
    service = RegulatoryIntelFeedService(db=db)
    digest = await service.generate_digest(
        user_id=request.user_id, period=request.period
    )
    return DigestSchema(
        id=str(digest.id),
        user_id=digest.user_id,
        period=digest.period,
        items_count=digest.items_count,
        highlights=digest.highlights,
        generated_at=digest.generated_at.isoformat()
        if digest.generated_at
        else None,
    )


@router.get("/articles", response_model=list[ArticleSchema], summary="List articles")
async def list_articles(db: DB) -> list[ArticleSchema]:
    """List all regulatory articles."""
    service = RegulatoryIntelFeedService(db=db)
    articles = service.list_articles()
    return [
        ArticleSchema(
            id=str(a.id),
            title=a.title,
            content=a.content,
            source=a.source,
            regulation=a.regulation,
            jurisdiction=a.jurisdiction,
            tags=a.tags,
            published_at=a.published_at.isoformat() if a.published_at else None,
        )
        for a in articles
    ]


@router.get("/stats", response_model=StatsSchema, summary="Get stats")
async def get_stats(db: DB) -> StatsSchema:
    """Get regulatory intel feed statistics."""
    service = RegulatoryIntelFeedService(db=db)
    stats = service.get_stats()
    return StatsSchema(
        total_feed_items=stats.total_feed_items,
        total_subscribers=stats.total_subscribers,
        total_digests=stats.total_digests,
        jurisdictions_covered=stats.jurisdictions_covered,
        avg_items_per_day=stats.avg_items_per_day,
    )
