"""Requirement schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.requirement import ObligationType, RequirementCategory
from app.schemas.base import BaseSchema, IDSchema, TimestampSchema


class RequirementCreate(BaseSchema):
    """Schema for creating a requirement."""

    regulation_id: UUID
    reference_id: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1, max_length=10000)
    obligation_type: ObligationType
    category: RequirementCategory
    subject: str = Field(..., min_length=1, max_length=500)
    action: str = Field(..., min_length=1, max_length=500)
    object: str | None = Field(None, max_length=500)
    data_types: list[str] = Field(default_factory=list, max_length=50)
    processes: list[str] = Field(default_factory=list, max_length=50)
    systems: list[str] = Field(default_factory=list, max_length=50)
    roles: list[str] = Field(default_factory=list, max_length=50)
    timeframe: str | None = Field(None, max_length=200)
    deadline_days: int | None = Field(None, ge=0, le=3650)
    source_text: str = Field(..., min_length=1, max_length=50000)
    citations: list[dict] = Field(default_factory=list)
    penalty_description: str | None = Field(None, max_length=2000)
    max_penalty_amount: float | None = Field(None, ge=0)
    penalty_currency: str | None = Field(None, max_length=3, pattern=r"^[A-Z]{3}$")
    extraction_confidence: float = Field(0.0, ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list, max_length=50)
    metadata: dict = Field(default_factory=dict)


class RequirementRead(IDSchema, TimestampSchema):
    """Schema for reading a requirement."""

    regulation_id: UUID
    reference_id: str
    title: str
    description: str
    obligation_type: ObligationType
    category: RequirementCategory
    subject: str
    action: str
    object: str | None
    data_types: list[str]
    processes: list[str]
    systems: list[str]
    roles: list[str]
    timeframe: str | None
    deadline_days: int | None
    source_text: str
    citations: list[dict]
    penalty_description: str | None
    max_penalty_amount: float | None
    penalty_currency: str | None
    extraction_confidence: float
    extracted_at: datetime | None
    human_reviewed: bool
    reviewed_by: str | None
    reviewed_at: datetime | None
    tags: list[str]
    metadata: dict


class RequirementSummary(IDSchema):
    """Brief requirement summary."""

    reference_id: str
    title: str
    obligation_type: ObligationType
    category: RequirementCategory
    extraction_confidence: float
    human_reviewed: bool
