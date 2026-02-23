"""CI/CD runtime compliance service."""

from __future__ import annotations

import hashlib
import time
import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    AttestationLevel,
    CICDRuntimeStats,
    DeploymentAttestation,
    DeploymentPhase,
    GateDecision,
    RollbackEvent,
    RuntimeCheck,
)


logger = structlog.get_logger(__name__)


class CICDRuntimeService:
    """Service for CI/CD runtime compliance checks."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._checks: list[RuntimeCheck] = []
        self._attestations: list[DeploymentAttestation] = []
        self._rollbacks: list[RollbackEvent] = []
        self._seed_frameworks = [
            "SOC2",
            "GDPR",
            "HIPAA",
            "PCI-DSS",
            "ISO27001",
        ]
        self._violation_patterns: dict[str, list[dict]] = {
            "secrets": [
                {"rule": "no-hardcoded-secrets", "severity": "critical"},
            ],
            "deps": [
                {"rule": "no-vulnerable-deps", "severity": "high"},
            ],
            "config": [
                {"rule": "secure-defaults", "severity": "medium"},
            ],
            "iac": [
                {"rule": "no-public-buckets", "severity": "high"},
            ],
        }

    async def check_deployment(
        self,
        deployment_id: str,
        repo: str,
        commit_sha: str,
        phase: str = "pre_deploy",
    ) -> RuntimeCheck:
        """Run compliance checks against a deployment."""
        start = time.monotonic()
        violations: list[dict] = []
        checks_passed = 0
        checks_failed = 0

        for pattern_name, rules in self._violation_patterns.items():
            if pattern_name in repo.lower() or pattern_name in commit_sha.lower():
                for rule in rules:
                    violations.append(
                        {
                            "pattern": pattern_name,
                            "rule": rule["rule"],
                            "severity": rule["severity"],
                        }
                    )
                    checks_failed += 1
            else:
                checks_passed += 1

        if checks_failed > 0:
            gate_decision = GateDecision.fail_gate
        elif violations:
            gate_decision = GateDecision.warn
        else:
            gate_decision = GateDecision.pass_gate

        duration_ms = (time.monotonic() - start) * 1000.0

        check = RuntimeCheck(
            id=uuid.uuid4(),
            deployment_id=deployment_id,
            repo=repo,
            phase=DeploymentPhase(phase),
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            gate_decision=gate_decision,
            violations=violations,
            duration_ms=duration_ms,
            checked_at=datetime.now(UTC),
        )
        self._checks.append(check)

        await logger.ainfo(
            "deployment_checked",
            deployment_id=deployment_id,
            gate_decision=gate_decision.value,
        )
        return check

    async def create_attestation(
        self,
        deployment_id: str,
        repo: str,
        commit_sha: str,
        score: float,
        frameworks: list[str] | None = None,
    ) -> DeploymentAttestation:
        """Create a deployment attestation with a hash signature."""
        checked_frameworks = frameworks or self._seed_frameworks[:3]

        if score >= 95.0:
            level = AttestationLevel.certified
        elif score >= 80.0:
            level = AttestationLevel.verified
        elif score >= 60.0:
            level = AttestationLevel.signed
        else:
            level = AttestationLevel.unsigned

        payload = f"{deployment_id}:{repo}:{commit_sha}:{score}"
        signature = hashlib.sha256(payload.encode()).hexdigest()

        attestation = DeploymentAttestation(
            id=uuid.uuid4(),
            deployment_id=deployment_id,
            repo=repo,
            commit_sha=commit_sha,
            level=level,
            compliance_score=score,
            frameworks_checked=checked_frameworks,
            signature=signature,
            attested_at=datetime.now(UTC),
        )
        self._attestations.append(attestation)

        await logger.ainfo(
            "attestation_created",
            deployment_id=deployment_id,
            level=level.value,
        )
        return attestation

    async def trigger_rollback(
        self,
        deployment_id: str,
        reason: str,
        scores: tuple[float, float],
    ) -> RollbackEvent:
        """Trigger a rollback for a deployment."""
        event = RollbackEvent(
            id=uuid.uuid4(),
            deployment_id=deployment_id,
            reason=reason,
            original_score=scores[0],
            new_score=scores[1],
            rolled_back_at=datetime.now(UTC),
        )
        self._rollbacks.append(event)

        await logger.ainfo(
            "rollback_triggered",
            deployment_id=deployment_id,
            reason=reason,
        )
        return event

    async def list_checks(
        self,
        deployment_id: str | None = None,
    ) -> list[RuntimeCheck]:
        """List runtime checks, optionally filtered by deployment."""
        if deployment_id:
            return [
                c for c in self._checks if c.deployment_id == deployment_id
            ]
        return list(self._checks)

    async def list_attestations(
        self,
        deployment_id: str | None = None,
    ) -> list[DeploymentAttestation]:
        """List attestations, optionally filtered by deployment."""
        if deployment_id:
            return [
                a
                for a in self._attestations
                if a.deployment_id == deployment_id
            ]
        return list(self._attestations)

    async def get_stats(self) -> CICDRuntimeStats:
        """Get aggregate CI/CD runtime statistics."""
        total = len(self._checks)
        gated = sum(
            1
            for c in self._checks
            if c.gate_decision == GateDecision.fail_gate
        )
        passed = sum(
            1
            for c in self._checks
            if c.gate_decision == GateDecision.pass_gate
        )
        durations = [c.duration_ms for c in self._checks]
        avg_duration = sum(durations) / len(durations) if durations else 0.0
        pass_rate = (passed / total * 100.0) if total else 0.0

        return CICDRuntimeStats(
            total_checks=total,
            deployments_gated=gated,
            rollbacks=len(self._rollbacks),
            attestations_issued=len(self._attestations),
            avg_check_duration_ms=avg_duration,
            pass_rate=pass_rate,
        )
