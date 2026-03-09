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


class PaginatedResponse[T](BaseModel):
    """Paginated response wrapper with cursor support.

    Supports both offset-based (page/page_size) and cursor-based (next_cursor)
    pagination. Use ``paginate()`` helper to build responses from SQLAlchemy queries.
    """

    model_config = ConfigDict(from_attributes=True)

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool = False
    has_previous: bool = False
    next_cursor: str | None = None


def paginate(
    items: list,
    total: int,
    page: int,
    page_size: int,
) -> PaginatedResponse:
    """Build a PaginatedResponse from a list of items and total count."""
    total_pages = max(1, (total + page_size - 1) // page_size)
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )


class MessageResponse(BaseSchema):
    """Simple message response."""

    message: str
    success: bool = True
