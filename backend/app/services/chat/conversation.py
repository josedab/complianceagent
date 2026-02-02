"""Conversation Manager - Tracks chat state and history."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

import structlog

logger = structlog.get_logger()

# UTC timezone for Python < 3.11 compatibility
UTC = timezone.utc


class MessageRole(str, Enum):
    """Role of a message in the conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class Message:
    """A single message in a conversation."""
    id: UUID = field(default_factory=uuid4)
    role: MessageRole = MessageRole.USER
    content: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    # Context and metadata
    context: dict[str, Any] = field(default_factory=dict)
    citations: list[dict[str, Any]] = field(default_factory=list)
    actions: list[dict[str, Any]] = field(default_factory=list)
    
    # Token tracking
    input_tokens: int = 0
    output_tokens: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "citations": self.citations,
            "actions": self.actions,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        return cls(
            id=UUID(data["id"]) if data.get("id") else uuid4(),
            role=MessageRole(data.get("role", "user")),
            content=data.get("content", ""),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now(UTC),
            context=data.get("context", {}),
            citations=data.get("citations", []),
            actions=data.get("actions", []),
            input_tokens=data.get("input_tokens", 0),
            output_tokens=data.get("output_tokens", 0),
        )


@dataclass
class ConversationState:
    """State of an ongoing conversation."""
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID | None = None
    user_id: UUID | None = None
    
    # Conversation history
    messages: list[Message] = field(default_factory=list)
    
    # Context
    active_repository: str | None = None  # owner/repo format
    active_regulations: list[str] = field(default_factory=list)
    active_requirement_id: UUID | None = None
    active_file_path: str | None = None
    
    # Session metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_activity: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    # Token budget
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    max_context_tokens: int = 32000
    
    # Settings
    streaming_enabled: bool = True
    deep_analysis_enabled: bool = True
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "messages": [m.to_dict() for m in self.messages],
            "active_repository": self.active_repository,
            "active_regulations": self.active_regulations,
            "active_requirement_id": str(self.active_requirement_id) if self.active_requirement_id else None,
            "active_file_path": self.active_file_path,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConversationState":
        return cls(
            id=UUID(data["id"]) if data.get("id") else uuid4(),
            organization_id=UUID(data["organization_id"]) if data.get("organization_id") else None,
            user_id=UUID(data["user_id"]) if data.get("user_id") else None,
            messages=[Message.from_dict(m) for m in data.get("messages", [])],
            active_repository=data.get("active_repository"),
            active_regulations=data.get("active_regulations", []),
            active_requirement_id=UUID(data["active_requirement_id"]) if data.get("active_requirement_id") else None,
            active_file_path=data.get("active_file_path"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(UTC),
            last_activity=datetime.fromisoformat(data["last_activity"]) if data.get("last_activity") else datetime.now(UTC),
            total_input_tokens=data.get("total_input_tokens", 0),
            total_output_tokens=data.get("total_output_tokens", 0),
        )

    def add_message(self, message: Message) -> None:
        """Add a message to the conversation."""
        self.messages.append(message)
        self.last_activity = datetime.now(UTC)
        self.total_input_tokens += message.input_tokens
        self.total_output_tokens += message.output_tokens

    def get_context_messages(self, max_messages: int = 20) -> list[Message]:
        """Get recent messages for context, respecting token budget."""
        # Start with most recent messages
        recent = self.messages[-max_messages:] if len(self.messages) > max_messages else self.messages
        return recent

    def clear_history(self) -> None:
        """Clear conversation history while keeping context."""
        self.messages = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0


class ConversationManager:
    """Manages conversation state with persistence."""

    CONVERSATION_KEY_PREFIX = "complianceagent:chat:conversation:"
    CONVERSATION_TTL = 60 * 60 * 24  # 24 hours

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self._local_cache: dict[str, ConversationState] = {}

    async def get_or_create(
        self,
        conversation_id: str | None = None,
        organization_id: UUID | None = None,
        user_id: UUID | None = None,
    ) -> ConversationState:
        """Get existing conversation or create new one."""
        if conversation_id:
            existing = await self.get(conversation_id)
            if existing:
                return existing
        
        # Create new conversation
        state = ConversationState(
            organization_id=organization_id,
            user_id=user_id,
        )
        await self.save(state)
        return state

    async def get(self, conversation_id: str) -> ConversationState | None:
        """Get a conversation by ID."""
        if self.redis:
            import json
            key = f"{self.CONVERSATION_KEY_PREFIX}{conversation_id}"
            data = await self.redis.get(key)
            if data:
                return ConversationState.from_dict(json.loads(data))
        else:
            return self._local_cache.get(conversation_id)
        return None

    async def save(self, state: ConversationState) -> None:
        """Save conversation state."""
        conversation_id = str(state.id)
        
        if self.redis:
            import json
            key = f"{self.CONVERSATION_KEY_PREFIX}{conversation_id}"
            await self.redis.set(
                key,
                json.dumps(state.to_dict()),
                ex=self.CONVERSATION_TTL,
            )
        else:
            self._local_cache[conversation_id] = state
        
        logger.debug("Conversation saved", conversation_id=conversation_id)

    async def delete(self, conversation_id: str) -> None:
        """Delete a conversation."""
        if self.redis:
            key = f"{self.CONVERSATION_KEY_PREFIX}{conversation_id}"
            await self.redis.delete(key)
        else:
            self._local_cache.pop(conversation_id, None)

    async def add_message(
        self,
        conversation_id: str,
        message: Message,
    ) -> ConversationState:
        """Add a message to a conversation."""
        state = await self.get(conversation_id)
        if not state:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        state.add_message(message)
        await self.save(state)
        return state

    async def set_context(
        self,
        conversation_id: str,
        repository: str | None = None,
        regulations: list[str] | None = None,
        requirement_id: UUID | None = None,
        file_path: str | None = None,
    ) -> ConversationState:
        """Update conversation context."""
        state = await self.get(conversation_id)
        if not state:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        if repository is not None:
            state.active_repository = repository
        if regulations is not None:
            state.active_regulations = regulations
        if requirement_id is not None:
            state.active_requirement_id = requirement_id
        if file_path is not None:
            state.active_file_path = file_path
        
        await self.save(state)
        return state

    async def list_conversations(
        self,
        organization_id: UUID,
        user_id: UUID | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List recent conversations for an organization/user."""
        conversations = []
        
        if self.redis:
            # Scan for matching keys
            pattern = f"{self.CONVERSATION_KEY_PREFIX}*"
            import json
            async for key in self.redis.scan_iter(match=pattern, count=100):
                data = await self.redis.get(key)
                if data:
                    state = ConversationState.from_dict(json.loads(data))
                    if state.organization_id == organization_id:
                        if user_id is None or state.user_id == user_id:
                            conversations.append({
                                "id": str(state.id),
                                "created_at": state.created_at.isoformat(),
                                "last_activity": state.last_activity.isoformat(),
                                "message_count": len(state.messages),
                                "active_repository": state.active_repository,
                            })
        else:
            for state in self._local_cache.values():
                if state.organization_id == organization_id:
                    if user_id is None or state.user_id == user_id:
                        conversations.append({
                            "id": str(state.id),
                            "created_at": state.created_at.isoformat(),
                            "last_activity": state.last_activity.isoformat(),
                            "message_count": len(state.messages),
                            "active_repository": state.active_repository,
                        })
        
        # Sort by last activity
        conversations.sort(key=lambda c: c["last_activity"], reverse=True)
        return conversations[:limit]

    async def cleanup_old_conversations(
        self,
        max_age_hours: int = 24,
    ) -> int:
        """Clean up old conversations."""
        cutoff = datetime.now(UTC) - timedelta(hours=max_age_hours)
        cleaned = 0
        
        if self.redis:
            # Redis handles TTL automatically
            pass
        else:
            to_delete = []
            for conv_id, state in self._local_cache.items():
                if state.last_activity < cutoff:
                    to_delete.append(conv_id)
            
            for conv_id in to_delete:
                del self._local_cache[conv_id]
                cleaned += 1
        
        return cleaned
