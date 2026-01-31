"""Answer Generator - Generates answers to compliance queries using AI and context."""

import time
from typing import Any
from uuid import UUID

import structlog

from app.services.query_engine.models import (
    ConversationContext,
    ParsedQuery,
    QueryAnswer,
    QueryIntent,
    SourceReference,
    SourceType,
)
from app.services.query_engine.parser import QueryParser, get_query_parser


logger = structlog.get_logger()


# Knowledge base for common questions
KNOWLEDGE_BASE: dict[str, dict[str, Any]] = {
    "GDPR": {
        "full_name": "General Data Protection Regulation",
        "jurisdiction": "European Union",
        "effective_date": "May 25, 2018",
        "key_principles": [
            "Lawfulness, fairness, and transparency",
            "Purpose limitation",
            "Data minimization",
            "Accuracy",
            "Storage limitation",
            "Integrity and confidentiality",
            "Accountability",
        ],
        "key_articles": {
            "5": "Principles relating to processing of personal data",
            "6": "Lawfulness of processing",
            "7": "Conditions for consent",
            "17": "Right to erasure (right to be forgotten)",
            "32": "Security of processing",
            "33": "Notification of personal data breach",
        },
    },
    "HIPAA": {
        "full_name": "Health Insurance Portability and Accountability Act",
        "jurisdiction": "United States",
        "effective_date": "April 14, 2003 (Privacy Rule)",
        "key_principles": [
            "Protect PHI (Protected Health Information)",
            "Minimum necessary standard",
            "Administrative safeguards",
            "Physical safeguards",
            "Technical safeguards",
        ],
        "key_requirements": {
            "164.308": "Administrative Safeguards",
            "164.310": "Physical Safeguards",
            "164.312": "Technical Safeguards",
            "164.314": "Organizational Requirements",
        },
    },
    "PCI-DSS": {
        "full_name": "Payment Card Industry Data Security Standard",
        "jurisdiction": "Global",
        "current_version": "4.0",
        "key_requirements": [
            "Install and maintain network security controls",
            "Apply secure configurations",
            "Protect stored account data",
            "Protect cardholder data with strong cryptography",
            "Protect against malware",
            "Develop secure systems and software",
            "Restrict access to system components",
            "Identify users and authenticate access",
            "Restrict physical access",
            "Log and monitor access",
            "Test security regularly",
            "Support information security with organizational policies",
        ],
    },
    "SOC2": {
        "full_name": "Service Organization Control 2",
        "jurisdiction": "Global (AICPA standard)",
        "trust_criteria": [
            "Security",
            "Availability",
            "Processing Integrity",
            "Confidentiality",
            "Privacy",
        ],
        "report_types": {
            "Type I": "Point-in-time assessment",
            "Type II": "Assessment over a period (usually 6-12 months)",
        },
    },
}


