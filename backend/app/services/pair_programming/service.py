"""Real-Time Compliance Pair Programming service."""

from __future__ import annotations

from uuid import UUID, uuid4

import structlog

from app.services.pair_programming.models import (
    ComplianceSuggestion,
    MultiFileAnalysisResult,
    PairSession,
    RefactoringSuggestion,
    RegulationContext,
    SuggestionSeverity,
    SuggestionStatus,
)


logger = structlog.get_logger()

_REGULATION_CONTEXTS: dict[str, list[RegulationContext]] = {
    "python": [
        RegulationContext(regulation="GDPR", article="Art. 32", title="Security of Processing",
            summary="Implement appropriate technical measures including encryption and pseudonymization.",
            relevance_score=0.92, applicable_patterns=["encryption", "hashing", "pii_handling"]),
        RegulationContext(regulation="HIPAA", article="§164.312(a)", title="Access Control",
            summary="Implement technical policies to allow access only to authorized persons.",
            relevance_score=0.85, applicable_patterns=["authentication", "authorization", "rbac"]),
    ],
    "typescript": [
        RegulationContext(regulation="GDPR", article="Art. 7", title="Conditions for Consent",
            summary="Consent must be freely given, specific, informed, and unambiguous.",
            relevance_score=0.88, applicable_patterns=["consent_form", "cookie_banner", "opt_in"]),
        RegulationContext(regulation="PCI-DSS", article="Req. 3", title="Protect Stored Cardholder Data",
            summary="Render PAN unreadable anywhere it is stored using encryption or hashing.",
            relevance_score=0.90, applicable_patterns=["card_number", "payment", "tokenization"]),
    ],
}

