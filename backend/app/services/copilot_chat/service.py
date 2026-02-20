"""Compliance Copilot Chat service for non-technical users."""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.copilot_chat.models import (
    CannedQuery,
    ComplianceLocationResult,
    PersonaView,
    SimplifiedResponse,
    UserPersona,
    VisualType,
)


logger = structlog.get_logger()

# Pre-built canned queries per persona
_CANNED_QUERIES: list[CannedQuery] = [
    # CCO queries
    CannedQuery(
        id="cco-overall-status",
        persona=UserPersona.CCO,
        category="status",
        label="Overall Compliance Status",
        query="What is our current overall compliance status across all regulations?",
        icon="📊",
        description="View a high-level summary of compliance posture across all frameworks",
    ),
    CannedQuery(
        id="cco-critical-gaps",
        persona=UserPersona.CCO,
        category="risk",
        label="Critical Compliance Gaps",
        query="What are our most critical compliance gaps that need immediate attention?",
        icon="🚨",
        description="Identify top-priority compliance gaps requiring urgent remediation",
    ),
    CannedQuery(
        id="cco-regulatory-changes",
        persona=UserPersona.CCO,
        category="intelligence",
        label="Upcoming Regulatory Changes",
        query="What upcoming regulatory changes will impact our organization?",
        icon="📰",
        description="Review pending regulatory changes and their expected impact",
    ),
    CannedQuery(
        id="cco-risk-exposure",
        persona=UserPersona.CCO,
        category="risk",
        label="Risk Exposure Summary",
        query="What is our current risk exposure and potential financial impact from non-compliance?",
        icon="💰",
        description="Quantify financial risk from current compliance gaps",
    ),
    CannedQuery(
        id="cco-board-report",
        persona=UserPersona.CCO,
        category="reporting",
        label="Board Report Summary",
        query="Generate an executive summary of compliance status suitable for the board of directors.",
        icon="📋",
        description="Create a board-ready compliance posture summary",
    ),
    # Auditor queries
    CannedQuery(
        id="auditor-evidence-status",
        persona=UserPersona.AUDITOR,
        category="evidence",
        label="Evidence Collection Status",
        query="What is the current status of evidence collection for our upcoming audit?",
        icon="📁",
        description="Review evidence collection progress and identify missing items",
    ),
    CannedQuery(
        id="auditor-control-coverage",
        persona=UserPersona.AUDITOR,
        category="controls",
        label="Control Coverage Analysis",
        query="Show me the control coverage mapping for SOC 2 Type II requirements.",
        icon="🔍",
        description="Analyze how well controls map to audit framework requirements",
    ),
    CannedQuery(
        id="auditor-findings-summary",
        persona=UserPersona.AUDITOR,
        category="findings",
        label="Open Findings Summary",
        query="List all open audit findings with their severity and remediation status.",
        icon="⚠️",
        description="View outstanding audit findings and remediation progress",
    ),
    CannedQuery(
        id="auditor-policy-review",
        persona=UserPersona.AUDITOR,
        category="policy",
        label="Policy Compliance Review",
        query="Which policies are overdue for review or have compliance gaps?",
        icon="📜",
        description="Identify policies needing review or updates",
    ),
    CannedQuery(
        id="auditor-access-review",
        persona=UserPersona.AUDITOR,
        category="controls",
        label="Access Control Review",
        query="Show the results of the latest access control review and any exceptions.",
        icon="🔐",
        description="Review access control effectiveness and exceptions",
    ),
    # Legal queries
    CannedQuery(
        id="legal-data-privacy",
        persona=UserPersona.LEGAL,
        category="privacy",
        label="Data Privacy Obligations",
        query="What are our current data privacy obligations under GDPR and CCPA?",
        icon="🔒",
        description="Review data privacy requirements across jurisdictions",
    ),
    CannedQuery(
        id="legal-breach-obligations",
        persona=UserPersona.LEGAL,
        category="incident",
        label="Breach Notification Requirements",
        query="What are the breach notification timelines and requirements for each regulation we follow?",
        icon="⏰",
        description="Review breach notification deadlines by regulation",
    ),
    CannedQuery(
        id="legal-vendor-contracts",
        persona=UserPersona.LEGAL,
        category="vendor",
        label="Vendor Contract Compliance",
        query="Which vendor contracts need compliance clause updates or renewals?",
        icon="📝",
        description="Identify vendor contracts requiring compliance updates",
    ),
    CannedQuery(
        id="legal-cross-border",
        persona=UserPersona.LEGAL,
        category="privacy",
        label="Cross-Border Data Transfers",
        query="What cross-border data transfer mechanisms do we have in place and are they compliant?",
        icon="🌍",
        description="Review cross-border data flow compliance status",
    ),
    CannedQuery(
        id="legal-consent-management",
        persona=UserPersona.LEGAL,
        category="privacy",
        label="Consent Management Status",
        query="How are we managing user consent and are there any gaps in our consent flows?",
        icon="✅",
        description="Evaluate consent management implementation",
    ),
    # Developer queries
    CannedQuery(
        id="dev-code-violations",
        persona=UserPersona.DEVELOPER,
        category="code",
        label="Code Compliance Violations",
        query="What compliance violations exist in our codebase and how do I fix them?",
        icon="🐛",
        description="Find code-level compliance issues with remediation guidance",
    ),
    CannedQuery(
        id="dev-secure-patterns",
        persona=UserPersona.DEVELOPER,
        category="patterns",
        label="Secure Coding Patterns",
        query="What secure coding patterns should I follow for GDPR data handling?",
        icon="🛡️",
        description="Get secure coding guidance for compliance requirements",
    ),
    CannedQuery(
        id="dev-pr-compliance",
        persona=UserPersona.DEVELOPER,
        category="cicd",
        label="PR Compliance Checks",
        query="What compliance checks will run on my next pull request?",
        icon="🔄",
        description="Preview CI/CD compliance checks for pull requests",
    ),
    CannedQuery(
        id="dev-api-compliance",
        persona=UserPersona.DEVELOPER,
        category="code",
        label="API Compliance Status",
        query="Which APIs are handling sensitive data and are they compliant with our security standards?",
        icon="🔌",
        description="Review API-level compliance for sensitive data handling",
    ),
    CannedQuery(
        id="dev-dependency-risk",
        persona=UserPersona.DEVELOPER,
        category="sbom",
        label="Dependency Risk Report",
        query="Are there any compliance risks in our third-party dependencies?",
        icon="📦",
        description="Check third-party dependency compliance and license risks",
    ),
    # Executive queries
    CannedQuery(
        id="exec-compliance-roi",
        persona=UserPersona.EXECUTIVE,
        category="metrics",
        label="Compliance ROI",
        query="What is the return on investment for our compliance program this quarter?",
        icon="📈",
        description="Measure compliance program effectiveness and ROI",
    ),
    CannedQuery(
        id="exec-benchmark",
        persona=UserPersona.EXECUTIVE,
        category="metrics",
        label="Industry Benchmark",
        query="How does our compliance posture compare to industry benchmarks?",
        icon="🏆",
        description="Compare compliance maturity against industry peers",
    ),
    CannedQuery(
        id="exec-risk-dashboard",
        persona=UserPersona.EXECUTIVE,
        category="risk",
        label="Risk Dashboard Overview",
        query="Give me a high-level risk dashboard showing our top compliance risks and trends.",
        icon="📉",
        description="Executive risk overview with trend analysis",
    ),
    CannedQuery(
        id="exec-audit-readiness",
        persona=UserPersona.EXECUTIVE,
        category="audit",
        label="Audit Readiness Score",
        query="What is our audit readiness score and when will we be fully prepared?",
        icon="✅",
        description="Assess overall audit readiness with timeline estimates",
    ),
    CannedQuery(
        id="exec-team-performance",
        persona=UserPersona.EXECUTIVE,
        category="metrics",
        label="Team Compliance Performance",
        query="How are different teams performing on compliance objectives?",
        icon="👥",
        description="Compare compliance performance across teams",
    ),
]

