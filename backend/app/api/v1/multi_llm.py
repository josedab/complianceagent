"""API endpoints for Multi-LLM Regulatory Parsing Engine."""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep
from app.services.multi_llm import (
    ConsensusStrategy,
    EscalationStatus,
    LLMProvider,
    MultiLLMService,
    ProviderConfig,
)


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---


class ParseRequest(BaseModel):
    """Request to parse regulatory text."""

    text: str = Field(..., min_length=10, description="Regulatory text to parse")
    framework: str = Field(default="", description="Regulatory framework hint")
    strategy: str | None = Field(default=None, description="Consensus strategy override")


class ProviderResultSchema(BaseModel):
    """Single provider result."""

    provider: str
    model_name: str
    obligations: list[dict[str, Any]]
    entities: list[str]
    confidence: float
    latency_ms: float
    error: str | None


class ConsensusResultSchema(BaseModel):
    """Consensus result response."""

    id: str
    status: str
    strategy: str
    provider_results: list[ProviderResultSchema]
    obligations: list[dict[str, Any]]
    entities: list[str]
    confidence: float
    agreement_score: float
    needs_human_review: bool
    total_latency_ms: float


class AddProviderRequest(BaseModel):
    """Request to add an LLM provider."""

    provider: str = Field(..., description="Provider name")
    model_name: str = Field(..., description="Model name")
    api_key: str = Field(default="", description="API key")
    base_url: str = Field(default="")
    max_tokens: int = Field(default=4096)
    temperature: float = Field(default=0.1)
    weight: float = Field(default=1.0)


class ProviderInfoSchema(BaseModel):
    """Provider info response."""

    provider: str
    model_name: str
    enabled: bool
    weight: float


class ConfigResponse(BaseModel):
    """Multi-LLM config response."""

    providers: list[ProviderInfoSchema]
    consensus_strategy: str
    min_providers: int
    divergence_threshold: float
    fallback_to_single: bool


# --- Endpoints ---


@router.post(
    "/parse",
    response_model=ConsensusResultSchema,
    summary="Parse regulatory text",
    description="Parse regulatory text using multiple LLMs with consensus",
)
async def parse_regulation(
    request: ParseRequest,
    db: DB,
    copilot: CopilotDep,
) -> ConsensusResultSchema:
    """Parse regulatory text with multi-LLM consensus."""
    service = MultiLLMService(db=db, copilot_client=copilot)
    strategy = ConsensusStrategy(request.strategy) if request.strategy else None

    result = await service.parse_regulation(
        text=request.text, framework=request.framework, strategy=strategy,
    )

    return ConsensusResultSchema(
        id=str(result.id),
        status=result.status.value,
        strategy=result.strategy.value,
        provider_results=[
            ProviderResultSchema(
                provider=pr.provider.value, model_name=pr.model_name,
                obligations=pr.obligations, entities=pr.entities,
                confidence=pr.confidence, latency_ms=pr.latency_ms,
                error=pr.error,
            )
            for pr in result.provider_results
        ],
        obligations=result.obligations,
        entities=result.entities,
        confidence=result.confidence,
        agreement_score=result.agreement_score,
        needs_human_review=result.needs_human_review,
        total_latency_ms=result.total_latency_ms,
    )


@router.get(
    "/providers",
    response_model=list[ProviderInfoSchema],
    summary="List LLM providers",
)
async def list_providers(db: DB, copilot: CopilotDep) -> list[ProviderInfoSchema]:
    """List configured LLM providers."""
    service = MultiLLMService(db=db, copilot_client=copilot)
    providers = await service.list_providers()
    return [
        ProviderInfoSchema(
            provider=p.provider.value, model_name=p.model_name,
            enabled=p.enabled, weight=p.weight,
        )
        for p in providers
    ]


@router.post(
    "/providers",
    response_model=ProviderInfoSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Add LLM provider",
)
async def add_provider(
    request: AddProviderRequest,
    db: DB,
    copilot: CopilotDep,
) -> ProviderInfoSchema:
    """Add a new LLM provider."""
    service = MultiLLMService(db=db, copilot_client=copilot)
    config = ProviderConfig(
        provider=LLMProvider(request.provider),
        model_name=request.model_name,
        api_key=request.api_key,
        base_url=request.base_url,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        weight=request.weight,
    )
    result = await service.add_provider(config)
    return ProviderInfoSchema(
        provider=result.provider.value, model_name=result.model_name,
        enabled=result.enabled, weight=result.weight,
    )


@router.delete(
    "/providers/{provider_name}",
    summary="Remove LLM provider",
)
async def remove_provider(
    provider_name: str,
    db: DB,
    copilot: CopilotDep,
) -> dict:
    """Remove an LLM provider."""
    service = MultiLLMService(db=db, copilot_client=copilot)
    removed = await service.remove_provider(LLMProvider(provider_name))
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    return {"status": "removed", "provider": provider_name}