_COMPLIANCE_RULES: list[dict] = [
    {"rule_id": "GDPR-PII-001", "pattern": "email|phone|ssn|name.*=", "regulation": "GDPR", "article": "Art. 5(1)(c)",
     "message": "PII detected without masking or encryption", "severity": "error", "fix": "Apply data masking: mask_pii(value)"},
    {"rule_id": "GDPR-LOG-002", "pattern": "print\\(.*user|log.*password", "regulation": "GDPR", "article": "Art. 5(1)(f)",
     "message": "Potential PII in log output", "severity": "warning", "fix": "Use structured logging with PII redaction"},
    {"rule_id": "HIPAA-ENC-001", "pattern": "password.*=.*plain|store.*unencrypted", "regulation": "HIPAA", "article": "§164.312(a)(2)(iv)",
     "message": "Unencrypted ePHI storage detected", "severity": "error", "fix": "Use AES-256 encryption: encrypt(data, key)"},
    {"rule_id": "PCI-CARD-001", "pattern": "card.*number|credit_card|pan\\b", "regulation": "PCI-DSS", "article": "Req. 3.4",
     "message": "Cardholder data without tokenization", "severity": "error", "fix": "Replace with tokenized reference: tokenize(card_number)"},
    {"rule_id": "SOC2-AUTH-001", "pattern": "admin.*password|hardcoded.*secret", "regulation": "SOC 2", "article": "CC6.1",
     "message": "Hardcoded credentials detected", "severity": "error", "fix": "Use environment variables or secret manager"},
    # --- GDPR Data Retention & Erasure ---
    {"rule_id": "GDPR-RET-001", "pattern": "retention.*forever|never.*delete|keep.*indefinite", "regulation": "GDPR", "article": "Art. 5(1)(e)",
     "message": "Data retained beyond necessity — storage limitation principle", "severity": "error", "fix": "Implement retention policies with automatic expiry: set_retention(data, max_days=365)"},
    {"rule_id": "GDPR-RET-002", "pattern": "ttl.*=.*0|expir.*none|no.*expiry", "regulation": "GDPR", "article": "Art. 5(1)(e)",
     "message": "Missing data expiration — storage limitation violation", "severity": "warning", "fix": "Set appropriate TTL: ttl=timedelta(days=retention_period)"},
    {"rule_id": "GDPR-DEL-001", "pattern": "soft.*delete|mark.*deleted|is_deleted", "regulation": "GDPR", "article": "Art. 17",
     "message": "Soft delete may not satisfy right to erasure requirements", "severity": "warning", "fix": "Implement hard delete with cascade: hard_delete_user_data(user_id)"},
    {"rule_id": "GDPR-DEL-002", "pattern": "backup.*user|archive.*personal", "regulation": "GDPR", "article": "Art. 17",
     "message": "Archived personal data must also support erasure", "severity": "info", "fix": "Ensure backups have erasure capability: register_erasure_handler(backup_store)"},
    # --- HIPAA Audit & Minimum Necessary ---
    {"rule_id": "HIPAA-AUD-001", "pattern": "patient.*record|medical.*data|health.*info", "regulation": "HIPAA", "article": "§164.312(b)",
     "message": "ePHI access without audit logging", "severity": "error", "fix": "Add audit trail: audit_log.record_access(user, resource, action)"},
    {"rule_id": "HIPAA-AUD-002", "pattern": "select.*\\*.*from.*patient|fetch_all.*medical", "regulation": "HIPAA", "article": "§164.312(b)",
     "message": "Broad ePHI query without audit trail", "severity": "warning", "fix": "Log query scope: audit_log.record_query(user, table, filter_criteria)"},
    {"rule_id": "HIPAA-MIN-001", "pattern": "select.*\\*.*from.*user|fetch_all_fields|get_complete_record", "regulation": "HIPAA", "article": "§164.502(b)",
     "message": "Fetching all fields violates minimum necessary principle", "severity": "warning", "fix": "Select only required fields: select_fields(table, ['name', 'appointment_date'])"},
    {"rule_id": "HIPAA-MIN-002", "pattern": "return.*all.*data|dump.*patient|export.*records", "regulation": "HIPAA", "article": "§164.502(b)",
     "message": "Exporting full records without minimum necessary filtering", "severity": "error", "fix": "Apply field-level filtering: export_filtered(records, allowed_fields)"},
    # --- PCI-DSS Input Validation & Session ---
    {"rule_id": "PCI-INP-001", "pattern": "eval\\(|exec\\(|os\\.system\\(|subprocess.*shell.*=.*True", "regulation": "PCI-DSS", "article": "Req. 6.5",
     "message": "Unsafe code execution — injection vulnerability", "severity": "error", "fix": "Use parameterized calls: subprocess.run(args, shell=False)"},
    {"rule_id": "PCI-INP-002", "pattern": "request\\.get\\(|params\\[|query_string", "regulation": "PCI-DSS", "article": "Req. 6.5",
     "message": "User input used without validation", "severity": "warning", "fix": "Validate and sanitize: validated = validate_input(raw_input, schema)"},
    {"rule_id": "PCI-SES-001", "pattern": "session.*expire.*=.*0|session.*timeout.*none|no.*session.*limit", "regulation": "PCI-DSS", "article": "Req. 6.5.10",
     "message": "Missing session timeout configuration", "severity": "error", "fix": "Set session timeout: session.configure(timeout_minutes=15)"},
    {"rule_id": "PCI-SES-002", "pattern": "session_id.*url|token.*query.*param|jwt.*url", "regulation": "PCI-DSS", "article": "Req. 6.5.10",
     "message": "Session token exposed in URL", "severity": "error", "fix": "Use secure cookies or headers: response.set_cookie(token, httponly=True, secure=True)"},
    # --- SOC 2 Change Management & Monitoring ---
    {"rule_id": "SOC2-CHG-001", "pattern": "deploy.*prod.*direct|push.*master|force.*push", "regulation": "SOC 2", "article": "CC8.1",
     "message": "Direct production deployment without change management", "severity": "error", "fix": "Use CI/CD pipeline with approvals: deploy_via_pipeline(artifact, approvers)"},
    {"rule_id": "SOC2-CHG-002", "pattern": "migrate.*run|alter.*table|schema.*change", "regulation": "SOC 2", "article": "CC8.1",
     "message": "Schema change without change management tracking", "severity": "warning", "fix": "Track migrations: register_change(migration_id, reviewer, rollback_plan)"},
    {"rule_id": "SOC2-MON-001", "pattern": "except.*pass|catch.*ignore|silent.*fail", "regulation": "SOC 2", "article": "CC7.2",
     "message": "Silent error suppression hinders monitoring", "severity": "warning", "fix": "Log exceptions: logger.error('operation_failed', error=str(e), context=ctx)"},
    {"rule_id": "SOC2-MON-002", "pattern": "disable.*alert|skip.*monitor|no.*metric", "regulation": "SOC 2", "article": "CC7.2",
     "message": "Monitoring or alerting disabled", "severity": "error", "fix": "Maintain monitoring: metrics.track(operation, status, duration)"},
    # --- CCPA Do-Not-Sell ---
    {"rule_id": "CCPA-DNS-001", "pattern": "share.*third.?party|send.*partner.*data|export.*vendor", "regulation": "CCPA", "article": "§1798.120",
     "message": "Data sharing without do-not-sell check", "severity": "error", "fix": "Check opt-out status: if not user.do_not_sell: share_data(partner, data)"},
    {"rule_id": "CCPA-DNS-002", "pattern": "sell.*data|monetize.*user|data.*broker", "regulation": "CCPA", "article": "§1798.120",
     "message": "Data sale without consumer opt-out mechanism", "severity": "error", "fix": "Implement opt-out: require_consent(user_id, purpose='data_sale')"},
    # --- EU AI Act Transparency ---
    {"rule_id": "EUAI-TRA-001", "pattern": "predict\\(|model\\.run|inference|classify\\(", "regulation": "EU AI Act", "article": "Art. 13",
     "message": "AI inference without transparency logging", "severity": "warning", "fix": "Log AI decisions: log_ai_decision(model_id, input_hash, output, confidence)"},
    {"rule_id": "EUAI-TRA-002", "pattern": "auto.*decision|automated.*reject|bot.*approve", "regulation": "EU AI Act", "article": "Art. 13",
     "message": "Automated decision-making without explainability", "severity": "error", "fix": "Provide explanations: explain_decision(model, input, output, factors)"},
]


