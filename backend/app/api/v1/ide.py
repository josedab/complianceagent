"""IDE integration API endpoints for real-time compliance analysis."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CurrentOrganization, OrgMember
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


def get_analyzer(organization_id: UUID, regulations: list[str] | None = None) -> IDEComplianceAnalyzer:
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
        diagnostics.append(DiagnosticResponse(
            range={
                "start": {"line": diag.range.start.line, "character": diag.range.start.character},
                "end": {"line": diag.range.end.line, "character": diag.range.end.character},
            },
            message=diag.message,
            severity=diag.severity.value,
            code=diag.code,
            source=diag.source,
            category=diag.category.value if diag.category else None,
            regulation=diag.regulation,
            article_reference=diag.article_reference,
        ))

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
        supported_languages=["python", "javascript", "typescript", "java", "go", "ruby", "php", "csharp"],
    )


@router.put("/config")
async def update_ide_config(
    regulations: list[str] | None = None,
    severity_threshold: str | None = None,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> IDEConfigResponse:
    """Update IDE integration configuration."""
    # Create new analyzer with updated config
    new_analyzer = IDEComplianceAnalyzer(
        enabled_regulations=regulations or ["GDPR", "CCPA", "HIPAA", "EU AI Act"],
        severity_threshold=DiagnosticSeverity(severity_threshold) if severity_threshold else DiagnosticSeverity.HINT,
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
        supported_languages=["python", "javascript", "typescript", "java", "go", "ruby", "php", "csharp"],
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
        try:
            category = DiagnosticCategory(request.category)
        except ValueError:
            pass

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
        try:
            category = DiagnosticCategory(request.category)
        except ValueError:
            pass

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
        issues.append(DeepAnalysisIssue(
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
        ))

    return DeepAnalysisResponse(
        issues=issues,
        analyzed_at=datetime.now(UTC),
    )


# WebSocket endpoint for real-time analysis
@router.websocket("/ws")
async def ide_websocket(
    websocket: WebSocket,
    db: DB,
):
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

                await websocket.send_json({
                    "type": "diagnostics",
                    "uri": result.uri,
                    "version": result.version,
                    "diagnostics": diagnostics,
                    "analysisTimeMs": result.analysis_time_ms,
                })

            elif action == "hover":
                hover_info = analyzer.get_hover_info(
                    uri=data.get("uri", ""),
                    content=data.get("content", ""),
                    line=data.get("line", 0),
                    character=data.get("character", 0),
                )

                await websocket.send_json({
                    "type": "hover",
                    "info": hover_info,
                })

            elif action == "setRegulations":
                analyzer = IDEComplianceAnalyzer(
                    enabled_regulations=data.get("regulations", []),
                )
                await websocket.send_json({
                    "type": "configUpdated",
                    "regulations": analyzer.enabled_regulations,
                })

            elif action == "deepAnalyze":
                suggester = get_copilot_suggester()
                suggestions = await suggester.analyze_code_block(
                    code=data.get("content", ""),
                    language=data.get("language", "python"),
                    regulations=data.get("regulations"),
                )

                issues = []
                for s in suggestions:
                    issues.append({
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
                    })

                await websocket.send_json({
                    "type": "deepAnalysis",
                    "issues": issues,
                })

    except WebSocketDisconnect:
        pass


# ============================================================================
# Team Suppressions Endpoints (New)
# ============================================================================


class TeamSuppressionRequest(BaseModel):
    """Request to create a team suppression."""
    
    rule_id: str
    pattern: str | None = None
    reason: str
    expires_at: datetime | None = None


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
    
    type: str  # false_positive, false_negative, severity_adjustment, helpful
    issue: dict[str, Any]
    reason: str | None = None


@router.get("/suppressions", response_model=list[TeamSuppressionResponse])
async def get_team_suppressions(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> list[TeamSuppressionResponse]:
    """Get team-wide suppressions for the organization."""
    # In a real implementation, this would fetch from database
    # For now, return empty list as placeholder
    return []


@router.post("/suppressions", response_model=TeamSuppressionResponse)
async def request_team_suppression(
    request: TeamSuppressionRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> TeamSuppressionResponse:
    """Request a new team-wide suppression.
    
    Suppressions require approval from an admin before taking effect.
    """
    # In a real implementation, this would save to database
    # and notify admins for approval
    from uuid import uuid4
    
    return TeamSuppressionResponse(
        id=str(uuid4()),
        rule_id=request.rule_id,
        pattern=request.pattern,
        reason=request.reason,
        created_by=str(member.user_id),
        created_at=datetime.now(UTC),
        expires_at=request.expires_at,
        approved=False,  # Requires admin approval
        approved_by=None,
        usage_count=0,
    )


@router.put("/suppressions/{suppression_id}/approve")
async def approve_team_suppression(
    suppression_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> TeamSuppressionResponse:
    """Approve a team suppression (admin only)."""
    # In a real implementation, this would update the database
    # and require admin role check
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Suppression not found",
    )


@router.delete("/suppressions/{suppression_id}")
async def delete_team_suppression(
    suppression_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, str]:
    """Delete a team suppression."""
    # In a real implementation, this would delete from database
    return {"status": "deleted"}


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
    
    # Log feedback for analysis
    logger.info(
        "IDE feedback received",
        organization_id=str(organization.id),
        user_id=str(member.user_id),
        feedback_type=request.type,
        rule_id=request.issue.get("requirementId"),
        reason=request.reason,
    )
    
    # In a real implementation, this would:
    # 1. Store feedback in database
    # 2. Aggregate for ML model training
    # 3. Auto-create suppressions if high false positive rate
    
    return {"status": "received", "message": "Thank you for your feedback!"}


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


@router.get("/stats/rules", response_model=list[RuleStatsResponse])
async def get_rule_statistics(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> list[RuleStatsResponse]:
    """Get aggregated statistics for compliance rules.
    
    Useful for understanding which rules are most effective
    and which may need tuning.
    """
    # In a real implementation, this would aggregate from database
    # For now, return sample data
    return [
        RuleStatsResponse(
            rule_id="GDPR-PII-001",
            total_detections=145,
            false_positive_rate=0.12,
            fix_rate=0.78,
            suppression_rate=0.10,
            avg_time_to_fix_minutes=15.5,
        ),
        RuleStatsResponse(
            rule_id="SOC2-CRED-001",
            total_detections=89,
            false_positive_rate=0.05,
            fix_rate=0.92,
            suppression_rate=0.03,
            avg_time_to_fix_minutes=5.2,
        ),
        RuleStatsResponse(
            rule_id="HIPAA-PHI-001",
            total_detections=67,
            false_positive_rate=0.18,
            fix_rate=0.65,
            suppression_rate=0.17,
            avg_time_to_fix_minutes=25.8,
        ),
    ]


@router.get("/stats/rules/{rule_id}", response_model=RuleStatsResponse)
async def get_rule_stats(
    rule_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> RuleStatsResponse:
    """Get statistics for a specific rule."""
    # In a real implementation, this would fetch from database
    return RuleStatsResponse(
        rule_id=rule_id,
        total_detections=0,
        false_positive_rate=0.0,
        fix_rate=0.0,
        suppression_rate=0.0,
        avg_time_to_fix_minutes=None,
    )
