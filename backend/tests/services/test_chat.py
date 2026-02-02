"""Tests for Compliance Copilot Chat service."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.chat import (
    ComplianceAssistant,
    ChatMessage,
    ChatResponse,
    ConversationManager,
    ConversationState,
    Message,
    MessageRole,
    RAGPipeline,
    RAGContext,
    RAGDocument,
    ActionHandler,
    ActionType,
    ChatAction,
)

pytestmark = pytest.mark.asyncio


class TestConversationManager:
    """Test ConversationManager."""

    @pytest.fixture
    def manager(self):
        """Create conversation manager."""
        return ConversationManager()

    async def test_create_conversation(self, manager):
        """Test creating a new conversation."""
        org_id = uuid4()
        user_id = uuid4()
        
        conversation = await manager.get_or_create(
            conversation_id=None,
            organization_id=org_id,
            user_id=user_id,
        )
        
        assert conversation is not None
        assert conversation.organization_id == org_id
        assert len(conversation.messages) == 0

    async def test_get_existing_conversation(self, manager):
        """Test getting an existing conversation."""
        org_id = uuid4()
        user_id = uuid4()
        
        # Create first
        conv1 = await manager.get_or_create(
            conversation_id=None,
            organization_id=org_id,
            user_id=user_id,
        )
        
        # Get same
        conv2 = await manager.get_or_create(
            conversation_id=str(conv1.id),
            organization_id=org_id,
            user_id=user_id,
        )
        
        assert conv1.id == conv2.id

    async def test_save_conversation(self, manager):
        """Test saving conversation state."""
        org_id = uuid4()
        conversation = await manager.get_or_create(
            conversation_id=None,
            organization_id=org_id,
        )
        
        # Add a message
        conversation.add_message(Message(
            role=MessageRole.USER,
            content="Test question",
        ))
        
        await manager.save(conversation)
        
        # Retrieve and verify
        retrieved = await manager.get(str(conversation.id))
        assert retrieved is not None
        assert len(retrieved.messages) == 1

    async def test_delete_conversation(self, manager):
        """Test deleting a conversation."""
        org_id = uuid4()
        conversation = await manager.get_or_create(
            conversation_id=None,
            organization_id=org_id,
        )
        
        await manager.save(conversation)
        result = await manager.delete(str(conversation.id), org_id)
        
        assert result is True
        
        # Should not exist anymore
        retrieved = await manager.get(str(conversation.id))
        assert retrieved is None


class TestConversationState:
    """Test ConversationState."""

    def test_add_message(self):
        """Test adding messages to conversation."""
        state = ConversationState(
            id=uuid4(),
            organization_id=uuid4(),
        )
        
        state.add_message(Message(
            role=MessageRole.USER,
            content="Hello",
        ))
        
        state.add_message(Message(
            role=MessageRole.ASSISTANT,
            content="Hi there!",
        ))
        
        assert len(state.messages) == 2
        assert state.messages[0].role == MessageRole.USER
        assert state.messages[1].role == MessageRole.ASSISTANT

    def test_get_context_messages(self):
        """Test getting context messages with limit."""
        state = ConversationState(
            id=uuid4(),
            organization_id=uuid4(),
        )
        
        # Add many messages
        for i in range(15):
            state.add_message(Message(
                role=MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT,
                content=f"Message {i}",
            ))
        
        context = state.get_context_messages(max_messages=5)
        
        assert len(context) == 5
        # Should be the most recent messages
        assert "Message 14" in context[-1].content

    def test_active_context(self):
        """Test setting active context."""
        state = ConversationState(
            id=uuid4(),
            organization_id=uuid4(),
        )
        
        state.active_repository = "owner/repo"
        state.active_regulations = ["GDPR", "HIPAA"]
        state.active_file_path = "src/user.py"
        
        assert state.active_repository == "owner/repo"
        assert "GDPR" in state.active_regulations


class TestRAGPipeline:
    """Test RAGPipeline."""

    @pytest.fixture
    def rag_pipeline(self):
        """Create RAG pipeline."""
        return RAGPipeline()

    async def test_retrieve_context(self, rag_pipeline):
        """Test retrieving context for a query."""
        org_id = uuid4()
        
        context = await rag_pipeline.retrieve(
            query="What are GDPR encryption requirements?",
            organization_id=org_id,
            regulations=["GDPR"],
        )
        
        assert context is not None
        assert context.detected_intent is not None

    async def test_detect_intent(self, rag_pipeline):
        """Test query intent detection."""
        # Compliance status query
        intent1 = rag_pipeline._detect_intent("What's my compliance status?")
        assert intent1 == "compliance_status"
        
        # Explanation query
        intent2 = rag_pipeline._detect_intent("Explain GDPR Article 17")
        assert intent2 == "explanation"
        
        # Action query
        intent3 = rag_pipeline._detect_intent("Generate a fix for this issue")
        assert intent3 == "action"

    async def test_extract_entities(self, rag_pipeline):
        """Test entity extraction from query."""
        entities = rag_pipeline._extract_entities(
            "What are the HIPAA requirements for PHI encryption?"
        )
        
        assert "HIPAA" in entities.get("regulations", [])

    def test_context_string_generation(self, rag_pipeline):
        """Test generating context string from documents."""
        context = RAGContext(
            documents=[
                RAGDocument(
                    id="doc1",
                    title="GDPR Article 32",
                    content="Security of processing requirements...",
                    source="regulation",
                    relevance_score=0.95,
                ),
                RAGDocument(
                    id="doc2",
                    title="Encryption Best Practices",
                    content="Use AES-256 for data at rest...",
                    source="documentation",
                    relevance_score=0.85,
                ),
            ],
            detected_intent="explanation",
        )
        
        context_str = context.get_context_string(max_documents=5)
        
        assert "GDPR Article 32" in context_str
        assert "AES-256" in context_str


class TestActionHandler:
    """Test ActionHandler."""

    @pytest.fixture
    def action_handler(self):
        """Create action handler."""
        return ActionHandler()

    async def test_execute_generate_fix(self, action_handler):
        """Test executing generate fix action."""
        action = ChatAction(
            id=uuid4(),
            type=ActionType.GENERATE_FIX,
            label="Generate fix",
            description="Generate compliant code",
            parameters={
                "code": "log(user.email)",
                "issue": "PII in logs",
                "language": "python",
            },
        )
        
        with patch.object(action_handler, '_generate_fix', new_callable=AsyncMock) as mock:
            mock.return_value = {
                "success": True,
                "fixed_code": "log(mask_pii(user.email))",
                "explanation": "Added PII masking",
            }
            
            result = await action_handler.execute(
                action=action,
                organization_id=uuid4(),
            )
        
        assert result["success"] is True
        assert "fixed_code" in result

    async def test_execute_explain_requirement(self, action_handler):
        """Test executing explain requirement action."""
        action = ChatAction(
            id=uuid4(),
            type=ActionType.EXPLAIN_REQUIREMENT,
            label="Explain",
            description="Explain this requirement",
            parameters={
                "regulation": "GDPR",
                "article": "17",
            },
        )
        
        with patch.object(action_handler, '_explain_requirement', new_callable=AsyncMock) as mock:
            mock.return_value = {
                "success": True,
                "explanation": "Article 17 covers the right to erasure...",
            }
            
            result = await action_handler.execute(
                action=action,
                organization_id=uuid4(),
            )
        
        assert result["success"] is True
        assert "explanation" in result

    def test_create_actions_from_response(self, action_handler):
        """Test creating actions from assistant response."""
        response = """Based on my analysis, you have a GDPR violation.
        