class AnswerGenerator:
    """Generates answers to compliance queries."""

    def __init__(self, parser: QueryParser | None = None):
        self.parser = parser or get_query_parser()
        self._contexts: dict[UUID, ConversationContext] = {}

    async def answer(
        self,
        query: str,
        organization_id: UUID | None = None,
        repository_id: UUID | None = None,
        context_id: UUID | None = None,
        codebase_context: dict[str, Any] | None = None,
    ) -> QueryAnswer:
        """Generate an answer to a compliance query.
        
        Args:
            query: Natural language question
            organization_id: Organization context
            repository_id: Repository context
            context_id: Conversation context for multi-turn
            codebase_context: Pre-loaded codebase information
            
        Returns:
            QueryAnswer with response and sources
        """
        start_time = time.perf_counter()
        
        # Parse the query
        parsed = self.parser.parse(query)
        
        # Get or create conversation context
        context = self._get_or_create_context(
            context_id, organization_id, repository_id
        )
        
        # Generate answer based on intent
        if parsed.intent == QueryIntent.REGULATION_INFO:
            answer = await self._answer_regulation_info(parsed, context)
        elif parsed.intent == QueryIntent.COMPLIANCE_STATUS:
            answer = await self._answer_compliance_status(parsed, context, codebase_context)
        elif parsed.intent == QueryIntent.REMEDIATION_GUIDANCE:
            answer = await self._answer_remediation(parsed, context)
        elif parsed.intent == QueryIntent.EVIDENCE_SEARCH:
            answer = await self._answer_evidence_search(parsed, context)
        elif parsed.intent == QueryIntent.POLICY_LOOKUP:
            answer = await self._answer_policy_lookup(parsed, context)
        elif parsed.intent == QueryIntent.CODE_REVIEW:
            answer = await self._answer_code_review(parsed, context, codebase_context)
        elif parsed.intent == QueryIntent.RISK_ASSESSMENT:
            answer = await self._answer_risk_assessment(parsed, context)
        elif parsed.intent == QueryIntent.AUDIT_PREP:
            answer = await self._answer_audit_prep(parsed, context)
        elif parsed.intent == QueryIntent.COMPARISON:
            answer = await self._answer_comparison(parsed, context)
        else:
            answer = await self._answer_unknown(parsed, context)
        
        # Update context
        context.queries.append(parsed)
        context.answers.append(answer)
        context.mentioned_regulations.update(parsed.regulations)
        
        # Set metadata
        answer.query_id = parsed.id
        answer.generated_at = answer.generated_at
        duration = (time.perf_counter() - start_time) * 1000
        
        logger.info(
            "Generated answer",
            intent=parsed.intent.value,
            confidence=answer.confidence,
            sources=len(answer.sources),
            duration_ms=duration,
        )
        
        return answer

    def _get_or_create_context(
        self,
        context_id: UUID | None,
        organization_id: UUID | None,
        repository_id: UUID | None,
    ) -> ConversationContext:
        """Get or create conversation context."""
        if context_id and context_id in self._contexts:
            return self._contexts[context_id]
        
        context = ConversationContext(
            organization_id=organization_id,
            repository_id=repository_id,
        )
        self._contexts[context.id] = context
        return context

    async def _answer_regulation_info(
        self,
        parsed: ParsedQuery,
        context: ConversationContext,
    ) -> QueryAnswer:
        """Answer questions about regulations."""
        answer = QueryAnswer(confidence=0.8)
        
        if not parsed.regulations:
            # Use context or ask for clarification
            if context.mentioned_regulations:
                parsed.regulations = list(context.mentioned_regulations)
            else:
                answer.answer = "I can help explain regulations like GDPR, HIPAA, PCI-DSS, SOC2, and more. Which regulation would you like to know about?"
                answer.confidence = 0.5
                answer.related_questions = [
                    "What is GDPR?",
                    "Explain HIPAA requirements",
                    "What is SOC2 compliance?",
                ]
                return answer
        
        # Build answer from knowledge base
        responses = []
        for reg in parsed.regulations[:2]:  # Limit to 2 regulations
            if reg in KNOWLEDGE_BASE:
                kb = KNOWLEDGE_BASE[reg]
                responses.append(f"**{reg}** ({kb.get('full_name', reg)})\n")
                
                if kb.get('jurisdiction'):
                    responses.append(f"- Jurisdiction: {kb['jurisdiction']}\n")
                
                if kb.get('key_principles'):
                    responses.append("- Key Principles:\n")
                    for p in kb['key_principles'][:5]:
                        responses.append(f"  - {p}\n")
                
                answer.sources.append(SourceReference(
                    source_type=SourceType.KNOWLEDGE_BASE,
                    source_id=reg,
                    title=f"{reg} Overview",
                    relevance_score=0.95,
                ))
        
        if responses:
            answer.answer = "".join(responses)
            answer.summary = f"Overview of {', '.join(parsed.regulations)}"
        else:
            answer.answer = f"I don't have detailed information about {', '.join(parsed.regulations)}. Would you like me to explain a different regulation?"
            answer.confidence = 0.3
        
        return answer

    async def _answer_compliance_status(
        self,
        parsed: ParsedQuery,
        context: ConversationContext,
        codebase_context: dict[str, Any] | None,
    ) -> QueryAnswer:
        """Answer compliance status questions."""
        answer = QueryAnswer(confidence=0.7)
        
        # If we have codebase context, use it
        if codebase_context:
            score = codebase_context.get("compliance_score", 0)
            issues = codebase_context.get("issues_count", 0)
            
            answer.answer = f"Based on the latest analysis:\n\n"
            answer.answer += f"- **Compliance Score**: {score:.0%}\n"
            answer.answer += f"- **Open Issues**: {issues}\n"
            
            if parsed.regulations:
                answer.answer += f"\nFor {', '.join(parsed.regulations)}:\n"
                for reg in parsed.regulations:
                    reg_score = codebase_context.get(f"{reg.lower()}_score", score)
                    answer.answer += f"- {reg}: {reg_score:.0%} compliant\n"
            
            answer.sources.append(SourceReference(
                source_type=SourceType.ANALYSIS_RESULT,
                source_id="latest_analysis",
                title="Latest Compliance Analysis",
                relevance_score=0.95,
            ))
        else:
            answer.answer = "I don't have current analysis data for your repository. Would you like me to run a compliance scan?"
            answer.action_items = ["Run compliance analysis"]
            answer.confidence = 0.4
        
        answer.related_questions = [
            "What are the critical issues?",
            "How do I improve my compliance score?",
            "Show me the evidence gaps",
        ]
        
        return answer

    async def _answer_remediation(
        self,
        parsed: ParsedQuery,
        context: ConversationContext,
    ) -> QueryAnswer:
        """Answer remediation guidance questions."""
        answer = QueryAnswer(confidence=0.75)
        
        # Extract what needs to be fixed
        keywords = parsed.keywords or []
        
        remediation_guides = {
            "encryption": [
                "Enable TLS 1.2+ for all data in transit",
                "Use AES-256 for data at rest encryption",
                "Implement proper key management with rotation",
            ],
            "authentication": [
                "Implement multi-factor authentication (MFA)",
                "Use strong password policies (12+ chars, complexity)",
                "Enable account lockout after failed attempts",
            ],
            "logging": [
                "Enable comprehensive audit logging",
                "Include user IDs, timestamps, and actions",
                "Retain logs for required period (often 1+ year)",
            ],
            "access control": [
                "Implement role-based access control (RBAC)",
                "Follow principle of least privilege",
                "Regular access reviews (quarterly recommended)",
            ],
            "data protection": [
                "Classify data by sensitivity level",
                "Implement data masking for sensitive fields",
                "Establish data retention policies",
            ],
        }
        
        matched_guides = []
        for kw in keywords:
            if kw in remediation_guides:
                matched_guides.append((kw, remediation_guides[kw]))
        
        if matched_guides:
            answer.answer = "Here's guidance for your remediation needs:\n\n"
            for topic, steps in matched_guides:
                answer.answer += f"**{topic.title()}**:\n"
                for i, step in enumerate(steps, 1):
                    answer.answer += f"{i}. {step}\n"
                answer.answer += "\n"
            
            answer.action_items = [step for _, steps in matched_guides for step in steps[:2]]
        else:
            answer.answer = "I can help with remediation for encryption, authentication, logging, access control, and data protection. What specific area do you need guidance on?"
            answer.confidence = 0.5
        
        return answer

    async def _answer_evidence_search(
        self,
        parsed: ParsedQuery,
        context: ConversationContext,
    ) -> QueryAnswer:
        """Answer evidence search questions."""
        answer = QueryAnswer(confidence=0.7)
        
        # Simulated evidence locations
        answer.answer = "To find compliance evidence, check these locations:\n\n"
        answer.answer += "**Policies & Procedures**:\n"
        answer.answer += "- `/docs/policies/` - Security and privacy policies\n"
        answer.answer += "- `/docs/procedures/` - Operational procedures\n\n"
        answer.answer += "**Technical Evidence**:\n"
        answer.answer += "- Infrastructure configurations in `/terraform/` or `/infrastructure/`\n"
        answer.answer += "- CI/CD logs showing change management\n"
        answer.answer += "- Monitoring dashboards for availability metrics\n"
        
        answer.sources.append(SourceReference(
            source_type=SourceType.CODEBASE,
            source_id="docs",
            title="Documentation Directory",
            snippet="Policy and procedure documents",
            relevance_score=0.85,
        ))
        
        return answer

    async def _answer_policy_lookup(
        self,
        parsed: ParsedQuery,
        context: ConversationContext,
    ) -> QueryAnswer:
        """Answer policy lookup questions."""
        answer = QueryAnswer(confidence=0.7)
        answer.answer = "Common compliance policies you should have documented:\n\n"
        answer.answer += "1. **Information Security Policy** - Overall security framework\n"
        answer.answer += "2. **Access Control Policy** - User authentication and authorization\n"
        answer.answer += "3. **Data Protection Policy** - How data is classified and protected\n"
        answer.answer += "4. **Incident Response Policy** - Steps for security incidents\n"
        answer.answer += "5. **Change Management Policy** - Process for system changes\n"
        return answer

    async def _answer_code_review(
        self,
        parsed: ParsedQuery,
        context: ConversationContext,
        codebase_context: dict[str, Any] | None,
    ) -> QueryAnswer:
        """Answer code review questions."""
        answer = QueryAnswer(confidence=0.6)
        
        if parsed.file_patterns:
            answer.answer = f"I can review these files for compliance issues:\n"
            for pattern in parsed.file_patterns:
                answer.answer += f"- `{pattern}`\n"
            answer.answer += "\nWould you like me to run a compliance scan on these files?"
            answer.action_items = ["Run compliance scan"]
        else:
            answer.answer = "I can review code for compliance issues. Please specify the files or directories to analyze, or I can scan the entire repository."
            answer.related_questions = [
                "Scan the entire repository",
                "Review the /src directory",
                "Check configuration files",
            ]
        
        return answer

    async def _answer_risk_assessment(
        self,
        parsed: ParsedQuery,
        context: ConversationContext,
    ) -> QueryAnswer:
        """Answer risk assessment questions."""
        answer = QueryAnswer(confidence=0.7)
        answer.answer = "Risk assessment for compliance typically considers:\n\n"
        answer.answer += "**High Risk Factors**:\n"
        answer.answer += "- Processing of personal/sensitive data without encryption\n"
        answer.answer += "- Missing audit logging\n"
        answer.answer += "- No access controls on sensitive systems\n\n"
        answer.answer += "**Medium Risk Factors**:\n"
        answer.answer += "- Outdated dependencies with known vulnerabilities\n"
        answer.answer += "- Incomplete documentation\n\n"
        answer.answer += "Would you like me to run a risk assessment on your codebase?"
        return answer

    async def _answer_audit_prep(
        self,
        parsed: ParsedQuery,
        context: ConversationContext,
    ) -> QueryAnswer:
        """Answer audit preparation questions."""
        answer = QueryAnswer(confidence=0.75)
        answer.answer = "**Audit Preparation Checklist**:\n\n"
        answer.answer += "1. ☐ Gather all policy documents\n"
        answer.answer += "2. ☐ Collect evidence for each control\n"
        answer.answer += "3. ☐ Run compliance scans and address issues\n"
        answer.answer += "4. ☐ Prepare system access for auditors\n"
        answer.answer += "5. ☐ Document compensating controls for any gaps\n"
        answer.answer += "6. ☐ Brief team on audit process\n"
        
        answer.action_items = [
            "Generate evidence report",
            "Run gap analysis",
            "Review open issues",
        ]
        
        return answer

    async def _answer_comparison(
        self,
        parsed: ParsedQuery,
        context: ConversationContext,
    ) -> QueryAnswer:
        """Answer comparison questions."""
        answer = QueryAnswer(confidence=0.7)
        
        regs = parsed.regulations
        if len(regs) >= 2:
            r1, r2 = regs[0], regs[1]
            answer.answer = f"**{r1} vs {r2}**:\n\n"
            
            if r1 in KNOWLEDGE_BASE and r2 in KNOWLEDGE_BASE:
                kb1, kb2 = KNOWLEDGE_BASE[r1], KNOWLEDGE_BASE[r2]
                answer.answer += f"- **Jurisdiction**: {kb1.get('jurisdiction', 'N/A')} vs {kb2.get('jurisdiction', 'N/A')}\n"
                answer.answer += f"- **Focus**: Data protection vs Healthcare data (example)\n"
        else:
            answer.answer = "I can compare compliance frameworks. Please mention two frameworks to compare, e.g., 'Compare GDPR and HIPAA'."
        
        return answer

    async def _answer_unknown(
        self,
        parsed: ParsedQuery,
        context: ConversationContext,
    ) -> QueryAnswer:
        """Handle unknown queries."""
        answer = QueryAnswer(confidence=0.3)
        
        clarifications = self.parser.suggest_clarifications(parsed)
        
        answer.answer = "I'm not sure I understand your question. "
        if clarifications:
            answer.answer += clarifications[0]
        else:
            answer.answer += "I can help with compliance status, regulation explanations, code review, remediation guidance, and audit preparation."
        
        answer.related_questions = [
            "What is my compliance status?",
            "Explain GDPR requirements",
            "How do I fix encryption issues?",
            "Prepare for SOC2 audit",
        ]
        
        return answer

    def get_context(self, context_id: UUID) -> ConversationContext | None:
        """Get conversation context."""
        return self._contexts.get(context_id)


# Global instance
_generator: AnswerGenerator | None = None


def get_answer_generator() -> AnswerGenerator:
    """Get or create answer generator."""
    global _generator
    if _generator is None:
        _generator = AnswerGenerator()
    return _generator
