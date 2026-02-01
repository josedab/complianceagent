"""Tests for compliance chatbot service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.services.chatbot import (
    ComplianceChatbot,
    ChatSession,
    ChatMessage,
    ChatResponse,
)

pytestmark = pytest.mark.asyncio


class TestComplianceChatbot:
    """Test suite for ComplianceChatbot."""

    @pytest.fixture
    def chatbot(self):
        """Create ComplianceChatbot instance."""
        return ComplianceChatbot()

    async def test_create_session(self, chatbot):
        """Test creating a chat session."""
        session = await chatbot.create_session(
            user_id="user-123",
            context={"organization": "test-org"},
        )
        
        assert session is not None
        assert session.session_id is not None
        assert session.user_id == "user-123"
        assert len(session.messages) == 0

    async def test_send_message(self, chatbot):
        """Test sending a message."""
        session = await chatbot.create_session(user_id="user-123")
        
        with patch.object(chatbot, "_generate_response") as mock_generate:
            mock_generate.return_value = ChatResponse(
                message_id="msg-002",
                content="Yes, GDPR requires encryption of personal data at rest under Article 32.",
                sources=[
                    {"regulation": "GDPR", "article": "32", "title": "Security of processing"},
                ],
                confidence=0.92,
                follow_up_questions=[
                    "What encryption algorithms are recommended?",
                    "Does this apply to backups as well?",
                ],
            )
            
            response = await chatbot.send_message(
                session_id=session.session_id,
                message="Does GDPR require encryption at rest?",
            )
            
            assert response is not None
            assert response.content is not None
            assert len(response.sources) >= 1
            assert response.confidence >= 0.8

    async def test_send_message_with_code_context(self, chatbot):
        """Test sending a message with code context."""
        session = await chatbot.create_session(
            user_id="user-123",
            context={"codebase": "test-repo"},
        )
        
        with patch.object(chatbot, "_generate_response") as mock_generate:
            mock_generate.return_value = ChatResponse(
                message_id="msg-003",
                content="Your user_service.py handles PII without encryption. GDPR Article 32 requires implementing encryption.",
                sources=[
                    {"regulation": "GDPR", "article": "32"},
                ],
                code_references=[
                    {"file": "src/user_service.py", "line": 45, "issue": "Unencrypted PII storage"},
                ],
                confidence=0.88,
            )
            
            response = await chatbot.send_message(
                session_id=session.session_id,
                message="Is our user service GDPR compliant?",
                code_context={
                    "files": ["src/user_service.py"],
                    "repository": "test-repo",
                },
            )
            
            assert response is not None
            assert response.code_references is not None
            assert len(response.code_references) >= 1

    async def test_quick_answer(self, chatbot):
        """Test getting a quick answer without session."""
        with patch.object(chatbot, "_generate_quick_answer") as mock_answer:
            mock_answer.return_value = ChatResponse(
                message_id="quick-001",
                content="Under HIPAA, PHI must be encrypted both at rest and in transit.",
                sources=[
                    {"regulation": "HIPAA", "section": "164.312", "title": "Technical Safeguards"},
                ],
                confidence=0.95,
            )
            
            response = await chatbot.quick_answer(
                question="What are HIPAA encryption requirements?",
                regulations=["HIPAA"],
            )
            
            assert response is not None
            assert "HIPAA" in response.content or "encrypt" in response.content.lower()

    async def test_explain_code_issue(self, chatbot):
        """Test explaining a code compliance issue."""
        with patch.object(chatbot, "_analyze_and_explain") as mock_explain:
            mock_explain.return_value = ChatResponse(
                message_id="explain-001",
                content="""This code stores user email addresses without encryption, violating GDPR Article 32.
                
**Why it's an issue:**
- Email is personal data under GDPR
- Article 32 requires appropriate technical measures including encryption