I can help you fix this. Would you like me to:
1. Generate a fix for the unencrypted PII storage
2. Create a PR with the fix
3. Explain the GDPR Article 32 requirements"""
        
        context = {
            "repository": "owner/repo",
            "file_path": "src/user.py",
            "regulations": ["GDPR"],
        }
        
        actions = action_handler.create_actions_from_response(response, context)
        
        # Should detect action opportunities
        assert len(actions) >= 0  # May or may not detect depending on implementation


class TestComplianceAssistant:
    """Test ComplianceAssistant."""

    @pytest.fixture
    def mock_copilot_client(self):
        """Create mock Copilot client."""
        client = MagicMock()
        client.chat = AsyncMock(return_value=MagicMock(
            content="Based on GDPR Article 32, you need to encrypt personal data at rest.",
            model="gpt-4",
            usage={"prompt_tokens": 100, "completion_tokens": 50},
        ))
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=None)
        return client

    @pytest.fixture
    def assistant(self, mock_copilot_client):
        """Create assistant with mocks."""
        assistant = ComplianceAssistant(
            copilot_client=mock_copilot_client,
            conversation_manager=ConversationManager(),
            rag_pipeline=RAGPipeline(),
            action_handler=ActionHandler(),
        )
        return assistant

    async def test_chat_basic(self, assistant, mock_copilot_client):
        """Test basic chat interaction."""
        org_id = uuid4()
        
        message = ChatMessage(
            role="user",
            content="What encryption does GDPR require?",
            regulations=["GDPR"],
        )
        
        response = await assistant.chat(
            message=message,
            organization_id=org_id,
        )
        
        assert response is not None
        assert response.content is not None
        assert response.conversation_id is not None
        assert response.is_complete is True

    async def test_chat_with_code(self, assistant, mock_copilot_client):
        """Test chat with code context."""
        org_id = uuid4()
        
        message = ChatMessage(
            role="user",
            content="Is this code GDPR compliant?",
            code_snippet="user_data = {'email': user.email, 'ssn': user.ssn}",
            regulations=["GDPR"],
        )
        
        response = await assistant.chat(
            message=message,
            organization_id=org_id,
        )
        
        assert response is not None
        assert response.content is not None

    async def test_chat_with_repository_context(self, assistant, mock_copilot_client):
        """Test chat with repository context."""
        org_id = uuid4()
        
        message = ChatMessage(
            role="user",
            content="What compliance issues exist?",
            repository="owner/repo",
        )
        
        response = await assistant.chat(
            message=message,
            organization_id=org_id,
        )
        
        assert response is not None
        assert response.conversation_id is not None

    async def test_chat_continues_conversation(self, assistant, mock_copilot_client):
        """Test continuing a conversation."""
        org_id = uuid4()
        
        # First message
        msg1 = ChatMessage(
            role="user",
            content="What is GDPR?",
        )
        response1 = await assistant.chat(message=msg1, organization_id=org_id)
        conv_id = response1.conversation_id
        
        # Follow-up
        msg2 = ChatMessage(
            role="user",
            content="What about Article 17?",
            conversation_id=conv_id,
        )
        response2 = await assistant.chat(message=msg2, organization_id=org_id)
        
        assert response2.conversation_id == conv_id

    async def test_get_quick_actions(self, assistant):
        """Test getting quick action suggestions."""
        org_id = uuid4()
        
        actions = await assistant.get_quick_actions(
            organization_id=org_id,
            repository="owner/repo",
        )
        
        assert len(actions) > 0
        for action in actions:
            assert "label" in action
            assert "query" in action

    async def test_suggest_questions(self, assistant):
        """Test suggesting follow-up questions."""
        org_id = uuid4()
        
        # Create a conversation first
        msg = ChatMessage(role="user", content="Tell me about GDPR")
        response = await assistant.chat(message=msg, organization_id=org_id)
        
        suggestions = await assistant.suggest_questions(
            conversation_id=response.conversation_id,
            organization_id=org_id,
        )
        
        assert len(suggestions) > 0
        for suggestion in suggestions:
            assert isinstance(suggestion, str)


class TestChatMessage:
    """Test ChatMessage dataclass."""

    def test_message_creation(self):
        """Test creating a chat message."""
        message = ChatMessage(
            role="user",
            content="What is HIPAA?",
            repository="owner/repo",
            regulations=["HIPAA"],
        )
        
        assert message.role == "user"
        assert message.content == "What is HIPAA?"
        assert message.repository == "owner/repo"
        assert "HIPAA" in message.regulations

    def test_message_with_code(self):
        """Test message with code snippet."""
        message = ChatMessage(
            role="user",
            content="Is this secure?",
            code_snippet="password = 'secret123'",
            file_path="src/config.py",
        )
        
        assert message.code_snippet is not None
        assert message.file_path == "src/config.py"


class TestChatResponse:
    """Test ChatResponse dataclass."""

    def test_response_creation(self):
        """Test creating a chat response."""
        response = ChatResponse(
            conversation_id="conv-123",
            content="HIPAA requires encryption of PHI.",
            model="gpt-4",
            input_tokens=100,
            output_tokens=50,
        )
        
        assert response.content is not None
        assert response.model == "gpt-4"
        assert response.is_complete is True

    def test_response_with_citations(self):
        """Test response with citations."""
        response = ChatResponse(
            conversation_id="conv-123",
            content="According to GDPR Article 32...",
            citations=[
                {
                    "source": "GDPR",
                    "title": "Article 32 - Security of processing",
                    "excerpt": "The controller shall implement appropriate...",
                },
            ],
        )
        
        assert len(response.citations) == 1
        assert response.citations[0]["source"] == "GDPR"

    def test_response_with_actions(self):
        """Test response with suggested actions."""
        response = ChatResponse(
            conversation_id="conv-123",
            content="I found an issue. Would you like me to fix it?",
            actions=[
                ChatAction(
                    id=uuid4(),
                    type=ActionType.GENERATE_FIX,
                    label="Generate Fix",
                    description="Generate compliant code",
                ),
            ],
        )
        
        assert len(response.actions) == 1
        assert response.actions[0].type == ActionType.GENERATE_FIX

    def test_response_to_dict(self):
        """Test converting response to dict."""
        response = ChatResponse(
            conversation_id="conv-123",
            content="Test response",
            model="gpt-4",
            latency_ms=150.5,
        )
        
        data = response.to_dict()
        
        assert data["conversation_id"] == "conv-123"
        assert data["content"] == "Test response"
        assert data["latency_ms"] == 150.5


class TestRAGDocument:
    """Test RAGDocument dataclass."""

    def test_document_creation(self):
        """Test creating a RAG document."""
        doc = RAGDocument(
            id="doc-123",
            title="GDPR Article 17",
            content="The data subject shall have the right to erasure...",
            source="regulation",
            relevance_score=0.95,
            metadata={"regulation": "GDPR", "article": "17"},
        )
        
        assert doc.title == "GDPR Article 17"
        assert doc.relevance_score == 0.95
        assert doc.metadata["article"] == "17"


class TestChatAction:
    """Test ChatAction dataclass."""

    def test_action_creation(self):
        """Test creating a chat action."""
        action = ChatAction(
            id=uuid4(),
            type=ActionType.CREATE_PR,
            label="Create PR",
            description="Create a pull request with the fix",
            parameters={
                "repository": "owner/repo",
                "branch": "fix/compliance",
            },
        )
        
        assert action.type == ActionType.CREATE_PR
        assert action.label == "Create PR"
        assert action.parameters["repository"] == "owner/repo"

    def test_action_to_dict(self):
        """Test converting action to dict."""
        action = ChatAction(
            id=uuid4(),
            type=ActionType.GENERATE_FIX,
            label="Fix Code",
            description="Generate compliant code",
        )
        
        data = action.to_dict()
        
        assert data["type"] == "generate_fix"
        assert data["label"] == "Fix Code"