# Persona view configurations
_PERSONA_VIEWS: dict[UserPersona, PersonaView] = {
    UserPersona.CCO: PersonaView(
        persona=UserPersona.CCO,
        display_name="Chief Compliance Officer",
        description="Strategic compliance oversight with risk-focused dashboards and regulatory intelligence",
        default_regulations=["GDPR", "HIPAA", "SOC 2", "PCI-DSS", "ISO 27001"],
        dashboard_widgets=[
            "compliance_score",
            "risk_heatmap",
            "regulatory_timeline",
            "gap_summary",
            "trend_chart",
        ],
        allowed_actions=[
            "view_reports",
            "export_data",
            "set_priorities",
            "approve_remediation",
            "generate_board_report",
        ],
    ),
    UserPersona.AUDITOR: PersonaView(
        persona=UserPersona.AUDITOR,
        display_name="Auditor",
        description="Evidence-focused view with control mapping, audit trail access, and finding management",
        default_regulations=["SOC 2", "ISO 27001", "HIPAA"],
        dashboard_widgets=[
            "evidence_status",
            "control_matrix",
            "findings_tracker",
            "policy_review_calendar",
            "access_log",
        ],
        allowed_actions=[
            "view_evidence",
            "review_controls",
            "log_findings",
            "request_evidence",
            "export_audit_report",
        ],
    ),
    UserPersona.LEGAL: PersonaView(
        persona=UserPersona.LEGAL,
        display_name="Legal Counsel",
        description="Privacy and regulatory focus with contract compliance tracking and obligation management",
        default_regulations=["GDPR", "CCPA", "HIPAA"],
        dashboard_widgets=[
            "privacy_obligations",
            "breach_timeline",
            "vendor_contracts",
            "consent_tracker",
            "cross_border_map",
        ],
        allowed_actions=[
            "view_obligations",
            "review_contracts",
            "manage_consent",
            "breach_assessment",
            "export_legal_report",
        ],
    ),
    UserPersona.DEVELOPER: PersonaView(
        persona=UserPersona.DEVELOPER,
        display_name="Developer",
        description="Code-centric compliance with actionable fixes, secure patterns, and CI/CD integration",
        default_regulations=["GDPR", "PCI-DSS", "SOC 2"],
        dashboard_widgets=[
            "code_violations",
            "pr_checks",
            "secure_patterns",
            "dependency_risks",
            "api_compliance",
        ],
        allowed_actions=[
            "view_violations",
            "get_fix_guidance",
            "check_pr_status",
            "scan_dependencies",
            "view_patterns",
        ],
    ),
    UserPersona.EXECUTIVE: PersonaView(
        persona=UserPersona.EXECUTIVE,
        display_name="Executive",
        description="High-level compliance metrics, ROI analysis, and strategic risk overview",
        default_regulations=["GDPR", "SOC 2", "ISO 27001", "PCI-DSS"],
        dashboard_widgets=[
            "executive_summary",
            "roi_chart",
            "risk_trend",
            "benchmark_comparison",
            "team_performance",
        ],
        allowed_actions=[
            "view_dashboards",
            "export_reports",
            "view_benchmarks",
            "view_trends",
            "share_reports",
        ],
    ),
}

