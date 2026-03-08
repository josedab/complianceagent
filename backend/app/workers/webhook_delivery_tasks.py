"""Celery tasks for outgoing webhook delivery with retry."""

import asyncio
from datetime import UTC, datetime
from uuid import UUID

import structlog

from app.core.database import get_db_context
from app.services.webhooks.delivery import backoff_seconds, deliver
from app.workers import celery_app


logger = structlog.get_logger(__name__)

_MAX_RETRIES = 5


@celery_app.task(
    name="app.workers.webhook_delivery_tasks.deliver_webhook",
    bind=True,
    max_retries=_MAX_RETRIES,
    default_retry_delay=1,
)
def deliver_webhook(
    self,
    webhook_id: str,
    payload: dict,
    retry_count: int = 0,
):
    """Deliver a webhook payload with exponential backoff retry.

    Args:
        webhook_id: UUID of the WebhookIntegrationRecord
        payload: JSON-serializable event payload
        retry_count: Current retry attempt number
    """
    logger.info(
        "webhook_task.delivering",
        webhook_id=webhook_id,
        retry=retry_count,
    )
    asyncio.run(_deliver_async(self, webhook_id, payload, retry_count))


async def _deliver_async(task, webhook_id: str, payload: dict, retry_count: int):
    from sqlalchemy import select

    from app.models.production_features import WebhookIntegrationRecord

    async with get_db_context() as db:
        result = await db.execute(
            select(WebhookIntegrationRecord).where(WebhookIntegrationRecord.id == UUID(webhook_id))
        )
        record = result.scalar_one_or_none()

        if not record or not record.active:
            logger.warning("webhook_task.skipped_inactive", webhook_id=webhook_id)
            return

        success, status_code, error = await deliver(
            url=record.url,
            payload=payload,
            secret=record.secret or "",
            headers=dict(record.headers) if record.headers else None,
        )

        if success:
            record.delivery_count = (record.delivery_count or 0) + 1
            record.last_delivery_at = datetime.now(UTC)
            await db.commit()
            logger.info(
                "webhook_task.delivered",
                webhook_id=webhook_id,
                status=status_code,
            )
            return

        record.failure_count = (record.failure_count or 0) + 1
        await db.commit()

        if retry_count < _MAX_RETRIES:
            delay = backoff_seconds(retry_count)
            logger.warning(
                "webhook_task.retrying",
                webhook_id=webhook_id,
                error=error,
                retry=retry_count + 1,
                delay=delay,
            )
            task.retry(
                kwargs={
                    "webhook_id": webhook_id,
                    "payload": payload,
                    "retry_count": retry_count + 1,
                },
                countdown=delay,
            )
        else:
            logger.error(
                "webhook_task.exhausted_retries",
                webhook_id=webhook_id,
                error=error,
            )


def dispatch_event(event_type: str, data: dict):
    """Dispatch an event to all active webhooks subscribed to this event type.

    Call this from any service that wants to trigger outgoing webhooks.
    """
    asyncio.run(_dispatch_async(event_type, data))


async def _dispatch_async(event_type: str, data: dict):
    import secrets

    from sqlalchemy import select

    from app.models.production_features import WebhookIntegrationRecord

    async with get_db_context() as db:
        result = await db.execute(
            select(WebhookIntegrationRecord).where(WebhookIntegrationRecord.active.is_(True))
        )
        webhooks = result.scalars().all()

        for wh in webhooks:
            subscribed = "*" in (wh.event_types or []) or event_type in (wh.event_types or [])
            if not subscribed:
                continue

            payload = {
                "event_type": event_type,
                "delivery_id": secrets.token_hex(8),
                "timestamp": datetime.now(UTC).isoformat(),
                "data": data,
            }

            deliver_webhook.delay(
                webhook_id=str(wh.id),
                payload=payload,
            )
