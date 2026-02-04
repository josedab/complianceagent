"""API endpoints for AI Explainability Layer (XAI Compliance)."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CurrentOrganization, OrgMember
from app.services.explainability import (
    ExplainabilityEngine,
    ExplanationConfidence,
    ExplanationFormat,
    get_explainability_engine,
)
from app.services.explainability.models import ExplanationRequest


router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================


class ExplainDecisionRequest(BaseModel):
    """Request to explain a compliance decision."""
    
    violation_type: str = Field(
        description="Type of violation (PII_LOGGING, MISSING_CONSENT, etc.)"
    )
    code_snippet: str | None = Field(
        default=None,
        description="Code snippet being analyzed"
    )
    file_path: str | None = Field(
        default=None,
        description="Path to the file"
    )
    regulation: str | None = Field(
        default=None,
        description="Primary regulation (GDPR, HIPAA, etc.)"
    )
    message: str | None = Field(
        default=None,
        description="Original diagnostic message"
    )
    format: str = Field(
        default="natural_language",
        description="Output format: natural_language, structured, legal, technical, executive"
    )
    detail_level: str = Field(
        default="standard",
        description="Detail level: minimal, standard, detailed, exhaustive"
    )
    include_citations: bool = Field(
        default=True,
        description="Include regulatory citations"
    )
    additional_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context for the explanation"
    )


class CitationResponse(BaseModel):
    """Regulatory citation in response."""
    
    regulation: str
    article: str
    section: str | None = None
    text_excerpt: str
    relevance_score: float
    url: str | None = None


class ReasoningStepResponse(BaseModel):
    """Single reasoning step in response."""
    
    step_number: int
    description: str
    evidence: str | None = None
    confidence: float
    citations: list[CitationResponse] = Field(default_factory=list)


class ExplanationResponse(BaseModel):
    """Complete explanation response."""
    
    id: str
    decision: str
    decision_type: str
    summary: str
    reasoning_chain: list[ReasoningStepResponse]
    primary_citations: list[CitationResponse]
    supporting_citations: list[CitationResponse]
    confidence: str
    confidence_score: float
    alternative_interpretations: list[str]
    assumptions: list[str]
    limitations: list[str]
    formatted_output: str
    processing_time_ms: float
    created_at: datetime


class AuditLogResponse(BaseModel):
    """Audit log entry response."""
    
    id: str
    organization_id: str
    user_id: str | None
    timestamp: datetime
    action_type: str
    input_summary: str
    result_summary: str
    decision: str
    confidence: str
    approval_status: str | None
    chain_hash: str | None


class AuditVerificationResponse(BaseModel):
    """Response from audit chain verification."""
    
    valid: bool
    verified_count: int
    failed_at: str | None = None
    message: str
    verified_at: datetime


class FairnessMetricsResponse(BaseModel):
    """Fairness metrics response."""
    
    explanation_id: str
    consistency_score: float
    bias_indicators: list[dict[str, Any]]
    evaluated_at: datetime


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/explain", response_model=ExplanationResponse)
async def explain_decision(
    request: ExplainDecisionRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> ExplanationResponse:
    """Generate an explainable, audit-proof explanation for a compliance decision.
    
    This endpoint provides transparent reasoning for AI compliance decisions,
    including:
    - Step-by-step reasoning chain
    - Regulatory citations with relevance scores
    - Confidence assessment
    - Alternative interpretations
    - Assumptions and limitations
    
    The explanation is formatted according to the requested format and stored
    in an immutable audit log for compliance verification.
    """
    engine = get_explainability_engine()
    
    try:
        format_enum = ExplanationFormat(request.format)
    except ValueError:
        format_enum = ExplanationFormat.NATURAL_LANGUAGE
    
    # Build decision context
    decision_context = {
        "violation_type": request.violation_type,
        "message": request.message,
        "decision_type": "violation",
        **request.additional_context,
    }
    
    explanation_request = ExplanationRequest(
        decision_context=decision_context,
        code_snippet=request.code_snippet,
        file_path=request.file_path,
        regulation=request.regulation,
        format=format_enum,
        detail_level=request.detail_level,
        include_citations=request.include_citations,
    )
    
    result = await engine.explain_decision(
        request=explanation_request,
        organization_id=organization.id,
        user_id=member.user_id,
    )
    
    explanation = result.explanation
    
    # Convert to response models
    def citation_to_response(c) -> CitationResponse:
        return CitationResponse(
            regulation=c.regulation,
            article=c.article,
            section=c.section,
            text_excerpt=c.text_excerpt,
            relevance_score=c.relevance_score,
            url=c.url,
        )
    
    def step_to_response(s) -> ReasoningStepResponse:
        return ReasoningStepResponse(
            step_number=s.step_number,
            description=s.description,
            evidence=s.evidence,
            confidence=s.confidence,
            citations=[citation_to_response(c) for c in s.citations],
        )
    
    return ExplanationResponse(
        id=str(explanation.id),
        decision=explanation.decision,
        decision_type=explanation.decision_type,
        summary=explanation.summary,
        reasoning_chain=[step_to_response(s) for s in explanation.reasoning_chain],
        primary_citations=[citation_to_response(c) for c in explanation.primary_citations],
        supporting_citations=[citation_to_response(c) for c in explanation.supporting_citations],
        confidence=explanation.confidence.value,
        confidence_score=explanation.confidence_score,
        alternative_interpretations=explanation.alternative_interpretations,
        assumptions=explanation.assumptions,
        limitations=explanation.limitations,
        formatted_output=result.formatted_output,
        processing_time_ms=explanation.processing_time_ms or 0,
        created_at=explanation.created_at,
    )


@router.get("/explanations/{explanation_id}", response_model=ExplanationResponse)
async def get_explanation(
    explanation_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> ExplanationResponse:
    """Retrieve a previously generated explanation by ID."""
    engine = get_explainability_engine()
    
    try:
        exp_uuid = UUID(explanation_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid explanation ID format",
        )
    
    explanation = await engine.get_explanation(exp_uuid)
    if not explanation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Explanation not found",
        )
    
    def citation_to_response(c) -> CitationResponse:
        return CitationResponse(
            regulation=c.regulation,
            article=c.article,
            section=c.section,
            text_excerpt=c.text_excerpt,
            relevance_score=c.relevance_score,
            url=c.url,
        )
    
    def step_to_response(s) -> ReasoningStepResponse:
        return ReasoningStepResponse(
            step_number=s.step_number,
            description=s.description,
            evidence=s.evidence,
            confidence=s.confidence,
            citations=[citation_to_response(c) for c in s.citations],
        )
    
    return ExplanationResponse(
        id=str(explanation.id),
        decision=explanation.decision,
        decision_type=explanation.decision_type,
        summary=explanation.summary,
        reasoning_chain=[step_to_response(s) for s in explanation.reasoning_chain],
        primary_citations=[citation_to_response(c) for c in explanation.primary_citations],
        supporting_citations=[citation_to_response(c) for c in explanation.supporting_citations],
        confidence=explanation.confidence.value,
        confidence_score=explanation.confidence_score,
        alternative_interpretations=explanation.alternative_interpretations,
        assumptions=explanation.assumptions,
        limitations=explanation.limitations,
        formatted_output=explanation.to_natural_language(),
        processing_time_ms=explanation.processing_time_ms or 0,
        created_at=explanation.created_at,
    )


@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def get_audit_logs(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    limit: int = 100,
) -> list[AuditLogResponse]:
    """Get audit logs for AI compliance decisions.
    
    Returns a list of audit log entries for all AI-generated explanations
    in the organization, sorted by most recent first.
    """
    engine = get_explainability_engine()
    
    logs = await engine.get_audit_logs(organization.id, limit=limit)
    
    return [
        AuditLogResponse(
            id=str(log.id),
            organization_id=str(log.organization_id),
            user_id=str(log.user_id) if log.user_id else None,
            timestamp=log.timestamp,
            action_type=log.action_type,
            input_summary=log.input_summary,
            result_summary=log.result_summary,
            decision=log.explanation.decision,
            confidence=log.explanation.confidence.value,
            approval_status=log.approval_status,
            chain_hash=log.chain_hash,
        )
        for log in logs
    ]


@router.get("/audit-logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> AuditLogResponse:
    """Get a specific audit log entry."""
    engine = get_explainability_engine()
    
    try:
        log_uuid = UUID(log_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid log ID format",
        )
    
    log = await engine.get_audit_log(log_uuid)
    if not log or log.organization_id != organization.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found",
        )
    
    return AuditLogResponse(
        id=str(log.id),
        organization_id=str(log.organization_id),
        user_id=str(log.user_id) if log.user_id else None,
        timestamp=log.timestamp,
        action_type=log.action_type,
        input_summary=log.input_summary,
        result_summary=log.result_summary,
        decision=log.explanation.decision,
        confidence=log.explanation.confidence.value,
        approval_status=log.approval_status,
        chain_hash=log.chain_hash,
    )


@router.get("/audit-logs/verify", response_model=AuditVerificationResponse)
async def verify_audit_chain(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> AuditVerificationResponse:
    """Verify the integrity of the audit chain.
    
    Validates that the hash chain for all audit logs is intact,
    ensuring no tampering has occurred. This is essential for
    compliance audits and regulatory inspections.
    """
    engine = get_explainability_engine()
    
    result = await engine.verify_audit_chain(organization.id)
    
    return AuditVerificationResponse(
        valid=result["valid"],
        verified_count=result["verified_count"],
        failed_at=result.get("failed_at"),
        message=result["message"],
        verified_at=datetime.now(UTC),
    )


@router.get("/fairness/{explanation_id}", response_model=FairnessMetricsResponse)
async def get_fairness_metrics(
    explanation_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> FairnessMetricsResponse:
    """Get fairness and bias metrics for an explanation.
    
    Evaluates the explanation for potential biases and provides
    metrics useful for EU AI Act compliance and responsible AI governance.
    """
    engine = get_explainability_engine()
    
    try:
        exp_uuid = UUID(explanation_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid explanation ID format",
        )
    
    try:
        metrics = await engine.evaluate_fairness(exp_uuid)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    
    return FairnessMetricsResponse(
        explanation_id=str(metrics.explanation_id),
        consistency_score=metrics.consistency_score,
        bias_indicators=[
            {
                "bias_type": b.bias_type,
                "description": b.description,
                "severity": b.severity,
                "mitigation": b.mitigation,
                "confidence": b.confidence,
            }
            for b in metrics.bias_indicators
        ],
        evaluated_at=metrics.evaluated_at,
    )


@router.post("/batch-explain")
async def batch_explain(
    requests: list[ExplainDecisionRequest],
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Generate explanations for multiple decisions in batch.
    
    Useful for analyzing multiple compliance findings at once,
    such as after a CI/CD scan or code review.
    """
    engine = get_explainability_engine()
    
    results = []
    errors = []
    
    for i, req in enumerate(requests[:50]):  # Limit to 50 per batch
        try:
            format_enum = ExplanationFormat(req.format)
        except ValueError:
            format_enum = ExplanationFormat.NATURAL_LANGUAGE
        
        decision_context = {
            "violation_type": req.violation_type,
            "message": req.message,
            "decision_type": "violation",
            **req.additional_context,
        }
        
        explanation_request = ExplanationRequest(
            decision_context=decision_context,
            code_snippet=req.code_snippet,
            file_path=req.file_path,
            regulation=req.regulation,
            format=format_enum,
            detail_level=req.detail_level,
            include_citations=req.include_citations,
        )
        
        try:
            result = await engine.explain_decision(
                request=explanation_request,
                organization_id=organization.id,
                user_id=member.user_id,
            )
            results.append({
                "index": i,
                "explanation_id": str(result.explanation.id),
                "decision": result.explanation.decision,
                "confidence": result.explanation.confidence.value,
                "summary": result.explanation.summary,
            })
        except Exception as e:
            errors.append({
                "index": i,
                "error": str(e),
            })
    
    return {
        "total_requested": len(requests),
        "successful": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
    }
