"""Compliance Copilot Chat API endpoints with streaming and RAG support."""

from datetime import datetime
from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CurrentOrganization, CurrentUser, OrgMember
from app.services.chat import get_compliance_assistant, ActionType

logger = structlog.get_logger()

router = APIRouter()


# Request/Response Models
class ChatMessageRequest(BaseModel):
    """Chat message request."""
    
    message: str = Field(..., description="The user's message")
    conversation_id: str | None = Field(None, description="Existing conversation ID to continue")
    
    # Context
    repository: str | None = Field(None, description="Repository context (owner/repo)")
    file_path: str | None = Field(None, description="File path being discussed")
    regulations: list[str] | None = Field(None, description="Specific regulations to focus on")
    
    # Attachments
    code_snippet: str | None = Field(None, description="Code snippet to analyze")
    file_content: str | None = Field(None, description="Full file content to analyze")
    
    # Options
    stream: bool = Field(False, description="Whether to stream the response")


class ChatActionRequest(BaseModel):
    """Request to execute a chat action."""
    
    action_type: str = Field(..., description="Type of action to execute")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Action parameters")


class ChatCitationResponse(BaseModel):
    """A citation in the chat response."""
    
    source: str
    title: str
    excerpt: str
    url: str | None = None
    relevance_score: float = 0.0


class ChatActionResponse(BaseModel):
    """A suggested action in the chat response."""
    
    id: str
    type: str
    label: str
    description: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class ChatMessageResponse(BaseModel):
    """Chat message response."""
    
    id: str
    conversation_id: str
    content: str
    
    # Context
    citations: list[ChatCitationResponse] = Field(default_factory=list)
    context_used: list[str] = Field(default_factory=list)
    
    # Actions
    actions: list[ChatActionResponse] = Field(default_factory=list)
    
    # Metadata
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationSummary(BaseModel):
    """Summary of a conversation."""
    
    id: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    last_message_preview: str = ""
    repository: str | None = None
    regulations: list[str] = Field(default_factory=list)


class QuickActionResponse(BaseModel):
    """Quick action suggestion."""
    
    label: str
    query: str
    icon: str


class FollowUpSuggestion(BaseModel):
    """Suggested follow-up question."""
    
    question: str


# Endpoints
@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> ChatMessageResponse:
    """Send a message to the compliance assistant.
    
    Returns a non-streaming response with the full assistant reply,
    citations, and suggested follow-up actions.
    """
    from app.services.chat import ChatMessage
    
    assistant = get_compliance_assistant()
    
    chat_message = ChatMessage(
        role="user",
        content=request.message,
        conversation_id=request.conversation_id,
        repository=request.repository,
        file_path=request.file_path,
        regulations=request.regulations,
        code_snippet=request.code_snippet,
        file_content=request.file_content,
    )
    
    try:
        response = await assistant.chat(
            message=chat_message,
            organization_id=organization.id,
            user_id=member.user_id,
        )
    except Exception as e:
        logger.error("Chat error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}",
        )
    
    return ChatMessageResponse(
        id=str(response.id),
        conversation_id=response.conversation_id,
        content=response.content,
        citations=[
            ChatCitationResponse(
                source=c.get("source", ""),
                title=c.get("title", ""),
                excerpt=c.get("excerpt", ""),
                url=c.get("url"),
                relevance_score=c.get("relevance_score", 0.0),
            )
            for c in response.citations
        ],
        context_used=response.context_used,
        actions=[
            ChatActionResponse(
                id=str(a.id),
                type=a.type.value if hasattr(a.type, "value") else str(a.type),
                label=a.label,
                description=a.description,
                parameters=a.parameters,
            )
            for a in response.actions
        ],
        model=response.model,
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
        latency_ms=response.latency_ms,
        timestamp=response.timestamp,
    )


