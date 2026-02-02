"""Compliance Assistant - AI-powered chat interface for compliance queries."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, AsyncIterator
from uuid import UUID, uuid4

import structlog

from app.agents.copilot import CopilotClient, CopilotMessage
from app.services.chat.actions import ActionHandler, ActionType, ChatAction
from app.services.chat.conversation import ConversationManager, ConversationState, Message, MessageRole
from app.services.chat.rag import RAGContext, RAGPipeline

logger = structlog.get_logger()

# UTC timezone for Python < 3.11 compatibility
UTC = timezone.utc


@dataclass
class ChatMessage:
    """A chat message for the API."""
    role: str
    content: str
    conversation_id: str | None = None
    
    # Context
    repository: str | None = None
    file_path: str | None = None
    regulations: list[str] | None = None
    
    # Attachments
    code_snippet: str | None = None
    file_content: str | None = None


@dataclass
class ChatResponse:
    """Response from the chat assistant."""
    id: UUID = field(default_factory=uuid4)
    conversation_id: str = ""
    content: str = ""
    
    # Citations and context
    citations: list[dict[str, Any]] = field(default_factory=list)
    context_used: list[str] = field(default_factory=list)
    
    # Suggested actions
    actions: list[ChatAction] = field(default_factory=list)
    
    # Metadata
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    # Streaming
    is_streaming: bool = False
    is_complete: bool = True
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "conversation_id": self.conversation_id,
            "content": self.content,
            "citations": self.citations,
            "context_used": self.context_used,
            "actions": [a.to_dict() for a in self.actions],
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp.isoformat(),
            "is_streaming": self.is_streaming,
            "is_complete": self.is_complete,
        }


class ComplianceAssistant:
    """AI-powered compliance assistant using Copilot SDK with RAG."""

    SYSTEM_PROMPT = """You are ComplianceAgent, an AI-powered compliance assistant for software developers.

Your capabilities:
1. Answer questions about regulations (GDPR, HIPAA, PCI-DSS, EU AI Act, SOX, etc.)
2. Analyze code for compliance issues
3. Explain requirements in developer-friendly terms
4. Help fix compliance violations
5. Generate compliant code modifications
6. Track compliance status across repositories

Guidelines:
- Always cite specific regulations and articles when applicable
- Provide actionable, code-specific advice
- Use the context provided to give accurate, relevant answers
- If you're unsure, say so and suggest how to find the answer
- Offer to generate fixes when you identify compliance issues
- Keep responses focused and practical

When discussing code:
- Reference specific file paths and line numbers from the context
- Explain why something is a compliance issue
- Suggest specific fixes with code examples

Available context:
{context}