@router.get(
    "/config",
    response_model=ConfigResponse,
    summary="Get multi-LLM configuration",
)
async def get_config(db: DB, copilot: CopilotDep) -> ConfigResponse:
    """Get current multi-LLM configuration."""
    service = MultiLLMService(db=db, copilot_client=copilot)
    config = await service.get_config()
    return ConfigResponse(
        providers=[
            ProviderInfoSchema(
                provider=p.provider.value, model_name=p.model_name,
                enabled=p.enabled, weight=p.weight,
            )
            for p in config.providers
        ],
        consensus_strategy=config.consensus_strategy.value,
        min_providers=config.min_providers,
        divergence_threshold=config.divergence_threshold,
        fallback_to_single=config.fallback_to_single,
    )


class ProviderHealthSchema(BaseModel):
    """Provider health metrics response."""

    provider: str
    model_name: str
    status: str
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    success_rate: float
    total_requests: int
    failed_requests: int
    last_error: str | None
    cost_per_1k_tokens: float
    total_tokens_used: int
    estimated_monthly_cost: float


class CostRecommendationSchema(BaseModel):
    """Cost optimization recommendation response."""

    id: str
    title: str
    description: str
    estimated_savings_monthly: float
    effort: str
    current_cost: float
    optimized_cost: float


@router.get(
    "/providers/health",
    response_model=list[ProviderHealthSchema],
    summary="Get provider health metrics",
)
async def get_provider_health(db: DB, copilot: CopilotDep) -> list[ProviderHealthSchema]:
    """Get health and latency metrics for all LLM providers."""
    service = MultiLLMService(db=db, copilot_client=copilot)
    metrics = await service.get_provider_health()
    return [
        ProviderHealthSchema(
            provider=m.provider.value, model_name=m.model_name,
            status=m.status, avg_latency_ms=round(m.avg_latency_ms, 1),
            p95_latency_ms=round(m.p95_latency_ms, 1),
            p99_latency_ms=round(m.p99_latency_ms, 1),
            success_rate=round(m.success_rate, 4),
            total_requests=m.total_requests,
            failed_requests=m.failed_requests,
            last_error=m.last_error,
            cost_per_1k_tokens=m.cost_per_1k_tokens,
            total_tokens_used=m.total_tokens_used,
            estimated_monthly_cost=round(m.estimated_monthly_cost, 2),
        )
        for m in metrics
    ]


@router.get(
    "/cost-recommendations",
    response_model=list[CostRecommendationSchema],
    summary="Get cost optimization recommendations",
)
async def get_cost_recommendations(db: DB, copilot: CopilotDep) -> list[CostRecommendationSchema]:
    """Get cost optimization recommendations for LLM usage."""
    service = MultiLLMService(db=db, copilot_client=copilot)
    recs = await service.get_cost_recommendations()
    return [
        CostRecommendationSchema(
            id=str(r.id), title=r.title, description=r.description,
            estimated_savings_monthly=round(r.estimated_savings_monthly, 2),
            effort=r.effort, current_cost=round(r.current_cost, 2),
            optimized_cost=round(r.optimized_cost, 2),
        )
        for r in recs
    ]


# --- Divergence Detection Schemas ---


class DivergenceDetailSchema(BaseModel):
    """Single divergence detail response."""

    id: str
    obligation_text: str
    providers_agree: list[str]
    providers_disagree: list[str]
    agreement_ratio: float
    divergence_type: str
    recommended_action: str
    auto_escalated: bool


class DivergenceReportSchema(BaseModel):
    """Divergence analysis report response."""

    consensus_id: str
    total_obligations: int
    agreed_count: int
    diverged_count: int
    divergence_rate: float
    divergences: list[DivergenceDetailSchema]
    needs_human_review: bool
    severity: str


class ProviderHealthDashboardSchema(BaseModel):
    """Provider health dashboard metrics response."""

    provider: str
    model_name: str
    enabled: bool
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    avg_latency_ms: float
    p95_latency_ms: float
    total_tokens_used: int
    estimated_cost_usd: float
    last_error: str | None
    last_used: str | None
    uptime_percentage: float


@router.get(
    "/divergence/{consensus_id}",
    response_model=DivergenceReportSchema,
    summary="Analyze semantic divergence",
)
async def analyze_divergence(
    consensus_id: str,
    db: DB,
    copilot: CopilotDep,
) -> DivergenceReportSchema:
    """Analyze semantic divergence in consensus results."""
    service = MultiLLMService(db=db, copilot_client=copilot)
    report = service.analyze_divergence(consensus_id)
    return DivergenceReportSchema(**report.to_dict())


@router.get(
    "/provider-health",
    response_model=list[ProviderHealthDashboardSchema],
    summary="Get provider health dashboard",
)
async def get_provider_health_dashboard(
    db: DB,
    copilot: CopilotDep,
) -> list[ProviderHealthDashboardSchema]:
    """Get health dashboard metrics for all LLM providers."""
    service = MultiLLMService(db=db, copilot_client=copilot)
    metrics = service.get_provider_health_dashboard()
    return [ProviderHealthDashboardSchema(**m) for m in metrics]


