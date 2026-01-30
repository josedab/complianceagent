"""Compliance diagnostic models for IDE integration."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DiagnosticSeverity(str, Enum):
    """Severity levels for compliance diagnostics."""

    ERROR = "error"  # Critical compliance violation
    WARNING = "warning"  # Potential compliance issue
    INFORMATION = "information"  # Compliance recommendation
    HINT = "hint"  # Best practice suggestion


class DiagnosticCategory(str, Enum):
    """Categories of compliance diagnostics."""

    DATA_PRIVACY = "data_privacy"
    DATA_RETENTION = "data_retention"
    CONSENT = "consent"
    SECURITY = "security"
    AI_TRANSPARENCY = "ai_transparency"
    AI_DOCUMENTATION = "ai_documentation"
    AUDIT_LOGGING = "audit_logging"
    ACCESS_CONTROL = "access_control"
    ENCRYPTION = "encryption"
    PII_HANDLING = "pii_handling"
    DATA_TRANSFER = "data_transfer"
    BREACH_NOTIFICATION = "breach_notification"


@dataclass
class Position:
    """Position in a text document (0-indexed)."""

    line: int
    character: int


@dataclass
class Range:
    """Range in a text document."""

    start: Position
    end: Position


@dataclass
class CodeAction:
    """Suggested fix for a compliance issue."""

    title: str
    kind: str  # quickfix, refactor, source
    edit: dict[str, Any] | None = None
    command: dict[str, Any] | None = None
    is_preferred: bool = False


@dataclass
class ComplianceDiagnostic:
    """A compliance diagnostic message for IDE display."""

    range: Range
    message: str
    severity: DiagnosticSeverity
    code: str  # e.g., "GDPR-001", "HIPAA-PHI-002"
    source: str = "ComplianceAgent"
    category: DiagnosticCategory | None = None
    regulation: str | None = None  # e.g., "GDPR", "HIPAA"
    requirement_id: str | None = None
    article_reference: str | None = None  # e.g., "Article 17"
    related_information: list[dict] = field(default_factory=list)
    code_actions: list[CodeAction] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)

    def to_lsp_diagnostic(self) -> dict[str, Any]:
        """Convert to LSP diagnostic format."""
        severity_map = {
            DiagnosticSeverity.ERROR: 1,
            DiagnosticSeverity.WARNING: 2,
            DiagnosticSeverity.INFORMATION: 3,
            DiagnosticSeverity.HINT: 4,
        }

        diagnostic = {
            "range": {
                "start": {"line": self.range.start.line, "character": self.range.start.character},
                "end": {"line": self.range.end.line, "character": self.range.end.character},
            },
            "message": self.message,
            "severity": severity_map[self.severity],
            "code": self.code,
            "source": self.source,
        }

        if self.related_information:
            diagnostic["relatedInformation"] = self.related_information

        # Store additional data for code actions
        diagnostic["data"] = {
            "category": self.category.value if self.category else None,
            "regulation": self.regulation,
            "requirement_id": self.requirement_id,
            "article_reference": self.article_reference,
            **self.data,
        }

        return diagnostic


@dataclass
class DiagnosticResult:
    """Result of analyzing a document for compliance issues."""

    uri: str
    version: int | None
    diagnostics: list[ComplianceDiagnostic]
    analysis_time_ms: float
    patterns_checked: int
    requirements_evaluated: int


# Pre-defined compliance patterns for common issues
COMPLIANCE_PATTERNS = {
    "pii_logging": {
        "pattern": r"(log|print|console\.log|logger)\s*\([^)]*\b(email|password|ssn|social_security|credit_card|phone|address)\b",
        "severity": DiagnosticSeverity.ERROR,
        "category": DiagnosticCategory.PII_HANDLING,
        "regulation": "GDPR",
        "code": "GDPR-LOG-001",
        "message": "Potential PII being logged. Personal data should not be logged without encryption or anonymization.",
        "article_reference": "Article 32",
    },
    "unencrypted_pii_storage": {
        "pattern": r"(store|save|write|insert)\s*\([^)]*\b(email|password|ssn|credit_card)\b[^)]*\)(?!.*encrypt)",
        "severity": DiagnosticSeverity.WARNING,
        "category": DiagnosticCategory.ENCRYPTION,
        "regulation": "GDPR",
        "code": "GDPR-ENC-001",
        "message": "PII may be stored without encryption. Consider encrypting sensitive data at rest.",
        "article_reference": "Article 32",
    },
    "hardcoded_retention": {
        "pattern": r"retention[_\s]*(period|days|time)\s*[=:]\s*\d+",
        "severity": DiagnosticSeverity.INFORMATION,
        "category": DiagnosticCategory.DATA_RETENTION,
        "regulation": "GDPR",
        "code": "GDPR-RET-001",
        "message": "Hardcoded retention period detected. Consider making this configurable per jurisdiction.",
        "article_reference": "Article 5(1)(e)",
    },
    "missing_consent_check": {
        "pattern": r"(collect|gather|process)\s*\(\s*[^)]*user[_\s]*(data|info)",
        "severity": DiagnosticSeverity.WARNING,
        "category": DiagnosticCategory.CONSENT,
        "regulation": "GDPR",
        "code": "GDPR-CON-001",
        "message": "Data collection without apparent consent verification. Ensure user consent is checked before processing.",
        "article_reference": "Article 7",
    },
    "ai_model_undocumented": {
        "pattern": r"(model\.predict|classifier\.fit|neural_network|deep_learning|machine_learning)\s*\(",
        "severity": DiagnosticSeverity.WARNING,
        "category": DiagnosticCategory.AI_DOCUMENTATION,
        "regulation": "EU AI Act",
        "code": "EUAI-DOC-001",
        "message": "AI/ML model usage detected. Ensure proper documentation exists per EU AI Act requirements.",
        "article_reference": "Article 11",
    },
    "ai_decision_no_explanation": {
        "pattern": r"(automated_decision|auto_reject|auto_approve|decision_engine)\s*\([^)]*\)(?!.*explain)",
        "severity": DiagnosticSeverity.ERROR,
        "category": DiagnosticCategory.AI_TRANSPARENCY,
        "regulation": "EU AI Act",
        "code": "EUAI-TRA-001",
        "message": "Automated decision without explanation mechanism. High-risk AI systems require explainability.",
        "article_reference": "Article 13",
    },
    "phi_unprotected": {
        "pattern": r"\b(diagnosis|treatment|prescription|medical_record|health_info|patient_data)\b(?!.*encrypt|.*protected|.*hipaa)",
        "severity": DiagnosticSeverity.ERROR,
        "category": DiagnosticCategory.DATA_PRIVACY,
        "regulation": "HIPAA",
        "code": "HIPAA-PHI-001",
        "message": "Protected Health Information (PHI) may be unprotected. Ensure HIPAA safeguards are in place.",
        "article_reference": "45 CFR 164.312",
    },
    "missing_audit_log": {
        "pattern": r"(delete|update|modify)\s*\(\s*[^)]*\b(user|account|record|data)\b[^)]*\)(?!.*audit|.*log)",
        "severity": DiagnosticSeverity.WARNING,
        "category": DiagnosticCategory.AUDIT_LOGGING,
        "regulation": "SOX",
        "code": "SOX-AUD-001",
        "message": "Data modification without apparent audit logging. Financial data changes should be audited.",
        "article_reference": "Section 802",
    },
    "cross_border_transfer": {
        "pattern": r"(transfer|send|export)\s*\([^)]*\b(eu|europe|gdpr|international)\b",
        "severity": DiagnosticSeverity.WARNING,
        "category": DiagnosticCategory.DATA_TRANSFER,
        "regulation": "GDPR",
        "code": "GDPR-TRA-001",
        "message": "Potential cross-border data transfer detected. Ensure adequate safeguards for international transfers.",
        "article_reference": "Chapter V",
    },
    "ccpa_sale_no_optout": {
        "pattern": r"(sell|share|monetize)\s*\([^)]*\b(user|consumer|personal)\b[^)]*data",
        "severity": DiagnosticSeverity.ERROR,
        "category": DiagnosticCategory.DATA_PRIVACY,
        "regulation": "CCPA",
        "code": "CCPA-OPT-001",
        "message": "Data sale/sharing without opt-out check. CCPA requires 'Do Not Sell' opt-out mechanism.",
        "article_reference": "Section 1798.120",
    },
}
