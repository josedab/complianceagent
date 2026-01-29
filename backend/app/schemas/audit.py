"""Audit and compliance action schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.audit import AuditEventType, ComplianceActionStatus
from app.schemas.base import BaseSchema, IDSchema, TimestampSchema


class AuditTrailRead(IDSchema, TimestampSchema):
    """Schema for reading an audit trail entry."""

    organization_id: UUID
    regulation_id: UUID | None
    requirement_id: UUID | None
    repository_id: UUID | None
    mapping_id: UUID | None
    compliance_action_id: UUID | None
    event_type: AuditEventType
    event_description: str
    event_data: dict
    actor_type: str
    actor_id: str | None
    actor_email: str | None
    ai_model: str | None
    ai_confidence: float | None
    entry_hash: str


class ComplianceActionCreate(BaseSchema):
    """Schema for creating a compliance action."""

    regulation_id: UUID
    requirement_id: UUID
    repository_id: UUID
    mapping_id: UUID | None = None
    title: str = Field(..., min_length=1, max_length=500)
    description: str
    priority: str = "medium"
    deadline: datetime | None = None
    assigned_to: UUID | None = None
    tags: list[str] = Field(default_factory=list)


class ComplianceActionUpdate(BaseSchema):
    """Schema for updating a compliance action."""

    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    status: ComplianceActionStatus | None = None
    priority: str | None = None
    deadline: datetime | None = None
    assigned_to: UUID | None = None
    tags: list[str] | None = None


class ComplianceActionRead(IDSchema, TimestampSchema):
    """Schema for reading a compliance action."""

    organization_id: UUID
    regulation_id: UUID
    requirement_id: UUID
    repository_id: UUID
    mapping_id: UUID | None
    title: str
    description: str
    status: ComplianceActionStatus
    priority: str
    deadline: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    assigned_to: UUID | None
    assigned_at: datetime | None
    impact_summary: str | None
    affected_files_count: int
    estimated_effort_hours: float | None
    risk_level: str | None
    pr_url: str | None
    pr_number: int | None
    pr_status: str | None
    verification_status: str | None
    tags: list[str]
