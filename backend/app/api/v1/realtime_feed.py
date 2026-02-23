"""API endpoints for Real-Time Compliance Feed."""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.realtime_feed import RealtimeFeedService


logger = structlog.get_logger()
router = APIRouter()


class PublishRequest(BaseModel):
    event_type: str = Field(...)
    source: str = Field(default="")
    repo: str = Field(default="")
    framework: str = Field(default="")
    severity: str = Field(default="info")
    title: str = Field(default="")
    detail: str = Field(default="")
    metadata: dict[str, Any] = Field(default_factory=dict)


class SubscribeRequest(BaseModel):
    user_id: str = Field(...)
    event_types: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    severity_min: str = Field(default="info")


class FeedItemSchema(BaseModel):
    id: str
    event_type: str
    source: str
    repo: str
    framework: str
    severity: str
    title: str
    detail: str
    metadata: dict[str, Any]
    created_at: str | None


class SubscriptionSchema(BaseModel):
    id: str
    user_id: str
    event_types: list[str]
    frameworks: list[str]
    severity_min: str
    active: bool


class FeedStatsSchema(BaseModel):
    total_items: int
    total_subscriptions: int
    active_subscriptions: int
    by_event_type: dict[str, int]
    by_severity: dict[str, int]


@router.get("/feed", response_model=list[FeedItemSchema], summary="List feed items")
async def list_feed(db: DB, limit: int = 50, event_type: str | None = None, severity: str | None = None) -> list[FeedItemSchema]:
    service = RealtimeFeedService(db=db)
    items = service.list_feed(limit=limit, event_type=event_type, severity=severity)
    return [
        FeedItemSchema(
            id=str(i.id),
            event_type=i.event_type,
            source=i.source,
            repo=i.repo,
            framework=i.framework,
            severity=i.severity,
            title=i.title,
            detail=i.detail,
            metadata=i.metadata,
            created_at=i.created_at.isoformat() if i.created_at else None,
        )
        for i in items
    ]


@router.post("/feed", response_model=FeedItemSchema, status_code=status.HTTP_201_CREATED, summary="Publish feed item")
async def publish(request: PublishRequest, db: DB) -> FeedItemSchema:
    service = RealtimeFeedService(db=db)
    i = await service.publish(
        event_type=request.event_type, source=request.source, repo=request.repo,
        framework=request.framework, severity=request.severity, title=request.title,
        detail=request.detail, metadata=request.metadata,
    )
    return FeedItemSchema(
        id=str(i.id), event_type=i.event_type, source=i.source, repo=i.repo,
        framework=i.framework, severity=i.severity, title=i.title, detail=i.detail,
        metadata=i.metadata, created_at=i.created_at.isoformat() if i.created_at else None,
    )


@router.post("/subscribe", response_model=SubscriptionSchema, status_code=status.HTTP_201_CREATED, summary="Subscribe to feed")
async def subscribe(request: SubscribeRequest, db: DB) -> SubscriptionSchema:
    service = RealtimeFeedService(db=db)
    s = await service.subscribe(
        user_id=request.user_id, event_types=request.event_types,
        frameworks=request.frameworks, severity_min=request.severity_min,
    )
    return SubscriptionSchema(
        id=str(s.id), user_id=s.user_id, event_types=s.event_types,
        frameworks=s.frameworks, severity_min=s.severity_min, active=s.active,
    )


@router.delete("/subscribe/{user_id}", summary="Unsubscribe from feed")
async def unsubscribe(user_id: str, db: DB) -> dict:
    service = RealtimeFeedService(db=db)
    ok = await service.unsubscribe(user_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return {"status": "unsubscribed", "user_id": user_id}


@router.get("/stats", response_model=FeedStatsSchema, summary="Get feed stats")
async def get_stats(db: DB) -> FeedStatsSchema:
    service = RealtimeFeedService(db=db)
    s = service.get_stats()
    return FeedStatsSchema(
        total_items=s.total_items, total_subscriptions=s.total_subscriptions,
        active_subscriptions=s.active_subscriptions, by_event_type=s.by_event_type,
        by_severity=s.by_severity,
    )
