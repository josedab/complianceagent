"""Base schema utilities."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
    )


class TimestampSchema(BaseSchema):
    """Schema with timestamp fields."""

    created_at: datetime
    updated_at: datetime


class IDSchema(BaseSchema):
    """Schema with ID field."""

    id: UUID


class PaginatedResponse(BaseSchema):
    """Paginated response wrapper."""

    items: list
    total: int
    page: int
    page_size: int
    total_pages: int


class MessageResponse(BaseSchema):
    """Simple message response."""

    message: str
    success: bool = True