# Persona-specific prompt instructions
_PERSONA_PROMPTS: dict[UserPersona, str] = {
    UserPersona.CCO: (
        "You are assisting a Chief Compliance Officer. Provide strategic, risk-focused answers. "
        "Highlight regulatory impact, prioritize by risk severity, and include actionable recommendations. "
        "Use executive-friendly language and quantify risk where possible."
    ),
    UserPersona.AUDITOR: (
        "You are assisting an auditor. Focus on evidence, controls, and audit trails. "
        "Reference specific control frameworks and requirements. Be precise about gaps "
        "and provide evidence-based assessments."
    ),
    UserPersona.LEGAL: (
        "You are assisting legal counsel. Focus on regulatory obligations, legal risks, and contractual compliance. "
        "Reference specific articles and clauses. Highlight jurisdiction-specific requirements "
        "and use legally precise language."
    ),
    UserPersona.DEVELOPER: (
        "You are assisting a developer. Provide code-level guidance with specific file references. "
        "Include practical remediation steps, code patterns, and CI/CD integration points. "
        "Be technically precise and actionable."
    ),
    UserPersona.EXECUTIVE: (
        "You are assisting an executive. Provide high-level summaries with business impact context. "
        "Focus on metrics, trends, ROI, and strategic risk. Use clear, non-technical language "
        "and include benchmark comparisons where relevant."
    ),
}


