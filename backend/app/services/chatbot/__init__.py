"""Regulatory compliance chatbot with AI-powered responses.

.. deprecated::
    This module is the legacy chatbot implementation. For new code, use
    :mod:`app.services.chat` which provides RAG, conversation management,
    streaming, and action handling. This module is maintained for backward
    compatibility with the ``/api/v1/chatbot`` endpoint.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import structlog

from app.agents.copilot import CopilotClient, CopilotMessage


logger = structlog.get_logger()


@dataclass
class ChatMessage:
    """A message in the chat conversation."""

    id: UUID = field(default_factory=uuid4)
    role: str = "user"  # user, assistant
    content: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatSession:
    """A chat session with conversation history."""

    id: UUID = field(default_factory=uuid4)
    organization_id: str = ""
    user_id: str = ""
    messages: list[ChatMessage] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


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
        self._sessions: dict[UUID, ChatSession] = {}
        self._copilot_client: CopilotClient | None = None

    async def _get_copilot_client(self) -> CopilotClient:
        """Get or create Copilot client."""
        if self._copilot_client is None:
            self._copilot_client = CopilotClient()
        return self._copilot_client

    def create_session(
        self,
        organization_id: str,
        user_id: str,
        context: dict[str, Any] | None = None,
    ) -> ChatSession:
        """Create a new chat session."""
        session = ChatSession(
            organization_id=organization_id,
            user_id=user_id,
            context=context or {},
        )
        self._sessions[session.id] = session
        return session

    def get_session(self, session_id: UUID) -> ChatSession | None:
        """Get an existing session."""
        return self._sessions.get(session_id)

    async def chat(
        self,
        session_id: UUID,
        message: str,
        codebase_context: dict[str, Any] | None = None,
    ) -> ChatMessage:
        """Send a message and get a response.

        Args:
            session_id: Chat session ID
            message: User's message
            codebase_context: Optional context about the user's codebase

        Returns:
            Assistant's response message
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Add user message
        user_message = ChatMessage(role="user", content=message)
        session.messages.append(user_message)

        # Build context for system prompt
        context_str = self._build_context_string(session.context, codebase_context)
        system_prompt = self.SYSTEM_PROMPT.format(context=context_str)

        # Prepare conversation history for Copilot
        copilot_messages = [
            CopilotMessage(role=m.role, content=m.content)
            for m in session.messages[-10:]  # Last 10 messages for context
        ]

        try:
            client = await self._get_copilot_client()
            async with client:
                response = await client.chat(
                    messages=copilot_messages,
                    system_message=system_prompt,
                    temperature=0.3,
                    max_tokens=2048,
                )

            assistant_message = ChatMessage(
                role="assistant",
                content=response.content,
                metadata={
                    "model": response.model,
                    "finish_reason": response.finish_reason,
                },
            )

        except Exception as e:
            logger.warning(f"Copilot chat failed: {e}")
            # Fallback response
            assistant_message = ChatMessage(
                role="assistant",
                content=self._generate_fallback_response(message),
                metadata={"fallback": True},
            )

        session.messages.append(assistant_message)
        session.updated_at = datetime.utcnow()

        return assistant_message

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

            import json
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content.rstrip("`"))

        except Exception as e:
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
        issue_code: str,
        issue_message: str,
        language: str,
    ) -> dict[str, Any]:
        """Explain a compliance issue in code and provide fix guidance."""
        client = await self._get_copilot_client()

        system_prompt = """You are a compliance-focused code reviewer.
Explain the compliance issue and provide guidance for fixing it.

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

**Issue**: {issue_code} - {issue_message}

Return JSON only."""

        try:
            async with client:
                response = await client.chat(
                    messages=[CopilotMessage(role="user", content=user_prompt)],
                    system_message=system_prompt,
                    temperature=0.3,
                    max_tokens=1024,
                )

            import json
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content.rstrip("`"))

        except Exception as e:
            logger.warning(f"Code explanation failed: {e}")
            return {
                "explanation": issue_message,
                "regulation": None,
                "risk": "Potential compliance violation",
                "fix_approach": "Review code against compliance requirements",
            }

    def clear_session(self, session_id: UUID) -> bool:
        """Clear/delete a chat session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

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


# Global chatbot instance
_chatbot: ComplianceChatbot | None = None


def get_compliance_chatbot() -> ComplianceChatbot:
    """Get or create the global compliance chatbot."""
    global _chatbot
    if _chatbot is None:
        _chatbot = ComplianceChatbot()
    return _chatbot