# --- Escalation & Failover Schemas ---


class EscalateRequest(BaseModel):
    """Request to escalate a consensus result for human review."""

    reason: str = Field(default="", description="Reason for escalation")


class EscalationTicketSchema(BaseModel):
    """Escalation ticket response."""

    id: str
    consensus_id: str
    regulation_text: str
    provider_interpretations: list[dict[str, Any]]
    agreement_score: float
    confidence_score: float
    divergence_summary: str
    priority: str
    status: str
    assigned_to: str | None
    resolution: str | None
    resolved_obligations: list[dict[str, Any]]
    created_at: str
    resolved_at: str | None


class ResolveEscalationRequest(BaseModel):
    """Request to resolve an escalation ticket."""

    resolution: str = Field(..., min_length=1, description="Human resolution description")
    resolved_obligations: list[dict[str, Any]] = Field(..., description="Verified obligations")
    resolved_by: str = Field(..., min_length=1, description="Reviewer identifier")


class FailoverEventSchema(BaseModel):
    """Failover event response."""

    id: str
    failed_provider: str
    failover_provider: str
    reason: str
    request_id: str
    latency_ms: float
    occurred_at: str


def _ticket_to_schema(ticket) -> EscalationTicketSchema:
    """Convert an EscalationTicket dataclass to its API schema."""
    return EscalationTicketSchema(
        id=str(ticket.id),
        consensus_id=str(ticket.consensus_id),
        regulation_text=ticket.regulation_text,
        provider_interpretations=ticket.provider_interpretations,
        agreement_score=round(ticket.agreement_score, 4),
        confidence_score=round(ticket.confidence_score, 4),
        divergence_summary=ticket.divergence_summary,
        priority=ticket.priority.value,
        status=ticket.status.value,
        assigned_to=ticket.assigned_to,
        resolution=ticket.resolution,
        resolved_obligations=ticket.resolved_obligations,
        created_at=ticket.created_at.isoformat(),
        resolved_at=ticket.resolved_at.isoformat() if ticket.resolved_at else None,
    )


# --- Escalation & Failover Endpoints ---


@router.post(
    "/escalate/{consensus_id}",
    response_model=EscalationTicketSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Escalate consensus for human review",
    description="Create an escalation ticket for a low-confidence consensus result",
)
async def escalate_for_review(
    consensus_id: str,
    request: EscalateRequest,
    db: DB,
    copilot: CopilotDep,
) -> EscalationTicketSchema:
    """Create an escalation ticket for human review."""
    from uuid import UUID as _UUID

    service = MultiLLMService(db=db, copilot_client=copilot)
    try:
        ticket = await service.escalate_for_review(
            consensus_id=_UUID(consensus_id), reason=request.reason,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return _ticket_to_schema(ticket)


@router.get(
    "/escalations",
    response_model=list[EscalationTicketSchema],
    summary="List escalation tickets",
    description="List human review escalation tickets with optional status filter",
)
async def list_escalations(
    db: DB,
    copilot: CopilotDep,
    escalation_status: str | None = None,
) -> list[EscalationTicketSchema]:
    """List escalation tickets, optionally filtered by status."""
    service = MultiLLMService(db=db, copilot_client=copilot)
    filter_status = EscalationStatus(escalation_status) if escalation_status else None
    tickets = await service.list_escalations(status=filter_status)
    return [_ticket_to_schema(t) for t in tickets]


@router.post(
    "/escalations/{ticket_id}/resolve",
    response_model=EscalationTicketSchema,
    summary="Resolve an escalation ticket",
    description="Resolve an escalation ticket with human-provided interpretation",
)
async def resolve_escalation(
    ticket_id: str,
    request: ResolveEscalationRequest,
    db: DB,
    copilot: CopilotDep,
) -> EscalationTicketSchema:
    """Resolve an escalation ticket with human-verified interpretation."""
    from uuid import UUID as _UUID

    service = MultiLLMService(db=db, copilot_client=copilot)
    try:
        ticket = await service.resolve_escalation(
            ticket_id=_UUID(ticket_id),
            resolution=request.resolution,
            resolved_obligations=request.resolved_obligations,
            resolved_by=request.resolved_by,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return _ticket_to_schema(ticket)


@router.get(
    "/failover-history",
    response_model=list[FailoverEventSchema],
    summary="Get provider failover history",
    description="Get recent provider failover events",
)
async def get_failover_history(
    db: DB,
    copilot: CopilotDep,
    limit: int = 50,
) -> list[FailoverEventSchema]:
    """Get recent provider failover events."""
    service = MultiLLMService(db=db, copilot_client=copilot)
    events = await service.get_failover_history(limit=limit)
    return [
        FailoverEventSchema(
            id=str(e.id),
            failed_provider=e.failed_provider,
            failover_provider=e.failover_provider,
            reason=e.reason,
            request_id=str(e.request_id),
            latency_ms=round(e.latency_ms, 2),
            occurred_at=e.occurred_at.isoformat(),
        )
        for e in events
    ]
