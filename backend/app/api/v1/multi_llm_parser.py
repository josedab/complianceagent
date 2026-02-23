"""API endpoints for Multi-LLM Legal Text Parser."""

import structlog
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.multi_llm_parser import MultiLLMParserService


logger = structlog.get_logger()
router = APIRouter()


# --- Request / Response Schemas ---


class ParseRequest(BaseModel):
    text: str = Field(..., description="Legal text to parse")
    strategy: str = Field("consensus", description="Parsing strategy to use")
    providers: list[str] = Field(default_factory=list, description="LLM providers to use")


class ToggleProviderRequest(BaseModel):
    enabled: bool = Field(..., description="Whether the provider should be enabled")


# --- Endpoints ---


@router.post("/parse")
async def parse_legal_text(request: ParseRequest, db: DB) -> dict:
    """Parse legal text using multiple LLM providers."""
    svc = MultiLLMParserService()
    return await svc.parse_legal_text(
        db,
        text=request.text,
        strategy=request.strategy,
        providers=request.providers,
    )


@router.get("/providers")
async def list_providers(db: DB) -> list[dict]:
    """List available LLM providers."""
    svc = MultiLLMParserService()
    return await svc.list_providers(db)


@router.put("/providers/{provider}/toggle")
async def toggle_provider(
    provider: str, request: ToggleProviderRequest, db: DB,
) -> dict:
    """Enable or disable an LLM provider."""
    svc = MultiLLMParserService()
    return await svc.toggle_provider(db, provider=provider, enabled=request.enabled)


@router.get("/stats")
async def get_stats(db: DB) -> dict:
    """Get multi-LLM parser statistics."""
    svc = MultiLLMParserService()
    return await svc.get_stats(db)
