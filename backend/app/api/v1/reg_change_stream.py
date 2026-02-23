"""API endpoints for Regulatory Change Stream."""

from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.reg_change_stream import ChangeSeverity, RegChangeStreamService, RegulatoryChange


logger = structlog.get_logger()
router = APIRouter()


class PublishChangeRequest(BaseModel):
    regulation: str = Field(...)
    jurisdiction: str = Field(default="")
    title: str = Field(...)
    summary: str = Field(default="")
    source_url: str = Field(default="")
    affected_articles: list[str] = Field(default_factory=list)
    affected_frameworks: list[str] = Field(default_factory=list)
    change_type: str = Field(default="amendment")
    effective_date: str = Field(default="")

class RegulatoryChangeSchema(BaseModel):
    id: str
    regulation: str
    jurisdiction: str
    title: str
    summary: str
    severity: str
    status: str
    source_url: str
    affected_articles: list[str]
    affected_frameworks: list[str]
    change_type: str
    detected_at: str | None

class SubscribeRequest(BaseModel):
    subscriber_id: str = Field(...)
    channel: str = Field(default="webhook")
    endpoint_url: str = Field(default="")
    severity_threshold: str = Field(default="medium")
    jurisdictions: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)

class SubscriptionSchema(BaseModel):
    id: str
    subscriber_id: str
    channel: str
    endpoint_url: str
    severity_threshold: str
    jurisdictions: list[str]
    frameworks: list[str]
    is_active: bool
    created_at: str | None

class StreamStatsSchema(BaseModel):
    total_changes: int
    changes_by_severity: dict[str, int]
    changes_by_jurisdiction: dict[str, int]
    active_subscriptions: int
    notifications_sent: int


@router.post("/changes", response_model=RegulatoryChangeSchema, status_code=status.HTTP_201_CREATED, summary="Publish regulatory change")
async def publish_change(request: PublishChangeRequest, db: DB) -> RegulatoryChangeSchema:
    service = RegChangeStreamService(db=db)
    change = RegulatoryChange(
        regulation=request.regulation, jurisdiction=request.jurisdiction,
        title=request.title, summary=request.summary, source_url=request.source_url,
        affected_articles=request.affected_articles, affected_frameworks=request.affected_frameworks,
        change_type=request.change_type, effective_date=request.effective_date,
    )
    result = await service.publish_change(change)
    return RegulatoryChangeSchema(
        id=str(result.id), regulation=result.regulation, jurisdiction=result.jurisdiction,
        title=result.title, summary=result.summary, severity=result.severity.value,
        status=result.status.value, source_url=result.source_url,
        affected_articles=result.affected_articles, affected_frameworks=result.affected_frameworks,
        change_type=result.change_type,
        detected_at=result.detected_at.isoformat() if result.detected_at else None,
    )

@router.get("/changes", response_model=list[RegulatoryChangeSchema], summary="List regulatory changes")
async def list_changes(db: DB, severity: str | None = None, jurisdiction: str | None = None, regulation: str | None = None, limit: int = 50) -> list[RegulatoryChangeSchema]:
    service = RegChangeStreamService(db=db)
    s = ChangeSeverity(severity) if severity else None
    changes = service.get_changes(severity=s, jurisdiction=jurisdiction, regulation=regulation, limit=limit)
    return [
        RegulatoryChangeSchema(
            id=str(c.id), regulation=c.regulation, jurisdiction=c.jurisdiction,
            title=c.title, summary=c.summary, severity=c.severity.value,
            status=c.status.value, source_url=c.source_url,
            affected_articles=c.affected_articles, affected_frameworks=c.affected_frameworks,
            change_type=c.change_type,
            detected_at=c.detected_at.isoformat() if c.detected_at else None,
        ) for c in changes
    ]

@router.post("/changes/{change_id}/acknowledge", summary="Acknowledge change")
async def acknowledge_change(change_id: UUID, db: DB) -> dict:
    service = RegChangeStreamService(db=db)
    change = await service.acknowledge_change(change_id)
    if not change:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change not found")
    return {"status": "acknowledged", "change_id": str(change_id)}

@router.post("/subscriptions", response_model=SubscriptionSchema, status_code=status.HTTP_201_CREATED, summary="Subscribe to changes")
async def subscribe(request: SubscribeRequest, db: DB) -> SubscriptionSchema:
    service = RegChangeStreamService(db=db)
    sub = await service.subscribe(
        subscriber_id=request.subscriber_id, channel=request.channel,
        endpoint_url=request.endpoint_url, severity_threshold=request.severity_threshold,
        jurisdictions=request.jurisdictions, frameworks=request.frameworks,
    )
    return SubscriptionSchema(
        id=str(sub.id), subscriber_id=sub.subscriber_id, channel=sub.channel.value,
        endpoint_url=sub.endpoint_url, severity_threshold=sub.severity_threshold.value,
        jurisdictions=sub.jurisdictions, frameworks=sub.frameworks, is_active=sub.is_active,
        created_at=sub.created_at.isoformat() if sub.created_at else None,
    )

@router.get("/subscriptions", response_model=list[SubscriptionSchema], summary="List subscriptions")
async def list_subscriptions(db: DB, active_only: bool = True) -> list[SubscriptionSchema]:
    service = RegChangeStreamService(db=db)
    subs = service.list_subscriptions(active_only=active_only)
    return [
        SubscriptionSchema(
            id=str(s.id), subscriber_id=s.subscriber_id, channel=s.channel.value,
            endpoint_url=s.endpoint_url, severity_threshold=s.severity_threshold.value,
            jurisdictions=s.jurisdictions, frameworks=s.frameworks, is_active=s.is_active,
            created_at=s.created_at.isoformat() if s.created_at else None,
        ) for s in subs
    ]

@router.delete("/subscriptions/{subscriber_id}", summary="Unsubscribe")
async def unsubscribe(subscriber_id: str, db: DB) -> dict:
    service = RegChangeStreamService(db=db)
    ok = await service.unsubscribe(subscriber_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return {"status": "unsubscribed"}

@router.get("/stats", response_model=StreamStatsSchema, summary="Get stream stats")
async def get_stats(db: DB) -> StreamStatsSchema:
    service = RegChangeStreamService(db=db)
    stats = service.get_stats()
    return StreamStatsSchema(
        total_changes=stats.total_changes, changes_by_severity=stats.changes_by_severity,
        changes_by_jurisdiction=stats.changes_by_jurisdiction,
        active_subscriptions=stats.active_subscriptions, notifications_sent=stats.notifications_sent,
    )
