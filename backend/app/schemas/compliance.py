"""Compliance-related schemas for analysis and generation."""

from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from app.models.codebase import ComplianceStatus
from app.schemas.base import BaseSchema


class FrameworkComplianceStatus(BaseSchema):
    """Compliance status for a single framework."""

    framework: str
    status: ComplianceStatus
    compliant_count: int
    total_count: int
    compliance_percentage: float
    critical_gaps: int
    major_gaps: int
    minor_gaps: int
    next_deadline: date | None = None


class ComplianceStatusResponse(BaseSchema):
    """Overall compliance status response."""

    organization_id: UUID
    repository_id: UUID | None = None
    overall_score: float
    overall_status: ComplianceStatus
    frameworks: list[FrameworkComplianceStatus]
    total_requirements: int
    compliant_requirements: int
    pending_actions: int
    overdue_actions: int
    upcoming_deadlines: list[dict] = Field(default_factory=list)
    recent_changes: list[dict] = Field(default_factory=list)
    assessed_at: datetime


class AffectedFile(BaseSchema):
    """File affected by a requirement."""

    path: str
    relevance_score: float
    functions: list[str] = Field(default_factory=list)
    classes: list[str] = Field(default_factory=list)
    status: ComplianceStatus
    gaps: list[str] = Field(default_factory=list)


class ImpactAssessmentResponse(BaseSchema):
    """Impact assessment for a regulatory change."""

    regulation_id: UUID
    requirement_id: UUID | None = None
    repository_id: UUID
    summary: str
    affected_files: list[AffectedFile]
    total_files_affected: int
    total_lines_affected: int
    estimated_effort_hours: float
    estimated_effort_description: str
    risk_level: str
    risk_factors: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    recommended_priority: str
    deadline: date | None = None
    days_until_deadline: int | None = None
    confidence: float
    assessed_at: datetime


class CodeGenerationRequest(BaseSchema):
    """Request for code generation."""

    mapping_id: UUID
    include_tests: bool = True
    include_documentation: bool = True
    style_guide: str | None = None
    additional_context: str | None = None


class GeneratedFile(BaseSchema):
    """A generated or modified file."""

    path: str
    operation: str  # create, modify, delete
    content: str | None = None
    diff: str | None = None
    language: str | None = None


class GeneratedTest(BaseSchema):
    """A generated test."""

    path: str
    test_type: str  # unit, integration, compliance
    content: str
    description: str


class CodeGenerationResponse(BaseSchema):
    """Response from code generation."""

    mapping_id: UUID
    requirement_id: UUID
    files: list[GeneratedFile]
    tests: list[GeneratedTest]
    documentation: str | None = None
    pr_title: str
    pr_body: str
    compliance_comments: list[dict] = Field(default_factory=list)
    confidence: float
    warnings: list[str] = Field(default_factory=list)
    generated_at: datetime
