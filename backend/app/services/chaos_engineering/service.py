"""Compliance Chaos Engineering service."""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID, uuid4

import structlog

from app.services.chaos_engineering.models import (
    ChaosExperiment,
    ChaosStats,
    ExperimentStatus,
    ExperimentType,
    GameDay,
)

logger = structlog.get_logger()

_EXPERIMENTS: list[ChaosExperiment] = [
    ChaosExperiment(
        id=uuid4(), name="Encryption Kill Switch",
        description="Disable TLS encryption on the user API service to test detection of unencrypted data in transit.",
        experiment_type=ExperimentType.REMOVE_ENCRYPTION,
        status=ExperimentStatus.COMPLETED,
        target_service="user-api", target_environment="staging",
        affected_frameworks=["GDPR", "PCI-DSS", "HIPAA"],
        time_to_detect_seconds=45.0, time_to_remediate_seconds=180.0,
        detection_method="drift_detection_service",
        started_at=datetime.utcnow() - timedelta(days=7),
        completed_at=datetime.utcnow() - timedelta(days=7) + timedelta(minutes=5),
    ),
    ChaosExperiment(
        id=uuid4(), name="Audit Log Black Hole",
        description="Silently drop all audit log events for the payment processing service.",
        experiment_type=ExperimentType.DISABLE_AUDIT_LOGS,
        status=ExperimentStatus.COMPLETED,
        target_service="payment-service", target_environment="staging",
        affected_frameworks=["PCI-DSS", "SOC 2"],
        time_to_detect_seconds=None, time_to_remediate_seconds=None,
        detection_method="none",
        started_at=datetime.utcnow() - timedelta(days=5),
        completed_at=datetime.utcnow() - timedelta(days=5) + timedelta(minutes=10),
    ),
    ChaosExperiment(
        id=uuid4(), name="PII Exposure Probe",
        description="Add unmasked PII fields to API responses to test output filtering.",
        experiment_type=ExperimentType.EXPOSE_PII,
        status=ExperimentStatus.DETECTED,
        target_service="profile-api", target_environment="staging",
        affected_frameworks=["GDPR", "HIPAA"],
        time_to_detect_seconds=12.5, time_to_remediate_seconds=60.0,
        detection_method="ide_linting_service",
        started_at=datetime.utcnow() - timedelta(hours=2),
    ),
    ChaosExperiment(
        id=uuid4(), name="Auth Bypass Injection",
        description="Disable JWT validation middleware on admin endpoints.",
        experiment_type=ExperimentType.BREAK_AUTH,
        status=ExperimentStatus.SCHEDULED,
        target_service="admin-api", target_environment="staging",
        affected_frameworks=["SOC 2", "ISO 27001"],
    ),
]

_GAME_DAYS: list[GameDay] = [
    GameDay(
        id=uuid4(), name="Q1 2025 Compliance Drill",
        description="Quarterly compliance chaos drill: 5 experiments across 3 services.",
        experiments=[e.id for e in _EXPERIMENTS[:3]],
        participants=["Security Team", "Compliance Team", "Platform Team"],
        team_readiness_score=72.5, total_experiments=3, experiments_detected=2,
        avg_detection_time_seconds=28.75, avg_remediation_time_seconds=120.0,
        scheduled_at=datetime.utcnow() - timedelta(days=7),
        completed_at=datetime.utcnow() - timedelta(days=7) + timedelta(hours=2),
    ),
]


class ChaosEngineeringService:
    """Service for compliance chaos engineering."""

    async def list_experiments(
        self, status: ExperimentStatus | None = None,
    ) -> list[ChaosExperiment]:
        if status:
            return [e for e in _EXPERIMENTS if e.status == status]
        return list(_EXPERIMENTS)

    async def get_experiment(self, experiment_id: UUID) -> ChaosExperiment | None:
        return next((e for e in _EXPERIMENTS if e.id == experiment_id), None)

    async def create_experiment(
        self, name: str, description: str,
        experiment_type: ExperimentType, target_service: str,
        target_environment: str = "staging",
    ) -> ChaosExperiment:
        if target_environment == "production":
            raise ValueError("Chaos experiments cannot target production")
        exp = ChaosExperiment(
            id=uuid4(), name=name, description=description,
            experiment_type=experiment_type, target_service=target_service,
            target_environment=target_environment,
        )
        _EXPERIMENTS.append(exp)
        logger.info("chaos.experiment_created", name=name, type=experiment_type.value)
        return exp

    async def run_experiment(self, experiment_id: UUID) -> ChaosExperiment:
        exp = await self.get_experiment(experiment_id)
        if not exp:
            raise ValueError(f"Experiment {experiment_id} not found")
        if exp.status != ExperimentStatus.SCHEDULED:
            raise ValueError(f"Experiment {experiment_id} cannot be run (status: {exp.status.value}); must be SCHEDULED")
        exp.status = ExperimentStatus.RUNNING
        exp.started_at = datetime.utcnow()
        logger.info("chaos.experiment_started", experiment_id=str(experiment_id))
        return exp

    async def list_game_days(self) -> list[GameDay]:
        return list(_GAME_DAYS)

    async def get_stats(self) -> ChaosStats:
        completed = [e for e in _EXPERIMENTS if e.status == ExperimentStatus.COMPLETED]
        detected = [e for e in completed if e.time_to_detect_seconds is not None]
        undetected = [e for e in completed if e.time_to_detect_seconds is None]
        avg_mttd = sum(e.time_to_detect_seconds for e in detected if e.time_to_detect_seconds) / max(len(detected), 1)
        avg_mttr = sum(e.time_to_remediate_seconds for e in detected if e.time_to_remediate_seconds) / max(len(detected), 1)
        return ChaosStats(
            total_experiments=len(_EXPERIMENTS),
            experiments_detected=len(detected),
            experiments_undetected=len(undetected),
            avg_mttd_seconds=avg_mttd, avg_mttr_seconds=avg_mttr,
            detection_rate=len(detected) / max(len(completed), 1),
            game_days_completed=len(_GAME_DAYS),
            controls_validated=len(detected) * 2,
            blind_spots_found=len(undetected),
        )
