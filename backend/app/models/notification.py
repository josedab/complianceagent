"""In-app notification model."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, JSONBType, UUIDType
from app.models.base import TimestampMixin, UUIDMixin


class NotificationRecord(Base, UUIDMixin, TimestampMixin):
    """In-app notification record."""

    __tablename__ = "notifications"

    organization_id: Mapped[UUIDType] = mapped_column(
        UUIDType, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUIDType] = mapped_column(
        UUIDType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    notification_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="medium", server_default="medium")
    is_read: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", index=True
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notification_metadata: Mapped[dict] = mapped_column(
        JSONBType, default=dict, server_default="{}"
    )
    action_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)


__all__ = ["NotificationRecord"]
