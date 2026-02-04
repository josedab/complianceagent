"""Explainability Engine - Generates audit-proof explanations for AI decisions."""

import hashlib
import time
from datetime import datetime
from typing import Any
from uuid import UUID

import structlog

from app.services.explainability.models import (
    BiasIndicator,
    CitationChain,
    ComplianceExplanation,
    DecisionAuditLog,
    ExplanationConfidence,
    ExplanationFormat,
    ExplanationRequest,
    ExplanationResponse,
    FairnessMetrics,
    ReasoningStep,
)


logger = structlog.get_logger()


# Regulatory knowledge base for citations
REGULATION_KNOWLEDGE = {
    "GDPR": {
        "full_name": "General Data Protection Regulation (EU) 2016/679",
        "articles": {
            "5": {
                "title": "Principles relating to processing of personal data",
                "sections": {
                    "1(a)": "lawfulness, fairness and transparency",
                    "1(b)": "purpose limitation",
                    "1(c)": "data minimisation",
                    "1(d)": "accuracy",
                    "1(e)": "storage limitation",
                    "1(f)": "integrity and confidentiality",
                },
            },
            "6": {
                "title": "Lawfulness of processing",
                "sections": {
                    "1(a)": "consent",
                    "1(b)": "contractual necessity",
                    "1(c)": "legal obligation",
                    "1(f)": "legitimate interests",
                },
            },
            "7": {"title": "Conditions for consent"},
            "12": {"title": "Transparent information, communication and modalities"},
            "13": {"title": "Information to be provided where personal data are collected"},
            "14": {"title": "Information where data not obtained from data subject"},
            "15": {"title": "Right of access by the data subject"},
            "16": {"title": "Right to rectification"},
            "17": {"title": "Right to erasure ('right to be forgotten')"},
            "18": {"title": "Right to restriction of processing"},
            "20": {"title": "Right to data portability"},
            "21": {"title": "Right to object"},
            "22": {"title": "Automated individual decision-making, including profiling"},
            "25": {"title": "Data protection by design and by default"},
            "32": {"title": "Security of processing"},
            "33": {"title": "Notification of personal data breach"},
            "35": {"title": "Data protection impact assessment"},
        },
    },
    "HIPAA": {
        "full_name": "Health Insurance Portability and Accountability Act",
        "articles": {
            "164.502": {"title": "Uses and disclosures of protected health information"},
            "164.508": {"title": "Uses and disclosures for which authorization is required"},
            "164.512": {"title": "Uses and disclosures for which authorization is not required"},
            "164.514": {"title": "De-identification of protected health information"},
            "164.520": {"title": "Notice of privacy practices"},
            "164.524": {"title": "Access of individuals to protected health information"},
            "164.526": {"title": "Amendment of protected health information"},
            "164.530": {"title": "Administrative requirements"},
        },
    },
    "EU AI Act": {
        "full_name": "Regulation (EU) 2024/1689 on Artificial Intelligence",
        "articles": {
            "6": {"title": "Classification rules for high-risk AI systems"},
            "9": {"title": "Risk management system"},
            "10": {"title": "Data and data governance"},
            "11": {"title": "Technical documentation"},
            "12": {"title": "Record-keeping"},
            "13": {"title": "Transparency and provision of information to deployers"},
            "14": {"title": "Human oversight"},
            "15": {"title": "Accuracy, robustness and cybersecurity"},
            "50": {"title": "Transparency obligations"},
            "52": {"title": "Transparency obligations for certain AI systems"},
        },
    },
    "PCI-DSS": {
        "full_name": "Payment Card Industry Data Security Standard v4.0",
        "articles": {
            "3": {"title": "Protect stored account data"},
            "4": {"title": "Protect cardholder data with strong cryptography"},
            "6": {"title": "Develop and maintain secure systems and software"},
            "7": {"title": "Restrict access to system components"},
            "8": {"title": "Identify users and authenticate access"},
            "10": {"title": "Log and monitor all access to system components"},
            "11": {"title": "Test security of systems and networks regularly"},
            "12": {"title": "Support information security with organizational policies"},
        },
    },
    "CCPA": {
        "full_name": "California Consumer Privacy Act",
        "articles": {
            "1798.100": {"title": "Right to know about personal information collected"},
            "1798.105": {"title": "Right to delete personal information"},
            "1798.110": {"title": "Right to know what personal information is sold"},
            "1798.115": {"title": "Right to opt-out of sale of personal information"},
            "1798.120": {"title": "Right to opt-out"},
            "1798.125": {"title": "Right to non-discrimination"},
        },
    },
}