@router.post("/message/stream")
async def send_message_stream(
    request: ChatMessageRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
):
    """Send a message with streaming response.
    
    Returns Server-Sent Events (SSE) with incremental response chunks.
    """
    from app.services.chat import ChatMessage
    import json
    
    assistant = get_compliance_assistant()
    
    chat_message = ChatMessage(
        role="user",
        content=request.message,
        conversation_id=request.conversation_id,
        repository=request.repository,
        file_path=request.file_path,
        regulations=request.regulations,
        code_snippet=request.code_snippet,
        file_content=request.file_content,
    )
    
    async def generate():
        try:
            async for chunk in assistant.chat_stream(
                message=chat_message,
                organization_id=organization.id,
                user_id=member.user_id,
            ):
                data = {
                    "id": str(chunk.id),
                    "conversation_id": chunk.conversation_id,
                    "content": chunk.content,
                    "is_complete": chunk.is_complete,
                }
                
                if chunk.is_complete:
                    data["citations"] = chunk.citations
                    data["context_used"] = chunk.context_used
                    data["actions"] = [a.to_dict() for a in chunk.actions]
                    data["model"] = chunk.model
                    data["input_tokens"] = chunk.input_tokens
                    data["output_tokens"] = chunk.output_tokens
                    data["latency_ms"] = chunk.latency_ms
                
                yield f"data: {json.dumps(data)}\n\n"
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error("Stream error", error=str(e))
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/conversation/{conversation_id}/action/{action_id}")
async def execute_action(
    conversation_id: str,
    action_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Execute a suggested action from a chat response."""
    assistant = get_compliance_assistant()
    
    try:
        result = await assistant.execute_action(
            conversation_id=conversation_id,
            action_id=action_id,
            organization_id=organization.id,
            user_id=member.user_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Action execution error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Action failed: {str(e)}",
        )


@router.get("/conversations", response_model=list[ConversationSummary])
async def list_conversations(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[ConversationSummary]:
    """List user's chat conversations."""
    assistant = get_compliance_assistant()
    
    conversations = await assistant.conversation_manager.list_conversations(
        organization_id=organization.id,
        user_id=member.user_id,
        limit=limit,
        offset=offset,
    )
    
    return [
        ConversationSummary(
            id=str(c.id),
            created_at=c.created_at,
            updated_at=c.updated_at,
            message_count=len(c.messages),
            last_message_preview=c.messages[-1].content[:100] if c.messages else "",
            repository=c.active_repository,
            regulations=c.active_regulations or [],
        )
        for c in conversations
    ]


@router.delete("/conversation/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, str]:
    """Delete a conversation."""
    assistant = get_compliance_assistant()
    
    success = await assistant.conversation_manager.delete(
        conversation_id=conversation_id,
        organization_id=organization.id,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    
    return {"status": "deleted"}


@router.get("/quick-actions", response_model=list[QuickActionResponse])
async def get_quick_actions(
    organization: CurrentOrganization,
    member: OrgMember,
    repository: str | None = Query(None),
) -> list[QuickActionResponse]:
    """Get quick action suggestions for the chat UI."""
    assistant = get_compliance_assistant()
    
    actions = await assistant.get_quick_actions(
        organization_id=organization.id,
        repository=repository,
    )
    
    return [
        QuickActionResponse(
            label=a["label"],
            query=a["query"],
            icon=a["icon"],
        )
        for a in actions
    ]


@router.get("/conversation/{conversation_id}/suggestions", response_model=list[FollowUpSuggestion])
async def get_follow_up_suggestions(
    conversation_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
) -> list[FollowUpSuggestion]:
    """Get suggested follow-up questions for a conversation."""
    assistant = get_compliance_assistant()
    
    suggestions = await assistant.suggest_questions(
        conversation_id=conversation_id,
        organization_id=organization.id,
    )
    
    return [FollowUpSuggestion(question=q) for q in suggestions]


@router.post("/analyze-code")
async def analyze_code(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    code: str,
    language: str,
    file_path: str | None = None,
    regulations: list[str] | None = Query(None),
) -> dict[str, Any]:
    """Analyze a code snippet for compliance issues.
    
    This is a specialized endpoint for code analysis that returns
    structured compliance findings without requiring a conversation.
    """
    from app.services.chat import ChatMessage
    
    assistant = get_compliance_assistant()
    
    prompt = f"Analyze this {language} code for compliance issues"
    if regulations:
        prompt += f" with focus on {', '.join(regulations)}"
    prompt += ". Return specific violations with line numbers, severity, and fix suggestions."
    
    chat_message = ChatMessage(
        role="user",
        content=prompt,
        code_snippet=code,
        file_path=file_path,
        regulations=regulations,
    )
    
    response = await assistant.chat(
        message=chat_message,
        organization_id=organization.id,
        user_id=member.user_id,
    )
    
    return {
        "analysis": response.content,
        "conversation_id": response.conversation_id,
        "citations": response.citations,
        "suggested_actions": [a.to_dict() for a in response.actions],
    }


@router.post("/explain-regulation")
async def explain_regulation(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    regulation: str,
    article: str | None = None,
    context: str | None = None,
) -> dict[str, Any]:
    """Get an explanation of a specific regulation or article.
    
    This endpoint provides developer-friendly explanations of regulatory
    requirements without needing a full conversation.
    """
    from app.services.chat import ChatMessage
    
    assistant = get_compliance_assistant()
    
    prompt = f"Explain {regulation}"
    if article:
        prompt += f" Article {article}"
    if context:
        prompt += f" in the context of: {context}"
    prompt += ". Focus on practical implementation requirements for developers."
    
    chat_message = ChatMessage(
        role="user",
        content=prompt,
        regulations=[regulation],
    )
    
    response = await assistant.chat(
        message=chat_message,
        organization_id=organization.id,
        user_id=member.user_id,
    )
    
    return {
        "explanation": response.content,
        "conversation_id": response.conversation_id,
        "citations": response.citations,
    }
