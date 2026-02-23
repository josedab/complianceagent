"""Pre-built fix templates for common compliance violations.

Provides ready-to-apply code templates for GDPR, HIPAA, PCI-DSS, SOC 2,
and EU AI Act violations across Python, TypeScript, Java, and Go.
"""

from dataclasses import dataclass, field
from enum import Enum

import structlog

from app.services.remediation_workflow.models import RemediationFix, WorkflowState


logger = structlog.get_logger()


class FixLanguage(str, Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"


@dataclass
class FixTemplate:
    """A reusable fix template for a specific violation pattern."""

    id: str = ""
    framework: str = ""
    violation_pattern: str = ""
    description: str = ""
    language: FixLanguage = FixLanguage.PYTHON
    template_code: str = ""
    file_pattern: str = ""
    confidence: float = 0.80
    tags: list[str] = field(default_factory=list)


# Valid state transitions — enforces the workflow state machine
VALID_TRANSITIONS: dict[WorkflowState, list[WorkflowState]] = {
    WorkflowState.DETECTED: [WorkflowState.PLANNING, WorkflowState.FAILED],
    WorkflowState.PLANNING: [WorkflowState.GENERATING, WorkflowState.FAILED],
    WorkflowState.GENERATING: [WorkflowState.REVIEW, WorkflowState.FAILED],
    WorkflowState.REVIEW: [WorkflowState.APPROVED, WorkflowState.DETECTED, WorkflowState.FAILED],
    WorkflowState.APPROVED: [WorkflowState.MERGING, WorkflowState.REVIEW, WorkflowState.FAILED],
    WorkflowState.MERGING: [WorkflowState.COMPLETED, WorkflowState.FAILED],
    WorkflowState.COMPLETED: [WorkflowState.ROLLED_BACK],
    WorkflowState.ROLLED_BACK: [WorkflowState.DETECTED],
    WorkflowState.FAILED: [WorkflowState.DETECTED],
}


def validate_transition(current: WorkflowState, target: WorkflowState) -> bool:
    """Check whether a state transition is valid."""
    allowed = VALID_TRANSITIONS.get(current, [])
    return target in allowed


# ── Built-in Fix Templates ───────────────────────────────────────────────

BUILTIN_TEMPLATES: list[FixTemplate] = [
    # GDPR
    FixTemplate(
        id="gdpr-consent-check",
        framework="gdpr",
        violation_pattern="missing_consent",
        description="Add user consent verification before data processing",
        language=FixLanguage.PYTHON,
        template_code=(
            "from compliance.gdpr import require_consent\n\n"
            '@require_consent(purpose="{purpose}")\n'
            "async def process_user_data(user_id: str, data: dict) -> dict:\n"
            '    """Process user data with consent verification."""\n'
            "    return await _process(user_id, data)\n"
        ),
        file_pattern="**/data/*.py",
        tags=["consent", "data-processing"],
    ),
    FixTemplate(
        id="gdpr-right-to-erasure",
        framework="gdpr",
        violation_pattern="missing_erasure",
        description="Implement right-to-erasure endpoint and data purge logic",
        language=FixLanguage.PYTHON,
        template_code=(
            "async def handle_erasure_request(user_id: str) -> dict:\n"
            '    """Handle GDPR Article 17 erasure request."""\n'
            "    tables = await get_user_data_locations(user_id)\n"
            "    for table in tables:\n"
            "        await purge_user_data(table, user_id)\n"
            '    await audit_log.record("erasure_completed", user_id=user_id)\n'
            '    return {"status": "erased", "tables_purged": len(tables)}\n'
        ),
        file_pattern="**/users/*.py",
        tags=["erasure", "right-to-be-forgotten"],
    ),
    FixTemplate(
        id="gdpr-data-minimization",
        framework="gdpr",
        violation_pattern="excessive_data_collection",
        description="Apply data minimization — collect only necessary fields",
        language=FixLanguage.TYPESCRIPT,
        template_code=(
            "import { pickFields } from '@compliance/gdpr';\n\n"
            "const REQUIRED_FIELDS = ['{field1}', '{field2}'] as const;\n\n"
            "function processUserData(raw: Record<string, unknown>) {\n"
            "  const minimized = pickFields(raw, REQUIRED_FIELDS);\n"
            "  return minimized;\n"
            "}\n"
        ),
        file_pattern="**/data/*.ts",
        tags=["minimization"],
    ),
    # HIPAA
    FixTemplate(
        id="hipaa-phi-encryption",
        framework="hipaa",
        violation_pattern="unencrypted_phi",
        description="Encrypt PHI data at rest and in transit",
        language=FixLanguage.PYTHON,
        template_code=(
            "from cryptography.fernet import Fernet\n\n"
            "def encrypt_phi(data: bytes, key: bytes) -> bytes:\n"
            '    """Encrypt PHI per HIPAA §164.312(a)(2)(iv)."""\n'
            "    f = Fernet(key)\n"
            "    return f.encrypt(data)\n\n"
            "def decrypt_phi(token: bytes, key: bytes) -> bytes:\n"
            "    f = Fernet(key)\n"
            "    return f.decrypt(token)\n"
        ),
        file_pattern="**/health/*.py",
        tags=["encryption", "phi"],
    ),
    FixTemplate(
        id="hipaa-audit-logging",
        framework="hipaa",
        violation_pattern="missing_audit_log",
        description="Add HIPAA-compliant audit logging for PHI access",
        language=FixLanguage.PYTHON,
        template_code=(
            "import structlog\n\n"
            "audit_logger = structlog.get_logger('hipaa_audit')\n\n"
            "def log_phi_access(\n"
            "    user_id: str, patient_id: str, action: str, reason: str,\n"
            ") -> None:\n"
            '    """Log PHI access per HIPAA §164.312(b)."""\n'
            "    audit_logger.info(\n"
            "        'phi_access',\n"
            "        user_id=user_id, patient_id=patient_id,\n"
            "        action=action, reason=reason,\n"
            "    )\n"
        ),
        file_pattern="**/health/*.py",
        tags=["audit", "phi-access"],
    ),
    # PCI-DSS
    FixTemplate(
        id="pci-card-tokenization",
        framework="pci-dss",
        violation_pattern="raw_card_storage",
        description="Tokenize card data before storage (PCI-DSS Req 3.4)",
        language=FixLanguage.PYTHON,
        template_code=(
            "import hashlib\nimport secrets\n\n"
            "def tokenize_card(card_number: str) -> str:\n"
            '    """Replace card number with irreversible token (PCI-DSS 3.4)."""\n'
            "    salt = secrets.token_hex(16)\n"
            "    token = hashlib.sha256(f'{salt}:{card_number}'.encode()).hexdigest()\n"
            "    return f'tok_{token[:24]}'\n"
        ),
        file_pattern="**/payments/*.py",
        tags=["tokenization", "card-data"],
    ),
    # SOC 2
    FixTemplate(
        id="soc2-access-logging",
        framework="soc2",
        violation_pattern="missing_access_log",
        description="Add access logging for SOC 2 CC6.1 control",
        language=FixLanguage.PYTHON,
        template_code=(
            "from datetime import datetime, UTC\n\n"
            "async def log_access_event(\n"
            "    user_id: str, resource: str, action: str, result: str,\n"
            ") -> None:\n"
            '    """Log access event for SOC 2 CC6.1."""\n'
            "    await audit_store.insert({\n"
            "        'user_id': user_id, 'resource': resource,\n"
            "        'action': action, 'result': result,\n"
            "        'timestamp': datetime.now(UTC).isoformat(),\n"
            "    })\n"
        ),
        file_pattern="**/auth/*.py",
        tags=["access-control", "audit"],
    ),
    # EU AI Act
    FixTemplate(
        id="euai-transparency-notice",
        framework="eu-ai-act",
        violation_pattern="missing_ai_disclosure",
        description="Add AI system transparency notice (EU AI Act Art. 52)",
        language=FixLanguage.TYPESCRIPT,
        template_code=(
            "export function AITransparencyNotice({ systemName }: { systemName: string }) {\n"
            "  return (\n"
            "    <div role='alert' className='ai-disclosure'>\n"
            "      <p>This content is generated by an AI system ({systemName}).</p>\n"
            "      <p>Outputs should be verified by a human before use in decisions.</p>\n"
            "    </div>\n"
            "  );\n"
            "}\n"
        ),
        file_pattern="**/components/*.tsx",
        tags=["transparency", "ai-disclosure"],
    ),
]


def get_templates_for_framework(framework: str) -> list[FixTemplate]:
    """Get all fix templates for a given regulatory framework."""
    return [t for t in BUILTIN_TEMPLATES if t.framework == framework.lower()]


def get_template_by_id(template_id: str) -> FixTemplate | None:
    """Get a specific template by ID."""
    for t in BUILTIN_TEMPLATES:
        if t.id == template_id:
            return t
    return None


def apply_template(
    template: FixTemplate,
    variables: dict[str, str] | None = None,
    file_path: str = "",
) -> RemediationFix:
    """Instantiate a fix template with provided variables."""
    code = template.template_code
    for key, value in (variables or {}).items():
        code = code.replace(f"{{{key}}}", value)

    return RemediationFix(
        file_path=file_path or template.file_pattern.replace("**", "src"),
        original_code="# Non-compliant code",
        fixed_code=code,
        description=template.description,
        violation_ref=template.violation_pattern,
        confidence=template.confidence,
    )
