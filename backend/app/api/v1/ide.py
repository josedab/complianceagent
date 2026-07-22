"""IDE integration API endpoints for real-time compliance analysis."""

import contextlib
import re
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select

from app.api.v1.deps import DB, CurrentOrganization, OrgAdmin, OrgMember
from app.models.ide_learning import IDERuleEventRecord, TeamSuppressionRecord
from app.services.ide import (
    DiagnosticSeverity,
    IDEComplianceAnalyzer,
    get_copilot_suggester,
)


router = APIRouter()


class AnalyzeDocumentRequest(BaseModel):
    """Request to analyze a document for compliance issues."""

    uri: str
    content: str
    language: str | None = None
    version: int | None = None
    regulations: list[str] | None = Field(
        default=None,
        description="List of regulations to check against. If not provided, all enabled regulations are used.",
    )


class DiagnosticResponse(BaseModel):
    """A single compliance diagnostic."""

    range: dict[str, dict[str, int]]
    message: str
    severity: str
    code: str
    source: str
    category: str | None = None
    regulation: str | None = None
    article_reference: str | None = None


class AnalyzeDocumentResponse(BaseModel):
    """Response from document analysis."""

    uri: str
    version: int | None
    diagnostics: list[DiagnosticResponse]
    analysis_time_ms: float
    patterns_checked: int
    analyzed_at: datetime


class AddPatternRequest(BaseModel):
    """Request to add a custom compliance pattern."""

    name: str
    pattern: str
    message: str
    severity: str = "warning"
    category: str | None = None
    regulation: str | None = None
    code: str | None = None


class HoverRequest(BaseModel):
    """Request for hover information."""

    uri: str
    content: str
    line: int
    character: int


class IDEConfigResponse(BaseModel):
    """IDE configuration response."""

    enabled_regulations: list[str]
    severity_threshold: str
    custom_patterns_count: int
    supported_languages: list[str]


class QuickFixRequest(BaseModel):
    """Request for AI-generated quick fix."""

    code: str
    diagnostic_code: str
    diagnostic_message: str
    regulation: str | None = None
    article_reference: str | None = None
    language: str = "python"
    fix_type: str = "auto"


class QuickFixResponse(BaseModel):
    """Response from quick fix generation."""

    original_code: str
    fixed_code: str
    explanation: str
    imports_added: list[str] | None = None
    compliance_comments: list[str] | None = None


class SuggestionRequest(BaseModel):
    """Request for AI-powered compliance suggestion."""

    code: str
    diagnostic_code: str
    diagnostic_message: str
    regulation: str | None = None
    category: str | None = None
    article_reference: str | None = None
    language: str = "python"
    context_before: str | None = None
    context_after: str | None = None


class SuggestionResponse(BaseModel):
    """Response from AI suggestion generation."""

    fix_code: str | None
    explanation: str | None
    confidence: float
    regulation_context: str | None = None
    related_requirements: list[str] | None = None


class RegulationTooltipRequest(BaseModel):
    """Request for regulation tooltip information."""

    regulation: str
    article_reference: str | None = None
    category: str | None = None


class RegulationTooltipResponse(BaseModel):
    """Response with regulation tooltip information."""

    title: str
    summary: str
    key_requirements: list[str]
    penalties: str
    examples: list[dict[str, str]]
    resources: list[dict[str, str]]


class DeepAnalysisRequest(BaseModel):
    """Request for deep AI code analysis."""

    code: str
    language: str = "python"
    regulations: list[str] | None = None


class DeepAnalysisIssue(BaseModel):
    """A single issue from deep analysis."""

    range: dict[str, dict[str, int]]
    message: str
    severity: str
    code: str
    regulation: str | None = None
    article_reference: str | None = None
    fix_code: str | None = None
    explanation: str | None = None
    confidence: float


class DeepAnalysisResponse(BaseModel):
    """Response from deep AI code analysis."""

    issues: list[DeepAnalysisIssue]
    analyzed_at: datetime


