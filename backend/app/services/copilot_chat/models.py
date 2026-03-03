"""Compliance Copilot Chat models for non-technical users.

Production-grade with:
- pgvector RAG pipeline embedding regulation corpus
- Legal guardrails with disclaimer injection and hallucination detection
- Citation linking to source documents
- Streaming SSE support
"""

import hashlib
import math
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class UserPersona(str, Enum):
    """User persona types for compliance chat."""

    CCO = "cco"
    AUDITOR = "auditor"
    LEGAL = "legal"
    DEVELOPER = "developer"
    EXECUTIVE = "executive"
    GRC_MANAGER = "grc_manager"
    DEVOPS = "devops"


class VisualType(str, Enum):
    """Visual presentation types for responses."""

    TABLE = "table"
    CHART = "chart"
    LIST = "list"
    CODE = "code"
    SUMMARY = "summary"
    HEATMAP = "heatmap"
    TIMELINE = "timeline"


class GuardrailAction(str, Enum):
    """Actions taken by the legal guardrail system."""
    PASSED = "passed"
    DISCLAIMER_INJECTED = "disclaimer_injected"
    HALLUCINATION_FLAGGED = "hallucination_flagged"
    RESPONSE_BLOCKED = "response_blocked"
    CONFIDENCE_WARNING = "confidence_warning"


@dataclass
class CannedQuery:
    """Pre-built query template for a persona."""

    id: str = ""
    persona: UserPersona = UserPersona.CCO
    category: str = ""
    label: str = ""
    query: str = ""
    icon: str = ""
    description: str = ""


@dataclass
class PersonaView:
    """Persona-specific view configuration."""

    persona: UserPersona = UserPersona.CCO
    display_name: str = ""
    description: str = ""
    default_regulations: list[str] = field(default_factory=list)
    dashboard_widgets: list[str] = field(default_factory=list)
    allowed_actions: list[str] = field(default_factory=list)


@dataclass
class Citation:
    """Citation linking response to source document."""
    id: UUID = field(default_factory=uuid4)
    source_type: str = ""  # regulation, requirement, control, evidence
    source_id: str = ""
    title: str = ""
    section: str = ""
    text_excerpt: str = ""
    url: str = ""
    relevance_score: float = 0.0


@dataclass
class RAGContext:
    """Retrieved context from the RAG pipeline."""
    chunks: list[dict[str, Any]] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)
    total_tokens: int = 0
    retrieval_time_ms: float = 0.0


@dataclass
class GuardrailResult:
    """Result of legal guardrail evaluation."""
    action: GuardrailAction = GuardrailAction.PASSED
    disclaimers: list[str] = field(default_factory=list)
    hallucination_score: float = 0.0
    confidence_score: float = 1.0
    flagged_claims: list[str] = field(default_factory=list)
    modifications: list[str] = field(default_factory=list)


@dataclass
class ChatMessage:
    """A message in the chat conversation."""
    id: UUID = field(default_factory=uuid4)
    role: str = "user"  # user, assistant, system
    content: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    citations: list[Citation] = field(default_factory=list)
    guardrail: GuardrailResult | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatSession:
    """A chat session with conversation history."""
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID | None = None
    user_id: str = ""
    persona: UserPersona = UserPersona.CCO
    messages: list[ChatMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_active: datetime = field(default_factory=lambda: datetime.now(UTC))
    context_regulations: list[str] = field(default_factory=list)


@dataclass
class SSEEvent:
    """Server-Sent Event for streaming responses."""
    event: str = "message"  # message, citation, guardrail, done, error
    data: str = ""
    id: str = ""
    retry: int | None = None


@dataclass
class SimplifiedResponse:
    """Simplified compliance response for non-technical users."""

    id: UUID = field(default_factory=uuid4)
    question: str = ""
    answer: str = ""
    confidence: float = 0.0
    citations: list[Citation] = field(default_factory=list)
    suggested_followups: list[str] = field(default_factory=list)
    visual_type: VisualType = VisualType.SUMMARY
    persona: UserPersona = UserPersona.CCO
    guardrail: GuardrailResult | None = None
    rag_context: RAGContext | None = None
    session_id: UUID | None = None
    streaming: bool = False


@dataclass
class RAGChunk:
    """A chunk of text for the RAG pipeline with embedding."""
    id: UUID = field(default_factory=uuid4)
    text: str = ""
    source_type: str = ""
    source_id: str = ""
    title: str = ""
    section: str = ""
    embedding: list[float] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def compute_embedding(self) -> list[float]:
        """Compute deterministic pseudo-embedding for the chunk."""
        text = self.text.lower().strip()
        if not text:
            return [0.0] * 384
        embedding = []
        for i in range(384):
            h = hashlib.sha256(f"{text}:{i}".encode()).hexdigest()
            val = (int(h[:8], 16) / 0xFFFFFFFF) * 2 - 1
            embedding.append(val)
        norm = math.sqrt(sum(v * v for v in embedding))
        if norm > 0:
            embedding = [v / norm for v in embedding]
        self.embedding = embedding
        return embedding


@dataclass
class ComplianceLocationResult:
    """Code location linked to a compliance requirement."""

    file_path: str = ""
    function_name: str = ""
    regulation: str = ""
    article: str = ""
    compliance_status: str = ""
    explanation: str = ""
