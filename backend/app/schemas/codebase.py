"""Codebase mapping schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.codebase import ComplianceStatus, GapSeverity, RepositoryProvider
from app.schemas.base import BaseSchema, IDSchema, TimestampSchema


class RepositoryCreate(BaseSchema):
    """Schema for creating a repository."""

    customer_profile_id: UUID
    provider: RepositoryProvider
    owner: str = Field(..., max_length=255)
    name: str = Field(..., max_length=255)
    default_branch: str = "main"
    installation_id: str | None = None


class RepositoryRead(IDSchema, TimestampSchema):
    """Schema for reading a repository."""

    customer_profile_id: UUID
    provider: RepositoryProvider
    owner: str
    name: str
    full_name: str
    default_branch: str
    is_active: bool
    last_analyzed_at: datetime | None
    last_analyzed_commit: str | None
    analysis_status: str
    primary_language: str | None
    languages: list[str]
    compliance_score: float | None
    total_requirements: int
    compliant_requirements: int
    gaps_critical: int
    gaps_major: int
    gaps_minor: int


class GapDetail(BaseSchema):
    """Detail of a compliance gap."""

    id: str
    severity: GapSeverity
    description: str
    file_path: str | None = None
    line_number: int | None = None
    suggestion: str | None = None
    remediation_effort: str | None = None


class CodebaseMappingCreate(BaseSchema):
    """Schema for creating a codebase mapping."""

    repository_id: UUID
    requirement_id: UUID
    compliance_status: ComplianceStatus = ComplianceStatus.PENDING_REVIEW
    compliance_notes: str | None = None


class CodebaseMappingRead(IDSchema, TimestampSchema):
    """Schema for reading a codebase mapping."""

    repository_id: UUID
    requirement_id: UUID
    compliance_status: ComplianceStatus
    compliance_notes: str | None
    affected_files: list[dict]
    affected_functions: list[dict]
    affected_classes: list[dict]
    data_flows: list[dict]
    existing_implementations: list[dict]
    gaps: list[dict]
    gap_count: int
    critical_gaps: int
    major_gaps: int
    minor_gaps: int
    estimated_effort_hours: float | None
    estimated_effort_description: str | None
    risk_level: str | None
    mapping_confidence: float
    analyzed_at: datetime | None
    analyzed_commit: str | None
    human_reviewed: bool
    reviewed_by: str | None
    reviewed_at: datetime | None
    implementation_pr_url: str | None
    implementation_pr_status: str | None
