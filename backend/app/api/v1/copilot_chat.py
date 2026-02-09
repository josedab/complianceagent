"""API endpoints for Compliance Copilot Chat (Non-Technical Users)."""

from collections.abc import AsyncIterator

import structlog
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep
from app.services.copilot_chat import (
    CopilotChatService,
    UserPersona,
)


logger = structlog.get_logger()
router = APIRouter()


# --- Request Models ---


class AskRequest(BaseModel):
    question: str = Field(
        ..., min_length=1, max_length=2000, description="Compliance question in natural language"
    )
    persona: str = Field(
        ..., description="User persona (cco, auditor, legal, developer, executive)"
    )
    regulations: list[str] | None = Field(
        default=None, description="Regulations to scope the answer to"
    )


class FindLocationsRequest(BaseModel):
    regulation: str = Field(..., description="Regulation framework (e.g., GDPR, HIPAA)")
    article: str = Field(default="", description="Specific article or requirement")


# --- Response Models ---


class CannedQuerySchema(BaseModel):
    id: str
    persona: str
    category: str
    label: str
    query: str
    icon: str
    description: str


class PersonaViewSchema(BaseModel):
    persona: str
    display_name: str
    description: str
    default_regulations: list[str]
    dashboard_widgets: list[str]
    allowed_actions: list[str]


class SimplifiedResponseSchema(BaseModel):
    id: str
    question: str
    answer: str
    confidence: float
    citations: list[str]
    suggested_followups: list[str]
    visual_type: str
    persona: str


class ComplianceLocationSchema(BaseModel):
    file_path: str
    function_name: str
    regulation: str
    article: str
    compliance_status: str
    explanation: str


# --- Helpers ---


def _parse_persona(value: str) -> UserPersona:
    """Parse and validate a persona string."""
    try:
        return UserPersona(value.lower())
    except ValueError as err:
        valid = [p.value for p in UserPersona]
        raise HTTPException(
            status_code=400, detail=f"Invalid persona '{value}'. Valid: {valid}"
        ) from err


# --- Endpoints ---


@router.post(
    "/ask",
    response_model=SimplifiedResponseSchema,
    summary="Ask a simplified compliance question",
    description="Ask a compliance question tailored to your persona with simplified, actionable answers",
)
async def ask_question(
    request: AskRequest, db: DB, copilot: CopilotDep
) -> SimplifiedResponseSchema:
    persona = _parse_persona(request.persona)
    service = CopilotChatService(db=db, copilot_client=copilot)
    result = await service.ask_simplified(
        question=request.question,
        persona=persona,
        org_id="default",
        regulations=request.regulations,
    )
    return SimplifiedResponseSchema(
        id=str(result.id),
        question=result.question,
        answer=result.answer,
        confidence=result.confidence,
        citations=result.citations,
        suggested_followups=result.suggested_followups,
        visual_type=result.visual_type.value,
        persona=result.persona.value,
    )


@router.get(
    "/canned-queries",
    response_model=list[CannedQuerySchema],
    summary="Get canned queries for a persona",
    description="Retrieve pre-built compliance queries tailored to a specific user persona",
)
async def get_canned_queries(
    persona: str,
    db: DB,
    copilot: CopilotDep,
    category: str | None = None,
) -> list[CannedQuerySchema]:
    p = _parse_persona(persona)
    service = CopilotChatService(db=db, copilot_client=copilot)
    queries = await service.get_canned_queries(persona=p, category=category)
    return [
        CannedQuerySchema(
            id=q.id,
            persona=q.persona.value,
            category=q.category,
            label=q.label,
            query=q.query,
            icon=q.icon,
            description=q.description,
        )
        for q in queries
    ]


@router.get(
    "/personas",
    response_model=list[PersonaViewSchema],
    summary="List available persona views",
    description="Get all available persona view configurations for the compliance chat",
)
async def list_personas() -> list[PersonaViewSchema]:
    from app.services.copilot_chat.service import _PERSONA_VIEWS

    return [
        PersonaViewSchema(
            persona=v.persona.value,
            display_name=v.display_name,
            description=v.description,
            default_regulations=v.default_regulations,
            dashboard_widgets=v.dashboard_widgets,
            allowed_actions=v.allowed_actions,
        )
        for v in _PERSONA_VIEWS.values()
    ]


@router.get(
    "/persona/{persona}",
    response_model=PersonaViewSchema,
    summary="Get specific persona view config",
    description="Retrieve the view configuration for a specific user persona",
)
async def get_persona_view(persona: str) -> PersonaViewSchema:
    p = _parse_persona(persona)

    from app.services.copilot_chat.service import _PERSONA_VIEWS

    view = _PERSONA_VIEWS.get(p)
    if not view:
        raise HTTPException(status_code=404, detail=f"Persona '{persona}' not found")
    return PersonaViewSchema(
        persona=view.persona.value,
        display_name=view.display_name,
        description=view.description,
        default_regulations=view.default_regulations,
        dashboard_widgets=view.dashboard_widgets,
        allowed_actions=view.allowed_actions,
    )


@router.post(
    "/find-locations",
    response_model=list[ComplianceLocationSchema],
    summary="Find code locations for a regulation",
    description="Locate code sections that implement or relate to a specific compliance requirement",
)
async def find_code_locations(
    request: FindLocationsRequest,
    db: DB,
    copilot: CopilotDep,
) -> list[ComplianceLocationSchema]:
    service = CopilotChatService(db=db, copilot_client=copilot)
    locations = await service.find_code_locations(
        regulation=request.regulation,
        article=request.article,
        org_id="default",
    )
    return [
        ComplianceLocationSchema(
            file_path=loc.file_path,
            function_name=loc.function_name,
            regulation=loc.regulation,
            article=loc.article,
            compliance_status=loc.compliance_status,
            explanation=loc.explanation,
        )
        for loc in locations
    ]


@router.get(
    "/executive-summary",
    response_model=SimplifiedResponseSchema,
    summary="Get executive compliance summary",
    description="Generate a high-level executive summary of the organization's compliance posture",
)
async def get_executive_summary(
    db: DB,
    copilot: CopilotDep,
    regulations: str | None = None,
) -> SimplifiedResponseSchema:
    service = CopilotChatService(db=db, copilot_client=copilot)
    reg_list = regulations.split(",") if regulations else None
    result = await service.get_executive_summary(org_id="default", regulations=reg_list)
    return SimplifiedResponseSchema(
        id=str(result.id),
        question=result.question,
        answer=result.answer,
        confidence=result.confidence,
        citations=result.citations,
        suggested_followups=result.suggested_followups,
        visual_type=result.visual_type.value,
        persona=result.persona.value,
    )


@router.post(
    "/ask/stream",
    summary="Ask a compliance question (streaming)",
    description="Streaming version of the ask endpoint for real-time responses",
)
async def ask_question_stream(
    request: AskRequest, db: DB, copilot: CopilotDep
) -> StreamingResponse:
    persona = _parse_persona(request.persona)
    service = CopilotChatService(db=db, copilot_client=copilot)

    async def generate() -> AsyncIterator[str]:
        result = await service.ask_simplified(
            question=request.question,
            persona=persona,
            org_id="default",
            regulations=request.regulations,
        )
        # Stream the answer in chunks
        chunk_size = 80
        for i in range(0, len(result.answer), chunk_size):
            yield result.answer[i : i + chunk_size]

    return StreamingResponse(generate(), media_type="text/plain")
