"""API endpoints for Knowledge Assistant conversations."""

from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.knowledge_assistant import KnowledgeAssistantService


logger = structlog.get_logger()
router = APIRouter()


class ConversationStartRequest(BaseModel):
    user_id: str = Field(...)
    mode: str = Field(default="qa")


class MessageSendRequest(BaseModel):
    content: str = Field(...)


@router.post("/conversations", status_code=status.HTTP_201_CREATED, summary="Start a conversation")
async def start_conversation(request: ConversationStartRequest, db: DB) -> dict:
    """Start a new conversation."""
    service = KnowledgeAssistantService(db=db)
    result = await service.start_conversation(
        user_id=request.user_id,
        mode=request.mode,
    )
    return {
        "id": str(result.id),
        "user_id": result.user_id,
        "mode": result.mode.value,
        "messages": [],
        "created_at": result.created_at.isoformat() if result.created_at else None,
    }


@router.post("/conversations/{conversation_id}/messages", summary="Send a message")
async def send_message(conversation_id: UUID, request: MessageSendRequest, db: DB) -> dict:
    """Send a message and get a response."""
    service = KnowledgeAssistantService(db=db)
    try:
        result = await service.send_message(
            conversation_id=conversation_id,
            content=request.content,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    return {
        "id": str(result.id),
        "role": result.role,
        "content": result.content,
        "citations": result.citations,
        "confidence": result.confidence.value,
        "timestamp": result.timestamp.isoformat() if result.timestamp else None,
    }


@router.get("/quick-actions", summary="Get quick actions")
async def get_quick_actions(db: DB) -> list[dict]:
    """List available quick actions."""
    service = KnowledgeAssistantService(db=db)
    actions = await service.list_quick_actions()
    return [
        {
            "id": a.id,
            "label": a.label,
            "description": a.description,
            "prompt": a.prompt,
            "category": a.category,
        }
        for a in actions
    ]


@router.get("/conversations/{conversation_id}", summary="Get a conversation")
async def get_conversation(conversation_id: UUID, db: DB) -> dict:
    """Get a conversation by ID."""
    service = KnowledgeAssistantService(db=db)
    try:
        result = await service.get_conversation(conversation_id=conversation_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    return {
        "id": str(result.id),
        "user_id": result.user_id,
        "mode": result.mode.value,
        "messages": [
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "citations": m.citations,
                "confidence": m.confidence.value,
                "timestamp": m.timestamp.isoformat() if m.timestamp else None,
            }
            for m in result.messages
        ],
        "created_at": result.created_at.isoformat() if result.created_at else None,
    }


@router.get("/conversations", summary="List conversations")
async def list_conversations(db: DB, user_id: str | None = None) -> list[dict]:
    """List conversations, optionally filtered by user."""
    service = KnowledgeAssistantService(db=db)
    conversations = await service.list_conversations(user_id=user_id)
    return [
        {
            "id": str(c.id),
            "user_id": c.user_id,
            "mode": c.mode.value,
            "messages": len(c.messages),
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in conversations
    ]


@router.get("/stats", summary="Get knowledge assistant stats")
async def get_stats(db: DB) -> dict:
    """Get assistant usage statistics."""
    service = KnowledgeAssistantService(db=db)
    stats = await service.get_stats()
    return {
        "total_conversations": stats.total_conversations,
        "total_messages": stats.total_messages,
        "by_mode": stats.by_mode,
        "avg_messages_per_conversation": stats.avg_messages_per_conversation,
        "positive_feedback_rate": stats.positive_feedback_rate,
    }
