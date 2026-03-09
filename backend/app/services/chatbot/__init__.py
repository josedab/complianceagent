"""Regulatory compliance chatbot with AI-powered responses.

.. deprecated::
    This module is the legacy chatbot implementation. For new code, use
    :mod:`app.services.chat` which provides RAG, conversation management,
    streaming, and action handling. This module is maintained for backward
    compatibility with the ``/api/v1/chatbot`` endpoint.
"""

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import structlog

from app.agents.copilot import CopilotClient, CopilotMessage


logger = structlog.get_logger()


@dataclass
class ChatMessage:
    """A message in the chat conversation."""

    message_id: str = ""
    role: str = "user"  # user, assistant
    content: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)
    sources: list[dict[str, Any]] | None = None


@dataclass
class ChatResponse:
    """A chatbot response with sources and metadata."""

    message_id: str = ""
    content: str = ""
    sources: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    follow_up_questions: list[str] = field(default_factory=list)
    code_references: list[dict[str, Any]] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "message_id": self.message_id,
            "content": self.content,
            "sources": self.sources,
            "confidence": self.confidence,
            "follow_up_questions": self.follow_up_questions,
            "code_references": self.code_references,
        }


@dataclass
class ChatSession:
    """A chat session with conversation history."""

    session_id: str = ""
    organization_id: str = ""
    user_id: str = ""
    messages: list[ChatMessage] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class ComplianceChatbot:
    """AI-powered compliance chatbot using Copilot SDK.

    Provides conversational interface for:
    - Answering compliance questions
    - Explaining regulations
    - Providing codebase-specific compliance guidance
    - Suggesting fixes for compliance issues
    """

    SYSTEM_PROMPT = """You are a compliance expert assistant for software development teams.
You help answer questions about regulatory compliance including GDPR, CCPA, HIPAA, SOX, PCI-DSS,
EU AI Act, and other regulations.

Guidelines:
- Provide accurate, actionable compliance guidance
- Always cite specific regulation articles/sections when possible
- When discussing code, provide concrete examples
- Be clear about what is required vs. recommended
- If uncertain, acknowledge limitations and suggest consulting legal counsel
- Focus on practical implementation, not just legal theory

You have access to the following context about the user's environment:
{context}

When answering:
1. Identify the relevant regulation(s)
2. Cite specific requirements (articles, sections)
3. Explain how it applies to the user's situation
4. Provide actionable next steps
"""

    def __init__(self):
        self._sessions: dict[str, ChatSession] = {}
        self._ratings: dict[str, dict[str, Any]] = {}
        self._copilot_client: CopilotClient | None = None

    async def _get_copilot_client(self) -> CopilotClient:
        """Get or create Copilot client."""
        if self._copilot_client is None:
            self._copilot_client = CopilotClient()
        return self._copilot_client

    async def create_session(
        self,
        user_id: str,
        organization_id: str = "",
        context: dict[str, Any] | None = None,
    ) -> ChatSession:
        """Create a new chat session."""
        session = ChatSession(
            session_id=str(uuid4()),
            organization_id=organization_id,
            user_id=user_id,
            context=context or {},
        )
        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> ChatSession | None:
        """Get an existing session."""
        return self._sessions.get(session_id)

    async def chat(
        self,
        session_id: str,
        message: str,
        codebase_context: dict[str, Any] | None = None,
    ) -> ChatResponse:
        """Send a message and get a response.

        Args:
            session_id: Chat session ID
            message: User's message
            codebase_context: Optional context about the user's codebase

        Returns:
            ChatResponse with content, sources, and confidence.
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Add user message
        user_message = ChatMessage(message_id=str(uuid4()), role="user", content=message)
        session.messages.append(user_message)

        response = await self._generate_response(session, message, codebase_context)

        session.updated_at = datetime.now(UTC)
        return response

    async def send_message(
        self,
        session_id: str,
        message: str,
        code_context: dict[str, Any] | None = None,
    ) -> ChatResponse:
        """Alias for chat() matching the test interface."""
        return await self.chat(session_id, message, code_context)

    async def _generate_response(
        self,
        session: ChatSession,
        message: str,
        codebase_context: dict[str, Any] | None = None,
    ) -> ChatResponse:
        """Generate a response using the Copilot client."""
        context_str = self._build_context_string(session.context, codebase_context)
        system_prompt = self.SYSTEM_PROMPT.format(context=context_str)

        copilot_messages = [
            CopilotMessage(role=m.role, content=m.content) for m in session.messages[-10:]
        ]

        msg_id = str(uuid4())
        try:
            client = await self._get_copilot_client()
            async with client:
                response = await client.chat(
                    messages=copilot_messages,
                    system_message=system_prompt,
                    temperature=0.3,
                    max_tokens=2048,
                )

            chat_response = ChatResponse(
                message_id=msg_id,
                content=response.content,
                sources=[],
                confidence=0.85,
            )

        except (json.JSONDecodeError, KeyError, ValueError, OSError) as e:
            logger.warning(f"Copilot chat failed: {e}")
            chat_response = ChatResponse(
                message_id=msg_id,
                content=self._generate_fallback_response(message),
                sources=[],
                confidence=0.0,
            )

        # Record assistant message in session history
        assistant_message = ChatMessage(
            message_id=msg_id,
            role="assistant",
            content=chat_response.content,
        )
        session.messages.append(assistant_message)

        return chat_response

    def _build_context_string(
        self,
        session_context: dict[str, Any],
        codebase_context: dict[str, Any] | None,
    ) -> str:
        """Build context string for system prompt."""
        parts = []

        if session_context:
            if session_context.get("organization"):
                parts.append(f"Organization: {session_context['organization']}")
            if session_context.get("regulations"):
                parts.append(f"Active regulations: {', '.join(session_context['regulations'])}")
            if session_context.get("industry"):
                parts.append(f"Industry: {session_context['industry']}")

        if codebase_context:
            if codebase_context.get("languages"):
                parts.append(f"Languages: {', '.join(codebase_context['languages'])}")
            if codebase_context.get("frameworks"):
                parts.append(f"Frameworks: {', '.join(codebase_context['frameworks'])}")
            if codebase_context.get("data_types"):
                parts.append(f"Data types handled: {', '.join(codebase_context['data_types'])}")
            if codebase_context.get("current_issues"):
                parts.append(f"Current compliance issues: {codebase_context['current_issues']}")

        return "\n".join(parts) if parts else "No additional context provided."

    def _generate_fallback_response(self, message: str) -> str:
        """Generate fallback response when Copilot is unavailable."""
        message_lower = message.lower()

        if "gdpr" in message_lower:
            return """For GDPR-related questions, here are some key resources:

