"""Chat service facade — unified entry point for compliance chat functionality."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import structlog

from app.services.chat.actions import ActionHandler, ActionResult, ActionType, ChatAction
from app.services.chat.assistant import ChatMessage, ChatResponse, ComplianceAssistant
from app.services.chat.conversation import (
    ConversationManager,
    ConversationState,
    Message,
    MessageRole,
)
from app.services.chat.rag import RAGContext, RAGDocument, RAGPipeline, RAGSource


if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from uuid import UUID


logger = structlog.get_logger(__name__)

__all__ = [
    "ActionResult",
    "ActionType",
    "ChatAction",
    "ChatMessage",
    "ChatResponse",
    "ChatService",
    "ConversationState",
    "Message",
    "MessageRole",
    "RAGContext",
    "RAGDocument",
    "RAGSource",
    "get_chat_service",
]


@dataclass
class ChatService:
    """Facade over chat sub-modules: assistant, conversation, RAG, and actions."""

    assistant: ComplianceAssistant = field(default_factory=ComplianceAssistant)
    conversation_manager: ConversationManager = field(default_factory=ConversationManager)
    rag_pipeline: RAGPipeline = field(default_factory=RAGPipeline)
    action_handler: ActionHandler = field(default_factory=ActionHandler)

    async def create_session(
        self,
        organization_id: UUID,
        user_id: UUID | None = None,
    ) -> ConversationState:
        """Create a new chat session and return its conversation state."""
        state = await self.conversation_manager.get_or_create(
            organization_id=organization_id,
            user_id=user_id,
        )
        logger.info("chat_session_created", conversation_id=str(state.id), org=str(organization_id))
        return state

    async def send_message(
        self,
        message: ChatMessage,
        organization_id: UUID,
        user_id: UUID | None = None,
        access_token: str | None = None,
        *,
        stream: bool = False,
    ) -> ChatResponse | AsyncIterator[ChatResponse]:
        """Send a message and receive a response (optionally streamed)."""
        if stream:
            return self.assistant.chat_stream(
                message,
                organization_id,
                user_id=user_id,
                access_token=access_token,
            )
        return await self.assistant.chat(
            message,
            organization_id,
            user_id=user_id,
            access_token=access_token,
        )

    async def get_history(
        self,
        conversation_id: str,
        max_messages: int = 50,
    ) -> list[Message]:
        """Retrieve message history for a conversation."""
        state = await self.conversation_manager.get(conversation_id)
        if state is None:
            return []
        return state.get_context_messages(max_messages=max_messages)

    async def execute_action(
        self,
        conversation_id: str,
        action_id: str,
        organization_id: UUID,
        user_id: UUID | None = None,
        access_token: str | None = None,
    ) -> dict[str, Any]:
        """Execute a suggested action within a conversation."""
        return await self.assistant.execute_action(
            conversation_id,
            action_id,
            organization_id,
            user_id=user_id,
            access_token=access_token,
        )

    async def search_context(
        self,
        query: str,
        organization_id: UUID,
        repository: str | None = None,
        regulations: list[str] | None = None,
        max_documents: int = 10,
    ) -> RAGContext:
        """Perform a RAG retrieval for the given query."""
        return await self.rag_pipeline.retrieve(
            query,
            organization_id,
            repository=repository,
            regulations=regulations,
            max_documents=max_documents,
        )


_service: ChatService | None = None


def get_chat_service() -> ChatService:
    """Return the global ChatService singleton."""
    global _service
    if _service is None:
        _service = ChatService()
        logger.info("chat_service_initialized")
    return _service
