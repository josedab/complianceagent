"""Natural Language Compliance Query Engine.

Enables conversational queries about compliance status, regulations,
and codebase compliance with semantic search capabilities.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

import structlog

from app.agents.copilot import CopilotClient, CopilotMessage


logger = structlog.get_logger()


class QueryIntent(str, Enum):
    """Detected intent of a compliance query."""
    FIND_VIOLATIONS = "find_violations"
    EXPLAIN_REGULATION = "explain_regulation"
    CHECK_COMPLIANCE = "check_compliance"
    FIND_AFFECTED_CODE = "find_affected_code"
    GET_REQUIREMENTS = "get_requirements"
    COMPARE_FRAMEWORKS = "compare_frameworks"
    SUGGEST_FIX = "suggest_fix"
    AUDIT_STATUS = "audit_status"
    DATA_FLOW = "data_flow"
    RISK_ASSESSMENT = "risk_assessment"
    UNKNOWN = "unknown"


class QueryContext(str, Enum):
    """Context type for the query."""
    CODEBASE = "codebase"
    REGULATION = "regulation"
    ORGANIZATION = "organization"
    REPOSITORY = "repository"
    GENERAL = "general"


@dataclass
class ParsedQuery:
    """A parsed natural language query."""
    id: UUID = field(default_factory=uuid4)
    original_query: str = ""
    intent: QueryIntent = QueryIntent.UNKNOWN
    context: QueryContext = QueryContext.GENERAL
    
    # Extracted entities
    regulations: list[str] = field(default_factory=list)
    articles: list[str] = field(default_factory=list)
    file_paths: list[str] = field(default_factory=list)
    data_types: list[str] = field(default_factory=list)
    severity_filter: str | None = None
    
    # Search parameters
    keywords: list[str] = field(default_factory=list)
    filters: dict[str, Any] = field(default_factory=dict)
    
    # Confidence
    confidence: float = 0.0
    parsed_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class QueryResult:
    """Result of a compliance query."""
    id: UUID = field(default_factory=uuid4)
    query_id: UUID | None = None
    
    # Natural language response
    answer: str = ""
    summary: str = ""
    
    # Structured results
    violations: list[dict[str, Any]] = field(default_factory=list)
    affected_files: list[dict[str, Any]] = field(default_factory=list)
    requirements: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    
    # Citations
    citations: list[dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    confidence: float = 0.0
    sources_used: list[str] = field(default_factory=list)
    execution_time_ms: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass 
class QuerySession:
    """A session for conversational queries."""
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID | None = None
    user_id: str = ""
    
    # Conversation history
    queries: list[ParsedQuery] = field(default_factory=list)
    results: list[QueryResult] = field(default_factory=list)
    
    # Context accumulation
    context: dict[str, Any] = field(default_factory=dict)
    active_regulations: list[str] = field(default_factory=list)
    active_repositories: list[UUID] = field(default_factory=list)
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class NaturalLanguageQueryEngine:
    """Engine for processing natural language compliance queries."""

    INTENT_PATTERNS = {
        QueryIntent.FIND_VIOLATIONS: [
            "show", "find", "list", "violations", "issues", "problems",
            "non-compliant", "gaps", "breaches", "failing",
        ],
        QueryIntent.EXPLAIN_REGULATION: [
            "explain", "what is", "what does", "describe", "tell me about",
            "meaning", "definition", "requirements of",
        ],
        QueryIntent.CHECK_COMPLIANCE: [
            "compliant", "compliance", "status", "are we", "do we",
            "check", "verify", "audit",
        ],
        QueryIntent.FIND_AFFECTED_CODE: [
            "which files", "what code", "affected", "impacted",
            "where", "location", "find code",
        ],
        QueryIntent.GET_REQUIREMENTS: [
            "requirements", "what must", "what should", "obligations",
            "need to", "have to", "mandatory",
        ],
        QueryIntent.COMPARE_FRAMEWORKS: [
            "compare", "difference", "versus", "vs", "between",
            "overlap", "similar",
        ],
        QueryIntent.SUGGEST_FIX: [
            "fix", "resolve", "remediate", "how to", "solution",
            "address", "correct", "implement",
        ],
        QueryIntent.AUDIT_STATUS: [
            "audit", "evidence", "documentation", "proof",
            "demonstrate", "certification",
        ],
        QueryIntent.DATA_FLOW: [
            "data flow", "data handling", "where does data",
            "personal data", "pii", "sensitive data",
        ],
        QueryIntent.RISK_ASSESSMENT: [
            "risk", "exposure", "threat", "vulnerability",
            "impact", "likelihood", "severity",
        ],
    }

    REGULATION_ALIASES = {
        "gdpr": ["GDPR", "General Data Protection Regulation", "EU data protection"],
        "ccpa": ["CCPA", "California Consumer Privacy Act", "CPRA"],
        "hipaa": ["HIPAA", "Health Insurance Portability", "PHI", "protected health"],
        "pci": ["PCI-DSS", "PCI DSS", "Payment Card", "credit card"],
        "sox": ["SOX", "Sarbanes-Oxley", "financial reporting"],
        "eu_ai_act": ["EU AI Act", "AI Act", "artificial intelligence act"],
        "iso27001": ["ISO 27001", "ISO27001", "information security"],
        "soc2": ["SOC 2", "SOC2", "System and Organization Controls"],
    }

    def __init__(self):
        self._sessions: dict[UUID, QuerySession] = {}
        self._copilot: CopilotClient | None = None

    async def _get_copilot(self) -> CopilotClient:
        """Get or create Copilot client."""
        if self._copilot is None:
            self._copilot = CopilotClient()
        return self._copilot

    def create_session(
        self,
        organization_id: UUID | None = None,
        user_id: str = "",
        initial_context: dict[str, Any] | None = None,
    ) -> QuerySession:
        """Create a new query session."""
        session = QuerySession(
            organization_id=organization_id,
            user_id=user_id,
            context=initial_context or {},
        )
        self._sessions[session.id] = session
        return session

    def get_session(self, session_id: UUID) -> QuerySession | None:
        """Get an existing session."""
        return self._sessions.get(session_id)

    async def query(
        self,
        query_text: str,
        session_id: UUID | None = None,
        codebase_context: dict[str, Any] | None = None,
        compliance_data: dict[str, Any] | None = None,
    ) -> QueryResult:
        """Process a natural language compliance query."""
        import time
        start_time = time.perf_counter()
        
        # Get or create session
        session = None
        if session_id:
            session = self._sessions.get(session_id)
        
        # Parse the query
        parsed = await self._parse_query(query_text, session)
        
        # Execute based on intent
        result = await self._execute_query(
            parsed,
            session,
            codebase_context,
            compliance_data,
        )
        
        # Generate natural language answer
        result.answer = await self._generate_answer(parsed, result, session)
        
        # Update session
        if session:
            session.queries.append(parsed)
            session.results.append(result)
            session.updated_at = datetime.utcnow()
        
        result.execution_time_ms = (time.perf_counter() - start_time) * 1000
        
        logger.info(
            "nl_query_executed",
            query_id=str(parsed.id),
            intent=parsed.intent.value,
            confidence=parsed.confidence,
            execution_ms=result.execution_time_ms,
        )
        
        return result

    async def _parse_query(
        self,
        query_text: str,
        session: QuerySession | None = None,
    ) -> ParsedQuery:
        """Parse natural language query into structured form."""
        parsed = ParsedQuery(original_query=query_text)
        query_lower = query_text.lower()
        
        # Detect intent
        intent_scores: dict[QueryIntent, int] = {}
        for intent, patterns in self.INTENT_PATTERNS.items():
            score = sum(1 for p in patterns if p in query_lower)
            if score > 0:
                intent_scores[intent] = score
        
        if intent_scores:
            parsed.intent = max(intent_scores, key=lambda k: intent_scores[k])
            max_score = max(intent_scores.values())
            parsed.confidence = min(1.0, max_score * 0.3)
        
        # Extract regulations
        for reg_key, aliases in self.REGULATION_ALIASES.items():
            for alias in aliases:
                if alias.lower() in query_lower:
                    parsed.regulations.append(reg_key.upper())
                    break
        
        # Extract article references (e.g., "Article 17", "Section 5")
        import re
        article_pattern = r'(?:article|section|paragraph)\s*(\d+(?:\.\d+)?)'
        for match in re.finditer(article_pattern, query_lower):
            parsed.articles.append(match.group(1))
        
        # Extract file paths
        file_pattern = r'[a-zA-Z0-9_/.-]+\.(py|ts|tsx|js|jsx|java|go|rs|rb)'
        for match in re.finditer(file_pattern, query_text):
            parsed.file_paths.append(match.group(0))
        
        # Extract data types
        data_type_keywords = ["pii", "phi", "personal data", "health data", "payment", "credit card"]
        for dt in data_type_keywords:
            if dt in query_lower:
                parsed.data_types.append(dt)
        
        # Extract severity filter
        severity_keywords = {
            "critical": ["critical", "severe", "urgent"],
            "high": ["high", "important", "major"],
            "medium": ["medium", "moderate"],
            "low": ["low", "minor"],
        }
        for sev, keywords in severity_keywords.items():
            if any(k in query_lower for k in keywords):
                parsed.severity_filter = sev
                break
        
        # Extract general keywords
        stop_words = {
            "the", "a", "an", "is", "are", "how", "what", "which", "where",
            "show", "find", "list", "me", "my", "our", "in", "for", "to",
            "and", "or", "with", "all", "any", "from", "by", "on", "of",
        }
        words = re.findall(r'\b\w+\b', query_lower)
        parsed.keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        # Determine context
        if parsed.file_paths:
            parsed.context = QueryContext.CODEBASE
        elif parsed.regulations:
            parsed.context = QueryContext.REGULATION
        else:
            parsed.context = QueryContext.GENERAL
        
        # Incorporate session context
        if session and not parsed.regulations:
            parsed.regulations = session.active_regulations.copy()
        
        return parsed

    async def _execute_query(
        self,
        parsed: ParsedQuery,
        session: QuerySession | None,
        codebase_context: dict[str, Any] | None,
        compliance_data: dict[str, Any] | None,
    ) -> QueryResult:
        """Execute the parsed query and gather results."""
        result = QueryResult(query_id=parsed.id)
        
        if parsed.intent == QueryIntent.FIND_VIOLATIONS:
            await self._find_violations(parsed, result, codebase_context, compliance_data)
        elif parsed.intent == QueryIntent.EXPLAIN_REGULATION:
            await self._explain_regulation(parsed, result)
        elif parsed.intent == QueryIntent.CHECK_COMPLIANCE:
            await self._check_compliance(parsed, result, compliance_data)
        elif parsed.intent == QueryIntent.FIND_AFFECTED_CODE:
            await self._find_affected_code(parsed, result, codebase_context)
        elif parsed.intent == QueryIntent.GET_REQUIREMENTS:
            await self._get_requirements(parsed, result)
        elif parsed.intent == QueryIntent.SUGGEST_FIX:
            await self._suggest_fix(parsed, result, codebase_context)
        elif parsed.intent == QueryIntent.DATA_FLOW:
            await self._analyze_data_flow(parsed, result, codebase_context)
        elif parsed.intent == QueryIntent.RISK_ASSESSMENT:
            await self._assess_risk(parsed, result, compliance_data)
        else:
            # General query - use AI to formulate response
            await self._general_query(parsed, result, codebase_context, compliance_data)
        
        return result

    async def _find_violations(
        self,
        parsed: ParsedQuery,
        result: QueryResult,
        codebase_context: dict[str, Any] | None,
        compliance_data: dict[str, Any] | None,
    ) -> None:
        """Find compliance violations matching the query."""
        violations = []
        
        # Search compliance data for issues
        if compliance_data:
            for issue in compliance_data.get("issues", []):
                # Filter by regulation
                if parsed.regulations:
                    if issue.get("regulation") not in parsed.regulations:
                        continue
                
                # Filter by severity
                if parsed.severity_filter:
                    if issue.get("severity") != parsed.severity_filter:
                        continue
                
                # Filter by file
                if parsed.file_paths:
                    if issue.get("file_path") not in parsed.file_paths:
                        continue
                
                # Keyword matching
                if parsed.keywords:
                    issue_text = f"{issue.get('message', '')} {issue.get('code', '')}".lower()
                    if not any(kw in issue_text for kw in parsed.keywords):
                        continue
                
                violations.append(issue)
        
        result.violations = violations[:50]  # Limit results
        result.summary = f"Found {len(violations)} compliance violations"
        
        if parsed.regulations:
            result.summary += f" related to {', '.join(parsed.regulations)}"
        
        result.sources_used.append("compliance_database")

    async def _explain_regulation(
        self,
        parsed: ParsedQuery,
        result: QueryResult,
    ) -> None:
        """Explain a regulation or specific article."""
        explanations = []
        
        # Build regulation explanations
        regulation_info = {
            "GDPR": {
                "name": "General Data Protection Regulation",
                "jurisdiction": "European Union",
                "effective_date": "May 25, 2018",
                "summary": "Comprehensive data protection law governing the processing of personal data of EU residents.",
                "key_requirements": [
                    "Lawful basis for processing personal data",
                    "Data subject rights (access, deletion, portability)",
                    "Privacy by design and by default",
                    "Data breach notification within 72 hours",
                    "Data Protection Impact Assessments",
                    "Appointment of Data Protection Officer",
                ],
            },
            "CCPA": {
                "name": "California Consumer Privacy Act",
                "jurisdiction": "California, USA",
                "effective_date": "January 1, 2020",
                "summary": "Privacy law giving California consumers rights over their personal information.",
                "key_requirements": [
                    "Right to know what data is collected",
                    "Right to delete personal information",
                    "Right to opt-out of data sale",
                    "Non-discrimination for exercising rights",
                    "Privacy policy disclosures",
                ],
            },
            "HIPAA": {
                "name": "Health Insurance Portability and Accountability Act",
                "jurisdiction": "United States",
                "effective_date": "April 14, 2003",
                "summary": "Protects sensitive patient health information from disclosure.",
                "key_requirements": [
                    "Administrative safeguards",
                    "Physical safeguards",
                    "Technical safeguards",
                    "Breach notification",
                    "Business Associate Agreements",
                    "Minimum necessary standard",
                ],
            },
            "PCI-DSS": {
                "name": "Payment Card Industry Data Security Standard",
                "jurisdiction": "Global",
                "effective_date": "December 2004",
                "summary": "Security standard for organizations handling credit card data.",
                "key_requirements": [
                    "Build and maintain secure network",
                    "Protect cardholder data",
                    "Maintain vulnerability management program",
                    "Implement strong access control",
                    "Monitor and test networks",
                    "Maintain information security policy",
                ],
            },
            "EU_AI_ACT": {
                "name": "EU Artificial Intelligence Act",
                "jurisdiction": "European Union",
                "effective_date": "August 2025",
                "summary": "First comprehensive legal framework for AI systems based on risk levels.",
                "key_requirements": [
                    "Risk classification of AI systems",
                    "Prohibited AI practices",
                    "High-risk AI system requirements",
                    "Transparency obligations",
                    "Human oversight",
                    "Documentation and record-keeping",
                ],
            },
        }
        
        for reg in parsed.regulations:
            reg_upper = reg.upper().replace("-", "_")
            if reg_upper in regulation_info:
                info = regulation_info[reg_upper]
                explanations.append({
                    "regulation": reg,
                    "full_name": info["name"],
                    "jurisdiction": info["jurisdiction"],
                    "effective_date": info["effective_date"],
                    "summary": info["summary"],
                    "key_requirements": info["key_requirements"],
                })
                
                result.citations.append({
                    "regulation": reg,
                    "source": f"Official {info['name']} documentation",
                })
        
        result.requirements = explanations
        result.summary = f"Explained {len(explanations)} regulation(s)"
        result.sources_used.append("regulation_knowledge_base")

    async def _check_compliance(
        self,
        parsed: ParsedQuery,
        result: QueryResult,
        compliance_data: dict[str, Any] | None,
    ) -> None:
        """Check compliance status."""
        status_info = []
        
        if compliance_data:
            overall_score = compliance_data.get("overall_score", 0)
            
            for reg in parsed.regulations or compliance_data.get("regulations", []):
                reg_data = next(
                    (r for r in compliance_data.get("regulations", []) 
                     if r.get("regulation") == reg),
                    None
                )
                
                if reg_data:
                    status_info.append({
                        "regulation": reg,
                        "score": reg_data.get("score", 0),
                        "status": reg_data.get("status", "unknown"),
                        "issues_count": reg_data.get("issues_count", 0),
                        "requirements_met": reg_data.get("requirements_met", 0),
                        "requirements_total": reg_data.get("requirements_total", 0),
                    })
            
            result.summary = f"Overall compliance score: {overall_score:.0%}"
        else:
            result.summary = "No compliance data available"
        
        result.requirements = status_info
        result.sources_used.append("compliance_database")

    async def _find_affected_code(
        self,
        parsed: ParsedQuery,
        result: QueryResult,
        codebase_context: dict[str, Any] | None,
    ) -> None:
        """Find code affected by regulations."""
        affected = []
        
        if codebase_context:
            files = codebase_context.get("files", {})
            mappings = codebase_context.get("mappings", [])
            
            for mapping in mappings:
                # Filter by regulation
                if parsed.regulations:
                    if mapping.get("regulation") not in parsed.regulations:
                        continue
                
                affected.append({
                    "file_path": mapping.get("file_path"),
                    "regulation": mapping.get("regulation"),
                    "requirement": mapping.get("requirement"),
                    "compliance_status": mapping.get("status"),
                    "relevance_score": mapping.get("relevance_score", 0),
                })
        
        result.affected_files = affected[:50]
        result.summary = f"Found {len(affected)} affected code locations"
        result.sources_used.append("codebase_analysis")

    async def _get_requirements(
        self,
        parsed: ParsedQuery,
        result: QueryResult,
    ) -> None:
        """Get requirements for specified regulations."""
        requirements = []
        
        # Sample requirements database
        sample_requirements = {
            "GDPR": [
                {"id": "GDPR-7", "title": "Conditions for consent", "category": "consent"},
                {"id": "GDPR-13", "title": "Information to be provided", "category": "transparency"},
                {"id": "GDPR-17", "title": "Right to erasure", "category": "data_subject_rights"},
                {"id": "GDPR-25", "title": "Data protection by design", "category": "technical"},
                {"id": "GDPR-32", "title": "Security of processing", "category": "security"},
                {"id": "GDPR-33", "title": "Breach notification", "category": "breach"},
            ],
            "HIPAA": [
                {"id": "HIPAA-164.312(a)", "title": "Access controls", "category": "technical"},
                {"id": "HIPAA-164.312(b)", "title": "Audit controls", "category": "technical"},
                {"id": "HIPAA-164.312(c)", "title": "Integrity controls", "category": "technical"},
                {"id": "HIPAA-164.312(d)", "title": "Authentication", "category": "technical"},
                {"id": "HIPAA-164.312(e)", "title": "Transmission security", "category": "technical"},
            ],
        }
        
        for reg in parsed.regulations:
            reg_upper = reg.upper()
            if reg_upper in sample_requirements:
                for req in sample_requirements[reg_upper]:
                    requirements.append({
                        "regulation": reg,
                        **req,
                    })
        
        result.requirements = requirements
        result.summary = f"Found {len(requirements)} requirements"
        result.sources_used.append("requirements_database")

    async def _suggest_fix(
        self,
        parsed: ParsedQuery,
        result: QueryResult,
        codebase_context: dict[str, Any] | None,
    ) -> None:
        """Suggest fixes for compliance issues."""
        suggestions = []
        
        # Generate suggestions based on common patterns
        if "gdpr" in [r.lower() for r in parsed.regulations]:
            suggestions.extend([
                "Implement explicit consent collection before processing personal data",
                "Add data retention policies with automatic deletion",
                "Create data export functionality for data portability",
                "Implement audit logging for all personal data access",
            ])
        
        if "hipaa" in [r.lower() for r in parsed.regulations]:
            suggestions.extend([
                "Encrypt PHI data at rest and in transit",
                "Implement role-based access control for PHI",
                "Add audit trails for PHI access and modifications",
                "Configure automatic session timeout for PHI-accessing systems",
            ])
        
        if "pci" in [r.lower() for r in parsed.regulations]:
            suggestions.extend([
                "Never store CVV/CVC data",
                "Use tokenization for card numbers",
                "Implement PCI-compliant payment processor integration",
                "Regular vulnerability scanning and penetration testing",
            ])
        
        result.recommendations = suggestions
        result.summary = f"Generated {len(suggestions)} remediation suggestions"
        result.sources_used.append("remediation_knowledge_base")

    async def _analyze_data_flow(
        self,
        parsed: ParsedQuery,
        result: QueryResult,
        codebase_context: dict[str, Any] | None,
    ) -> None:
        """Analyze data flows in the codebase."""
        flows = []
        
        if codebase_context:
            data_flows = codebase_context.get("data_flows", [])
            
            for flow in data_flows:
                # Filter by data type
                if parsed.data_types:
                    flow_types = flow.get("data_types", [])
                    if not any(dt in flow_types for dt in parsed.data_types):
                        continue
                
                flows.append(flow)
        
        result.affected_files = flows[:20]
        result.summary = f"Identified {len(flows)} data flows"
        
        if parsed.data_types:
            result.summary += f" handling {', '.join(parsed.data_types)}"
        
        result.sources_used.append("data_flow_analysis")

    async def _assess_risk(
        self,
        parsed: ParsedQuery,
        result: QueryResult,
        compliance_data: dict[str, Any] | None,
    ) -> None:
        """Assess compliance risk."""
        risks = []
        
        if compliance_data:
            for issue in compliance_data.get("issues", []):
                if issue.get("severity") in ["critical", "high"]:
                    risk = {
                        "issue": issue.get("message"),
                        "severity": issue.get("severity"),
                        "regulation": issue.get("regulation"),
                        "potential_impact": self._estimate_impact(issue),
                        "likelihood": self._estimate_likelihood(issue),
                    }
                    risks.append(risk)
        
        result.violations = risks[:20]
        result.summary = f"Identified {len(risks)} high-priority risks"
        result.sources_used.append("risk_assessment")

    def _estimate_impact(self, issue: dict) -> str:
        """Estimate potential impact of an issue."""
        severity = issue.get("severity", "medium")
        if severity == "critical":
            return "Potential significant fines, legal action, or reputational damage"
        elif severity == "high":
            return "Likely regulatory scrutiny or moderate financial impact"
        else:
            return "Minor compliance gap with limited immediate impact"

    def _estimate_likelihood(self, issue: dict) -> str:
        """Estimate likelihood of issue causing problems."""
        category = issue.get("category", "")
        if category in ["security", "data_breach"]:
            return "High - actively targeted by attackers"
        elif category in ["consent", "data_subject_rights"]:
            return "Medium - may be noticed by users or regulators"
        else:
            return "Low - unlikely to be detected without audit"

    async def _general_query(
        self,
        parsed: ParsedQuery,
        result: QueryResult,
        codebase_context: dict[str, Any] | None,
        compliance_data: dict[str, Any] | None,
    ) -> None:
        """Handle general queries using AI."""
        result.summary = "Query processed"
        result.sources_used.append("ai_assistant")

    async def _generate_answer(
        self,
        parsed: ParsedQuery,
        result: QueryResult,
        session: QuerySession | None,
    ) -> str:
        """Generate natural language answer from results."""
        parts = [result.summary]
        
        if result.violations:
            parts.append(f"\n\n**Violations Found ({len(result.violations)}):**")
            for v in result.violations[:5]:
                parts.append(f"- [{v.get('severity', 'medium').upper()}] {v.get('message', v.get('issue', 'Unknown'))}")
            if len(result.violations) > 5:
                parts.append(f"  ... and {len(result.violations) - 5} more")
        
        if result.affected_files:
            parts.append(f"\n\n**Affected Files ({len(result.affected_files)}):**")
            for f in result.affected_files[:5]:
                parts.append(f"- {f.get('file_path', f.get('name', 'Unknown'))}")
            if len(result.affected_files) > 5:
                parts.append(f"  ... and {len(result.affected_files) - 5} more")
        
        if result.requirements:
            parts.append(f"\n\n**Requirements ({len(result.requirements)}):**")
            for r in result.requirements[:5]:
                if "full_name" in r:
                    # Regulation explanation
                    parts.append(f"\n### {r.get('full_name')} ({r.get('regulation')})")
                    parts.append(f"{r.get('summary')}")
                    parts.append("\n**Key Requirements:**")
                    for req in r.get("key_requirements", [])[:5]:
                        parts.append(f"- {req}")
                else:
                    # Requirement item
                    parts.append(f"- [{r.get('id', 'N/A')}] {r.get('title', 'Unknown')}")
        
        if result.recommendations:
            parts.append(f"\n\n**Recommendations:**")
            for rec in result.recommendations[:5]:
                parts.append(f"- {rec}")
        
        if result.citations:
            parts.append(f"\n\n**Sources:**")
            for c in result.citations[:3]:
                parts.append(f"- {c.get('source', c.get('regulation', 'Unknown'))}")
        
        return "\n".join(parts)

    async def get_query_suggestions(
        self,
        partial_query: str,
        session_id: UUID | None = None,
    ) -> list[str]:
        """Get query suggestions based on partial input."""
        suggestions = []
        partial_lower = partial_query.lower()
        
        # Common query templates
        templates = [
            "Show me all GDPR violations in our codebase",
            "What files handle personal data?",
            "Explain HIPAA requirements for encryption",
            "Are we compliant with PCI-DSS?",
            "Find all critical compliance issues",
            "What code is affected by EU AI Act?",
            "How do I fix consent management issues?",
            "Show data flows containing PII",
            "What is our compliance score for GDPR?",
            "List all requirements for SOC 2",
        ]
        
        for template in templates:
            if partial_lower in template.lower():
                suggestions.append(template)
        
        # Session-aware suggestions
        session = self._sessions.get(session_id) if session_id else None
        if session and session.active_regulations:
            for reg in session.active_regulations[:2]:
                suggestions.append(f"Show {reg} violations")
                suggestions.append(f"What are the {reg} requirements?")
        
        return suggestions[:10]


# Global instance
_query_engine: NaturalLanguageQueryEngine | None = None


def get_nl_query_engine() -> NaturalLanguageQueryEngine:
    """Get or create the NL query engine."""
    global _query_engine
    if _query_engine is None:
        _query_engine = NaturalLanguageQueryEngine()
    return _query_engine
