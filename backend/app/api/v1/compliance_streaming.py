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


# --- Production Endpoints: Webhooks & Alert Policies ---


class RegisterWebhookRequest(BaseModel):
    name: str = Field(..., description="Webhook name")
    target: str = Field(default="generic", description="Target: slack, pagerduty, teams, generic")
    url: str = Field(..., description="Webhook URL")
    channels: list[str] = Field(default_factory=list)
    event_types: list[str] = Field(default_factory=list)
    min_severity: str = Field(default="medium")


class CreateAlertPolicyRequest(BaseModel):
    name: str = Field(...)
    channel: str = Field(...)
    condition_type: str = Field(default="threshold")
    metric: str = Field(...)
    operator: str = Field(default="lt")
    threshold: float = Field(...)
    severity: str = Field(default="medium")
    window_seconds: int = Field(default=300)
    cooldown_seconds: int = Field(default=3600)


@router.post("/webhooks", summary="Register webhook integration")
async def register_webhook(request: RegisterWebhookRequest, db: DB) -> dict:
    svc = ComplianceStreamingService(db)
    webhook = await svc.register_webhook(
        name=request.name, target=request.target, url=request.url,
        channels=request.channels, event_types=request.event_types,
        min_severity=request.min_severity,
    )
    return {"id": str(webhook.id), "name": webhook.name, "target": webhook.target.value, "url": webhook.url}


@router.get("/webhooks", summary="List webhook integrations")
async def list_webhooks(db: DB) -> list[dict]:
    svc = ComplianceStreamingService(db)
    webhooks = svc.list_webhooks()
    return [{"id": str(w.id), "name": w.name, "target": w.target.value, "url": w.url, "active": w.active, "delivery_count": w.delivery_count} for w in webhooks]


@router.delete("/webhooks/{webhook_id}", summary="Remove webhook")
async def remove_webhook(webhook_id: str, db: DB) -> dict:
    from uuid import UUID as PyUUID
    svc = ComplianceStreamingService(db)
    ok = await svc.remove_webhook(PyUUID(webhook_id))
    return {"removed": ok}


@router.post("/alert-policies", summary="Create alert policy")
async def create_alert_policy(request: CreateAlertPolicyRequest, db: DB) -> dict:
    svc = ComplianceStreamingService(db)
    policy = await svc.create_alert_policy(
        name=request.name, channel=request.channel, condition_type=request.condition_type,
        metric=request.metric, operator=request.operator, threshold=request.threshold,
        severity=request.severity, window_seconds=request.window_seconds,
        cooldown_seconds=request.cooldown_seconds,
    )
    return {"id": str(policy.id), "name": policy.name, "metric": policy.metric, "threshold": policy.threshold}


@router.get("/alert-policies", summary="List alert policies")
async def list_alert_policies(db: DB) -> list[dict]:
    svc = ComplianceStreamingService(db)
    policies = svc.list_alert_policies()
    return [{"id": str(p.id), "name": p.name, "metric": p.metric, "operator": p.operator, "threshold": p.threshold, "severity": p.severity.value, "active": p.active, "fire_count": p.fire_count} for p in policies]


@router.get("/alerts", summary="List recent alert firings")
async def list_alert_firings(db: DB, limit: int = 50) -> list[dict]:
    svc = ComplianceStreamingService(db)
    firings = svc.list_alert_firings(limit=limit)
    return [{"id": str(f.id), "policy_name": f.policy_name, "severity": f.severity.value, "message": f.message, "fired_at": f.fired_at.isoformat() if f.fired_at else None} for f in firings]
