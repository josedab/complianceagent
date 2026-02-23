"""Knowledge assistant models for compliance Q&A and analysis."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class ConversationMode(str, Enum):
    """Modes of conversation interaction."""

    qa = "qa"
    analysis = "analysis"
    recommendation = "recommendation"
    investigation = "investigation"


class ResponseConfidence(str, Enum):
    """Confidence level of assistant responses."""

    high = "high"
    medium = "medium"
    low = "low"
    uncertain = "uncertain"


@dataclass
class AssistantMessage:
    """A message in a conversation."""

    id: UUID = field(default_factory=uuid4)
    role: str = "user"
    content: str = ""
    citations: list[dict] = field(default_factory=list)
    confidence: ResponseConfidence = ResponseConfidence.high
    timestamp: datetime | None = None


@dataclass
class Conversation:
    """A conversation session with the assistant."""

    id: UUID = field(default_factory=uuid4)
    user_id: str = ""
    mode: ConversationMode = ConversationMode.qa
    messages: list[AssistantMessage] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    created_at: datetime | None = None


@dataclass
class QuickAction:
    """A pre-built quick action for common queries."""

    id: str = ""
    label: str = ""
    description: str = ""
    prompt: str = ""
    category: str = ""


@dataclass
class AssistantStats:
    """Aggregate assistant usage statistics."""

    total_conversations: int = 0
    total_messages: int = 0
    by_mode: dict = field(default_factory=dict)
    avg_messages_per_conversation: float = 0.0
    positive_feedback_rate: float = 0.0
