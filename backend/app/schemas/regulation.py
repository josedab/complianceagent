"""Regulation schemas."""

from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from app.models.regulation import (
    ChangeType,
    Jurisdiction,
    RegulationStatus,
    RegulatoryFramework,
)
from app.schemas.base import BaseSchema, IDSchema, TimestampSchema


class RegulatorySourceCreate(BaseSchema):
    """Schema for creating a regulatory source."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    url: str = Field(..., min_length=1, max_length=2048)
    jurisdiction: Jurisdiction
    framework: RegulatoryFramework | None = None
    check_interval_hours: int = Field(24, ge=1, le=720)
    parser_type: str = Field("html", max_length=50)
    parser_config: dict = Field(default_factory=dict)


class RegulatorySourceRead(IDSchema, TimestampSchema):
    """Schema for reading a regulatory source."""

    name: str
    description: str | None
    url: str
    jurisdiction: Jurisdiction
    framework: RegulatoryFramework | None
    is_active: bool
    check_interval_hours: int
    last_checked_at: datetime | None
    last_change_detected_at: datetime | None
    consecutive_failures: int
    total_checks: int
    successful_checks: int


class RegulationCreate(BaseSchema):
    """Schema for creating a regulation."""

    name: str = Field(..., min_length=1, max_length=500)
    short_name: str | None = Field(None, max_length=100)
    official_reference: str | None = Field(None, max_length=500)
    jurisdiction: Jurisdiction
    framework: RegulatoryFramework
    status: RegulationStatus = RegulationStatus.EFFECTIVE
    published_date: date | None = None
    effective_date: date | None = None
    enforcement_date: date | None = None
    source_url: str | None = Field(None, max_length=2048)
    content_summary: str | None = Field(None, max_length=10000)
    change_type: ChangeType | None = None
    parent_regulation_id: UUID | None = None
    tags: list[str] = Field(default_factory=list, max_length=50)
    metadata: dict = Field(default_factory=dict)


class RegulationRead(IDSchema, TimestampSchema):
    """Schema for reading a regulation."""

    source_id: UUID | None
    name: str
    short_name: str | None
    official_reference: str | None
    jurisdiction: Jurisdiction
    framework: RegulatoryFramework
    status: RegulationStatus
    published_date: date | None
    effective_date: date | None
    enforcement_date: date | None
    expiry_date: date | None
    source_url: str | None
    content_summary: str | None
    change_type: ChangeType | None
    parent_regulation_id: UUID | None
    version: int
    is_parsed: bool
    parsed_at: datetime | None
    parsing_confidence: float | None
    tags: list[str]
    metadata: dict
    requirements_count: int = 0


class RegulationSummary(IDSchema):
    """Brief regulation summary."""

    name: str
    short_name: str | None
    jurisdiction: Jurisdiction
    framework: RegulatoryFramework
    status: RegulationStatus
    effective_date: date | None
    requirements_count: int = 0
