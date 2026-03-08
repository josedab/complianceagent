"""Outgoing webhook registration and management endpoints."""

import secrets
from datetime import UTC, datetime
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import Field
from sqlalchemy import select

from app.api.v1.deps import DB, CurrentUser
from app.models.production_features import WebhookIntegrationRecord
from app.schemas.base import BaseSchema, MessageResponse
from app.services.webhooks.delivery import deliver


logger = structlog.get_logger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class WebhookCreateRequest(BaseSchema):
    """Register a new outgoing webhook."""

    name: str = Field(..., min_length=1, max_length=200)
    url: str = Field(..., min_length=1, max_length=1000)
    event_types: list[str] = Field(
        default_factory=lambda: ["*"],
        max_length=50,
        description="Event types to subscribe to. Use '*' for all.",
    )
    target: str = Field("generic", pattern=r"^(generic|slack|teams)$")


class WebhookRead(BaseSchema):
    """Webhook integration details."""

    id: str
    name: str
    url: str
    target: str
    event_types: list[str]
    active: bool
    delivery_count: int
    failure_count: int
    last_delivery_at: str | None = None
    created_at: str


class WebhookListResponse(BaseSchema):
    """List of webhooks."""

    items: list[WebhookRead]
    total: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", response_model=WebhookRead, status_code=status.HTTP_201_CREATED)
async def register_webhook(body: WebhookCreateRequest, user: CurrentUser, db: DB) -> dict:
    """Register an outgoing webhook endpoint."""
    secret = secrets.token_hex(32)

    record = WebhookIntegrationRecord(
        name=body.name,
        url=body.url,
        target=body.target,
        event_types=body.event_types,
        secret=secret,
        active=True,
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)

    logger.info("webhook.registered", id=str(record.id), url=body.url, user=user.email)

    return _to_read(record)


@router.get("", response_model=WebhookListResponse)
async def list_webhooks(
    user: CurrentUser,
    db: DB,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> dict:
    """List registered outgoing webhooks."""
    result = await db.execute(
        select(WebhookIntegrationRecord)
        .where(WebhookIntegrationRecord.active.is_(True))
        .order_by(WebhookIntegrationRecord.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    records = result.scalars().all()
    return {"items": [_to_read(r) for r in records], "total": len(list(records))}


@router.delete("/{webhook_id}", response_model=MessageResponse)
async def deactivate_webhook(webhook_id: UUID, user: CurrentUser, db: DB) -> dict:
    """Deactivate an outgoing webhook."""
    result = await db.execute(
        select(WebhookIntegrationRecord).where(WebhookIntegrationRecord.id == webhook_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

    record.active = False
    await db.flush()
    logger.info("webhook.deactivated", id=str(webhook_id), user=user.email)
    return {"message": "Webhook deactivated", "success": True}


@router.post("/{webhook_id}/test", response_model=MessageResponse)
async def test_webhook(webhook_id: UUID, user: CurrentUser, db: DB) -> dict:
    """Send a test payload to a registered webhook."""
    result = await db.execute(
        select(WebhookIntegrationRecord).where(WebhookIntegrationRecord.id == webhook_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

    payload = {
        "event_type": "webhook.test",
        "delivery_id": secrets.token_hex(8),
        "timestamp": datetime.now(UTC).isoformat(),
        "data": {"message": "This is a test delivery from ComplianceAgent"},
    }

    success, status_code, error = await deliver(
        url=record.url,
        payload=payload,
        secret=record.secret,
        headers=dict(record.headers) if record.headers else None,
    )

    if success:
        record.delivery_count = (record.delivery_count or 0) + 1
        record.last_delivery_at = datetime.now(UTC)
        await db.flush()
        return {"message": f"Test delivered successfully (HTTP {status_code})", "success": True}

    record.failure_count = (record.failure_count or 0) + 1
    await db.flush()
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"Webhook delivery failed: {error}",
    )


def _to_read(record: WebhookIntegrationRecord) -> dict:
    return {
        "id": str(record.id),
        "name": record.name,
        "url": record.url,
        "target": record.target,
        "event_types": record.event_types or [],
        "active": record.active,
        "delivery_count": record.delivery_count or 0,
        "failure_count": record.failure_count or 0,
        "last_delivery_at": record.last_delivery_at.isoformat()
        if record.last_delivery_at
        else None,
        "created_at": record.created_at.isoformat(),
    }
