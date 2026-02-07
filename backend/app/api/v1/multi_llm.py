"""API endpoints for Multi-LLM Regulatory Parsing Engine."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep

from app.services.multi_llm import (
    ConsensusStrategy,
    LLMProvider,
    MultiLLMConfig,
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