class PairProgrammingService:
    """Service for real-time compliance pair programming."""

    async def analyze_code(
        self, code: str, file_path: str, language: str = "python",
    ) -> list[ComplianceSuggestion]:
        import re
        if not code:
            return []
        suggestions = []
        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            for rule in _COMPLIANCE_RULES:
                try:
                    match = re.search(rule["pattern"], line, re.IGNORECASE)
                except re.error:
                    logger.warning("pair.bad_regex", rule_id=rule["rule_id"], pattern=rule["pattern"])
                    continue
                if match:
                    suggestions.append(ComplianceSuggestion(
                        id=uuid4(), file_path=file_path, line_number=i,
                        severity=SuggestionSeverity(rule["severity"]),
                        rule_id=rule["rule_id"], regulation=rule["regulation"],
                        article=rule["article"], message=rule["message"],
                        explanation=f"This line may violate {rule['regulation']} {rule['article']}.",
                        suggested_fix=rule["fix"], original_code=line.strip(),
                        confidence=0.85,
                    ))
        logger.info("pair.code_analyzed", file=file_path, suggestions=len(suggestions))
        for s in suggestions:
            self._suggestions[s.id] = s
        return suggestions

    async def start_session(
        self, user_id: UUID, repository: str, language: str = "python",
    ) -> PairSession:
        session = PairSession(
            id=uuid4(), user_id=user_id, repository=repository, language=language,
        )
        self._sessions[session.id] = session
        logger.info("pair.session_started", session_id=str(session.id))
        return session

    async def get_regulation_context(self, language: str) -> list[RegulationContext]:
        return _REGULATION_CONTEXTS.get(language, _REGULATION_CONTEXTS["python"])

    async def get_compliance_rules(self) -> list[dict]:
        return list(_COMPLIANCE_RULES)

    # --- Session & Suggestion Tracking ---

    _sessions: dict[UUID, PairSession] = {}
    _suggestions: dict[UUID, ComplianceSuggestion] = {}

    async def analyze_multi_file(
        self, files: list[dict[str, str]], language: str = "python",
    ) -> MultiFileAnalysisResult:
        """Analyze multiple files and return consolidated results with cross-file issues."""
        result = MultiFileAnalysisResult()
        all_suggestions: list[ComplianceSuggestion] = []

        for file_info in files:
            file_path = file_info.get("file_path", "")
            code = file_info.get("code", "")
            suggestions = await self.analyze_code(code, file_path, language)
            if suggestions:
                result.suggestions_by_file[file_path] = suggestions
                all_suggestions.extend(suggestions)
                for s in suggestions:
                    self._suggestions[s.id] = s

        result.files_analyzed = len(files)
        result.total_suggestions = len(all_suggestions)

        # Cross-file dependency analysis: detect same rule violations across files
        rule_to_files: dict[str, list[str]] = {}
        for s in all_suggestions:
            rule_to_files.setdefault(s.rule_id, []).append(s.file_path)

        for rule_id, affected in rule_to_files.items():
            unique_files = sorted(set(affected))
            if len(unique_files) > 1:
                rule_info = next((r for r in _COMPLIANCE_RULES if r["rule_id"] == rule_id), {})
                result.cross_file_issues.append({
                    "rule_id": rule_id,
                    "regulation": rule_info.get("regulation", ""),
                    "article": rule_info.get("article", ""),
                    "message": f"Violation of {rule_id} found across {len(unique_files)} files",
                    "affected_files": unique_files,
                    "recommendation": "Centralize compliance handling to avoid repeated violations",
                })

        # Identify refactoring opportunities from cross-file patterns
        result.refactoring_opportunities = [
            opp.__dict__ for opp in await self.get_refactoring_suggestions(files, language)
        ]

        logger.info("pair.multi_file_analyzed", files=len(files), suggestions=result.total_suggestions,
                     cross_file_issues=len(result.cross_file_issues))
        return result

    async def get_session_summary(self, session_id: UUID) -> dict:
        """Return session statistics."""
        session = self._sessions.get(session_id)
        if not session:
            logger.warning("pair.session_not_found", session_id=str(session_id))
            return {"error": "Session not found", "session_id": str(session_id)}

        session_suggestions = list(self._suggestions.values())
        accepted = sum(1 for s in session_suggestions if s.status == SuggestionStatus.ACCEPTED)
        dismissed = sum(1 for s in session_suggestions if s.status == SuggestionStatus.DISMISSED)
        pending = sum(1 for s in session_suggestions if s.status == SuggestionStatus.PENDING)

        return {
            "session_id": str(session.id),
            "repository": session.repository,
            "language": session.language,
            "started_at": session.started_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "suggestions_given": session.suggestions_given,
            "suggestions_accepted": accepted,
            "suggestions_dismissed": dismissed,
            "suggestions_pending": pending,
            "violations_prevented": session.violations_prevented,
            "acceptance_rate": round(accepted / max(accepted + dismissed, 1), 2),
        }

    async def accept_suggestion(self, suggestion_id: UUID) -> ComplianceSuggestion | None:
        """Mark a suggestion as accepted."""
        suggestion = self._suggestions.get(suggestion_id)
        if suggestion:
            suggestion.status = SuggestionStatus.ACCEPTED
            logger.info("pair.suggestion_accepted", suggestion_id=str(suggestion_id))
        else:
            logger.warning("pair.suggestion_not_found", suggestion_id=str(suggestion_id))
        return suggestion

    async def dismiss_suggestion(self, suggestion_id: UUID) -> ComplianceSuggestion | None:
        """Mark a suggestion as dismissed."""
        suggestion = self._suggestions.get(suggestion_id)
        if suggestion:
            suggestion.status = SuggestionStatus.DISMISSED
            logger.info("pair.suggestion_dismissed", suggestion_id=str(suggestion_id))
        else:
            logger.warning("pair.suggestion_not_found", suggestion_id=str(suggestion_id))
        return suggestion

    async def get_refactoring_suggestions(
        self, files: list[dict[str, str]], language: str = "python",
    ) -> list[RefactoringSuggestion]:
        """Analyze code for multi-file compliance refactoring opportunities."""
        import re
        suggestions: list[RefactoringSuggestion] = []

        # Collect per-file pattern hits
        pii_files: list[str] = []
        consent_files: list[str] = []
        crypto_files: list[str] = []
        audit_files: list[str] = []
        session_files: list[str] = []
        ai_files: list[str] = []

        for file_info in files:
            file_path = file_info.get("file_path", "")
            code = file_info.get("code", "")
            if re.search(r"email|phone|ssn|personal.*data|pii", code, re.IGNORECASE):
                pii_files.append(file_path)
            if re.search(r"consent|opt.?in|gdpr.*accept|cookie.*agree", code, re.IGNORECASE):
                consent_files.append(file_path)
            if re.search(r"encrypt|decrypt|hash|cipher|aes|rsa", code, re.IGNORECASE):
                crypto_files.append(file_path)
            if re.search(r"audit|log.*access|track.*action|record.*event", code, re.IGNORECASE):
                audit_files.append(file_path)
            if re.search(r"session|token|cookie|jwt", code, re.IGNORECASE):
                session_files.append(file_path)
            if re.search(r"predict|model\\.run|inference|classify|ml_|ai_", code, re.IGNORECASE):
                ai_files.append(file_path)

        if len(pii_files) > 1:
            suggestions.append(RefactoringSuggestion(
                id=uuid4(), title="Centralize PII handling",
                description="Multiple files handle PII independently. Create a unified PII service with masking, encryption, and access controls.",
                affected_files=pii_files, regulation="GDPR", article="Art. 5(1)(c)",
                effort_estimate="high", priority=9,
                suggested_approach="Create a PiiService class that provides mask(), encrypt(), and validate_access() methods. Replace direct PII manipulation across files.",
            ))

        if len(consent_files) > 1:
            suggestions.append(RefactoringSuggestion(
                id=uuid4(), title="Add consent management layer",
                description="Consent handling is scattered across files. Implement a centralized consent management system.",
                affected_files=consent_files, regulation="GDPR", article="Art. 7",
                effort_estimate="high", priority=8,
                suggested_approach="Create a ConsentManager that tracks user consent per purpose. All data processing checks consent via ConsentManager.has_consent(user, purpose).",
            ))

        if len(crypto_files) > 1:
            suggestions.append(RefactoringSuggestion(
                id=uuid4(), title="Unify cryptographic operations",
                description="Encryption logic is duplicated. Centralize into a crypto service with key management.",
                affected_files=crypto_files, regulation="HIPAA", article="§164.312(a)(2)(iv)",
                effort_estimate="medium", priority=8,
                suggested_approach="Create a CryptoService with encrypt(), decrypt(), hash() methods using a consistent algorithm and centralized key management.",
            ))

        if len(audit_files) > 1:
            suggestions.append(RefactoringSuggestion(
                id=uuid4(), title="Standardize audit logging",
                description="Audit logging implementations vary across files. Standardize with a unified audit service.",
                affected_files=audit_files, regulation="HIPAA", article="§164.312(b)",
                effort_estimate="medium", priority=7,
                suggested_approach="Create an AuditService with record_access(), record_modification(), record_query() methods that write to a tamper-evident log.",
            ))

        if len(session_files) > 1:
            suggestions.append(RefactoringSuggestion(
                id=uuid4(), title="Consolidate session management",
                description="Session handling is spread across files. Centralize for consistent timeout, rotation, and security controls.",
                affected_files=session_files, regulation="PCI-DSS", article="Req. 6.5.10",
                effort_estimate="medium", priority=7,
                suggested_approach="Create a SessionManager with create(), validate(), rotate(), and expire() methods with configurable timeouts.",
            ))

        if ai_files:
            suggestions.append(RefactoringSuggestion(
                id=uuid4(), title="Add AI transparency layer",
                description="AI/ML operations need transparency logging and explainability per EU AI Act.",
                affected_files=ai_files, regulation="EU AI Act", article="Art. 13",
                effort_estimate="high", priority=6,
                suggested_approach="Create an AiTransparencyService that wraps model calls with logging of inputs, outputs, confidence scores, and decision factors.",
            ))

        logger.info("pair.refactoring_analyzed", files=len(files), opportunities=len(suggestions))
        return suggestions