**Recommended fix:**
Encrypt the email field before storage using AES-256.""",
                sources=[{"regulation": "GDPR", "article": "32"}],
                confidence=0.9,
            )
            
            response = await chatbot.explain_code_issue(
                code_snippet="""
                def store_user(user):
                    db.users.insert({'email': user.email})
                """,
                issue_type="unencrypted_pii",
                regulations=["GDPR"],
            )
            
            assert response is not None
            assert "encrypt" in response.content.lower() or "GDPR" in response.content

    async def test_get_session_history(self, chatbot):
        """Test getting session history."""
        session = await chatbot.create_session(user_id="user-123")
        
        # Add some messages
        with patch.object(chatbot, "_generate_response") as mock_generate:
            mock_generate.return_value = ChatResponse(
                message_id="msg-001",
                content="Test response",
                sources=[],
                confidence=0.9,
            )
            
            await chatbot.send_message(session.session_id, "Question 1")
            await chatbot.send_message(session.session_id, "Question 2")
        
        history = await chatbot.get_session_history(session.session_id)
        
        assert len(history) >= 2

    async def test_get_suggested_questions(self, chatbot):
        """Test getting suggested questions."""
        suggestions = await chatbot.get_suggested_questions(
            context={"regulations": ["GDPR", "CCPA"]},
        )
        
        assert len(suggestions) >= 3
        for suggestion in suggestions:
            assert isinstance(suggestion, str)

    async def test_end_session(self, chatbot):
        """Test ending a session."""
        session = await chatbot.create_session(user_id="user-123")
        
        result = await chatbot.end_session(session.session_id)
        
        assert result is True

    async def test_rate_response(self, chatbot):
        """Test rating a response."""
        session = await chatbot.create_session(user_id="user-123")
        
        with patch.object(chatbot, "_generate_response") as mock_generate:
            mock_generate.return_value = ChatResponse(
                message_id="msg-to-rate",
                content="Test response",
                sources=[],
                confidence=0.9,
            )
            
            response = await chatbot.send_message(session.session_id, "Test question")
        
        result = await chatbot.rate_response(
            message_id=response.message_id,
            rating=5,
            feedback="Very helpful!",
        )
        
        assert result is True

    async def test_search_knowledge_base(self, chatbot):
        """Test searching the knowledge base."""
        with patch.object(chatbot, "_search_regulations") as mock_search:
            mock_search.return_value = [
                {
                    "regulation": "GDPR",
                    "article": "17",
                    "title": "Right to erasure",
                    "relevance": 0.95,
                },
                {
                    "regulation": "CCPA",
                    "section": "1798.105",
                    "title": "Consumer right to delete",
                    "relevance": 0.88,
                },
            ]
            
            results = await chatbot.search_knowledge_base(
                query="right to delete personal data",
                regulations=["GDPR", "CCPA"],
            )
            
            assert len(results) >= 2


class TestChatSession:
    """Test ChatSession dataclass."""

    def test_session_creation(self):
        """Test creating a session."""
        session = ChatSession(
            session_id="sess-123",
            user_id="user-456",
            created_at=datetime.utcnow(),
            messages=[],
            context={"org": "test"},
        )
        
        assert session.session_id == "sess-123"
        assert session.user_id == "user-456"
        assert len(session.messages) == 0

    def test_session_add_message(self):
        """Test adding message to session."""
        session = ChatSession(
            session_id="sess-123",
            user_id="user-456",
            created_at=datetime.utcnow(),
            messages=[],
            context={},
        )
        
        message = ChatMessage(
            message_id="msg-001",
            role="user",
            content="Test question",
            timestamp=datetime.utcnow(),
        )
        
        session.messages.append(message)
        
        assert len(session.messages) == 1


class TestChatMessage:
    """Test ChatMessage dataclass."""

    def test_message_creation(self):
        """Test creating a message."""
        message = ChatMessage(
            message_id="msg-001",
            role="user",
            content="What is GDPR?",
            timestamp=datetime.utcnow(),
        )
        
        assert message.role == "user"
        assert message.content == "What is GDPR?"

    def test_assistant_message(self):
        """Test creating assistant message."""
        message = ChatMessage(
            message_id="msg-002",
            role="assistant",
            content="GDPR is the General Data Protection Regulation...",
            timestamp=datetime.utcnow(),
            sources=[{"regulation": "GDPR"}],
        )
        
        assert message.role == "assistant"
        assert message.sources is not None


class TestChatResponse:
    """Test ChatResponse dataclass."""

    def test_response_creation(self):
        """Test creating a response."""
        response = ChatResponse(
            message_id="msg-001",
            content="Test answer",
            sources=[{"regulation": "GDPR", "article": "5"}],
            confidence=0.85,
        )
        
        assert response.confidence == 0.85
        assert len(response.sources) == 1

    def test_response_with_follow_ups(self):
        """Test response with follow-up questions."""
        response = ChatResponse(
            message_id="msg-001",
            content="Answer",
            sources=[],
            confidence=0.9,
            follow_up_questions=["Q1?", "Q2?"],
        )
        
        assert len(response.follow_up_questions) == 2

    def test_response_with_code_references(self):
        """Test response with code references."""
        response = ChatResponse(
            message_id="msg-001",
            content="Your code has issues",
            sources=[],
            confidence=0.88,
            code_references=[
                {"file": "main.py", "line": 10, "issue": "Problem"},
            ],
        )
        
        assert len(response.code_references) == 1

    def test_response_to_dict(self):
        """Test converting response to dict."""
        response = ChatResponse(
            message_id="msg-001",
            content="Test",
            sources=[],
            confidence=0.9,
        )
        
        response_dict = response.to_dict()
        
        assert response_dict["message_id"] == "msg-001"
        assert response_dict["confidence"] == 0.9
