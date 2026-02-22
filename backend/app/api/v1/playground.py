"""Public compliance playground endpoint — no authentication required.

Allows users to paste code snippets and get instant compliance analysis
against selected frameworks. Rate-limited to prevent abuse.
"""

from __future__ import annotations

from enum import Enum

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


logger = structlog.get_logger()
router = APIRouter()


# ── Compliance patterns (subset of IDE scanner patterns) ─────────────────

_PATTERNS: dict[str, list[dict]] = {
    "GDPR": [
        {
            "id": "GDPR-001",
            "pattern": "personal_data",
            "keywords": ["email", "name", "address", "phone", "ip_address", "cookie", "user_agent"],
            "severity": "high",
            "message": "Potential personal data processing detected. Ensure GDPR Article 6 lawful basis.",
        },
        {
            "id": "GDPR-002",
            "pattern": "consent",
            "keywords": ["consent", "opt_in", "opt_out", "unsubscribe", "permission"],
            "severity": "medium",
            "message": "Consent-related code detected. Verify GDPR Article 7 consent requirements.",
        },
        {
            "id": "GDPR-003",
            "pattern": "data_transfer",
            "keywords": ["transfer", "export", "send_to", "api_call", "third_party", "webhook"],
            "severity": "high",
            "message": "Data transfer detected. Check GDPR Chapter V cross-border transfer rules.",
        },
        {
            "id": "GDPR-004",
            "pattern": "retention",
            "keywords": ["delete", "purge", "expire", "retention", "ttl", "cleanup"],
            "severity": "medium",
            "message": "Data lifecycle code detected. Verify GDPR Article 5(1)(e) storage limitation.",
        },
    ],
    "HIPAA": [
        {
            "id": "HIPAA-001",
            "pattern": "phi",
            "keywords": ["patient", "diagnosis", "medical", "health", "prescription", "ssn", "mrn"],
            "severity": "critical",
            "message": "Protected Health Information (PHI) detected. Apply HIPAA §164.502 minimum necessary.",
        },
        {
            "id": "HIPAA-002",
            "pattern": "encryption",
            "keywords": ["encrypt", "decrypt", "plaintext", "password", "secret", "token"],
            "severity": "high",
            "message": "Sensitive data handling without clear encryption. HIPAA §164.312(a)(2)(iv) requires encryption.",
        },
        {
            "id": "HIPAA-003",
            "pattern": "access_log",
            "keywords": ["access_log", "audit_trail", "log_access", "who_accessed"],
            "severity": "medium",
            "message": "Access logging detected. Ensure HIPAA §164.312(b) audit controls.",
        },
    ],
    "PCI-DSS": [
        {
            "id": "PCI-001",
            "pattern": "cardholder",
            "keywords": ["credit_card", "card_number", "pan", "cvv", "expiry", "cardholder"],
            "severity": "critical",
            "message": "Cardholder data detected. PCI-DSS Requirement 3: Protect stored cardholder data.",
        },
        {
            "id": "PCI-002",
            "pattern": "tokenization",
            "keywords": ["token", "tokenize", "mask", "redact", "truncate"],
            "severity": "medium",
            "message": "Tokenization code found. Verify PCI-DSS Requirement 3.4 rendering PAN unreadable.",
        },
    ],
    "SOC2": [
        {
            "id": "SOC2-001",
            "pattern": "logging",
            "keywords": ["logger", "logging", "audit", "event_log", "track"],
            "severity": "medium",
            "message": "Logging detected. Ensure SOC 2 CC7.2 security event monitoring.",
        },
        {
            "id": "SOC2-002",
            "pattern": "auth",
            "keywords": ["authenticate", "authorize", "login", "session", "jwt", "oauth"],
            "severity": "high",
            "message": "Authentication code detected. Verify SOC 2 CC6.1 logical access controls.",
        },
    ],
    "EU-AI-ACT": [
        {
            "id": "EUAI-001",
            "pattern": "model",
            "keywords": [
                "model",
                "predict",
                "inference",
                "train",
                "ml",
                "ai",
                "neural",
                "classifier",
            ],
            "severity": "high",
            "message": "AI/ML system detected. Check EU AI Act risk classification (Article 6).",
        },
        {
            "id": "EUAI-002",
            "pattern": "bias",
            "keywords": ["bias", "fairness", "demographic", "protected_class", "discrimination"],
            "severity": "critical",
            "message": "Potential bias-sensitive code. EU AI Act Article 10 requires bias monitoring.",
        },
    ],
}


