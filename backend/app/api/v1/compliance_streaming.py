"""API endpoints for Compliance Event Streaming."""

import structlog
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.compliance_streaming import ComplianceStreamingService


logger = structlog.get_logger()
router = APIRouter()


# --- Request / Response Schemas ---


class PublishEventRequest(BaseModel):
    event_type: str = Field(..., description="Type of compliance event")
    channel: str = Field(..., description="Channel to publish to")
    payload: dict = Field(..., description="Event payload data")
    tenant_id: str = Field(..., description="Tenant identifier")
    repo: str = Field(..., description="Repository associated with the event")


class SubscribeRequest(BaseModel):
    client_id: str = Field(..., description="Unique client identifier")
    channels: list[str] = Field(..., description="Channels to subscribe to")
    event_types: list[str] = Field(default_factory=list, description="Event types to filter")
    filters: dict = Field(default_factory=dict, description="Additional subscription filters")


# --- Endpoints ---


@router.post("/publish")
async def publish_event(request: PublishEventRequest, db: DB) -> dict:
    """Publish a compliance event to a channel."""
    svc = ComplianceStreamingService()
    return await svc.publish(
        db,
        event_type=request.event_type,
        channel=request.channel,
        payload=request.payload,
        tenant_id=request.tenant_id,
        repo=request.repo,
    )


@router.post("/subscribe")
async def subscribe(request: SubscribeRequest, db: DB) -> dict:
    """Subscribe a client to compliance event channels."""
    svc = ComplianceStreamingService()
    return await svc.subscribe(
        db,
        client_id=request.client_id,
        channels=request.channels,
        event_types=request.event_types,
        filters=request.filters,
    )


@router.delete("/subscribe/{client_id}")
async def unsubscribe(client_id: str, db: DB) -> dict:
    """Unsubscribe a client from all channels."""
    svc = ComplianceStreamingService()
    return await svc.unsubscribe(db, client_id=client_id)


@router.get("/events")
async def get_recent_events(
    db: DB,
    channel: str | None = Query(None, description="Filter by channel"),
    event_type: str | None = Query(None, description="Filter by event type"),
    limit: int = Query(50, ge=1, le=500, description="Maximum events to return"),
) -> list[dict]:
    """Get recent compliance events."""
    svc = ComplianceStreamingService()
    return await svc.get_recent_events(
        db, channel=channel, event_type=event_type, limit=limit,
    )


@router.get("/channels")
async def list_channels(db: DB) -> list[dict]:
    """List available event channels."""
    svc = ComplianceStreamingService()
    return await svc.list_channels(db)


@router.get("/subscriptions")
async def list_subscriptions(db: DB) -> list[dict]:
    """List active subscriptions."""
    svc = ComplianceStreamingService()
    return await svc.list_subscriptions(db)


@router.get("/stats")
async def get_stats(db: DB) -> dict:
    """Get streaming statistics."""
    svc = ComplianceStreamingService()
    return await svc.get_stats(db)
