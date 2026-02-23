"""Knowledge assistant service for compliance Q&A and analysis."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.knowledge_assistant.models import (
    AssistantMessage,
    AssistantStats,
    Conversation,
    ConversationMode,
    QuickAction,
    ResponseConfidence,
)


logger = structlog.get_logger()

# Knowledge base for keyword matching
_KNOWLEDGE_BASE: dict[str, dict] = {
    "gdpr": {
        "summary": "The General Data Protection Regulation (GDPR) is the EU's comprehensive data protection law. It requires lawful basis for processing, data subject rights, DPO appointment, and breach notification within 72 hours.",
        "key_articles": ["Art. 5 - Principles", "Art. 6 - Lawful basis", "Art. 17 - Right to erasure", "Art. 25 - Data protection by design", "Art. 33 - Breach notification"],
        "framework": "GDPR",
    },
    "hipaa": {
        "summary": "HIPAA protects sensitive patient health information (PHI). Covered entities must implement administrative, physical, and technical safeguards. Breach notification is required within 60 days.",
        "key_articles": ["Privacy Rule", "Security Rule", "Breach Notification Rule", "Enforcement Rule"],
        "framework": "HIPAA",
    },
    "pci": {
        "summary": "PCI DSS ensures secure handling of cardholder data. It mandates network security, access control, encryption, vulnerability management, and regular testing across 12 requirements.",
        "key_articles": ["Req 1 - Network Security", "Req 3 - Stored Data Protection", "Req 6 - Secure Systems", "Req 8 - Access Control", "Req 11 - Testing"],
        "framework": "PCI DSS",
    },
    "soc2": {
        "summary": "SOC 2 evaluates controls relevant to security, availability, processing integrity, confidentiality, and privacy (Trust Services Criteria). Type II reports cover a period of operation.",
        "key_articles": ["CC1 - Control Environment", "CC6 - Logical Access", "CC7 - System Operations", "CC8 - Change Management"],
        "framework": "SOC 2",
    },
    "breach": {
        "summary": "Data breach response requires immediate containment, assessment of scope and impact, notification to authorities (72 hours under GDPR, 60 days under HIPAA), and affected individual notification.",
        "key_articles": ["GDPR Art. 33-34", "HIPAA Breach Notification Rule", "State breach notification laws"],
        "framework": "Cross-framework",
    },
    "encryption": {
        "summary": "Encryption requirements vary by framework: AES-256 for data at rest, TLS 1.2+ for data in transit. Key management must include rotation, access controls, and secure storage.",
        "key_articles": ["PCI DSS Req 3-4", "HIPAA Technical Safeguards", "GDPR Art. 32"],
        "framework": "Cross-framework",
    },
}


class KnowledgeAssistantService:
    """Service for compliance knowledge Q&A and analysis."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._conversations: dict[UUID, Conversation] = {}
        self._quick_actions = self._build_quick_actions()

    def _build_quick_actions(self) -> list[QuickAction]:
        """Build pre-defined quick actions."""
        return [
            QuickAction(
                id="qa-gdpr-overview",
                label="GDPR Overview",
                description="Get a summary of GDPR requirements and key articles",
                prompt="What are the key requirements of GDPR?",
                category="frameworks",
            ),
            QuickAction(
                id="qa-hipaa-overview",
                label="HIPAA Overview",
                description="Get a summary of HIPAA requirements and safeguards",
                prompt="What are the key requirements of HIPAA?",
                category="frameworks",
            ),
            QuickAction(
                id="qa-breach-response",
                label="Breach Response Guide",
                description="Step-by-step guide for handling a data breach",
                prompt="What steps should I take when a data breach occurs?",
                category="incident",
            ),
            QuickAction(
                id="qa-encryption-reqs",
                label="Encryption Requirements",
                description="Overview of encryption requirements across frameworks",
                prompt="What are the encryption requirements for compliance?",
                category="technical",
            ),
            QuickAction(
                id="qa-audit-prep",
                label="Audit Preparation",
                description="Checklist for preparing for a compliance audit",
                prompt="How should I prepare for an upcoming compliance audit?",
                category="audit",
            ),
            QuickAction(
                id="qa-risk-assessment",
                label="Risk Assessment",
                description="Guide for conducting a compliance risk assessment",
                prompt="How do I conduct a compliance risk assessment?",
                category="risk",
            ),
        ]

    def _classify_intent(self, content: str) -> tuple[str, ResponseConfidence]:
        """Classify the intent of a user message using keyword matching."""
        content_lower = content.lower()
        for keyword, knowledge in _KNOWLEDGE_BASE.items():
            if keyword in content_lower:
                return keyword, ResponseConfidence.high
        compliance_terms = ["compliance", "regulation", "audit", "control", "policy", "risk"]
        if any(term in content_lower for term in compliance_terms):
            return "general_compliance", ResponseConfidence.medium
        return "unknown", ResponseConfidence.low

    def _generate_response(self, intent: str, content: str) -> tuple[str, list[dict]]:
        """Generate a response based on classified intent."""
        if intent in _KNOWLEDGE_BASE:
            knowledge = _KNOWLEDGE_BASE[intent]
            response = knowledge["summary"]
            citations = [
                {"source": knowledge["framework"], "references": knowledge["key_articles"]}
            ]
            return response, citations

        if intent == "general_compliance":
            return (
                "Compliance involves adhering to regulatory frameworks relevant to your organization. "
                "Key areas include data protection (GDPR, HIPAA), payment security (PCI DSS), "
                "and operational controls (SOC 2). I can provide detailed guidance on any specific framework.",
                [{"source": "General", "references": ["GDPR", "HIPAA", "PCI DSS", "SOC 2"]}],
            )

        return (
            "I can help with compliance questions about GDPR, HIPAA, PCI DSS, SOC 2, "
            "breach response, encryption requirements, and more. Please ask a specific question.",
            [],
        )

    async def start_conversation(
        self,
        user_id: str,
        mode: str = "qa",
    ) -> Conversation:
        """Start a new conversation."""
        conversation = Conversation(
            id=uuid4(),
            user_id=user_id,
            mode=ConversationMode(mode),
            created_at=datetime.now(UTC),
        )
        self._conversations[conversation.id] = conversation
        logger.info("Conversation started", conversation_id=str(conversation.id), mode=mode)
        return conversation

    async def send_message(
        self,
        conversation_id: UUID,
        content: str,
    ) -> AssistantMessage:
        """Send a message and get a response with citations."""
        if conversation_id not in self._conversations:
            raise ValueError(f"Conversation not found: {conversation_id}")

        conversation = self._conversations[conversation_id]

        user_msg = AssistantMessage(
            id=uuid4(),
            role="user",
            content=content,
            timestamp=datetime.now(UTC),
        )
        conversation.messages.append(user_msg)

        intent, confidence = self._classify_intent(content)
        response_text, citations = self._generate_response(intent, content)

        assistant_msg = AssistantMessage(
            id=uuid4(),
            role="assistant",
            content=response_text,
            citations=citations,
            confidence=confidence,
            timestamp=datetime.now(UTC),
        )
        conversation.messages.append(assistant_msg)

        logger.info(
            "Message processed",
            conversation_id=str(conversation_id),
            intent=intent,
            confidence=confidence.value,
        )
        return assistant_msg

    async def list_quick_actions(self) -> list[QuickAction]:
        """List available quick actions."""
        return self._quick_actions

    async def get_conversation(self, conversation_id: UUID) -> Conversation:
        """Get a conversation by ID."""
        if conversation_id not in self._conversations:
            raise ValueError(f"Conversation not found: {conversation_id}")
        return self._conversations[conversation_id]

    async def list_conversations(self, user_id: str | None = None) -> list[Conversation]:
        """List conversations, optionally filtered by user."""
        conversations = list(self._conversations.values())
        if user_id:
            conversations = [c for c in conversations if c.user_id == user_id]
        return conversations

    async def get_stats(self) -> AssistantStats:
        """Get assistant usage statistics."""
        conversations = list(self._conversations.values())
        total_messages = sum(len(c.messages) for c in conversations)
        by_mode: dict[str, int] = {}
        for c in conversations:
            mode_key = c.mode.value
            by_mode[mode_key] = by_mode.get(mode_key, 0) + 1
        avg_msgs = total_messages / len(conversations) if conversations else 0.0
        return AssistantStats(
            total_conversations=len(conversations),
            total_messages=total_messages,
            by_mode=by_mode,
            avg_messages_per_conversation=round(avg_msgs, 2),
            positive_feedback_rate=0.85,
        )