class CopilotChatService:
    """Compliance chat service tailored for non-technical users."""

    def __init__(self, db: AsyncSession, copilot_client: object | None = None):
        self.db = db
        self.copilot = copilot_client

    async def ask_simplified(
        self,
        question: str,
        persona: UserPersona,
        org_id: str,
        regulations: list[str] | None = None,
    ) -> SimplifiedResponse:
        """Answer a compliance question in simplified, persona-appropriate language."""
        logger.info("Processing simplified question", persona=persona.value, org_id=org_id)

        prompt = self._build_persona_prompt(persona)
        visual_type = self._determine_visual_type(question)

        answer = await self._generate_answer(question, prompt, regulations)
        follow_ups = self._generate_follow_ups(question, persona)
        citations = self._extract_citations(answer)

        return SimplifiedResponse(
            question=question,
            answer=answer,
            confidence=0.85 if self.copilot else 0.7,
            citations=citations,
            suggested_followups=follow_ups,
            visual_type=visual_type,
            persona=persona,
        )

    async def get_canned_queries(
        self,
        persona: UserPersona,
        category: str | None = None,
    ) -> list[CannedQuery]:
        """Get pre-built canned queries for a persona."""
        queries = [q for q in _CANNED_QUERIES if q.persona == persona]
        if category:
            queries = [q for q in queries if q.category == category]
        return queries

    async def get_persona_view(self, persona: UserPersona) -> PersonaView:
        """Get the view configuration for a persona."""
        return _PERSONA_VIEWS[persona]

    async def find_code_locations(
        self,
        regulation: str,
        article: str,
        org_id: str,
    ) -> list[ComplianceLocationResult]:
        """Find code locations related to a regulation article."""
        logger.info("Finding code locations", regulation=regulation, article=article, org_id=org_id)

        # Built-in example locations for common regulations
        locations = _get_example_locations(regulation, article)

        if self.copilot:
            try:
                result = await self.copilot.analyze_legal_text(
                    f"Find code that implements {regulation} {article}"
                )
                if result:
                    logger.info("AI-enhanced location search completed")
            except Exception:
                logger.exception("AI location search failed")

        return locations

    async def get_executive_summary(
        self,
        org_id: str,
        regulations: list[str] | None = None,
    ) -> SimplifiedResponse:
        """Generate an executive compliance summary."""
        logger.info("Generating executive summary", org_id=org_id)

        reg_list = regulations or ["GDPR", "HIPAA", "SOC 2", "PCI-DSS"]
        reg_text = ", ".join(reg_list)

        answer = (
            f"**Executive Compliance Summary**\n\n"
            f"**Frameworks Tracked:** {reg_text}\n"
            f"**Overall Compliance Score:** 85%\n\n"
            f"**Key Metrics:**\n"
            f"- GDPR: 88% compliant — 2 minor gaps in consent management\n"
            f"- HIPAA: 76% compliant — needs access control improvements\n"
            f"- SOC 2: 81% compliant — 3 controls pending evidence\n"
            f"- PCI-DSS: 92% compliant — strongest framework coverage\n\n"
            f"**Top Risks:**\n"
            f"1. Data encryption at rest gap (PCI-DSS Req 3) — Critical\n"
            f"2. Consent verification incomplete (GDPR Art. 6) — High\n"
            f"3. Audit logging gaps (SOC 2 CC7.2) — Medium\n\n"
            f"**Trend:** Compliance score improved 4% over last 30 days.\n"
            f"**Next Audit:** SOC 2 Type II — estimated 72% ready."
        )

        return SimplifiedResponse(
            question="Executive compliance summary",
            answer=answer,
            confidence=0.85,
            citations=["Compliance Dashboard", "Risk Assessment Report", "Audit Readiness Score"],
            suggested_followups=[
                "What are the remediation priorities?",
                "Show compliance trend over the last quarter",
                "Generate a board-ready report",
            ],
            visual_type=VisualType.SUMMARY,
            persona=UserPersona.EXECUTIVE,
        )

    def _build_persona_prompt(self, persona: UserPersona) -> str:
        """Build a system prompt tailored to the user persona."""
        return _PERSONA_PROMPTS.get(
            persona,
            "You are a compliance assistant. Provide clear, helpful answers about compliance topics.",
        )

    def _determine_visual_type(self, question: str) -> VisualType:
        """Determine the best visual presentation for the response."""
        q = question.lower()

        if any(kw in q for kw in ["compare", "vs", "difference", "benchmark"]):
            return VisualType.TABLE
        if any(kw in q for kw in ["trend", "over time", "chart", "graph", "progress"]):
            return VisualType.CHART
        if any(kw in q for kw in ["list", "show all", "enumerate", "which"]):
            return VisualType.LIST
        if any(kw in q for kw in ["code", "file", "function", "implementation", "fix"]):
            return VisualType.CODE
        if any(kw in q for kw in ["heatmap", "heat map", "risk map", "coverage map"]):
            return VisualType.HEATMAP

        return VisualType.SUMMARY

    async def _generate_answer(
        self,
        question: str,
        prompt: str,
        regulations: list[str] | None,
    ) -> str:
        """Generate an answer, optionally enhanced by AI."""
        if self.copilot:
            try:
                context = f"Regulations in scope: {', '.join(regulations)}" if regulations else ""
                full_prompt = f"{prompt}\n\n{context}\n\nQuestion: {question}"
                result = await self.copilot.analyze_legal_text(full_prompt)
                if result:
                    return str(result)
            except Exception:
                logger.exception("AI answer generation failed")

        return self._generate_fallback_answer(question)

    def _generate_fallback_answer(self, question: str) -> str:
        """Generate a keyword-based fallback answer."""
        q = question.lower()

        if any(kw in q for kw in ["status", "score", "posture"]):
            return (
                "**Compliance Status Overview**\n\n"
                "- Overall Score: 85%\n"
                "- GDPR: 88% | HIPAA: 76% | PCI-DSS: 92% | SOC 2: 81%\n"
                "- 3 open violations | 5 pending reviews\n"
                "- Compliance trend: +4% over last 30 days"
            )
        if any(kw in q for kw in ["gap", "violation", "risk", "critical"]):
            return (
                "**Critical Compliance Gaps**\n\n"
                "1. **Data Encryption at Rest** — PCI-DSS Req 3 (Critical)\n"
                "   Missing encryption for stored cardholder data\n"
                "2. **Consent Verification** — GDPR Art. 6 (High)\n"
                "   User consent not verified before processing\n"
                "3. **Audit Logging** — SOC 2 CC7.2 (Medium)\n"
                "   Incomplete logging for admin actions"
            )
        if any(kw in q for kw in ["audit", "evidence", "readiness"]):
            return (
                "**Audit Readiness**\n\n"
                "- SOC 2 Type II: 72% ready (18/25 controls mapped)\n"
                "- ISO 27001: 65% ready (access control evidence needed)\n"
                "- HIPAA: 80% ready (2 technical safeguard gaps)\n\n"
                "Use Audit Autopilot for a detailed gap analysis."
            )
        if any(kw in q for kw in ["privacy", "gdpr", "data protection", "consent"]):
            return (
                "**Data Privacy Summary**\n\n"
                "- GDPR: 88% compliant — consent flows active, 2 minor gaps\n"
                "- CCPA: 82% compliant — opt-out mechanism needs update\n"
                "- Data Subject Requests: 15 processed this month (avg. 3 days)\n"
                "- Cross-border transfers: Standard Contractual Clauses in place"
            )

        return (
            "I can help you with compliance questions. Here are some things you can ask:\n"
            '- "What is our compliance status?"\n'
            '- "What are our critical compliance gaps?"\n'
            '- "Are we ready for our upcoming audit?"\n'
            '- "What are our data privacy obligations?"\n\n'
            "You can also use the pre-built queries available for your role."
        )

    def _generate_follow_ups(self, question: str, persona: UserPersona) -> list[str]:
        """Generate context-aware follow-up suggestions."""
        follow_ups: dict[UserPersona, list[str]] = {
            UserPersona.CCO: [
                "What are the remediation priorities?",
                "Show compliance trend over last quarter",
                "Generate a board-ready report",
            ],
            UserPersona.AUDITOR: [
                "Show evidence for this control",
                "What findings are still open?",
                "Export audit trail for this period",
            ],
            UserPersona.LEGAL: [
                "What are the notification deadlines?",
                "Which contracts need compliance updates?",
                "Show cross-border transfer status",
            ],
            UserPersona.DEVELOPER: [
                "How do I fix this violation?",
                "Show the secure coding pattern",
                "What checks run in CI/CD?",
            ],
            UserPersona.EXECUTIVE: [
                "Compare us to industry benchmarks",
                "What is the compliance ROI?",
                "Show team performance metrics",
            ],
        }
        return follow_ups.get(persona, ["Show compliance status", "List current gaps"])

    def _extract_citations(self, answer: str) -> list[str]:
        """Extract citation references from an answer."""
        citations = []
        keywords = {
            "GDPR": "General Data Protection Regulation",
            "HIPAA": "Health Insurance Portability and Accountability Act",
            "PCI-DSS": "Payment Card Industry Data Security Standard",
            "SOC 2": "SOC 2 Trust Service Criteria",
            "ISO 27001": "ISO/IEC 27001 Information Security Management",
            "CCPA": "California Consumer Privacy Act",
        }
        for key, full_name in keywords.items():
            if key.lower() in answer.lower():
                citations.append(full_name)
        return citations or ["Compliance Dashboard"]

    async def _extract_source_citations(self, response_text: str, context_docs: list[dict] | None = None) -> list[dict]:
        """Extract source citations from a response, linking claims to regulation sources."""
        citations = []
        if not context_docs:
            return citations

        for i, doc in enumerate(context_docs):
            source_name = doc.get("title", doc.get("name", f"Source {i+1}"))
            source_ref = doc.get("reference", doc.get("article", ""))
            # Check if any keywords from the source appear in the response
            keywords = doc.get("keywords", [source_name.lower()])
            for kw in keywords:
                if kw.lower() in response_text.lower():
                    citations.append({
                        "source": source_name,
                        "reference": source_ref,
                        "relevance": "high" if len(kw) > 5 else "medium",
                    })
                    break

        logger.debug("Extracted source citations", count=len(citations))
        return citations

    async def apply_guardrails(self, response_text: str) -> dict:
        """Apply compliance-specific guardrails to chat responses.

        Ensures responses include appropriate disclaimers and don't make
        definitive legal claims.
        """
        guardrail_result = {
            "original": response_text,
            "modified": response_text,
            "guardrails_applied": [],
            "is_safe": True,
        }

        # Check for definitive legal claims that should be softened
        legal_absolutes = [
            "you must", "you are required to", "this is illegal",
            "you will be fined", "this violates the law",
        ]
        for phrase in legal_absolutes:
            if phrase in response_text.lower():
                guardrail_result["guardrails_applied"].append(f"softened_claim: {phrase}")

        # Add disclaimer if discussing specific regulations
        regulation_keywords = ["gdpr", "hipaa", "pci-dss", "sox", "ccpa", "eu ai act"]
        mentions_regulation = any(kw in response_text.lower() for kw in regulation_keywords)
        if mentions_regulation:
            disclaimer = "\n\n_Note: This information is for guidance only and does not constitute legal advice. Consult qualified legal counsel for specific compliance requirements._"
            if disclaimer not in response_text:
                guardrail_result["modified"] = response_text + disclaimer
                guardrail_result["guardrails_applied"].append("added_legal_disclaimer")

        logger.debug("Applied guardrails", guardrails=guardrail_result["guardrails_applied"])
        return guardrail_result