class Language(str, Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    GO = "go"


class PlaygroundRequest(BaseModel):
    code: str = Field(..., min_length=10, max_length=50000, description="Code snippet to analyze")
    language: Language = Language.PYTHON
    frameworks: list[str] = Field(
        default=["GDPR", "HIPAA", "PCI-DSS"],
        description="Regulatory frameworks to check against",
    )


class Finding(BaseModel):
    rule_id: str
    framework: str
    severity: str
    message: str
    line: int | None = None
    snippet: str = ""


class PlaygroundResponse(BaseModel):
    findings: list[Finding]
    summary: dict[str, int]
    scanned_lines: int
    frameworks_checked: list[str]


def _scan_code(code: str, frameworks: list[str]) -> list[Finding]:
    """Run pattern-based compliance scanning on a code snippet."""
    findings: list[Finding] = []
    lines = code.lower().split("\n")

    for framework in frameworks:
        patterns = _PATTERNS.get(framework, [])
        for pattern in patterns:
            for line_num, line in enumerate(lines, start=1):
                for keyword in pattern["keywords"]:
                    if keyword in line:
                        # Find original (non-lowered) snippet
                        original_line = (
                            code.split("\n")[line_num - 1]
                            if line_num <= len(code.split("\n"))
                            else ""
                        )
                        findings.append(
                            Finding(
                                rule_id=pattern["id"],
                                framework=framework,
                                severity=pattern["severity"],
                                message=pattern["message"],
                                line=line_num,
                                snippet=original_line.strip()[:200],
                            )
                        )
                        break  # one match per pattern per line

    # Deduplicate by (rule_id, line)
    seen: set[tuple[str, int | None]] = set()
    unique: list[Finding] = []
    for f in findings:
        key = (f.rule_id, f.line)
        if key not in seen:
            seen.add(key)
            unique.append(f)

    return unique


@router.post(
    "/scan",
    response_model=PlaygroundResponse,
    summary="Scan code for compliance issues (no auth required)",
)
async def playground_scan(request: PlaygroundRequest) -> PlaygroundResponse:
    """Analyze a code snippet for compliance issues.

    This is a public endpoint for the interactive playground.
    No authentication required. Rate-limited to 30 requests/minute.
    """
    valid_frameworks = [fw for fw in request.frameworks if fw in _PATTERNS]
    if not valid_frameworks:
        raise HTTPException(
            status_code=400, detail=f"No valid frameworks. Choose from: {list(_PATTERNS.keys())}"
        )

    findings = _scan_code(request.code, valid_frameworks)

    summary: dict[str, int] = {}
    for f in findings:
        summary[f.severity] = summary.get(f.severity, 0) + 1

    logger.info(
        "playground_scan",
        language=request.language.value,
        frameworks=valid_frameworks,
        lines=len(request.code.split("\n")),
        findings=len(findings),
    )

    return PlaygroundResponse(
        findings=findings,
        summary=summary,
        scanned_lines=len(request.code.split("\n")),
        frameworks_checked=valid_frameworks,
    )


@router.get(
    "/frameworks",
    summary="List available compliance frameworks",
)
async def list_frameworks() -> dict:
    """List available frameworks and their rule counts."""
    return {
        "frameworks": {
            name: {"rules": len(rules), "severities": list({r["severity"] for r in rules})}
            for name, rules in _PATTERNS.items()
        }
    }