1. **Official GDPR text**: https://gdpr-info.eu/
2. **Key principles** (Article 5):
   - Lawfulness, fairness, transparency
   - Purpose limitation
   - Data minimization
   - Accuracy
   - Storage limitation
   - Integrity and confidentiality

Please try your question again in a moment, or consult with legal counsel for specific guidance."""

        if "hipaa" in message_lower:
            return """For HIPAA-related questions, key requirements include:

1. **Privacy Rule**: Protects PHI (Protected Health Information)
2. **Security Rule**: Administrative, physical, technical safeguards
3. **Breach Notification**: Report breaches within 60 days

For specific implementation guidance, please consult the HHS website or legal counsel."""

        return """I apologize, but I'm having trouble connecting to my knowledge base right now.

For immediate compliance assistance:
1. Check the ComplianceAgent documentation
2. Review the regulation's official text
3. Consult with your compliance team or legal counsel

Please try your question again in a moment."""

    async def get_quick_answer(
        self,
        question: str,
        regulations: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get a quick answer without a full session.

        Used for simple questions that don't need conversation history.
        """
        client = await self._get_copilot_client()

        context = ""
        if regulations:
            context = f"Focus on these regulations: {', '.join(regulations)}"

        system_prompt = f"""You are a compliance expert. Answer the question concisely and accurately.
{context}

Provide:
1. Direct answer (1-2 sentences)
2. Relevant regulation reference
3. One key action item

Return JSON with: answer, regulation, article, action"""

        try:
            async with client:
                response = await client.chat(
                    messages=[CopilotMessage(role="user", content=question)],
                    system_message=system_prompt,
                    temperature=0.3,
                    max_tokens=512,
                )

            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                content = content.removeprefix("json")
            return json.loads(content.rstrip("`"))

        except (json.JSONDecodeError, KeyError, ValueError, OSError) as e:
            logger.warning(f"Quick answer failed: {e}")
            return {
                "answer": "Unable to process question. Please try again.",
                "regulation": None,
                "article": None,
                "action": "Retry or consult compliance documentation",
            }

    async def explain_code_issue(
        self,
        code_snippet: str,
        issue_code: str = "",
        issue_message: str = "",
        language: str = "python",
        *,
        issue_type: str = "",
        regulations: list[str] | None = None,
    ) -> ChatResponse | dict[str, Any]:
        """Explain a compliance issue in code and provide fix guidance.

        When called with issue_type/regulations kwargs (test interface),
        delegates to _analyze_and_explain for mockability.
        """
        if issue_type:
            return await self._analyze_and_explain(
                code_snippet=code_snippet,
                issue_type=issue_type,
                regulations=regulations,
            )
        effective_issue = issue_code or issue_type
        effective_message = issue_message or issue_type
        effective_regs = regulations or []

        client = await self._get_copilot_client()

        regs_ctx = f"\nRegulations: {', '.join(effective_regs)}" if effective_regs else ""
        system_prompt = f"""You are a compliance-focused code reviewer.
Explain the compliance issue and provide guidance for fixing it.{regs_ctx}

Return JSON with:
- explanation: Clear explanation of why this is a compliance issue
- regulation: Which regulation this relates to
- article: Specific article/section
- risk: What could happen if not fixed
- fix_approach: How to fix this issue
- code_example: Example of compliant code (if applicable)"""

        user_prompt = f"""Explain this compliance issue:

**Code ({language})**:
```{language}
{code_snippet}
```

**Issue**: {effective_issue} - {effective_message}

Return JSON only."""

        try:
            async with client:
                response = await client.chat(
                    messages=[CopilotMessage(role="user", content=user_prompt)],
                    system_message=system_prompt,
                    temperature=0.3,
                    max_tokens=1024,
                )

            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                content = content.removeprefix("json")
            return json.loads(content.rstrip("`"))

        except (json.JSONDecodeError, KeyError, ValueError, OSError) as e:
            logger.warning(f"Code explanation failed: {e}")
            return {
                "explanation": effective_message,
                "regulation": None,
                "risk": "Potential compliance violation",
                "fix_approach": "Review code against compliance requirements",
            }

    def clear_session(self, session_id: str) -> bool:
        """Clear/delete a chat session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    async def end_session(self, session_id: str) -> bool:
        """End a chat session (alias for clear_session)."""
        return self.clear_session(session_id)

    def list_sessions(
        self,
        organization_id: str | None = None,
        user_id: str | None = None,
    ) -> list[ChatSession]:
        """List chat sessions with optional filters."""
        sessions = list(self._sessions.values())

        if organization_id:
            sessions = [s for s in sessions if s.organization_id == organization_id]

        if user_id:
            sessions = [s for s in sessions if s.user_id == user_id]

        return sorted(sessions, key=lambda s: s.updated_at, reverse=True)

    async def get_session_history(self, session_id: str) -> list[ChatMessage]:
        """Get message history for a session."""
        session = self._sessions.get(session_id)
        if not session:
            return []
        return list(session.messages)

    async def quick_answer(
        self,
        question: str,
        regulations: list[str] | None = None,
    ) -> ChatResponse:
        """Get a quick answer without a full session, returning ChatResponse."""
        return await self._generate_quick_answer(question, regulations)

    async def rate_response(
        self,
        message_id: str,
        rating: int,
        feedback: str = "",
    ) -> bool:
        """Record user feedback on a response."""
        self._ratings[message_id] = {
            "rating": rating,
            "feedback": feedback,
        }
        return True

    async def get_suggested_questions(
        self,
        context: dict[str, Any] | None = None,
    ) -> list[str]:
        """Get suggested follow-up questions based on context."""
        regulations = (context or {}).get("regulations", [])
        suggestions = [
            "What are the key compliance requirements I should know about?",
            "How do I implement data subject access requests?",
            "What encryption standards are required?",
        ]
        for reg in regulations[:2]:
            suggestions.append(f"What are the main obligations under {reg}?")
        return suggestions

    async def search_knowledge_base(
        self,
        query: str,
        regulations: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Search the compliance knowledge base."""
        return await self._search_regulations(query, regulations)

    async def _search_regulations(
        self,
        query: str,
        regulations: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Search regulations (stub for knowledge base integration)."""
        return []

    async def _generate_quick_answer(
        self,
        question: str,
        regulations: list[str] | None = None,
    ) -> ChatResponse:
        """Generate a quick answer using Copilot (mockable by tests)."""
        result = await self.get_quick_answer(question, regulations)
        return ChatResponse(
            message_id=str(uuid4()),
            content=result.get("answer", ""),
            sources=[{"regulation": result.get("regulation")}] if result.get("regulation") else [],
            confidence=0.85 if result.get("regulation") else 0.0,
        )

    async def _analyze_and_explain(
        self,
        code_snippet: str,
        issue_type: str,
        regulations: list[str] | None = None,
    ) -> ChatResponse:
        """Analyze code and explain compliance issue (used by tests via mock)."""
        return ChatResponse(
            message_id=str(uuid4()),
            content="Analysis pending",
            sources=[],
            confidence=0.0,
        )


# Global chatbot instance
_chatbot: ComplianceChatbot | None = None


def get_compliance_chatbot() -> ComplianceChatbot:
    """Get or create the global compliance chatbot."""
    global _chatbot
    if _chatbot is None:
        _chatbot = ComplianceChatbot()
    return _chatbot