# Global analyzer instance (can be customized per-organization in production)
_analyzer_cache: dict[UUID, IDEComplianceAnalyzer] = {}


def get_analyzer(
    organization_id: UUID, regulations: list[str] | None = None
) -> IDEComplianceAnalyzer:
    """Get or create an analyzer for an organization."""
    cache_key = organization_id
    if cache_key not in _analyzer_cache:
        _analyzer_cache[cache_key] = IDEComplianceAnalyzer(
            enabled_regulations=regulations or ["GDPR", "CCPA", "HIPAA", "EU AI Act", "SOX"],
        )
    return _analyzer_cache[cache_key]


@router.post("/analyze", response_model=AnalyzeDocumentResponse)
async def analyze_document(
    request: AnalyzeDocumentRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> AnalyzeDocumentResponse:
    """Analyze a document for compliance issues.

    This endpoint is used by IDE extensions to get real-time compliance
    diagnostics for code being edited.
    """
    analyzer = get_analyzer(organization.id, request.regulations)

    result = analyzer.analyze_document(
        uri=request.uri,
        content=request.content,
        language=request.language,
        version=request.version,
    )

    diagnostics = []
    for diag in result.diagnostics:
        diagnostics.append(
            DiagnosticResponse(
                range={
                    "start": {
                        "line": diag.range.start.line,
                        "character": diag.range.start.character,
                    },
                    "end": {"line": diag.range.end.line, "character": diag.range.end.character},
                },
                message=diag.message,
                severity=diag.severity.value,
                code=diag.code,
                source=diag.source,
                category=diag.category.value if diag.category else None,
                regulation=diag.regulation,
                article_reference=diag.article_reference,
            )
        )

    if result.diagnostics:
        detected_at = datetime.now(UTC)
        db.add_all(
            [
                IDERuleEventRecord(
                    organization_id=organization.id,
                    user_id=member.user_id,
                    rule_id=diag.code,
                    event_type="detection",
                    file_path=request.uri,
                    event_metadata={
                        "message": diag.message,
                        "severity": diag.severity.value,
                        "regulation": diag.regulation,
                        "article_reference": diag.article_reference,
                        "line": diag.range.start.line,
                        "detected_at": detected_at.isoformat(),
                    },
                )
                for diag in result.diagnostics
            ]
        )
        await db.flush()

    return AnalyzeDocumentResponse(
        uri=result.uri,
        version=result.version,
        diagnostics=diagnostics,
        analysis_time_ms=result.analysis_time_ms,
        patterns_checked=result.patterns_checked,
        analyzed_at=datetime.now(UTC),
    )


@router.post("/hover")
async def get_hover_info(
    request: HoverRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any] | None:
    """Get compliance hover information for a position.

    Returns detailed information when hovering over code with compliance issues.
    """
    analyzer = get_analyzer(organization.id)
    return analyzer.get_hover_info(
        uri=request.uri,
        content=request.content,
        line=request.line,
        character=request.character,
    )


@router.post("/patterns")
async def add_custom_pattern(
    request: AddPatternRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Add a custom compliance pattern for the organization."""
    analyzer = get_analyzer(organization.id)

    try:
        analyzer.add_custom_pattern(
            name=request.name,
            pattern=request.pattern,
            message=request.message,
            severity=DiagnosticSeverity(request.severity),
            regulation=request.regulation,
            code=request.code,
        )
        return {"success": True, "pattern_name": request.name}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid pattern: {e!s}",
        ) from e


@router.delete("/patterns/{pattern_name}")
async def remove_custom_pattern(
    pattern_name: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Remove a custom compliance pattern."""
    analyzer = get_analyzer(organization.id)

    if analyzer.remove_custom_pattern(pattern_name):
        return {"success": True}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Pattern '{pattern_name}' not found",
    )


@router.get("/config", response_model=IDEConfigResponse)
async def get_ide_config(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> IDEConfigResponse:
    """Get IDE integration configuration."""
    analyzer = get_analyzer(organization.id)

    return IDEConfigResponse(
        enabled_regulations=analyzer.enabled_regulations,
        severity_threshold=analyzer.severity_threshold.value,
        custom_patterns_count=len(analyzer.custom_patterns),
        supported_languages=[
            "python",
            "javascript",
            "typescript",
            "java",
            "go",
            "ruby",
            "php",
            "csharp",
        ],
    )


@router.put("/config")
async def update_ide_config(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    regulations: list[str] | None = None,
    severity_threshold: str | None = None,
) -> IDEConfigResponse:
    """Update IDE integration configuration."""
    # Create new analyzer with updated config
    new_analyzer = IDEComplianceAnalyzer(
        enabled_regulations=regulations or ["GDPR", "CCPA", "HIPAA", "EU AI Act"],
        severity_threshold=DiagnosticSeverity(severity_threshold)
        if severity_threshold
        else DiagnosticSeverity.HINT,
    )

    # Copy custom patterns from old analyzer
    old_analyzer = _analyzer_cache.get(organization.id)
    if old_analyzer:
        new_analyzer.custom_patterns = old_analyzer.custom_patterns
        new_analyzer._compile_patterns()

    _analyzer_cache[organization.id] = new_analyzer

    return IDEConfigResponse(
        enabled_regulations=new_analyzer.enabled_regulations,
        severity_threshold=new_analyzer.severity_threshold.value,
        custom_patterns_count=len(new_analyzer.custom_patterns),
        supported_languages=[
            "python",
            "javascript",
            "typescript",
            "java",
            "go",
            "ruby",
            "php",
            "csharp",
        ],
    )


# ============================================================================
# Copilot-Powered Endpoints (New)
# ============================================================================


@router.post("/suggest", response_model=SuggestionResponse)
async def get_ai_suggestion(
    request: SuggestionRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> SuggestionResponse:
    """Get AI-powered compliance suggestion for a code issue.

    Uses GitHub Copilot SDK to generate context-aware suggestions
    for fixing compliance violations.
    """
    from app.services.ide.diagnostic import (
        ComplianceDiagnostic,
        DiagnosticCategory,
        DiagnosticSeverity,
        Position,
        Range,
    )

    suggester = get_copilot_suggester()

    # Create diagnostic from request
    category = None
    if request.category:
        with contextlib.suppress(ValueError):
            category = DiagnosticCategory(request.category)

    diagnostic = ComplianceDiagnostic(
        range=Range(start=Position(0, 0), end=Position(0, len(request.code))),
        message=request.diagnostic_message,
        severity=DiagnosticSeverity.WARNING,
        code=request.diagnostic_code,
        regulation=request.regulation,
        category=category,
        article_reference=request.article_reference,
    )

    suggestion = await suggester.generate_suggestion(
        code=request.code,
        diagnostic=diagnostic,
        language=request.language,
        context_before=request.context_before,
        context_after=request.context_after,
    )

    return SuggestionResponse(
        fix_code=suggestion.fix_code,
        explanation=suggestion.explanation,
        confidence=suggestion.confidence,
        regulation_context=suggestion.regulation_context,
        related_requirements=suggestion.related_requirements,
    )


@router.post("/quickfix", response_model=QuickFixResponse)
async def generate_quick_fix(
    request: QuickFixRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> QuickFixResponse:
    """Generate AI-powered quick fix for a compliance issue.

    Produces production-ready code that addresses the compliance
    violation while maintaining code style and patterns.
    """
    from app.services.ide.diagnostic import (
        ComplianceDiagnostic,
        DiagnosticSeverity,
        Position,
        Range,
    )

    suggester = get_copilot_suggester()

    diagnostic = ComplianceDiagnostic(
        range=Range(start=Position(0, 0), end=Position(0, len(request.code))),
        message=request.diagnostic_message,
        severity=DiagnosticSeverity.WARNING,
        code=request.diagnostic_code,
        regulation=request.regulation,
        article_reference=request.article_reference,
    )

    result = await suggester.generate_quick_fix(
        code=request.code,
        diagnostic=diagnostic,
        language=request.language,
        fix_type=request.fix_type,
    )

    return QuickFixResponse(
        original_code=result.original_code,
        fixed_code=result.fixed_code,
        explanation=result.explanation,
        imports_added=result.imports_added,
        compliance_comments=result.compliance_comments,
    )


@router.post("/tooltip", response_model=RegulationTooltipResponse)
async def get_regulation_tooltip(
    request: RegulationTooltipRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> RegulationTooltipResponse:
    """Get detailed regulation information for IDE tooltip display.

    Provides comprehensive regulation context including requirements,
    penalties, and code examples.
    """
    from app.services.ide.diagnostic import DiagnosticCategory

    suggester = get_copilot_suggester()

    category = None
    if request.category:
        with contextlib.suppress(ValueError):
            category = DiagnosticCategory(request.category)

    tooltip = await suggester.get_regulation_tooltip(
        regulation=request.regulation,
        article_reference=request.article_reference,
        category=category,
    )

    return RegulationTooltipResponse(
        title=tooltip.get("title", request.regulation),
        summary=tooltip.get("summary", ""),
        key_requirements=tooltip.get("key_requirements", []),
        penalties=tooltip.get("penalties", ""),
        examples=tooltip.get("examples", []),
        resources=tooltip.get("resources", []),
    )


@router.post("/deep-analyze", response_model=DeepAnalysisResponse)
async def deep_analyze_code(
    request: DeepAnalysisRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> DeepAnalysisResponse:
    """Perform deep AI analysis of code for compliance issues.

    Uses Copilot SDK for comprehensive analysis beyond pattern matching,
    identifying nuanced compliance issues and providing detailed fixes.
    """
    suggester = get_copilot_suggester()

    suggestions = await suggester.analyze_code_block(
        code=request.code,
        language=request.language,
        regulations=request.regulations,
    )

    issues = []
    for s in suggestions:
        issues.append(
            DeepAnalysisIssue(
                range={
                    "start": {
                        "line": s.diagnostic.range.start.line,
                        "character": s.diagnostic.range.start.character,
                    },
                    "end": {
                        "line": s.diagnostic.range.end.line,
                        "character": s.diagnostic.range.end.character,
                    },
                },
                message=s.diagnostic.message,
                severity=s.diagnostic.severity.value,
                code=s.diagnostic.code,
                regulation=s.diagnostic.regulation,
                article_reference=s.diagnostic.article_reference,
                fix_code=s.fix_code,
                explanation=s.explanation,
                confidence=s.confidence,
            )
        )

    return DeepAnalysisResponse(
        issues=issues,
        analyzed_at=datetime.now(UTC),
    )


# WebSocket endpoint for real-time analysis
@router.websocket("/ws")
async def ide_websocket(
    websocket: WebSocket,
    db: DB,
) -> None:
    """WebSocket endpoint for real-time IDE analysis.

    Provides bidirectional communication for continuous compliance monitoring.
    """
    await websocket.accept()

    # Default analyzer for unauthenticated connections (demo mode)
    analyzer = IDEComplianceAnalyzer()

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "analyze":
                result = analyzer.analyze_document(
                    uri=data.get("uri", ""),
                    content=data.get("content", ""),
                    language=data.get("language"),
                    version=data.get("version"),
                )

                diagnostics = [d.to_lsp_diagnostic() for d in result.diagnostics]

                await websocket.send_json(
                    {
                        "type": "diagnostics",
                        "uri": result.uri,
                        "version": result.version,
                        "diagnostics": diagnostics,
                        "analysisTimeMs": result.analysis_time_ms,
                    }
                )

            elif action == "hover":
                hover_info = analyzer.get_hover_info(
                    uri=data.get("uri", ""),
                    content=data.get("content", ""),
                    line=data.get("line", 0),
                    character=data.get("character", 0),
                )

                await websocket.send_json(
                    {
                        "type": "hover",
                        "info": hover_info,
                    }
                )

            elif action == "setRegulations":
                analyzer = IDEComplianceAnalyzer(
                    enabled_regulations=data.get("regulations", []),
                )
                await websocket.send_json(
                    {
                        "type": "configUpdated",
                        "regulations": analyzer.enabled_regulations,
                    }
                )

            elif action == "deepAnalyze":
                suggester = get_copilot_suggester()
                suggestions = await suggester.analyze_code_block(
                    code=data.get("content", ""),
                    language=data.get("language", "python"),
                    regulations=data.get("regulations"),
                )

                issues = []
                for s in suggestions:
                    issues.append(
                        {
                            "range": {
                                "start": {
                                    "line": s.diagnostic.range.start.line,
                                    "character": s.diagnostic.range.start.character,
                                },
                                "end": {
                                    "line": s.diagnostic.range.end.line,
                                    "character": s.diagnostic.range.end.character,
                                },
                            },
                            "message": s.diagnostic.message,
                            "severity": s.diagnostic.severity.value,
                            "code": s.diagnostic.code,
                            "fixCode": s.fix_code,
                            "explanation": s.explanation,
                        }
                    )

                await websocket.send_json(
                    {
                        "type": "deepAnalysis",
                        "issues": issues,
                    }
                )

    except WebSocketDisconnect:
        pass


# ============================================================================
# Team Suppressions Endpoints (New)
# ============================================================================


class TeamSuppressionRequest(BaseModel):
    """Request to create a team suppression."""

    rule_id: str = Field(min_length=1, max_length=200)
    pattern: str | None = Field(default=None, max_length=2000)
    reason: str = Field(min_length=1, max_length=5000)
    expires_at: datetime | None = None

    @field_validator("pattern")
    @classmethod
    def validate_pattern(cls, value: str | None) -> str | None:
        if value:
            try:
                re.compile(value)
            except re.error as exc:
                raise ValueError(f"Invalid regular expression: {exc}") from exc
        return value


class TeamSuppressionResponse(BaseModel):
    """Team suppression entry."""

    id: str
    rule_id: str
    pattern: str | None
    reason: str
    created_by: str
    created_at: datetime
    expires_at: datetime | None
    approved: bool
    approved_by: str | None
    usage_count: int


class FeedbackRequest(BaseModel):
    """Request to submit feedback on a detection."""

    type: Literal["false_positive", "false_negative", "severity_adjustment", "helpful"]
    issue: dict[str, Any]
    user_action: Literal["suppressed", "fixed", "ignored", "reported"] | None = None
    context: dict[str, Any] = Field(default_factory=dict)
    reason: str | None = Field(default=None, max_length=5000)
    timestamp: datetime | None = None
    time_to_fix_minutes: float | None = Field(default=None, ge=0)


class FeedbackBatchRequest(BaseModel):
    """Bounded batch of IDE feedback events."""

    items: list[FeedbackRequest] = Field(min_length=1, max_length=100)


def _suppression_response(record: TeamSuppressionRecord) -> TeamSuppressionResponse:
    return TeamSuppressionResponse(
        id=str(record.id),
        rule_id=record.rule_id,
        pattern=record.pattern,
        reason=record.reason,
        created_by=str(record.created_by),
        created_at=record.created_at,
        expires_at=record.expires_at,
        approved=record.approved,
        approved_by=str(record.approved_by) if record.approved_by else None,
        usage_count=record.usage_count,
    )


def _feedback_rule_id(request: FeedbackRequest) -> str:
    value = request.issue.get("requirementId") or request.issue.get("rule_id")
    rule_id = str(value or "").strip()
    if not rule_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Feedback issue must include requirementId or rule_id",
        )
    return rule_id


async def _store_feedback(
    request: FeedbackRequest,
    organization_id: UUID,
    user_id: UUID,
    db: DB,
) -> None:
    rule_id = _feedback_rule_id(request)
    line = request.issue.get("line")
    document_uri = request.context.get("file") or request.issue.get("file")
    db.add(
        IDERuleEventRecord(
            organization_id=organization_id,
            user_id=user_id,
            rule_id=rule_id,
            event_type=request.type,
            file_path=str(document_uri) if document_uri else None,
            reason=request.reason,
            event_metadata={
                "user_action": request.user_action,
                "line": int(line) if isinstance(line, (int, float)) else None,
                "issue": request.issue,
                "context": request.context,
                "time_to_fix_minutes": request.time_to_fix_minutes,
                "occurred_at": (request.timestamp or datetime.now(UTC)).isoformat(),
            },
        )
    )


@router.get("/suppressions", response_model=list[TeamSuppressionResponse])
async def get_team_suppressions(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> list[TeamSuppressionResponse]:
    """Get team-wide suppressions for the organization."""
    result = await db.execute(
        select(TeamSuppressionRecord)
        .where(TeamSuppressionRecord.organization_id == organization.id)
        .order_by(TeamSuppressionRecord.created_at.desc())
    )
    now = datetime.now(UTC)
    records = [
        record
        for record in result.scalars().all()
        if record.expires_at is None or record.expires_at > now
    ]
    return [_suppression_response(record) for record in records]


@router.post(
    "/suppressions",
    response_model=TeamSuppressionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_team_suppression(
    request: TeamSuppressionRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> TeamSuppressionResponse:
    """Request a new team-wide suppression.

    Suppressions require approval from an admin before taking effect.
    """
    if request.expires_at and request.expires_at <= datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="expires_at must be in the future",
        )
    existing_result = await db.execute(
        select(TeamSuppressionRecord).where(
            TeamSuppressionRecord.organization_id == organization.id,
            TeamSuppressionRecord.rule_id == request.rule_id,
            TeamSuppressionRecord.pattern == request.pattern,
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A matching team suppression already exists",
        )

    record = TeamSuppressionRecord(
        organization_id=organization.id,
        rule_id=request.rule_id,
        pattern=request.pattern,
        reason=request.reason,
        created_by=member.user_id,
        expires_at=request.expires_at,
        approved=False,
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return _suppression_response(record)


@router.put(
    "/suppressions/{suppression_id}/approve",
    response_model=TeamSuppressionResponse,
)
async def approve_team_suppression(
    suppression_id: UUID,
    organization: CurrentOrganization,
    admin: OrgAdmin,
    db: DB,
) -> TeamSuppressionResponse:
    """Approve a team suppression (admin only)."""
    result = await db.execute(
        select(TeamSuppressionRecord).where(
            TeamSuppressionRecord.id == suppression_id,
            TeamSuppressionRecord.organization_id == organization.id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suppression not found",
        )
    if record.expires_at and record.expires_at <= datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Expired suppressions cannot be approved",
        )

    record.approved = True
    record.approved_by = admin.user_id
    record.approved_at = datetime.now(UTC)
    await db.flush()
    return _suppression_response(record)


@router.delete("/suppressions/{suppression_id}")
async def delete_team_suppression(
    suppression_id: UUID,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, str]:
    """Delete a team suppression."""
    result = await db.execute(
        select(TeamSuppressionRecord).where(
            TeamSuppressionRecord.id == suppression_id,
            TeamSuppressionRecord.organization_id == organization.id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suppression not found",
        )
    if record.created_by != member.user_id and member.role not in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the requester or an organization admin may delete this suppression",
        )

    await db.delete(record)
    await db.flush()
    return {"status": "deleted"}


@router.post(
    "/suppressions/{suppression_id}/usage",
    response_model=TeamSuppressionResponse,
)
async def record_team_suppression_usage(
    suppression_id: UUID,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> TeamSuppressionResponse:
    """Record use of an approved, unexpired team suppression."""
    result = await db.execute(
        select(TeamSuppressionRecord).where(
            TeamSuppressionRecord.id == suppression_id,
            TeamSuppressionRecord.organization_id == organization.id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suppression not found",
        )
    if not record.approved:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Suppression has not been approved",
        )
    if record.expires_at and record.expires_at <= datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Suppression has expired",
        )

    record.usage_count += 1
    await db.flush()
    return _suppression_response(record)


@router.post("/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, str]:
    """Submit feedback on a compliance detection.

    Feedback is used to improve detection accuracy through machine learning.
    """
    import structlog

    logger = structlog.get_logger()

    await _store_feedback(request, organization.id, member.user_id, db)
    await db.flush()
    logger.info(
        "IDE feedback received",
        organization_id=str(organization.id),
        user_id=str(member.user_id),
        feedback_type=request.type,
        rule_id=request.issue.get("requirementId"),
        reason=request.reason,
    )

    return {"status": "received", "message": "Thank you for your feedback!"}


@router.post("/feedback/batch")
async def submit_feedback_batch(
    request: FeedbackBatchRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, int | str]:
    """Persist a bounded batch of IDE feedback events atomically."""
    for item in request.items:
        await _store_feedback(item, organization.id, member.user_id, db)
    await db.flush()
    return {"status": "received", "accepted": len(request.items)}


# ============================================================================
# Rule Statistics Endpoints (New)
# ============================================================================


class RuleStatsResponse(BaseModel):
    """Statistics for a compliance rule."""

    rule_id: str
    total_detections: int
    false_positive_rate: float
    fix_rate: float
    suppression_rate: float
    avg_time_to_fix_minutes: float | None


async def _get_rule_statistics(
    organization_id: UUID,
    db: DB,
    rule_id: str | None = None,
) -> list[RuleStatsResponse]:
    statement = select(IDERuleEventRecord).where(
        IDERuleEventRecord.organization_id == organization_id
    )
    if rule_id is not None:
        statement = statement.where(IDERuleEventRecord.rule_id == rule_id)
    result = await db.execute(statement)

    grouped: dict[str, list[IDERuleEventRecord]] = defaultdict(list)
    for event in result.scalars().all():
        grouped[event.rule_id].append(event)

    statistics: list[RuleStatsResponse] = []
    for current_rule_id, events in sorted(grouped.items()):
        total_detections = sum(event.event_type == "detection" for event in events)
        denominator = total_detections or 1
        false_positives = sum(event.event_type == "false_positive" for event in events)
        fixed = sum(event.event_metadata.get("user_action") == "fixed" for event in events)
        suppressed = sum(
            event.event_metadata.get("user_action") == "suppressed" for event in events
        )
        fix_times = [
            float(event.event_metadata["time_to_fix_minutes"])
            for event in events
            if event.event_metadata.get("time_to_fix_minutes") is not None
        ]
        statistics.append(
            RuleStatsResponse(
                rule_id=current_rule_id,
                total_detections=total_detections,
                false_positive_rate=min(false_positives / denominator, 1.0),
                fix_rate=min(fixed / denominator, 1.0),
                suppression_rate=min(suppressed / denominator, 1.0),
                avg_time_to_fix_minutes=(sum(fix_times) / len(fix_times) if fix_times else None),
            )
        )
    return statistics


@router.get("/stats/rules", response_model=list[RuleStatsResponse])
async def get_rule_statistics(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> list[RuleStatsResponse]:
    """Get organization-scoped effectiveness statistics for compliance rules."""
    return await _get_rule_statistics(organization.id, db)


@router.get("/stats/rules/{rule_id}", response_model=RuleStatsResponse)
async def get_rule_stats(
    rule_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> RuleStatsResponse:
    """Get statistics for a specific rule."""
    statistics = await _get_rule_statistics(organization.id, db, rule_id)
    if statistics:
        return statistics[0]
    return RuleStatsResponse(
        rule_id=rule_id,
        total_detections=0,
        false_positive_rate=0.0,
        fix_rate=0.0,
        suppression_rate=0.0,
        avg_time_to_fix_minutes=None,
    )