Current session:
- Repository: {repository}
- Regulations: {regulations}
- User intent: {intent}"""

    def __init__(
        self,
        copilot_client: CopilotClient | None = None,
        conversation_manager: ConversationManager | None = None,
        rag_pipeline: RAGPipeline | None = None,
        action_handler: ActionHandler | None = None,
    ):
        self.copilot = copilot_client
        self.conversation_manager = conversation_manager or ConversationManager()
        self.rag_pipeline = rag_pipeline
        self.action_handler = action_handler

    async def chat(
        self,
        message: ChatMessage,
        organization_id: UUID,
        user_id: UUID | None = None,
        access_token: str | None = None,
    ) -> ChatResponse:
        """Process a chat message and return a response."""
        import time
        start_time = time.perf_counter()
        
        # Get or create conversation
        conversation = await self.conversation_manager.get_or_create(
            conversation_id=message.conversation_id,
            organization_id=organization_id,
            user_id=user_id,
        )
        
        # Update context from message
        if message.repository:
            conversation.active_repository = message.repository
        if message.regulations:
            conversation.active_regulations = message.regulations
        if message.file_path:
            conversation.active_file_path = message.file_path
        
        # Add user message to history
        user_message = Message(
            role=MessageRole.USER,
            content=message.content,
            context={
                "repository": message.repository,
                "file_path": message.file_path,
                "has_code": bool(message.code_snippet or message.file_content),
            },
        )
        conversation.add_message(user_message)
        
        # Retrieve context using RAG
        rag_context = None
        if self.rag_pipeline:
            rag_context = await self.rag_pipeline.retrieve(
                query=message.content,
                organization_id=organization_id,
                repository=conversation.active_repository,
                regulations=conversation.active_regulations,
            )
        
        # Build prompt with context
        context_str = self._build_context(
            rag_context=rag_context,
            code_snippet=message.code_snippet,
            file_content=message.file_content,
            file_path=message.file_path,
        )
        
        # Build system prompt
        system_prompt = self.SYSTEM_PROMPT.format(
            context=context_str,
            repository=conversation.active_repository or "Not specified",
            regulations=", ".join(conversation.active_regulations) if conversation.active_regulations else "All applicable",
            intent=rag_context.detected_intent if rag_context else "general",
        )
        
        # Build message history for Copilot
        copilot_messages = self._build_copilot_messages(conversation)
        
        # Get response from Copilot
        if not self.copilot:
            self.copilot = CopilotClient()
        
        async with self.copilot:
            copilot_response = await self.copilot.chat(
                messages=copilot_messages,
                system_message=system_prompt,
                temperature=0.7,
                max_tokens=4096,
            )
        
        # Add assistant response to history
        assistant_message = Message(
            role=MessageRole.ASSISTANT,
            content=copilot_response.content,
            citations=rag_context.get_citations() if rag_context else [],
            input_tokens=copilot_response.usage.get("prompt_tokens", 0),
            output_tokens=copilot_response.usage.get("completion_tokens", 0),
        )
        conversation.add_message(assistant_message)
        
        # Extract suggested actions
        actions = []
        if self.action_handler:
            actions = self.action_handler.create_actions_from_response(
                copilot_response.content,
                {
                    "repository": conversation.active_repository,
                    "file_path": conversation.active_file_path,
                    "regulations": conversation.active_regulations,
                },
            )
        
        # Save conversation
        await self.conversation_manager.save(conversation)
        
        latency = (time.perf_counter() - start_time) * 1000
        
        return ChatResponse(
            conversation_id=str(conversation.id),
            content=copilot_response.content,
            citations=rag_context.get_citations() if rag_context else [],
            context_used=[doc.title for doc in (rag_context.documents if rag_context else [])],
            actions=actions,
            model=copilot_response.model,
            input_tokens=copilot_response.usage.get("prompt_tokens", 0),
            output_tokens=copilot_response.usage.get("completion_tokens", 0),
            latency_ms=latency,
        )

    async def chat_stream(
        self,
        message: ChatMessage,
        organization_id: UUID,
        user_id: UUID | None = None,
        access_token: str | None = None,
    ) -> AsyncIterator[ChatResponse]:
        """Process a chat message with streaming response."""
        import time
        start_time = time.perf_counter()
        
        # Get or create conversation
        conversation = await self.conversation_manager.get_or_create(
            conversation_id=message.conversation_id,
            organization_id=organization_id,
            user_id=user_id,
        )
        
        # Update context
        if message.repository:
            conversation.active_repository = message.repository
        if message.regulations:
            conversation.active_regulations = message.regulations
        
        # Add user message
        user_message = Message(
            role=MessageRole.USER,
            content=message.content,
        )
        conversation.add_message(user_message)
        
        # Retrieve context
        rag_context = None
        if self.rag_pipeline:
            rag_context = await self.rag_pipeline.retrieve(
                query=message.content,
                organization_id=organization_id,
                repository=conversation.active_repository,
                regulations=conversation.active_regulations,
            )
        
        # Build context
        context_str = self._build_context(
            rag_context=rag_context,
            code_snippet=message.code_snippet,
            file_content=message.file_content,
            file_path=message.file_path,
        )
        
        system_prompt = self.SYSTEM_PROMPT.format(
            context=context_str,
            repository=conversation.active_repository or "Not specified",
            regulations=", ".join(conversation.active_regulations) if conversation.active_regulations else "All applicable",
            intent=rag_context.detected_intent if rag_context else "general",
        )
        
        copilot_messages = self._build_copilot_messages(conversation)
        
        # Stream response
        response_id = uuid4()
        full_content = ""
        
        if not self.copilot:
            self.copilot = CopilotClient()
        
        async with self.copilot:
            # Note: In production, this would use Copilot's streaming API
            # For now, we simulate streaming by chunking the response
            copilot_response = await self.copilot.chat(
                messages=copilot_messages,
                system_message=system_prompt,
                temperature=0.7,
                max_tokens=4096,
            )
            
            # Simulate streaming by yielding chunks
            content = copilot_response.content
            chunk_size = 50
            
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                full_content += chunk
                
                yield ChatResponse(
                    id=response_id,
                    conversation_id=str(conversation.id),
                    content=full_content,
                    is_streaming=True,
                    is_complete=i + chunk_size >= len(content),
                    latency_ms=(time.perf_counter() - start_time) * 1000,
                )
        
        # Final response with full content and metadata
        assistant_message = Message(
            role=MessageRole.ASSISTANT,
            content=full_content,
            citations=rag_context.get_citations() if rag_context else [],
        )
        conversation.add_message(assistant_message)
        await self.conversation_manager.save(conversation)
        
        actions = []
        if self.action_handler:
            actions = self.action_handler.create_actions_from_response(
                full_content,
                {"repository": conversation.active_repository},
            )
        
        yield ChatResponse(
            id=response_id,
            conversation_id=str(conversation.id),
            content=full_content,
            citations=rag_context.get_citations() if rag_context else [],
            context_used=[doc.title for doc in (rag_context.documents if rag_context else [])],
            actions=actions,
            model=copilot_response.model,
            input_tokens=copilot_response.usage.get("prompt_tokens", 0),
            output_tokens=copilot_response.usage.get("completion_tokens", 0),
            latency_ms=(time.perf_counter() - start_time) * 1000,
            is_streaming=False,
            is_complete=True,
        )

    async def execute_action(
        self,
        conversation_id: str,
        action_id: str,
        organization_id: UUID,
        user_id: UUID | None = None,
        access_token: str | None = None,
    ) -> dict[str, Any]:
        """Execute a suggested action."""
        conversation = await self.conversation_manager.get(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        # Find action in conversation history
        action = None
        for msg in conversation.messages:
            for act in msg.actions:
                if str(act.get("id")) == action_id:
                    action = ChatAction(
                        id=UUID(act["id"]),
                        type=ActionType(act["type"]),
                        parameters=act.get("parameters", {}),
                    )
                    break
        
        if not action and self.action_handler:
            # Create action from parameters
            raise ValueError(f"Action {action_id} not found in conversation")
        
        if not self.action_handler:
            raise ValueError("Action handler not available")
        
        return await self.action_handler.execute(
            action=action,
            organization_id=organization_id,
            user_id=user_id,
            access_token=access_token,
        )

    def _build_context(
        self,
        rag_context: RAGContext | None,
        code_snippet: str | None,
        file_content: str | None,
        file_path: str | None,
    ) -> str:
        """Build context string for the prompt."""
        parts = []
        
        # Add RAG context
        if rag_context and rag_context.documents:
            parts.append("### Retrieved Information")
            parts.append(rag_context.get_context_string(max_documents=5, max_total_length=5000))
        
        # Add code context
        if code_snippet:
            parts.append(f"### Code Snippet")
            if file_path:
                parts.append(f"File: {file_path}")
            parts.append(f"```\n{code_snippet[:3000]}\n```")
        
        if file_content and not code_snippet:
            parts.append(f"### File Content")
            if file_path:
                parts.append(f"File: {file_path}")
            parts.append(f"```\n{file_content[:5000]}\n```")
        
        if not parts:
            return "No specific context provided. Answer based on general compliance knowledge."
        
        return "\n\n".join(parts)

    def _build_copilot_messages(
        self,
        conversation: ConversationState,
    ) -> list[CopilotMessage]:
        """Build message list for Copilot API."""
        messages = []
        
        # Get recent context messages
        context_messages = conversation.get_context_messages(max_messages=10)
        
        for msg in context_messages:
            if msg.role == MessageRole.SYSTEM:
                continue  # System messages go separately
            messages.append(CopilotMessage(
                role=msg.role.value,
                content=msg.content,
            ))
        
        return messages

    async def get_quick_actions(
        self,
        organization_id: UUID,
        repository: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get quick action suggestions for the chat UI."""
        actions = [
            {
                "label": "Check compliance status",
                "query": "What's my compliance status?" + (f" for {repository}" if repository else ""),
                "icon": "shield-check",
            },
            {
                "label": "Explain GDPR requirements",
                "query": "Explain the key GDPR requirements for data processing",
                "icon": "book",
            },
            {
                "label": "Find compliance issues",
                "query": "What compliance issues exist in my codebase?",
                "icon": "alert-triangle",
            },
            {
                "label": "Generate compliance report",
                "query": "Generate a compliance summary report",
                "icon": "file-text",
            },
        ]
        
        if repository:
            actions.insert(1, {
                "label": f"Analyze {repository}",
                "query": f"Analyze {repository} for compliance issues",
                "icon": "search",
            })
        
        return actions

    async def suggest_questions(
        self,
        conversation_id: str,
        organization_id: UUID,
    ) -> list[str]:
        """Suggest follow-up questions based on conversation context."""
        conversation = await self.conversation_manager.get(conversation_id)
        if not conversation or not conversation.messages:
            return [
                "What regulations apply to my software?",
                "How do I ensure GDPR compliance?",
                "What data do I need to protect under HIPAA?",
            ]
        
        last_message = conversation.messages[-1]
        content_lower = last_message.content.lower()
        
        suggestions = []
        
        # Context-aware suggestions
        if "gdpr" in content_lower:
            suggestions.extend([
                "What are the consent requirements under GDPR?",
                "How do I implement the right to erasure?",
                "What data retention periods does GDPR require?",
            ])
        elif "hipaa" in content_lower:
            suggestions.extend([
                "What is considered PHI under HIPAA?",
                "How should I encrypt health data?",
                "What are HIPAA audit trail requirements?",
            ])
        elif "pci" in content_lower:
            suggestions.extend([
                "How should I store credit card data?",
                "What encryption is required for PCI-DSS?",
                "What are PCI-DSS logging requirements?",
            ])
        else:
            suggestions.extend([
                "Can you show me affected files?",
                "Generate a fix for this issue",
                "What's the deadline for compliance?",
            ])
        
        return suggestions[:3]
