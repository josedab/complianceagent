"""Configurable policy enforcement gates for PR compliance checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

import structlog


logger = structlog.get_logger()


class GateAction(str, Enum):
    BLOCK = "block"
    WARN = "warn"
    REQUIRE_APPROVAL = "require_approval"
    LOG_ONLY = "log_only"


class GateStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    PENDING_APPROVAL = "pending_approval"
    SKIPPED = "skipped"


@dataclass
class PolicyGate:
    """A configurable policy enforcement gate."""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    regulation: str = ""
    condition: str = ""  # e.g., "touches_pii", "modifies_auth", "cross_border_data"
    action: GateAction = GateAction.WARN
    required_approvers: list[str] = field(default_factory=list)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class GateEvaluationResult:
    """Result of evaluating a PR against a policy gate."""
    gate_id: UUID = field(default_factory=uuid4)
    gate_name: str = ""
    status: GateStatus = GateStatus.PASSED
    action: GateAction = GateAction.LOG_ONLY
    reason: str = ""
    matched_files: list[str] = field(default_factory=list)
    required_approvers: list[str] = field(default_factory=list)
    evaluated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PolicyEvaluationSummary:
    """Summary of all gate evaluations for a PR."""
    pr_number: int = 0
    repository: str = ""
    overall_status: GateStatus = GateStatus.PASSED
    gates_evaluated: int = 0
    gates_passed: int = 0
    gates_failed: int = 0
    gates_pending: int = 0
    results: list[GateEvaluationResult] = field(default_factory=list)
    can_merge: bool = True
    evaluated_at: datetime = field(default_factory=datetime.utcnow)


# Condition matchers: file path patterns and content patterns that trigger gates
_CONDITION_MATCHERS: dict[str, dict[str, Any]] = {
    "touches_pii": {
        "file_patterns": ["**/models/user*", "**/auth/*", "**/profile*", "**/customer*"],
        "content_patterns": ["email", "phone", "ssn", "social_security", "date_of_birth", "address"],
        "description": "Changes touch files containing PII",
    },
    "modifies_auth": {
        "file_patterns": ["**/auth/*", "**/login*", "**/session*", "**/jwt*", "**/oauth*", "**/permission*"],
        "content_patterns": ["password", "token", "secret", "api_key", "credential"],
        "description": "Changes modify authentication or authorization logic",
    },
    "modifies_encryption": {
        "file_patterns": ["**/crypto*", "**/encrypt*", "**/security/*", "**/tls*"],
        "content_patterns": ["aes", "rsa", "encrypt", "decrypt", "cipher", "hash"],
        "description": "Changes modify encryption or cryptographic functions",
    },
    "cross_border_data": {
        "file_patterns": ["**/transfer*", "**/export*", "**/sync*", "**/replicate*"],
        "content_patterns": ["region", "jurisdiction", "cross_border", "data_transfer", "scc"],
        "description": "Changes may affect cross-border data transfers",
    },
    "modifies_logging": {
        "file_patterns": ["**/logging*", "**/audit*", "**/telemetry*", "**/monitoring*"],
        "content_patterns": ["log_level", "audit_trail", "log_format"],
        "description": "Changes modify logging or audit trail configuration",
    },
    "payment_processing": {
        "file_patterns": ["**/payment*", "**/billing*", "**/checkout*", "**/stripe*"],
        "content_patterns": ["card_number", "cvv", "pan", "payment_method", "charge"],
        "description": "Changes touch payment processing code",
    },
    "health_data": {
        "file_patterns": ["**/patient*", "**/medical*", "**/health*", "**/clinical*", "**/ehr*"],
        "content_patterns": ["diagnosis", "prescription", "medical_record", "phi", "hipaa"],
        "description": "Changes touch health/medical data handling",
    },
    "infrastructure_change": {
        "file_patterns": ["**/terraform/*", "**/cloudformation/*", "**/k8s/*", "**/*.tf", "**/docker*"],
        "content_patterns": ["aws_", "gcp_", "azure_", "resource", "provider"],
        "description": "Changes modify infrastructure configuration",
    },
    "third_party_dependency": {
        "file_patterns": ["**/requirements*.txt", "**/package.json", "**/go.mod", "**/Cargo.toml", "**/pom.xml"],
        "content_patterns": [],
        "description": "Changes add or modify third-party dependencies",
    },
    "data_retention": {
        "file_patterns": ["**/retention*", "**/cleanup*", "**/purge*", "**/archive*", "**/ttl*"],
        "content_patterns": ["retention_days", "expiry", "delete_after", "purge", "ttl"],
        "description": "Changes affect data retention or deletion policies",
    },
}


class PolicyGateService:
    """Service for managing and evaluating PR policy enforcement gates."""

    def __init__(self):
        self._gates: dict[UUID, PolicyGate] = {}
        self._evaluations: dict[str, PolicyEvaluationSummary] = {}
        self._init_default_gates()

    def _init_default_gates(self) -> None:
        """Initialize default policy gates."""
        defaults = [
            PolicyGate(name="PII Protection Gate", description="Require privacy team approval for changes touching PII",
                       regulation="GDPR", condition="touches_pii", action=GateAction.REQUIRE_APPROVAL,
                       required_approvers=["privacy-team"]),
            PolicyGate(name="Authentication Security Gate", description="Block merging if auth changes lack security review",
                       regulation="SOC 2", condition="modifies_auth", action=GateAction.REQUIRE_APPROVAL,
                       required_approvers=["security-team"]),
            PolicyGate(name="Encryption Compliance Gate", description="Warn on encryption changes for HIPAA compliance",
                       regulation="HIPAA", condition="modifies_encryption", action=GateAction.WARN),
            PolicyGate(name="Cross-Border Data Gate", description="Block cross-border data transfers without legal review",
                       regulation="GDPR", condition="cross_border_data", action=GateAction.BLOCK),
            PolicyGate(name="Payment Data Gate", description="Require PCI-DSS review for payment code changes",
                       regulation="PCI-DSS", condition="payment_processing", action=GateAction.REQUIRE_APPROVAL,
                       required_approvers=["pci-compliance"]),
            PolicyGate(name="Health Data Gate", description="Block health data changes without HIPAA review",
                       regulation="HIPAA", condition="health_data", action=GateAction.BLOCK),
            PolicyGate(name="Infrastructure Change Gate", description="Warn on infrastructure changes for SOC 2",
                       regulation="SOC 2", condition="infrastructure_change", action=GateAction.WARN),
            PolicyGate(name="Dependency Review Gate", description="Log third-party dependency changes for supply chain review",
                       regulation="SOC 2", condition="third_party_dependency", action=GateAction.LOG_ONLY),
            PolicyGate(name="Audit Trail Gate", description="Require approval for logging/audit changes",
                       regulation="SOC 2", condition="modifies_logging", action=GateAction.REQUIRE_APPROVAL,
                       required_approvers=["compliance-team"]),
            PolicyGate(name="Data Retention Gate", description="Warn on data retention policy changes",
                       regulation="GDPR", condition="data_retention", action=GateAction.WARN),
        ]
        for gate in defaults:
            self._gates[gate.id] = gate

    async def list_gates(self, enabled_only: bool = False) -> list[PolicyGate]:
        gates = list(self._gates.values())
        if enabled_only:
            gates = [g for g in gates if g.enabled]
        return sorted(gates, key=lambda g: g.name)

    async def get_gate(self, gate_id: UUID) -> PolicyGate | None:
        return self._gates.get(gate_id)

    async def create_gate(self, name: str, description: str, regulation: str,
                          condition: str, action: GateAction,
                          required_approvers: list[str] | None = None) -> PolicyGate:
        if condition not in _CONDITION_MATCHERS:
            msg = f"Unknown condition: {condition}. Available: {', '.join(_CONDITION_MATCHERS.keys())}"
            raise ValueError(msg)
        gate = PolicyGate(
            name=name, description=description, regulation=regulation,
            condition=condition, action=action,
            required_approvers=required_approvers or [],
        )
        self._gates[gate.id] = gate
        logger.info("policy_gate.created", gate_id=str(gate.id), name=name)
        return gate

    async def update_gate(self, gate_id: UUID, **kwargs) -> PolicyGate | None:
        gate = self._gates.get(gate_id)
        if not gate:
            return None
        for key, value in kwargs.items():
            if hasattr(gate, key) and value is not None:
                setattr(gate, key, value)
        logger.info("policy_gate.updated", gate_id=str(gate_id))
        return gate

    async def delete_gate(self, gate_id: UUID) -> bool:
        if gate_id in self._gates:
            del self._gates[gate_id]
            logger.info("policy_gate.deleted", gate_id=str(gate_id))
            return True
        return False

    async def evaluate_pr(self, pr_number: int, repository: str,
                          changed_files: list[dict[str, Any]]) -> PolicyEvaluationSummary:
        """Evaluate a PR against all enabled policy gates."""
        import fnmatch

        enabled_gates = [g for g in self._gates.values() if g.enabled]
        results: list[GateEvaluationResult] = []

        for gate in enabled_gates:
            matcher = _CONDITION_MATCHERS.get(gate.condition)
            if not matcher:
                continue

            matched_files: list[str] = []
            for file_info in changed_files:
                file_path = file_info.get("filename", file_info.get("path", ""))
                content = file_info.get("patch", file_info.get("content", ""))

                # Check file patterns
                for pattern in matcher.get("file_patterns", []):
                    if fnmatch.fnmatch(file_path, pattern):
                        matched_files.append(file_path)
                        break

                # Check content patterns
                if file_path not in matched_files:
                    for pattern in matcher.get("content_patterns", []):
                        if pattern.lower() in content.lower():
                            matched_files.append(file_path)
                            break

            if matched_files:
                status = GateStatus.FAILED if gate.action == GateAction.BLOCK else (
                    GateStatus.PENDING_APPROVAL if gate.action == GateAction.REQUIRE_APPROVAL else GateStatus.PASSED
                )
                results.append(GateEvaluationResult(
                    gate_id=gate.id, gate_name=gate.name, status=status,
                    action=gate.action, reason=matcher.get("description", ""),
                    matched_files=matched_files, required_approvers=gate.required_approvers,
                ))
            else:
                results.append(GateEvaluationResult(
                    gate_id=gate.id, gate_name=gate.name, status=GateStatus.PASSED,
                    action=gate.action, reason="No matching files",
                ))

        gates_failed = sum(1 for r in results if r.status == GateStatus.FAILED)
        gates_pending = sum(1 for r in results if r.status == GateStatus.PENDING_APPROVAL)
        gates_passed = sum(1 for r in results if r.status == GateStatus.PASSED)

        overall = GateStatus.FAILED if gates_failed > 0 else (
            GateStatus.PENDING_APPROVAL if gates_pending > 0 else GateStatus.PASSED
        )

        summary = PolicyEvaluationSummary(
            pr_number=pr_number, repository=repository, overall_status=overall,
            gates_evaluated=len(results), gates_passed=gates_passed,
            gates_failed=gates_failed, gates_pending=gates_pending,
            results=results, can_merge=(gates_failed == 0),
        )

        eval_key = f"{repository}#{pr_number}"
        self._evaluations[eval_key] = summary
        logger.info("policy_gate.evaluated", pr=pr_number, repo=repository,
                     status=overall.value, can_merge=summary.can_merge)
        return summary

    async def get_evaluation(self, repository: str, pr_number: int) -> PolicyEvaluationSummary | None:
        return self._evaluations.get(f"{repository}#{pr_number}")

    async def get_available_conditions(self) -> dict[str, dict[str, Any]]:
        return {k: {"description": v["description"], "file_patterns": v["file_patterns"]}
                for k, v in _CONDITION_MATCHERS.items()}


_policy_gate_service: PolicyGateService | None = None


def get_policy_gate_service() -> PolicyGateService:
    global _policy_gate_service
    if _policy_gate_service is None:
        _policy_gate_service = PolicyGateService()
    return _policy_gate_service
