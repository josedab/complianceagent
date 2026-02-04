"""Models for AI Explainability Layer."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ExplanationFormat(str, Enum):
    """Output format for explanations."""
    
    NATURAL_LANGUAGE = "natural_language"
    STRUCTURED = "structured"
    LEGAL = "legal"
    TECHNICAL = "technical"
    EXECUTIVE = "executive"


class ExplanationConfidence(str, Enum):
    """Confidence level for explanations."""
    
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"


class CitationChain(BaseModel):
    """Chain of regulatory citations supporting a decision."""
    
    id: UUID = Field(default_factory=uuid4)
    regulation: str
    article: str
    section: str | None = None
    paragraph: str | None = None
    text_excerpt: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    url: str | None = None
    effective_date: datetime | None = None
    
    def to_citation_string(self) -> str:
        """Format as a citation string."""
        parts = [self.regulation, self.article]
        if self.section:
            parts.append(f"Section {self.section}")
        if self.paragraph:
            parts.append(f"Para. {self.paragraph}")
        return ", ".join(parts)


class ReasoningStep(BaseModel):
    """A single step in the reasoning chain."""
    
    step_number: int
    description: str
    evidence: str | None = None
    citations: list[CitationChain] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    logic_type: str = "deductive"  # deductive, inductive, abductive
    
    def to_natural_language(self) -> str:
        """Convert to natural language explanation."""
        text = f"Step {self.step_number}: {self.description}"
        if self.evidence:
            text += f"\n  Evidence: {self.evidence}"
        if self.citations:
            cites = ", ".join(c.to_citation_string() for c in self.citations)
            text += f"\n  Based on: {cites}"
        return text


class ComplianceExplanation(BaseModel):
    """Complete explanation for a compliance decision."""
    
    id: UUID = Field(default_factory=uuid4)
    decision: str
    decision_type: str  # violation, compliant, needs_review, uncertain
    summary: str
    reasoning_chain: list[ReasoningStep] = Field(default_factory=list)
    primary_citations: list[CitationChain] = Field(default_factory=list)
    supporting_citations: list[CitationChain] = Field(default_factory=list)
    confidence: ExplanationConfidence = ExplanationConfidence.MEDIUM
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.5)
    alternative_interpretations: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    model_version: str = "1.0.0"
    processing_time_ms: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    def to_natural_language(self) -> str:
        """Convert entire explanation to natural language."""
        lines = [
            f"## Decision: {self.decision}",
            "",
            f"**Summary:** {self.summary}",
            "",
            "### Reasoning",
        ]
        
        for step in self.reasoning_chain:
            lines.append(step.to_natural_language())
            lines.append("")
        
        if self.primary_citations:
            lines.append("### Primary Regulatory Basis")
            for cite in self.primary_citations:
                lines.append(f"- {cite.to_citation_string()}")
                lines.append(f"  \"{cite.text_excerpt[:200]}...\"")
            lines.append("")
        
        if self.assumptions:
            lines.append("### Assumptions Made")
            for assumption in self.assumptions:
                lines.append(f"- {assumption}")
            lines.append("")
        
        if self.limitations:
            lines.append("### Limitations")
            for limitation in self.limitations:
                lines.append(f"- {limitation}")
            lines.append("")
        
        lines.append(f"**Confidence:** {self.confidence.value} ({self.confidence_score:.0%})")
        
        return "\n".join(lines)
    
    def to_audit_format(self) -> dict[str, Any]:
        """Convert to audit-ready format."""
        return {
            "explanation_id": str(self.id),
            "timestamp": self.created_at.isoformat(),
            "decision": self.decision,
            "decision_type": self.decision_type,
            "summary": self.summary,
            "confidence": {
                "level": self.confidence.value,
                "score": self.confidence_score,
            },
            "reasoning_chain": [
                {
                    "step": s.step_number,
                    "description": s.description,
                    "evidence": s.evidence,
                    "citations": [c.model_dump() for c in s.citations],
                    "confidence": s.confidence,
                }
                for s in self.reasoning_chain
            ],
            "regulatory_basis": {
                "primary": [c.model_dump() for c in self.primary_citations],
                "supporting": [c.model_dump() for c in self.supporting_citations],
            },
            "assumptions": self.assumptions,
            "limitations": self.limitations,
            "alternative_interpretations": self.alternative_interpretations,
            "model_info": {
                "version": self.model_version,
                "processing_time_ms": self.processing_time_ms,
            },
            "metadata": self.metadata,
        }


class DecisionAuditLog(BaseModel):
    """Audit log entry for an AI compliance decision."""
    
    id: UUID = Field(default_factory=uuid4)
    organization_id: UUID
    user_id: UUID | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action_type: str  # analyze, generate, validate, recommend
    input_summary: str
    input_hash: str
    explanation: ComplianceExplanation
    result_summary: str
    result_hash: str
    approval_status: str | None = None  # pending, approved, rejected
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    reviewer_notes: str | None = None
    chain_hash: str | None = None  # For tamper-proof audit chain
    previous_log_id: UUID | None = None
    
    def compute_chain_hash(self, previous_hash: str | None = None) -> str:
        """Compute tamper-proof chain hash."""
        import hashlib
        
        data = f"{self.id}:{self.timestamp.isoformat()}:{self.input_hash}:{self.result_hash}"
        if previous_hash:
            data = f"{previous_hash}:{data}"
        return hashlib.sha256(data.encode()).hexdigest()


class BiasIndicator(BaseModel):
    """Indicator of potential bias in AI decision."""
    
    bias_type: str  # demographic, historical, sampling, confirmation
    description: str
    severity: str  # low, medium, high
    mitigation: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)


class FairnessMetrics(BaseModel):
    """Fairness metrics for AI compliance decisions."""
    
    explanation_id: UUID
    demographic_parity: float | None = None
    equalized_odds: float | None = None
    calibration_score: float | None = None
    consistency_score: float = Field(ge=0.0, le=1.0)
    bias_indicators: list[BiasIndicator] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)


class ExplanationRequest(BaseModel):
    """Request for generating an explanation."""
    
    decision_context: dict[str, Any]
    code_snippet: str | None = None
    file_path: str | None = None
    regulation: str | None = None
    format: ExplanationFormat = ExplanationFormat.NATURAL_LANGUAGE
    detail_level: str = "standard"  # minimal, standard, detailed, exhaustive
    include_alternatives: bool = False
    include_citations: bool = True
    max_reasoning_steps: int = 10


class ExplanationResponse(BaseModel):
    """Response containing explanation."""
    
    explanation: ComplianceExplanation
    formatted_output: str
    audit_log_id: UUID | None = None
    warnings: list[str] = Field(default_factory=list)
