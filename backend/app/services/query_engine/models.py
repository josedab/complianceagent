"""Data models for Natural Language Compliance Query Engine."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class QueryIntent(str, Enum):
    """Detected intent of a compliance query."""
    
    COMPLIANCE_STATUS = "compliance_status"
    REGULATION_INFO = "regulation_info"
    CODE_REVIEW = "code_review"
    EVIDENCE_SEARCH = "evidence_search"
    REMEDIATION_GUIDANCE = "remediation_guidance"
    RISK_ASSESSMENT = "risk_assessment"
    POLICY_LOOKUP = "policy_lookup"
    AUDIT_PREP = "audit_prep"
    COMPARISON = "comparison"
    UNKNOWN = "unknown"


class SourceType(str, Enum):
    """Types of sources for answers."""
    
    CODEBASE = "codebase"
    REGULATION = "regulation"
    EVIDENCE = "evidence"
    POLICY = "policy"
    KNOWLEDGE_BASE = "knowledge_base"
    ANALYSIS_RESULT = "analysis_result"


@dataclass
class QueryEntity:
    """An entity extracted from a query."""
    
    entity_type: str  # regulation, framework, file, control, etc.
    value: str
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedQuery:
    """A parsed natural language query."""
    
    id: UUID = field(default_factory=uuid4)
    original_query: str = ""
    normalized_query: str = ""
    intent: QueryIntent = QueryIntent.UNKNOWN
    confidence: float = 0.0
    
    # Extracted entities
    entities: list[QueryEntity] = field(default_factory=list)
    
    # Context
    regulations: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    file_patterns: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    
    # Temporal context
    time_reference: str | None = None  # "last week", "since January", etc.
    
    # Metadata
    parsed_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SourceReference:
    """A reference to a source used in an answer."""
    
    source_type: SourceType
    source_id: str = ""
    title: str = ""
    url: str | None = None
    snippet: str = ""
    relevance_score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryAnswer:
    """An answer to a compliance query."""
    
    id: UUID = field(default_factory=uuid4)
    query_id: UUID | None = None
    
    # Answer content
    answer: str = ""
    summary: str = ""
    confidence: float = 0.0
    
    # Supporting information
    sources: list[SourceReference] = field(default_factory=list)
    related_questions: list[str] = field(default_factory=list)
    action_items: list[str] = field(default_factory=list)
    
    # Context
    codebase_context: dict[str, Any] = field(default_factory=dict)
    regulation_context: dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    generated_at: datetime = field(default_factory=datetime.utcnow)
    model_used: str = ""
    tokens_used: int = 0


@dataclass
class ConversationContext:
    """Context for multi-turn conversations."""
    
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID | None = None
    repository_id: UUID | None = None
    
    # History
    queries: list[ParsedQuery] = field(default_factory=list)
    answers: list[QueryAnswer] = field(default_factory=list)
    
    # Accumulated context
    mentioned_regulations: set[str] = field(default_factory=set)
    mentioned_files: set[str] = field(default_factory=set)
    topic_focus: str | None = None
    
    # Session
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)


# Intent detection patterns
INTENT_PATTERNS: dict[QueryIntent, list[str]] = {
    QueryIntent.COMPLIANCE_STATUS: [
        "are we compliant",
        "compliance status",
        "how compliant",
        "compliance score",
        "compliance level",
        "pass audit",
        "audit ready",
    ],
    QueryIntent.REGULATION_INFO: [
        "what is",
        "explain",
        "tell me about",
        "what does .* require",
        "requirements for",
        "definition of",
        "meaning of",
    ],
    QueryIntent.CODE_REVIEW: [
        "review",
        "check",
        "scan",
        "analyze",
        "find issues",
        "violations in",
        "problems with",
    ],
    QueryIntent.EVIDENCE_SEARCH: [
        "where is evidence",
        "find evidence",
        "show evidence",
        "documentation for",
        "proof of",
        "evidence for",
    ],
    QueryIntent.REMEDIATION_GUIDANCE: [
        "how to fix",
        "how do I",
        "remediate",
        "resolve",
        "address",
        "implement",
        "what should I do",
    ],
    QueryIntent.RISK_ASSESSMENT: [
        "risk",
        "impact",
        "severity",
        "priority",
        "critical",
        "what happens if",
    ],
    QueryIntent.POLICY_LOOKUP: [
        "policy",
        "procedure",
        "guideline",
        "standard",
        "best practice",
    ],
    QueryIntent.AUDIT_PREP: [
        "audit",
        "prepare for",
        "auditor",
        "assessment",
        "certification",
    ],
    QueryIntent.COMPARISON: [
        "difference between",
        "compare",
        "versus",
        "vs",
        "better",
        "which",
    ],
}


# Known regulation patterns for entity extraction
REGULATION_PATTERNS: list[tuple[str, str]] = [
    (r"\bgdpr\b", "GDPR"),
    (r"\bhipaa\b", "HIPAA"),
    (r"\bpci[\s-]?dss\b", "PCI-DSS"),
    (r"\bsoc\s?2\b", "SOC2"),
    (r"\biso\s?27001\b", "ISO27001"),
    (r"\bccpa\b", "CCPA"),
    (r"\bsox\b", "SOX"),
    (r"\beu\s?ai\s?act\b", "EU AI Act"),
    (r"\bnist\b", "NIST"),
    (r"\bfedramp\b", "FedRAMP"),
]
