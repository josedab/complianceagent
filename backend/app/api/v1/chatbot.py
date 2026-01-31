"""Chatbot API endpoints."""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.api.v1.deps import DB, CurrentOrganization, OrgMember


router = APIRouter()


class ChatSessionResponse(BaseModel):
    """Chat session response."""

    id: str
    created_at: datetime


class ChatRequest(BaseModel):
    """Chat message request."""

    message: str
    codebase_context: dict[str, Any] | None = None


class ChatResponse(BaseModel):
    """Chat message response."""

    id: str
    role: str
    content: str
    timestamp: datetime


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    context: dict[str, Any] | None = None,
) -> ChatSessionResponse:
    """Create a new chat session."""
    from app.services.chatbot import get_compliance_chatbot

    chatbot = get_compliance_chatbot()
    session = chatbot.create_session(
        organization_id=str(organization.id),
        user_id=str(member.user_id),
        context=context,
    )

    return ChatSessionResponse(
        id=str(session.id),
        created_at=session.created_at,
    )


@router.post("/sessions/{session_id}/messages", response_model=ChatResponse)
async def send_chat_message(
    session_id: str,
    request: ChatRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> ChatResponse:
    """Send a message in a chat session."""
    from app.services.chatbot import get_compliance_chatbot

    chatbot = get_compliance_chatbot()

    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID",
        )

    try:
        response = await chatbot.chat(
            session_id=session_uuid,
            message=request.message,
            codebase_context=request.codebase_context,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return ChatResponse(
        id=str(response.id),
        role=response.role,
        content=response.content,
        timestamp=response.timestamp,
    )


@router.post("/quick")
async def quick_chat(
    question: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    regulations: list[str] | None = Query(default=None),
) -> dict[str, Any]:
    """Get a quick answer without a full session."""
    from app.services.chatbot import get_compliance_chatbot

    chatbot = get_compliance_chatbot()
    return await chatbot.get_quick_answer(question, regulations)


@router.post("/explain-issue")
async def explain_code_issue(
    code_snippet: str,
    issue_code: str,
    issue_message: str,
    language: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Explain a compliance issue in code."""
    from app.services.chatbot import get_compliance_chatbot

    chatbot = get_compliance_chatbot()
    return await chatbot.explain_code_issue(
        code_snippet=code_snippet,
        issue_code=issue_code,
        issue_message=issue_message,
        language=language,
    )
