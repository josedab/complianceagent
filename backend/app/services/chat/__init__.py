"""Compliance Copilot Chat Service."""

from app.services.chat.conversation import ConversationManager, ConversationState, Message, MessageRole
from app.services.chat.rag import RAGPipeline, RAGContext, RAGSource, RAGDocument
from app.services.chat.assistant import ComplianceAssistant, ChatMessage, ChatResponse
from app.services.chat.actions import ActionHandler, ChatAction, ActionType, ActionResult

__all__ = [
    "ConversationManager",
    "ConversationState",
    "Message",
    "MessageRole",
    "RAGPipeline",
    "RAGContext",
    "RAGSource",
    "RAGDocument",
    "ComplianceAssistant",
    "ChatMessage",
    "ChatResponse",
    "ActionHandler",
    "ChatAction",
    "ActionType",
    "ActionResult",
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
