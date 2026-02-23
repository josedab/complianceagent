"""CI/CD runtime compliance models."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class GateDecision(str, Enum):
    """Decision made at a deployment gate."""

    pass_gate = "pass_gate"  # noqa: S105
    fail_gate = "fail_gate"
    warn = "warn"
    skip = "skip"


class DeploymentPhase(str, Enum):
    """Phase of a deployment pipeline."""

    pre_deploy = "pre_deploy"
    deploying = "deploying"
    post_deploy = "post_deploy"
    rollback = "rollback"


class AttestationLevel(str, Enum):
    """Level of deployment attestation."""

    unsigned = "unsigned"
    signed = "signed"
    verified = "verified"
    certified = "certified"


@dataclass
class RuntimeCheck:
    """Result of a CI/CD runtime compliance check."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    deployment_id: str = ""
    repo: str = ""
    phase: DeploymentPhase = DeploymentPhase.pre_deploy
    checks_passed: int = 0
    checks_failed: int = 0
    gate_decision: GateDecision = GateDecision.pass_gate
    violations: list[dict] = field(default_factory=list)
    duration_ms: float = 0.0
    checked_at: datetime | None = None


@dataclass
class DeploymentAttestation:
    """Attestation record for a deployment."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    deployment_id: str = ""
    repo: str = ""
    commit_sha: str = ""
    level: AttestationLevel = AttestationLevel.unsigned
    compliance_score: float = 0.0
    frameworks_checked: list[str] = field(default_factory=list)
    signature: str = ""
    attested_at: datetime | None = None


@dataclass
class RollbackEvent:
    """Record of a deployment rollback triggered by compliance."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    deployment_id: str = ""
    reason: str = ""
    original_score: float = 0.0
    new_score: float = 0.0
    rolled_back_at: datetime | None = None


@dataclass
class CICDRuntimeStats:
    """Aggregate statistics for CI/CD runtime checks."""

    total_checks: int = 0
    deployments_gated: int = 0
    rollbacks: int = 0
    attestations_issued: int = 0
    avg_check_duration_ms: float = 0.0
    pass_rate: float = 0.0
