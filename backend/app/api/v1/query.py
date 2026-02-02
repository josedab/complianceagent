"""API endpoints for Natural Language Compliance Query Engine."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.query_engine import (
    AnswerGenerator,
    QueryParser,
    get_answer_generator,
    get_query_parser,
)


router = APIRouter(prefix="/query", tags=["query"])


# Request/Response Models
class QueryRequest(BaseModel):
    """Request to ask a compliance question."""
    
    query: str = Field(..., min_length=2, max_length=1000)
    organization_id: UUID | None = None
    repository_id: UUID | None = None
    context_id: UUID | None = Field(None, description="For multi-turn conversations")
    codebase_context: dict[str, Any] | None = Field(None, description="Pre-loaded codebase info")


class ParseRequest(BaseModel):
    """Request to parse a query without answering."""
    
    query: str = Field(..., min_length=2, max_length=1000)


class QueryResponse(BaseModel):
    """Response to a compliance query."""
    
    answer_id: UUID
    query_id: UUID
    answer: str
    summary: str
    confidence: float
    sources: list[dict[str, Any]]
    related_questions: list[str]
    action_items: list[str]
    context_id: UUID | None


class ParseResponse(BaseModel):
    """Parsed query response."""
    
    query_id: UUID
    original_query: str
    intent: str
    confidence: float
    regulations: list[str]
    entities: list[dict[str, Any]]
    keywords: list[str]
    clarification_needed: bool
    suggested_clarifications: list[str]


# Query Endpoints
@router.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    """Ask a compliance question in natural language.
    
    Supports questions about:
    - Compliance status ("Are we GDPR compliant?")
    - Regulations ("What does HIPAA Article 164.312 require?")
    - Code review ("Review my authentication code")
    - Remediation ("How do I fix encryption issues?")
    - Evidence ("Where is my SOC2 evidence?")
    - Audit prep ("How do I prepare for an audit?")
    
    Use context_id for multi-turn conversations that remember previous context.
    """
    generator = get_answer_generator()
    
    answer = await generator.answer(
        query=request.query,
        organization_id=request.organization_id,
        repository_id=request.repository_id,
        context_id=request.context_id,
        codebase_context=request.codebase_context,
    )
    
    # Get context ID for continuation
    context_id = None
    if request.context_id:
        context_id = request.context_id
    else:
        context = generator.get_context(answer.query_id)
        if context:
            context_id = context.id
    
    return QueryResponse(
        answer_id=answer.id,
        query_id=answer.query_id,
        answer=answer.answer,
        summary=answer.summary,
        confidence=answer.confidence,
        sources=[
            {
                "type": s.source_type.value,
                "id": s.source_id,
                "title": s.title,
                "snippet": s.snippet,
                "relevance": s.relevance_score,
            }
            for s in answer.sources
        ],
        related_questions=answer.related_questions,
        action_items=answer.action_items,
        context_id=context_id,
    )


@router.post("/parse", response_model=ParseResponse)
async def parse_query(request: ParseRequest):
    """Parse a query to extract intent and entities without generating an answer.
    
    Useful for:
    - Understanding what the system detected in a query
    - Building custom UI based on detected intent
    - Debugging query understanding issues
    """
    parser = get_query_parser()
    parsed = parser.parse(request.query)
    
    clarifications = parser.suggest_clarifications(parsed)
    
    return ParseResponse(
        query_id=parsed.id,
        original_query=parsed.original_query,
        intent=parsed.intent.value,
        confidence=parsed.confidence,
        regulations=parsed.regulations,
        entities=[
            {
                "type": e.entity_type,
                "value": e.value,
                "confidence": e.confidence,
            }
            for e in parsed.entities
        ],
        keywords=parsed.keywords,
        clarification_needed=len(clarifications) > 0,
        suggested_clarifications=clarifications,
    )


@router.get("/context/{context_id}")
async def get_conversation_context(context_id: UUID):
    """Get conversation context for multi-turn interactions."""
    generator = get_answer_generator()
    context = generator.get_context(context_id)
    
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    
    return {
        "context_id": str(context.id),
        "organization_id": str(context.organization_id) if context.organization_id else None,
        "repository_id": str(context.repository_id) if context.repository_id else None,
        "turns": len(context.queries),
        "mentioned_regulations": list(context.mentioned_regulations),
        "mentioned_files": list(context.mentioned_files),
        "topic_focus": context.topic_focus,
        "created_at": context.created_at.isoformat(),
        "last_activity": context.last_activity.isoformat(),
        "history": [
            {
                "query": q.original_query,
                "intent": q.intent.value,
                "answer_summary": a.summary if i < len(context.answers) else None,
            }
            for i, (q, a) in enumerate(zip(context.queries, context.answers))
        ],
    }


@router.post("/suggest")
async def suggest_questions(
    organization_id: UUID | None = None,
    context_id: UUID | None = None,
):
    """Suggest relevant compliance questions.
    
    Provides contextual suggestions based on:
    - Organization's compliance profile
    - Previous conversation context
    - Common compliance questions
    """
    generator = get_answer_generator()
    
    suggestions = [
        {
            "category": "Compliance Status",
            "questions": [
                "What is my current compliance status?",
                "Are there any critical compliance issues?",
                "Which regulations am I closest to meeting?",
            ],
        },
        {
            "category": "Regulations",
            "questions": [
                "What is GDPR and does it apply to me?",
                "Explain HIPAA requirements for software",
                "What are the SOC2 trust criteria?",
            ],
        },
        {
            "category": "Remediation",
            "questions": [
                "How do I implement encryption at rest?",
                "What's needed for proper audit logging?",
                "How do I set up access controls?",
            ],
        },
        {
            "category": "Audit Preparation",
            "questions": [
                "How do I prepare for a SOC2 audit?",
                "What evidence do I need for HIPAA?",
                "Create an audit readiness checklist",
            ],
        },
    ]
    
    # Add context-specific suggestions
    if context_id:
        context = generator.get_context(context_id)
        if context and context.mentioned_regulations:
            regs = list(context.mentioned_regulations)[:3]
            suggestions.insert(0, {
                "category": "Continue Conversation",
                "questions": [
                    f"Tell me more about {regs[0]}" if regs else "Continue",
                    "What are the compliance gaps?",
                    "Show me evidence for this",
                ],
            })
    
    return {"suggestions": suggestions}


@router.get("/intents")
async def list_supported_intents():
    """List all supported query intents."""
    from app.services.query_engine.models import QueryIntent
    
    intents = [
        {
            "intent": QueryIntent.COMPLIANCE_STATUS.value,
            "description": "Check compliance status and scores",
            "examples": ["Are we compliant?", "What's our compliance score?"],
        },
        {
            "intent": QueryIntent.REGULATION_INFO.value,
            "description": "Get information about regulations",
            "examples": ["What is GDPR?", "Explain HIPAA requirements"],
        },
        {
            "intent": QueryIntent.CODE_REVIEW.value,
            "description": "Review code for compliance issues",
            "examples": ["Review my authentication code", "Scan for violations"],
        },
        {
            "intent": QueryIntent.EVIDENCE_SEARCH.value,
            "description": "Find compliance evidence",
            "examples": ["Where is my SOC2 evidence?", "Find encryption documentation"],
        },
        {
            "intent": QueryIntent.REMEDIATION_GUIDANCE.value,
            "description": "Get help fixing compliance issues",
            "examples": ["How do I fix this?", "Implement encryption"],
        },
        {
            "intent": QueryIntent.RISK_ASSESSMENT.value,
            "description": "Assess compliance risks",
            "examples": ["What are the risks?", "Impact of this issue"],
        },
        {
            "intent": QueryIntent.POLICY_LOOKUP.value,
            "description": "Look up policies and procedures",
            "examples": ["Show security policy", "Access control guidelines"],
        },
        {
            "intent": QueryIntent.AUDIT_PREP.value,
            "description": "Prepare for compliance audits",
            "examples": ["Prepare for SOC2 audit", "Audit checklist"],
        },
        {
            "intent": QueryIntent.COMPARISON.value,
            "description": "Compare regulations or frameworks",
            "examples": ["Compare GDPR and CCPA", "SOC2 vs ISO27001"],
        },
    ]
    
    return {"intents": intents}


# Natural Language Query Session Endpoints
class NLQueryRequest(BaseModel):
    """Request for natural language compliance query."""
    
    query: str = Field(..., min_length=2, max_length=2000)
    session_id: UUID | None = None
    codebase_context: dict[str, Any] | None = None
    compliance_data: dict[str, Any] | None = None


class CreateNLSessionRequest(BaseModel):
    """Request to create an NL query session."""
    
    organization_id: UUID | None = None
    user_id: str = ""
    initial_context: dict[str, Any] | None = None


@router.post("/nl/sessions")
async def create_nl_session(request: CreateNLSessionRequest):
    """Create a new natural language query session.
    
    Sessions maintain conversation context across multiple queries,
    allowing for follow-up questions and contextual answers.
    """
    from app.services.query_engine import get_nl_query_engine
    
    engine = get_nl_query_engine()
    session = engine.create_session(
        organization_id=request.organization_id,
        user_id=request.user_id,
        initial_context=request.initial_context,
    )
    
    return {
        "session_id": str(session.id),
        "organization_id": str(session.organization_id) if session.organization_id else None,
        "user_id": session.user_id,
        "created_at": session.created_at.isoformat(),
    }


@router.post("/nl/query")
async def nl_query(request: NLQueryRequest):
    """Execute a natural language compliance query.
    
    Supports queries like:
    - "Show me all GDPR violations in our user service"
    - "What files handle personal data?"
    - "Explain HIPAA Article 164.312 requirements"
    - "Are we compliant with PCI-DSS?"
    - "How do I fix consent management issues?"
    - "What is our compliance score for GDPR?"
    
    Provide session_id for conversational context across queries.
    """
    from app.services.query_engine import get_nl_query_engine
    
    engine = get_nl_query_engine()
    
    result = await engine.query(
        query_text=request.query,
        session_id=request.session_id,
        codebase_context=request.codebase_context,
        compliance_data=request.compliance_data,
    )
    
    return {
        "result_id": str(result.id),
        "query_id": str(result.query_id),
        "answer": result.answer,
        "summary": result.summary,
        "confidence": result.confidence,
        "violations": result.violations[:20],
        "affected_files": result.affected_files[:20],
        "requirements": result.requirements[:10],
        "recommendations": result.recommendations[:10],
        "citations": result.citations,
        "sources_used": result.sources_used,
        "execution_time_ms": result.execution_time_ms,
    }


@router.get("/nl/sessions/{session_id}")
async def get_nl_session(session_id: UUID):
    """Get a natural language query session."""
    from app.services.query_engine import get_nl_query_engine
    
    engine = get_nl_query_engine()
    session = engine.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": str(session.id),
        "organization_id": str(session.organization_id) if session.organization_id else None,
        "user_id": session.user_id,
        "query_count": len(session.queries),
        "active_regulations": session.active_regulations,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "history": [
            {
                "query": q.original_query,
                "intent": q.intent.value,
                "confidence": q.confidence,
                "answer_summary": session.results[i].summary if i < len(session.results) else None,
            }
            for i, q in enumerate(session.queries)
        ],
    }


@router.get("/nl/suggestions")
async def get_query_suggestions(
    partial_query: str = "",
    session_id: UUID | None = None,
):
    """Get query suggestions based on partial input.
    
    Provides autocomplete suggestions for compliance queries.
    """
    from app.services.query_engine import get_nl_query_engine
    
    engine = get_nl_query_engine()
    suggestions = await engine.get_query_suggestions(
        partial_query=partial_query,
        session_id=session_id,
    )
    
    return {"suggestions": suggestions}