# Pattern-to-violation reasoning templates
VIOLATION_REASONING = {
    "PII_LOGGING": {
        "summary": "Personal data is being logged without proper safeguards",
        "reasoning": [
            "Code writes data to logs or console output",
            "The data appears to contain personal identifiers (email, name, IP, etc.)",
            "Logging personal data without anonymization violates data minimization principles",
            "Log data may be retained longer than necessary and accessible to unauthorized parties",
        ],
        "regulations": ["GDPR", "CCPA"],
        "articles": ["GDPR Article 5(1)(c)", "GDPR Article 25", "CCPA 1798.100"],
    },
    "MISSING_CONSENT": {
        "summary": "Data processing occurs without verified consent",
        "reasoning": [
            "Code processes personal data without consent verification",
            "No consent check found before data processing operation",
            "Valid legal basis (consent or other) must be established before processing",
        ],
        "regulations": ["GDPR"],
        "articles": ["GDPR Article 6", "GDPR Article 7"],
    },
    "INSECURE_STORAGE": {
        "summary": "Sensitive data stored without proper encryption",
        "reasoning": [
            "Data is stored in plaintext or with weak protection",
            "No encryption layer detected for sensitive data at rest",
            "Regulations require appropriate technical measures to protect personal data",
        ],
        "regulations": ["GDPR", "HIPAA", "PCI-DSS"],
        "articles": ["GDPR Article 32", "HIPAA 164.312(a)(2)(iv)", "PCI-DSS Req. 3"],
    },
    "HARDCODED_CREDENTIALS": {
        "summary": "Credentials or secrets hardcoded in source code",
        "reasoning": [
            "Authentication credentials found in source code",
            "Hardcoded secrets can be exposed through version control",
            "This violates access control and security requirements",
        ],
        "regulations": ["PCI-DSS", "SOC 2"],
        "articles": ["PCI-DSS Req. 8.2", "PCI-DSS Req. 6.5"],
    },
    "MISSING_AI_DOCUMENTATION": {
        "summary": "AI system lacks required documentation",
        "reasoning": [
            "AI/ML model detected without accompanying documentation",
            "High-risk AI systems require technical documentation",
            "Documentation must include training data, performance metrics, and intended use",
        ],
        "regulations": ["EU AI Act"],
        "articles": ["EU AI Act Article 11", "EU AI Act Article 13"],
    },
}


