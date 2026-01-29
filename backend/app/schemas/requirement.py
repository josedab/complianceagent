"""Requirement schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.requirement import ObligationType, RequirementCategory
from app.schemas.base import BaseSchema, IDSchema, TimestampSchema


class RequirementCreate(BaseSchema):
    """Schema for creating a requirement."""

    regulation_id: UUID
    reference_id: str = Field(..., max_length=100)
    title: str = Field(..., min_length=1, max_length=500)
    description: str
    obligation_type: ObligationType
    category: RequirementCategory
    subject: str
    action: str
    object: str | None = None
    data_types: list[str] = Field(default_factory=list)
    processes: list[str] = Field(default_factory=list)
    systems: list[str] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)
    timeframe: str | None = None
    deadline_days: int | None = None
    source_text: str
    citations: list[dict] = Field(default_factory=list)
    penalty_description: str | None = None
    max_penalty_amount: float | None = None
    penalty_currency: str | None = None
    extraction_confidence: float = 0.0
    tags: list[str] = Field(default_factory=list)
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