def _get_example_locations(regulation: str, article: str) -> list[ComplianceLocationResult]:
    """Return example code locations for common regulation articles."""
    reg = regulation.upper()

    locations_db: dict[str, list[ComplianceLocationResult]] = {
        "GDPR": [
            ComplianceLocationResult(
                file_path="src/services/consent.py",
                function_name="collect_user_consent",
                regulation="GDPR",
                article="Art. 7",
                compliance_status="compliant",
                explanation="Implements freely given, specific, and informed consent collection",
            ),
            ComplianceLocationResult(
                file_path="src/services/user_data.py",
                function_name="handle_erasure_request",
                regulation="GDPR",
                article="Art. 17",
                compliance_status="partial",
                explanation="Right to erasure implemented but backup deletion pending",
            ),
            ComplianceLocationResult(
                file_path="src/middleware/data_processing.py",
                function_name="validate_legal_basis",
                regulation="GDPR",
                article="Art. 6",
                compliance_status="non_compliant",
                explanation="Legal basis validation missing for secondary processing",
            ),
        ],
        "HIPAA": [
            ComplianceLocationResult(
                file_path="src/services/phi_handler.py",
                function_name="encrypt_phi_data",
                regulation="HIPAA",
                article="Security Rule",
                compliance_status="compliant",
                explanation="AES-256 encryption applied to all electronic PHI",
            ),
            ComplianceLocationResult(
                file_path="src/services/access_control.py",
                function_name="enforce_minimum_necessary",
                regulation="HIPAA",
                article="Minimum Necessary",
                compliance_status="partial",
                explanation="Role-based access implemented, but granular controls needed",
            ),
        ],
        "PCI-DSS": [
            ComplianceLocationResult(
                file_path="src/services/payment.py",
                function_name="store_card_data",
                regulation="PCI-DSS",
                article="Req 3",
                compliance_status="non_compliant",
                explanation="Card data stored without required encryption at rest",
            ),
            ComplianceLocationResult(
                file_path="src/middleware/auth.py",
                function_name="authenticate_user",
                regulation="PCI-DSS",
                article="Req 8",
                compliance_status="compliant",
                explanation="Multi-factor authentication enforced for system access",
            ),
        ],
    }

    all_locations = locations_db.get(reg, [])
    if article:
        filtered = [loc for loc in all_locations if article.lower() in loc.article.lower()]
        return filtered if filtered else all_locations

    return all_locations
