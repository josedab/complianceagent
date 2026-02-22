"""Compliance Copilot Chat Service."""

from app.services.chat.actions import ActionHandler, ActionResult, ActionType, ChatAction
from app.services.chat.assistant import ChatMessage, ChatResponse, ComplianceAssistant
from app.services.chat.conversation import (
    ConversationManager,
    ConversationState,
    Message,
    MessageRole,
)
from app.services.chat.rag import RAGContext, RAGDocument, RAGPipeline, RAGSource


__all__ = [
    "ActionHandler",
    "ActionResult",
    "ActionType",
    "ChatAction",
    "ChatMessage",
    "ChatResponse",
    "ComplianceAssistant",
    "ConversationManager",
    "ConversationState",
    "Message",
    "MessageRole",
    "RAGContext",
    "RAGDocument",
    "RAGPipeline",
    "RAGSource",
]


# Global assistant instance
_assistant: ComplianceAssistant | None = None


def get_compliance_assistant() -> ComplianceAssistant:
    """Get or create the global compliance assistant."""
    global _assistant
    if _assistant is None:
        _assistant = ComplianceAssistant(
            conversation_manager=ConversationManager(),
            rag_pipeline=RAGPipeline(),
            action_handler=ActionHandler(),
        )
    return _assistant
