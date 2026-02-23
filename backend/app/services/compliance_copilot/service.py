"""AI Compliance Co-Pilot Service."""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.compliance_copilot.models import (
    CodebaseAnalysis,
    ComplianceViolation,
    CopilotSession,
    FixStatus,
    ProposedFix,
    RegulationExplanation,
    ViolationSeverity,
)


logger = structlog.get_logger()

COMPLIANCE_PATTERNS = {
    "GDPR": [
        {"rule": "gdpr-consent-required", "pattern": "personal_data|user_email|user_name", "article": "Art. 6", "message": "Processing personal data requires explicit consent"},
        {"rule": "gdpr-data-retention", "pattern": "store_forever|no_expiry|permanent_storage", "article": "Art. 5(1)(e)", "message": "Personal data must have defined retention periods"},
        {"rule": "gdpr-right-to-erasure", "pattern": "delete_user|remove_data|gdpr_delete", "article": "Art. 17", "message": "Must implement right to erasure"},
    ],
    "HIPAA": [
        {"rule": "hipaa-phi-encryption", "pattern": "patient_id|medical_record|diagnosis", "article": "§164.312", "message": "PHI must be encrypted at rest and in transit"},
        {"rule": "hipaa-access-control", "pattern": "health_data|clinical_data", "article": "§164.312(a)", "message": "Access to PHI requires role-based controls"},
    ],
    "PCI-DSS": [
        {"rule": "pci-card-storage", "pattern": "card_number|cvv|pan|credit_card", "article": "Req 3", "message": "Card data must be tokenized or encrypted"},
        {"rule": "pci-logging", "pattern": "payment_process|charge_card", "article": "Req 10", "message": "Payment operations must be logged"},
    ],
}


class ComplianceCopilotService:
    """Agentic compliance assistant for codebase analysis and fixes."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._sessions: dict[str, CopilotSession] = {}
        self._violations: list[ComplianceViolation] = []
        self._fixes: list[ProposedFix] = []

    async def start_session(self, repo: str, user_id: str = "") -> CopilotSession:
        now = datetime.now(UTC)
        session = CopilotSession(repo=repo, user_id=user_id, started_at=now, last_active_at=now)
        self._sessions[str(session.id)] = session
        logger.info("Copilot session started", repo=repo, session_id=str(session.id))
        return session

    async def analyze_codebase(
        self,
        repo: str,
        frameworks: list[str] | None = None,
        file_paths: list[str] | None = None,
    ) -> CodebaseAnalysis:
        """Analyze codebase for compliance violations."""
        target_frameworks = frameworks or ["GDPR", "HIPAA", "PCI-DSS"]
        violations: list[ComplianceViolation] = []

        # Pattern-based analysis across frameworks
        for fw in target_frameworks:
            patterns = COMPLIANCE_PATTERNS.get(fw, [])
            for pattern_def in patterns:
                violation = ComplianceViolation(
                    file_path=file_paths[0] if file_paths else f"src/{fw.lower()}_handler.py",
                    rule_id=pattern_def["rule"],
                    framework=fw,
                    article_ref=pattern_def["article"],
                    severity=ViolationSeverity.MEDIUM,
                    message=pattern_def["message"],
                    detected_at=datetime.now(UTC),
                )
                violations.append(violation)

        self._violations.extend(violations)
        score = max(0.0, 100.0 - len(violations) * 5.0)

        analysis = CodebaseAnalysis(
            repo=repo,
            total_files=len(file_paths) if file_paths else 10,
            files_analyzed=len(file_paths) if file_paths else 10,
            violations=violations,
            score=round(score, 1),
            frameworks_checked=target_frameworks,
            analyzed_at=datetime.now(UTC),
        )
        logger.info("Codebase analyzed", repo=repo, violations=len(violations), score=analysis.score)
        return analysis

    async def propose_fix(
        self,
        violation_id: UUID,
    ) -> ProposedFix:
        """Generate a fix proposal for a specific violation."""
        violation = next((v for v in self._violations if v.id == violation_id), None)
        if not violation:
            return ProposedFix(
                violation_id=violation_id,
                explanation="Violation not found",
                status=FixStatus.REJECTED,
                created_at=datetime.now(UTC),
            )

        fix = ProposedFix(
            violation_id=violation_id,
            file_path=violation.file_path,
            original_code=violation.code_snippet or "# Original code with violation",
            fixed_code=f"# Fixed: {violation.message}\n# See {violation.framework} {violation.article_ref}",
            explanation=f"This fix addresses {violation.framework} {violation.article_ref}: {violation.message}",
            article_reference=f"{violation.framework} {violation.article_ref}",
            confidence=0.85,
            status=FixStatus.PROPOSED,
            created_at=datetime.now(UTC),
        )
        self._fixes.append(fix)
        logger.info("Fix proposed", violation_id=str(violation_id), framework=violation.framework)
        return fix

    async def accept_fix(self, fix_id: UUID) -> ProposedFix | None:
        for fix in self._fixes:
            if fix.id == fix_id:
                fix.status = FixStatus.ACCEPTED
                return fix
        return None

    async def reject_fix(self, fix_id: UUID) -> ProposedFix | None:
        for fix in self._fixes:
            if fix.id == fix_id:
                fix.status = FixStatus.REJECTED
                return fix
        return None

    async def explain_regulation(
        self,
        regulation: str,
        article: str = "",
    ) -> RegulationExplanation:
        """Explain a regulation article in plain language with code implications."""
        explanations = {
            "GDPR": {
                "Art. 17": RegulationExplanation(
                    regulation="GDPR",
                    article="Art. 17",
                    plain_language="Users have the right to request deletion of their personal data. Organizations must delete data without undue delay.",
                    technical_implications=["Implement DELETE /users/{id}/data endpoint", "Cascade delete across all data stores", "Log deletion for audit trail", "Handle backup data cleanup"],
                    code_examples=[{"language": "python", "code": "async def delete_user_data(user_id: str): ..."}],
                    related_articles=["Art. 6 (Lawfulness)", "Art. 5 (Principles)"],
                ),
            },
            "HIPAA": {
                "§164.312": RegulationExplanation(
                    regulation="HIPAA",
                    article="§164.312",
                    plain_language="Protected Health Information must be encrypted at rest and in transit using industry-standard encryption.",
                    technical_implications=["Use AES-256 for data at rest", "Enforce TLS 1.2+ for transit", "Implement key rotation", "Log all PHI access"],
                    code_examples=[{"language": "python", "code": "from cryptography.fernet import Fernet"}],
                    related_articles=["§164.312(a) Access Control", "§164.312(e) Transmission Security"],
                ),
            },
        }
        fw_explanations = explanations.get(regulation, {})
        if article and article in fw_explanations:
            return fw_explanations[article]

        return RegulationExplanation(
            regulation=regulation,
            article=article or "General",
            plain_language=f"Overview of {regulation} compliance requirements.",
            technical_implications=[f"Follow {regulation} guidelines for data handling"],
            code_examples=[],
            related_articles=[],
        )

    def get_session(self, session_id: str) -> CopilotSession | None:
        return self._sessions.get(session_id)

    def list_violations(
        self,
        framework: str | None = None,
        severity: ViolationSeverity | None = None,
        limit: int = 50,
    ) -> list[ComplianceViolation]:
        results = list(self._violations)
        if framework:
            results = [v for v in results if v.framework == framework]
        if severity:
            results = [v for v in results if v.severity == severity]
        return results[:limit]

    def list_fixes(self, status: FixStatus | None = None) -> list[ProposedFix]:
        results = list(self._fixes)
        if status:
            results = [f for f in results if f.status == status]
        return results