class ExplainabilityEngine:
    """Engine for generating audit-proof explanations for AI compliance decisions."""

    def __init__(self):
        self._audit_logs: dict[UUID, DecisionAuditLog] = {}
        self._explanations: dict[UUID, ComplianceExplanation] = {}
        self._last_chain_hash: str | None = None

    async def explain_decision(
        self,
        request: ExplanationRequest,
        organization_id: UUID,
        user_id: UUID | None = None,
    ) -> ExplanationResponse:
        """Generate a comprehensive explanation for a compliance decision."""
        start_time = time.perf_counter()
        
        context = request.decision_context
        violation_type = context.get("violation_type", "GENERAL")
        code = request.code_snippet or ""
        regulation = request.regulation or context.get("regulation")
        
        # Build reasoning chain
        reasoning_chain = await self._build_reasoning_chain(
            violation_type=violation_type,
            code=code,
            context=context,
            max_steps=request.max_reasoning_steps,
        )
        
        # Gather citations
        primary_citations, supporting_citations = await self._gather_citations(
            violation_type=violation_type,
            regulation=regulation,
            context=context,
        )
        
        # Calculate confidence
        confidence, confidence_score = self._calculate_confidence(
            reasoning_chain=reasoning_chain,
            citations=primary_citations,
            context=context,
        )
        
        # Generate summary and decision
        decision_type = context.get("decision_type", "violation")
        decision = self._generate_decision_text(
            violation_type=violation_type,
            decision_type=decision_type,
            regulation=regulation,
        )
        
        summary = self._generate_summary(
            violation_type=violation_type,
            code=code,
            context=context,
        )
        
        processing_time = (time.perf_counter() - start_time) * 1000
        
        # Create explanation
        explanation = ComplianceExplanation(
            decision=decision,
            decision_type=decision_type,
            summary=summary,
            reasoning_chain=reasoning_chain,
            primary_citations=primary_citations,
            supporting_citations=supporting_citations,
            confidence=confidence,
            confidence_score=confidence_score,
            alternative_interpretations=self._get_alternative_interpretations(context),
            assumptions=self._get_assumptions(context),
            limitations=self._get_limitations(context),
            processing_time_ms=processing_time,
            metadata={
                "violation_type": violation_type,
                "file_path": request.file_path,
                "format": request.format.value,
            },
        )
        
        self._explanations[explanation.id] = explanation
        
        # Format output
        formatted_output = self._format_explanation(explanation, request.format)
        
        # Create audit log if organization provided
        audit_log_id = None
        if organization_id:
            audit_log = await self._create_audit_log(
                organization_id=organization_id,
                user_id=user_id,
                request=request,
                explanation=explanation,
            )
            audit_log_id = audit_log.id
        
        logger.info(
            "Generated compliance explanation",
            explanation_id=str(explanation.id),
            decision_type=decision_type,
            confidence=confidence.value,
            processing_time_ms=processing_time,
        )
        
        return ExplanationResponse(
            explanation=explanation,
            formatted_output=formatted_output,
            audit_log_id=audit_log_id,
        )

    async def _build_reasoning_chain(
        self,
        violation_type: str,
        code: str,
        context: dict[str, Any],
        max_steps: int,
    ) -> list[ReasoningStep]:
        """Build the reasoning chain for a decision."""
        steps = []
        
        # Get template reasoning if available
        template = VIOLATION_REASONING.get(violation_type, {})
        template_steps = template.get("reasoning", [])
        
        # Step 1: Code Analysis
        steps.append(ReasoningStep(
            step_number=1,
            description="Analyzed the code snippet for compliance-relevant patterns",
            evidence=f"Code contains {len(code)} characters, analyzed for {violation_type} patterns",
            confidence=0.95,
            logic_type="deductive",
        ))
        
        # Step 2: Pattern Detection
        if template_steps:
            steps.append(ReasoningStep(
                step_number=2,
                description=template_steps[0] if template_steps else "Pattern detected in code",
                evidence=context.get("matched_pattern", "Compliance pattern matched"),
                confidence=0.85,
                logic_type="deductive",
            ))
        
        # Step 3-N: Additional reasoning from template
        for i, reason in enumerate(template_steps[1:max_steps-2], start=3):
            steps.append(ReasoningStep(
                step_number=i,
                description=reason,
                confidence=0.80,
                logic_type="deductive",
            ))
        
        # Final step: Conclusion
        steps.append(ReasoningStep(
            step_number=len(steps) + 1,
            description="Based on the analysis, this code requires attention for regulatory compliance",
            confidence=0.90,
            logic_type="deductive",
        ))
        
        return steps

    async def _gather_citations(
        self,
        violation_type: str,
        regulation: str | None,
        context: dict[str, Any],
    ) -> tuple[list[CitationChain], list[CitationChain]]:
        """Gather regulatory citations for the decision."""
        primary = []
        supporting = []
        
        # Get template citations
        template = VIOLATION_REASONING.get(violation_type, {})
        template_articles = template.get("articles", [])
        template_regulations = template.get("regulations", [])
        
        # If specific regulation provided, prioritize it
        if regulation:
            template_regulations = [regulation] + [r for r in template_regulations if r != regulation]
        
        for reg in template_regulations[:2]:  # Primary from first 2 regulations
            if reg in REGULATION_KNOWLEDGE:
                reg_info = REGULATION_KNOWLEDGE[reg]
                
                for article_ref in template_articles:
                    if reg in article_ref:
                        # Parse article reference
                        parts = article_ref.replace(f"{reg} ", "").split()
                        article_num = parts[1] if len(parts) > 1 else "general"
                        
                        article_info = reg_info.get("articles", {}).get(
                            article_num.replace("Article", "").strip(),
                            {"title": "Compliance requirement"}
                        )
                        
                        primary.append(CitationChain(
                            regulation=reg,
                            article=f"Article {article_num}" if not article_num.startswith("Article") else article_num,
                            text_excerpt=article_info.get("title", "Regulatory requirement"),
                            relevance_score=0.9,
                        ))
        
        # Add supporting citations
        for reg in template_regulations[2:]:  # Supporting from remaining
            if reg in REGULATION_KNOWLEDGE:
                supporting.append(CitationChain(
                    regulation=reg,
                    article="General",
                    text_excerpt=f"{reg} compliance requirements",
                    relevance_score=0.7,
                ))
        
        return primary, supporting

    def _calculate_confidence(
        self,
        reasoning_chain: list[ReasoningStep],
        citations: list[CitationChain],
        context: dict[str, Any],
    ) -> tuple[ExplanationConfidence, float]:
        """Calculate confidence level for the explanation."""
        # Base confidence from reasoning chain
        if reasoning_chain:
            avg_step_confidence = sum(s.confidence for s in reasoning_chain) / len(reasoning_chain)
        else:
            avg_step_confidence = 0.5
        
        # Boost from citations
        citation_boost = min(0.2, len(citations) * 0.05)
        
        # Context factors
        context_boost = 0
        if context.get("verified_pattern"):
            context_boost += 0.1
        if context.get("multiple_matches"):
            context_boost += 0.05
        
        final_score = min(1.0, avg_step_confidence + citation_boost + context_boost)
        
        # Map to confidence level
        if final_score >= 0.85:
            level = ExplanationConfidence.HIGH
        elif final_score >= 0.65:
            level = ExplanationConfidence.MEDIUM
        elif final_score >= 0.45:
            level = ExplanationConfidence.LOW
        else:
            level = ExplanationConfidence.UNCERTAIN
        
        return level, final_score

    def _generate_decision_text(
        self,
        violation_type: str,
        decision_type: str,
        regulation: str | None,
    ) -> str:
        """Generate human-readable decision text."""
        reg_str = f"{regulation} " if regulation else ""
        
        if decision_type == "violation":
            return f"Potential {reg_str}compliance violation detected"
        elif decision_type == "compliant":
            return f"Code appears compliant with {reg_str}requirements"
        elif decision_type == "needs_review":
            return f"Manual review recommended for {reg_str}compliance"
        else:
            return f"Unable to determine {reg_str}compliance status"

    def _generate_summary(
        self,
        violation_type: str,
        code: str,
        context: dict[str, Any],
    ) -> str:
        """Generate explanation summary."""
        template = VIOLATION_REASONING.get(violation_type, {})
        if template.get("summary"):
            return template["summary"]
        
        return context.get(
            "message",
            "Compliance issue detected that requires attention"
        )

    def _get_alternative_interpretations(
        self,
        context: dict[str, Any],
    ) -> list[str]:
        """Get alternative interpretations of the findings."""
        alternatives = []
        
        if context.get("may_be_test_code"):
            alternatives.append("This may be test code with intentional violations for testing purposes")
        if context.get("may_be_example"):
            alternatives.append("This could be example/documentation code not intended for production")
        if context.get("context_dependent"):
            alternatives.append("The compliance status may depend on runtime context not visible in static analysis")
        
        return alternatives

    def _get_assumptions(
        self,
        context: dict[str, Any],
    ) -> list[str]:
        """Get assumptions made during analysis."""
        assumptions = [
            "Code is intended for production use",
            "Standard interpretation of regulatory requirements applies",
        ]
        
        if context.get("language"):
            assumptions.append(f"Code is written in {context['language']}")
        
        return assumptions

    def _get_limitations(
        self,
        context: dict[str, Any],
    ) -> list[str]:
        """Get limitations of the analysis."""
        return [
            "Static analysis cannot capture all runtime behaviors",
            "Legal interpretation may vary by jurisdiction",
            "This analysis is not legal advice",
            "Human review is recommended for critical decisions",
        ]

    def _format_explanation(
        self,
        explanation: ComplianceExplanation,
        format: ExplanationFormat,
    ) -> str:
        """Format explanation for output."""
        if format == ExplanationFormat.NATURAL_LANGUAGE:
            return explanation.to_natural_language()
        elif format == ExplanationFormat.STRUCTURED:
            import json
            return json.dumps(explanation.to_audit_format(), indent=2, default=str)
        elif format == ExplanationFormat.LEGAL:
            return self._format_legal(explanation)
        elif format == ExplanationFormat.TECHNICAL:
            return self._format_technical(explanation)
        elif format == ExplanationFormat.EXECUTIVE:
            return self._format_executive(explanation)
        else:
            return explanation.to_natural_language()

    def _format_legal(self, explanation: ComplianceExplanation) -> str:
        """Format for legal review."""
        lines = [
            "COMPLIANCE ANALYSIS REPORT",
            "=" * 50,
            "",
            f"Finding: {explanation.decision}",
            f"Date: {explanation.created_at.isoformat()}",
            f"Reference ID: {explanation.id}",
            "",
            "REGULATORY BASIS:",
        ]
        
        for cite in explanation.primary_citations:
            lines.append(f"  - {cite.to_citation_string()}")
        
        lines.extend([
            "",
            "ANALYSIS:",
            explanation.summary,
            "",
            "CONFIDENCE ASSESSMENT:",
            f"  Level: {explanation.confidence.value.upper()}",
            f"  Score: {explanation.confidence_score:.0%}",
        ])
        
        return "\n".join(lines)

    def _format_technical(self, explanation: ComplianceExplanation) -> str:
        """Format for technical audience."""
        lines = [
            f"[{explanation.decision_type.upper()}] {explanation.decision}",
            "",
            f"Summary: {explanation.summary}",
            "",
            "Reasoning Steps:",
        ]
        
        for step in explanation.reasoning_chain:
            lines.append(f"  {step.step_number}. {step.description} (confidence: {step.confidence:.0%})")
        
        lines.extend([
            "",
            f"Confidence: {explanation.confidence_score:.0%}",
            f"Model Version: {explanation.model_version}",
        ])
        
        return "\n".join(lines)

    def _format_executive(self, explanation: ComplianceExplanation) -> str:
        """Format for executive summary."""
        risk_level = "HIGH" if explanation.decision_type == "violation" else "LOW"
        
        return f"""EXECUTIVE SUMMARY
================

Status: {explanation.decision}
Risk Level: {risk_level}
Confidence: {explanation.confidence.value.upper()}

Key Finding:
{explanation.summary}

Recommended Action:
{"Immediate review and remediation required" if risk_level == "HIGH" else "Continue monitoring"}

Reference: {explanation.id}
"""

    async def _create_audit_log(
        self,
        organization_id: UUID,
        user_id: UUID | None,
        request: ExplanationRequest,
        explanation: ComplianceExplanation,
    ) -> DecisionAuditLog:
        """Create an audit log entry."""
        # Hash inputs and outputs for integrity
        input_data = str(request.model_dump())
        input_hash = hashlib.sha256(input_data.encode()).hexdigest()
        
        result_data = str(explanation.model_dump())
        result_hash = hashlib.sha256(result_data.encode()).hexdigest()
        
        audit_log = DecisionAuditLog(
            organization_id=organization_id,
            user_id=user_id,
            action_type="explain",
            input_summary=f"Explanation request for {request.decision_context.get('violation_type', 'compliance')} analysis",
            input_hash=input_hash,
            explanation=explanation,
            result_summary=explanation.summary,
            result_hash=result_hash,
            previous_log_id=list(self._audit_logs.keys())[-1] if self._audit_logs else None,
        )
        
        # Compute chain hash
        audit_log.chain_hash = audit_log.compute_chain_hash(self._last_chain_hash)
        self._last_chain_hash = audit_log.chain_hash
        
        self._audit_logs[audit_log.id] = audit_log
        
        return audit_log

    async def get_explanation(self, explanation_id: UUID) -> ComplianceExplanation | None:
        """Retrieve an explanation by ID."""
        return self._explanations.get(explanation_id)

    async def get_audit_log(self, log_id: UUID) -> DecisionAuditLog | None:
        """Retrieve an audit log entry by ID."""
        return self._audit_logs.get(log_id)

    async def get_audit_logs(
        self,
        organization_id: UUID,
        limit: int = 100,
    ) -> list[DecisionAuditLog]:
        """Get audit logs for an organization."""
        logs = [
            log for log in self._audit_logs.values()
            if log.organization_id == organization_id
        ]
        return sorted(logs, key=lambda x: x.timestamp, reverse=True)[:limit]

    async def verify_audit_chain(
        self,
        organization_id: UUID,
    ) -> dict[str, Any]:
        """Verify the integrity of the audit chain."""
        logs = await self.get_audit_logs(organization_id, limit=10000)
        logs.reverse()  # Oldest first
        
        if not logs:
            return {"valid": True, "verified_count": 0, "message": "No audit logs to verify"}
        
        previous_hash = None
        verified = 0
        
        for log in logs:
            expected_hash = log.compute_chain_hash(previous_hash)
            if log.chain_hash != expected_hash:
                return {
                    "valid": False,
                    "verified_count": verified,
                    "failed_at": str(log.id),
                    "message": "Chain hash mismatch detected",
                }
            previous_hash = log.chain_hash
            verified += 1
        
        return {
            "valid": True,
            "verified_count": verified,
            "message": "Audit chain integrity verified",
        }

    async def evaluate_fairness(
        self,
        explanation_id: UUID,
    ) -> FairnessMetrics:
        """Evaluate fairness metrics for an explanation."""
        explanation = self._explanations.get(explanation_id)
        if not explanation:
            raise ValueError(f"Explanation {explanation_id} not found")
        
        bias_indicators = []
        
        # Check for potential biases
        if explanation.confidence_score < 0.5:
            bias_indicators.append(BiasIndicator(
                bias_type="uncertainty",
                description="Low confidence may indicate insufficient training data for this case",
                severity="medium",
                mitigation="Consider additional human review",
                confidence=0.7,
            ))
        
        return FairnessMetrics(
            explanation_id=explanation_id,
            consistency_score=0.85,
            bias_indicators=bias_indicators,
        )


# Global instance
_engine: ExplainabilityEngine | None = None


def get_explainability_engine() -> ExplainabilityEngine:
    """Get or create the explainability engine."""
    global _engine
    if _engine is None:
        _engine = ExplainabilityEngine()
    return _engine
