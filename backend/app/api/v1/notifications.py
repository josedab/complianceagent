"""Notifications API endpoints."""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_organization, get_current_user
from app.core.database import get_db
from app.models.notification import NotificationRecord
from app.models.organization import Organization
from app.models.user import User


logger = structlog.get_logger()

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    notification_type: str
    title: str
    message: str
    priority: str
    is_read: bool
    read_at: datetime | None
    notification_metadata: dict
    action_url: str | None
    created_at: datetime


@router.get("", response_model=dict)
async def list_notifications(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    is_read: bool | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
) -> dict:
    """List notifications for the current user in the current organization."""
    base_where = (
        NotificationRecord.user_id == current_user.id,
        NotificationRecord.organization_id == current_org.id,
    )
    if is_read is not None:
        filters = (*base_where, NotificationRecord.is_read == is_read)
    else:
        filters = base_where

    total_result = await db.execute(
        select(func.count()).select_from(NotificationRecord).where(*filters)
    )
    total = total_result.scalar_one()

    items_result = await db.execute(
        select(NotificationRecord)
        .where(*filters)
        .order_by(NotificationRecord.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    items = items_result.scalars().all()

    return {
        "items": [NotificationResponse.model_validate(r).model_dump() for r in items],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/unread-count", response_model=dict)
async def unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
) -> dict:
    """Return count of unread notifications for current user+org."""
    result = await db.execute(
        select(func.count())
        .select_from(NotificationRecord)
        .where(
            NotificationRecord.user_id == current_user.id,
            NotificationRecord.organization_id == current_org.id,
            NotificationRecord.is_read == False,  # noqa: E712
        )
    )
    return {"unread": result.scalar_one()}


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
) -> NotificationResponse:
    """Mark a notification as read."""
    result = await db.execute(
        select(NotificationRecord).where(
            NotificationRecord.id == notification_id,
            NotificationRecord.user_id == current_user.id,
            NotificationRecord.organization_id == current_org.id,
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    record.is_read = True
    record.read_at = datetime.now(UTC)
    await db.flush()
    return NotificationResponse.model_validate(record)


@router.post("/mark-all-read", response_model=dict)
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
) -> dict:
    """Mark all unread notifications as read for current user+org."""
    result = await db.execute(
        update(NotificationRecord)
        .where(
            NotificationRecord.user_id == current_user.id,
            NotificationRecord.organization_id == current_org.id,
            NotificationRecord.is_read == False,  # noqa: E712
        )
        .values(is_read=True, read_at=datetime.now(UTC))
    )
    return {"updated": result.rowcount}


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
) -> None:
    """Hard-delete a notification."""
    result = await db.execute(
        select(NotificationRecord).where(
            NotificationRecord.id == notification_id,
            NotificationRecord.user_id == current_user.id,
            NotificationRecord.organization_id == current_org.id,
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    await db.delete(record)
    await db.flush()
