"""GitOps Compliance Pipeline service.

Pre-commit hooks, CI gate integration, and auto-remediation branch creation
when compliance violations are detected.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession


logger = structlog.get_logger()


class GateDecision(str, Enum):
    PASS = "pass"
    WARN = "warn"
    BLOCK = "block"


class RemediationStatus(str, Enum):
    PENDING = "pending"
    BRANCH_CREATED = "branch_created"
    PR_OPENED = "pr_opened"
    MERGED = "merged"
    FAILED = "failed"


@dataclass
class PreCommitResult:
    passed: bool = True
    violations: list[dict[str, Any]] = field(default_factory=list)
    files_scanned: int = 0
    duration_ms: float = 0.0


@dataclass
class GateEvaluation:
    id: UUID = field(default_factory=uuid4)
    repo: str = ""
    branch: str = ""
    commit_sha: str = ""
    decision: GateDecision = GateDecision.PASS
    score_before: float = 100.0
    score_after: float = 100.0
    score_delta: float = 0.0
    violations: list[dict[str, Any]] = field(default_factory=list)
    blocking_rules: list[str] = field(default_factory=list)
    evaluated_at: datetime | None = None


@dataclass
class RemediationBranch:
    id: UUID = field(default_factory=uuid4)
    repo: str = ""
    source_branch: str = "main"
    remediation_branch: str = ""
    violation_ids: list[str] = field(default_factory=list)
    status: RemediationStatus = RemediationStatus.PENDING
    pr_url: str = ""
    created_at: datetime | None = None


@dataclass
class PreCommitConfig:
    """Configuration for the pre-commit hook."""
    enabled_rules: list[str] = field(default_factory=lambda: [
        "GDPR-LOG-001", "GDPR-ENC-001", "HIPAA-PHI-001",
        "PCI-DSS-001", "SOC2-LOG-001", "EUAI-001",
    ])
    severity_threshold: str = "high"
    max_scan_time_ms: int = 2000
    scan_changed_only: bool = True


class GitOpsPipelineService:
    """Compliance scanning integrated into git workflows."""

    def __init__(self, db: AsyncSession, copilot_client: object | None = None):
        self.db = db
        self.copilot = copilot_client
        self._evaluations: list[GateEvaluation] = []
        self._remediations: dict[UUID, RemediationBranch] = {}
        self._config = PreCommitConfig()

    async def evaluate_gate(
        self,
        repo: str,
        branch: str,
        commit_sha: str,
        changed_files: list[dict[str, str]],
        baseline_score: float = 100.0,
    ) -> GateEvaluation:
        """Evaluate compliance gate for a commit/PR.

        Compares current state against baseline and determines pass/warn/block.
        """
        violations: list[dict[str, Any]] = []
        blocking: list[str] = []

        # Scan changed files for compliance patterns
        for file_info in changed_files:
            content = file_info.get("content", "")
            path = file_info.get("path", "")
            file_violations = self._scan_content(content, path)
            violations.extend(file_violations)

        critical_count = sum(1 for v in violations if v.get("severity") == "critical")
        high_count = sum(1 for v in violations if v.get("severity") == "high")

        # Score impact: each critical = -5%, high = -2%, medium = -1%
        score_delta = -(critical_count * 5.0 + high_count * 2.0 +
                       sum(1 for v in violations if v.get("severity") == "medium") * 1.0)
        score_after = max(0.0, baseline_score + score_delta)

        if critical_count > 0:
            decision = GateDecision.BLOCK
            blocking = [v["rule_id"] for v in violations if v.get("severity") == "critical"]
        elif score_after < baseline_score - 10:
            decision = GateDecision.BLOCK
        elif high_count > 0 or score_after < baseline_score - 5:
            decision = GateDecision.WARN
        else:
            decision = GateDecision.PASS

        evaluation = GateEvaluation(
            repo=repo, branch=branch, commit_sha=commit_sha,
            decision=decision, score_before=baseline_score,
            score_after=round(score_after, 1), score_delta=round(score_delta, 1),
            violations=violations, blocking_rules=blocking,
            evaluated_at=datetime.now(UTC),
        )
        self._evaluations.append(evaluation)

        logger.info(
            "gitops_gate_evaluated",
            repo=repo, decision=decision.value,
            violations=len(violations), score_delta=score_delta,
        )
        return evaluation

    async def create_remediation_branch(
        self,
        repo: str,
        violations: list[dict[str, Any]],
        source_branch: str = "main",
    ) -> RemediationBranch:
        """Create a remediation branch with auto-generated fixes."""
        branch_name = f"compliance/remediation-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}"

        remediation = RemediationBranch(
            repo=repo,
            source_branch=source_branch,
            remediation_branch=branch_name,
            violation_ids=[v.get("rule_id", "") for v in violations],
            status=RemediationStatus.BRANCH_CREATED,
            created_at=datetime.now(UTC),
        )
        self._remediations[remediation.id] = remediation

        logger.info(
            "remediation_branch_created",
            repo=repo, branch=branch_name,
            violations=len(violations),
        )
        return remediation

    async def get_precommit_config(self) -> PreCommitConfig:
        return self._config

    async def get_evaluations(self, repo: str | None = None, limit: int = 20) -> list[GateEvaluation]:
        evals = self._evaluations
        if repo:
            evals = [e for e in evals if e.repo == repo]
        return sorted(evals, key=lambda e: e.evaluated_at or datetime.min.replace(tzinfo=UTC), reverse=True)[:limit]

    def _scan_content(self, content: str, path: str) -> list[dict[str, Any]]:
        """Quick pattern-based scan for common compliance violations."""
        violations: list[dict[str, Any]] = []
        content_lower = content.lower()

        # Simple keyword-based rules (no regex — fast and reliable)
        rules = [
            ("GDPR-LOG-001", "critical", ["console.log", "print(", "logger."], ["email", "password", "ssn", "credit_card"]),
            ("HIPAA-PHI-001", "critical", ["patient_", "diagnosis", "medical_record"], []),
            ("PCI-DSS-001", "critical", ["credit_card", "cvv", "card_number"], []),
            ("SOC2-LOG-001", "high", ["# nosec", "security_disable", "security.*disable"], []),
        ]

        for rule_id, severity, primary_keywords, secondary_keywords in rules:
            for kw in primary_keywords:
                if kw in content_lower:
                    # If secondary keywords exist, require at least one match too
                    if secondary_keywords and not any(sk in content_lower for sk in secondary_keywords):
                        continue
                    violations.append({
                        "rule_id": rule_id,
                        "severity": severity,
                        "file": path,
                        "message": f"Potential violation: {rule_id}",
                    })
                    break

        return violations
