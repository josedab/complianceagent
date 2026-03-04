"""Compliance Certification Autopilot Service."""

import secrets
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.cert_autopilot.models import (
    AuditorPortalSession,
    AutoCollectedEvidence,
    CertificationFramework,
    CertificationJourney,
    CertificationPhase,
    CertificationReadinessReport,
    ControlGap,
    EvidenceSourceType,
    GapAnalysisItem,
    GapStatus,
)


logger = structlog.get_logger()

_SOC2_CONTROLS = [
    ControlGap(
        control_id="CC1.1",
        control_name="Control Environment",
        framework=CertificationFramework.SOC2_TYPE2,
        evidence_needed=["Org chart", "Code of conduct"],
        remediation_steps=["Document control environment policies"],
        estimated_hours=8.0,
    ),
    ControlGap(
        control_id="CC2.1",
        control_name="Information and Communication",
        framework=CertificationFramework.SOC2_TYPE2,
        evidence_needed=["Communication policies", "Incident response plan"],
        remediation_steps=["Establish communication channels"],
        estimated_hours=6.0,
    ),
    ControlGap(
        control_id="CC3.1",
        control_name="Risk Assessment",
        framework=CertificationFramework.SOC2_TYPE2,
        evidence_needed=["Risk register", "Risk assessment report"],
        remediation_steps=["Conduct annual risk assessment"],
        estimated_hours=16.0,
    ),
    ControlGap(
        control_id="CC4.1",
        control_name="Monitoring Activities",
        framework=CertificationFramework.SOC2_TYPE2,
        evidence_needed=["Monitoring dashboards", "Alert configurations"],
        remediation_steps=["Implement continuous monitoring"],
        estimated_hours=20.0,
    ),
    ControlGap(
        control_id="CC5.1",
        control_name="Control Activities",
        framework=CertificationFramework.SOC2_TYPE2,
        evidence_needed=["Access control matrix", "Change management log"],
        remediation_steps=["Review and document control activities"],
        estimated_hours=12.0,
    ),
    ControlGap(
        control_id="CC6.1",
        control_name="Logical and Physical Access",
        framework=CertificationFramework.SOC2_TYPE2,
        evidence_needed=["Access reviews", "MFA configuration"],
        remediation_steps=["Enforce MFA for all systems", "Quarterly access reviews"],
        estimated_hours=24.0,
    ),
    ControlGap(
        control_id="CC7.1",
        control_name="System Operations",
        framework=CertificationFramework.SOC2_TYPE2,
        evidence_needed=["Incident logs", "Runbooks"],
        remediation_steps=["Document operational procedures"],
        estimated_hours=10.0,
    ),
    ControlGap(
        control_id="CC8.1",
        control_name="Change Management",
        framework=CertificationFramework.SOC2_TYPE2,
        evidence_needed=["Change request logs", "Approval workflows"],
        remediation_steps=["Implement change advisory board process"],
        estimated_hours=14.0,
    ),
    ControlGap(
        control_id="CC9.1",
        control_name="Risk Mitigation",
        framework=CertificationFramework.SOC2_TYPE2,
        evidence_needed=["Vendor assessments", "Insurance policies"],
        remediation_steps=["Complete vendor risk assessments"],
        estimated_hours=18.0,
    ),
    ControlGap(
        control_id="A1.1",
        control_name="Availability",
        framework=CertificationFramework.SOC2_TYPE2,
        evidence_needed=["SLA documentation", "Uptime reports"],
        remediation_steps=["Define and monitor SLAs"],
        estimated_hours=8.0,
    ),
    ControlGap(
        control_id="C1.1",
        control_name="Confidentiality",
        framework=CertificationFramework.SOC2_TYPE2,
        evidence_needed=["Encryption policies", "Data classification"],
        remediation_steps=["Encrypt data at rest and in transit"],
        estimated_hours=16.0,
    ),
]

_ISO27001_CONTROLS = [
    ControlGap(
        control_id="A.5",
        control_name="Information Security Policies",
        framework=CertificationFramework.ISO27001,
        evidence_needed=["ISMS policy document"],
        remediation_steps=["Draft and approve ISMS policy"],
        estimated_hours=12.0,
    ),
    ControlGap(
        control_id="A.6",
        control_name="Organization of Information Security",
        framework=CertificationFramework.ISO27001,
        evidence_needed=["Roles and responsibilities matrix"],
        remediation_steps=["Define security roles"],
        estimated_hours=8.0,
    ),
    ControlGap(
        control_id="A.7",
        control_name="Human Resource Security",
        framework=CertificationFramework.ISO27001,
        evidence_needed=["Background check policy", "Security training records"],
        remediation_steps=["Implement security awareness training"],
        estimated_hours=10.0,
    ),
    ControlGap(
        control_id="A.8",
        control_name="Asset Management",
        framework=CertificationFramework.ISO27001,
        evidence_needed=["Asset inventory", "Data classification policy"],
        remediation_steps=["Create and maintain asset register"],
        estimated_hours=14.0,
    ),
    ControlGap(
        control_id="A.9",
        control_name="Access Control",
        framework=CertificationFramework.ISO27001,
        evidence_needed=["Access control policy", "User access reviews"],
        remediation_steps=["Implement least privilege access"],
        estimated_hours=20.0,
    ),
    ControlGap(
        control_id="A.10",
        control_name="Cryptography",
        framework=CertificationFramework.ISO27001,
        evidence_needed=["Encryption standards document", "Key management procedure"],
        remediation_steps=["Define cryptographic controls"],
        estimated_hours=12.0,
    ),
    ControlGap(
        control_id="A.12",
        control_name="Operations Security",
        framework=CertificationFramework.ISO27001,
        evidence_needed=["Change management procedures", "Capacity plans"],
        remediation_steps=["Document operational procedures"],
        estimated_hours=16.0,
    ),
    ControlGap(
        control_id="A.13",
        control_name="Communications Security",
        framework=CertificationFramework.ISO27001,
        evidence_needed=["Network security policy", "Firewall rules"],
        remediation_steps=["Implement network segmentation"],
        estimated_hours=18.0,
    ),
    ControlGap(
        control_id="A.16",
        control_name="Incident Management",
        framework=CertificationFramework.ISO27001,
        evidence_needed=["Incident response plan", "Incident log"],
        remediation_steps=["Establish incident response team"],
        estimated_hours=14.0,
    ),
    ControlGap(
        control_id="A.18",
        control_name="Compliance",
        framework=CertificationFramework.ISO27001,
        evidence_needed=["Legal requirements register", "Audit reports"],
        remediation_steps=["Identify applicable legal requirements"],
        estimated_hours=10.0,
    ),
]

_CONTROL_REGISTRY: dict[CertificationFramework, list[ControlGap]] = {
    CertificationFramework.SOC2_TYPE2: _SOC2_CONTROLS,
    CertificationFramework.ISO27001: _ISO27001_CONTROLS,
}

_PHASE_ORDER = list(CertificationPhase)

# Maps control IDs to evidence source types that can auto-collect for them
_AUTO_COLLECTION_MAP: dict[str, list[EvidenceSourceType]] = {
    # SOC 2 controls
    "CC4.1": [EvidenceSourceType.CI_CD_PIPELINE, EvidenceSourceType.CLOUD_CONFIG],
    "CC5.1": [EvidenceSourceType.ACCESS_LOG, EvidenceSourceType.GIT_COMMIT],
    "CC6.1": [EvidenceSourceType.ACCESS_LOG, EvidenceSourceType.CLOUD_CONFIG],
    "CC7.1": [EvidenceSourceType.CI_CD_PIPELINE, EvidenceSourceType.ACCESS_LOG],
    "CC8.1": [EvidenceSourceType.GIT_COMMIT, EvidenceSourceType.CI_CD_PIPELINE],
    "A1.1": [EvidenceSourceType.CLOUD_CONFIG, EvidenceSourceType.CI_CD_PIPELINE],
    "C1.1": [EvidenceSourceType.CLOUD_CONFIG],
    # ISO 27001 controls
    "A.9": [EvidenceSourceType.ACCESS_LOG, EvidenceSourceType.CLOUD_CONFIG],
    "A.10": [EvidenceSourceType.CLOUD_CONFIG],
    "A.12": [EvidenceSourceType.GIT_COMMIT, EvidenceSourceType.CI_CD_PIPELINE],
    "A.13": [EvidenceSourceType.CLOUD_CONFIG],
    "A.16": [EvidenceSourceType.ACCESS_LOG, EvidenceSourceType.CI_CD_PIPELINE],
}

# Cross-framework control mappings (SOC 2 <-> ISO 27001)
_CROSS_FRAMEWORK_MAP: dict[str, list[str]] = {
    "CC5.1": ["A.9"],
    "CC6.1": ["A.9"],
    "CC7.1": ["A.12", "A.16"],
    "CC8.1": ["A.12"],
    "C1.1": ["A.10"],
    "A.9": ["CC5.1", "CC6.1"],
    "A.10": ["C1.1"],
    "A.12": ["CC7.1", "CC8.1"],
    "A.16": ["CC7.1"],
}

_TARGET_AUTO_COLLECTION_RATE = 80.0


class CertificationAutopilotService:
    """Service for managing compliance certification journeys."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._journeys: list[CertificationJourney] = []
        self._gaps: dict[str, list[ControlGap]] = {}
        self._gap_analysis_items: dict[str, list[GapAnalysisItem]] = {}
        self._auto_collected_evidence: dict[str, list[AutoCollectedEvidence]] = {}
        self._auditor_sessions: dict[str, list[AuditorPortalSession]] = {}
        self._readiness_reports: dict[str, list[CertificationReadinessReport]] = {}

    # ── Existing journey management ──────────────────────────────────────

    async def start_journey(
        self,
        framework: CertificationFramework,
        organization_id: str,
    ) -> CertificationJourney:
        """Start a new certification journey."""
        controls = _CONTROL_REGISTRY.get(framework, [])
        journey = CertificationJourney(
            framework=framework,
            organization_id=organization_id,
            current_phase=CertificationPhase.GAP_ANALYSIS,
            controls_total=len(controls),
            controls_met=0,
            evidence_collected=0,
            readiness_score=0.0,
            estimated_completion=datetime.now(UTC) + timedelta(days=180),
        )
        self._journeys.append(journey)
        logger.info(
            "Certification journey started",
            framework=framework.value,
            organization_id=organization_id,
        )
        return journey

    async def get_journey(self, journey_id: UUID) -> CertificationJourney | None:
        """Get a certification journey by ID."""
        return next((j for j in self._journeys if j.id == journey_id), None)

    async def list_journeys(self, organization_id: str | None = None) -> list[CertificationJourney]:
        """List all certification journeys."""
        results = list(self._journeys)
        if organization_id:
            results = [j for j in results if j.organization_id == organization_id]
        return results

    async def run_gap_analysis(self, journey_id: UUID) -> list[ControlGap]:
        """Run a gap analysis for a certification journey."""
        journey = next((j for j in self._journeys if j.id == journey_id), None)
        if not journey:
            return []

        controls = _CONTROL_REGISTRY.get(journey.framework, [])
        # Deterministic: first third are met, rest are gaps
        gaps: list[ControlGap] = []
        met_count = len(controls) // 3
        for i, control in enumerate(controls):
            gap = ControlGap(
                control_id=control.control_id,
                control_name=control.control_name,
                framework=control.framework,
                status="met" if i < met_count else "not_met",
                evidence_needed=control.evidence_needed,
                remediation_steps=control.remediation_steps,
                estimated_hours=control.estimated_hours,
            )
            gaps.append(gap)

        journey.controls_met = met_count
        journey.readiness_score = round((met_count / len(controls)) * 100, 1) if controls else 0.0
        self._gaps[str(journey_id)] = gaps

        logger.info(
            "Gap analysis complete", journey_id=str(journey_id), gaps=len(controls) - met_count
        )
        return gaps

    async def collect_evidence(self, journey_id: UUID, control_id: str, evidence: str) -> bool:
        """Record evidence collection for a control."""
        journey = next((j for j in self._journeys if j.id == journey_id), None)
        if not journey:
            return False

        gaps = self._gaps.get(str(journey_id), [])
        gap = next((g for g in gaps if g.control_id == control_id), None)
        if gap and gap.status == "not_met":
            gap.status = "evidence_collected"
            journey.evidence_collected += 1
            logger.info("Evidence collected", journey_id=str(journey_id), control_id=control_id)
            return True
        return False

    async def advance_phase(self, journey_id: UUID) -> CertificationJourney | None:
        """Advance a journey to the next phase."""
        journey = next((j for j in self._journeys if j.id == journey_id), None)
        if not journey:
            return None

        current_idx = _PHASE_ORDER.index(journey.current_phase)
        if current_idx < len(_PHASE_ORDER) - 1:
            journey.phases_completed.append(journey.current_phase.value)
            journey.current_phase = _PHASE_ORDER[current_idx + 1]
            # Update readiness score based on phase progress
            journey.readiness_score = round(((current_idx + 1) / len(_PHASE_ORDER)) * 100, 1)
            logger.info(
                "Phase advanced", journey_id=str(journey_id), new_phase=journey.current_phase.value
            )
        return journey

    async def get_readiness_dashboard(self, journey_id: UUID) -> dict:
        """Get a readiness dashboard for a certification journey."""
        journey = next((j for j in self._journeys if j.id == journey_id), None)
        if not journey:
            return {}

        gaps = self._gaps.get(str(journey_id), [])
        met = sum(1 for g in gaps if g.status == "met")
        evidence = sum(1 for g in gaps if g.status == "evidence_collected")
        not_met = sum(1 for g in gaps if g.status == "not_met")
        total_hours = sum(g.estimated_hours for g in gaps if g.status == "not_met")

        auto_evidence = self._auto_collected_evidence.get(str(journey_id), [])
        auto_rate = self._compute_auto_collection_rate(journey_id)

        return {
            "journey_id": str(journey_id),
            "framework": journey.framework.value,
            "current_phase": journey.current_phase.value,
            "readiness_score": journey.readiness_score,
            "controls_total": journey.controls_total,
            "controls_met": met,
            "controls_evidence_collected": evidence,
            "controls_not_met": not_met,
            "remaining_hours": round(total_hours, 1),
            "auto_collection_rate": auto_rate,
            "auto_collection_target": _TARGET_AUTO_COLLECTION_RATE,
            "meets_auto_collection_target": auto_rate >= _TARGET_AUTO_COLLECTION_RATE,
            "total_auto_collected_evidence": len(auto_evidence),
            "estimated_completion": journey.estimated_completion.isoformat()
            if journey.estimated_completion
            else None,
        }

    # ── Automated control mapping & gap analysis ─────────────────────────

    async def run_control_mapping_gap_analysis(
        self, journey_id: UUID
    ) -> list[GapAnalysisItem]:
        """Run automated control mapping with gap analysis for SOC 2 / ISO 27001.

        Identifies gaps, maps controls across frameworks, and flags which
        controls support auto-collection of evidence.
        """
        journey = next((j for j in self._journeys if j.id == journey_id), None)
        if not journey:
            return []

        controls = _CONTROL_REGISTRY.get(journey.framework, [])
        items: list[GapAnalysisItem] = []
        met_count = len(controls) // 3

        for i, control in enumerate(controls):
            status = GapStatus.MET if i < met_count else GapStatus.NOT_MET
            mapped_sources = _AUTO_COLLECTION_MAP.get(control.control_id, [])
            cross_mappings = _CROSS_FRAMEWORK_MAP.get(control.control_id, [])

            item = GapAnalysisItem(
                journey_id=journey_id,
                control_id=control.control_id,
                control_name=control.control_name,
                framework=control.framework,
                status=status,
                evidence_needed=list(control.evidence_needed),
                remediation_steps=list(control.remediation_steps),
                estimated_hours=control.estimated_hours,
                auto_collectible=len(mapped_sources) > 0,
                mapped_sources=list(mapped_sources),
                cross_framework_mappings=list(cross_mappings),
            )
            items.append(item)

        journey.controls_met = met_count
        journey.readiness_score = (
            round((met_count / len(controls)) * 100, 1) if controls else 0.0
        )
        self._gap_analysis_items[str(journey_id)] = items
        # Keep legacy _gaps in sync
        self._gaps[str(journey_id)] = [
            ControlGap(
                control_id=item.control_id,
                control_name=item.control_name,
                framework=item.framework,
                status=item.status.value,
                evidence_needed=item.evidence_needed,
                remediation_steps=item.remediation_steps,
                estimated_hours=item.estimated_hours,
            )
            for item in items
        ]

        auto_collectible = sum(1 for it in items if it.auto_collectible)
        logger.info(
            "Control mapping gap analysis complete",
            journey_id=str(journey_id),
            total_controls=len(controls),
            gaps=len(controls) - met_count,
            auto_collectible=auto_collectible,
        )
        return items

    # ── Evidence auto-collection ─────────────────────────────────────────

    async def auto_collect_evidence(
        self,
        journey_id: UUID,
        control_id: str,
        source_type: EvidenceSourceType,
        content: str,
        source_name: str = "",
        metadata: dict | None = None,
    ) -> AutoCollectedEvidence | None:
        """Auto-collect evidence from a source for a specific control.

        Computes a content hash for integrity verification and stores the
        evidence record.
        """
        journey = next((j for j in self._journeys if j.id == journey_id), None)
        if not journey:
            return None

        evidence = AutoCollectedEvidence(
            journey_id=journey_id,
            control_id=control_id,
            source_type=source_type,
            source_name=source_name or source_type.value,
            content=content,
            collected_at=datetime.now(UTC),
            verified=True,
            metadata=metadata or {},
        )
        evidence.compute_hash()

        jid = str(journey_id)
        self._auto_collected_evidence.setdefault(jid, []).append(evidence)

        # Update gap status if applicable
        gap_items = self._gap_analysis_items.get(jid, [])
        for item in gap_items:
            if item.control_id == control_id and item.status == GapStatus.NOT_MET:
                item.status = GapStatus.EVIDENCE_COLLECTED
                item.evidence_collected.append(evidence.id)
                break

        gaps = self._gaps.get(jid, [])
        for gap in gaps:
            if gap.control_id == control_id and gap.status == "not_met":
                gap.status = "evidence_collected"
                break

        journey.evidence_collected += 1
        logger.info(
            "Evidence auto-collected",
            journey_id=jid,
            control_id=control_id,
            source_type=source_type.value,
        )
        return evidence

    async def auto_collect_from_git_commits(
        self,
        journey_id: UUID,
        commits: list[dict],
    ) -> list[AutoCollectedEvidence]:
        """Collect evidence from git commit data.

        Each commit dict should contain: hash, message, author, date.
        Maps commits to relevant controls (change management, operations).
        """
        journey = next((j for j in self._journeys if j.id == journey_id), None)
        if not journey:
            return []

        target_controls = [
            cid
            for cid, sources in _AUTO_COLLECTION_MAP.items()
            if EvidenceSourceType.GIT_COMMIT in sources
        ]
        framework_controls = {
            c.control_id for c in _CONTROL_REGISTRY.get(journey.framework, [])
        }
        target_controls = [c for c in target_controls if c in framework_controls]

        results: list[AutoCollectedEvidence] = []
        for control_id in target_controls:
            content = "\n".join(
                f"{c.get('date', '')} | {c.get('hash', '')[:8]} | "
                f"{c.get('author', '')} | {c.get('message', '')}"
                for c in commits
            )
            evidence = await self.auto_collect_evidence(
                journey_id=journey_id,
                control_id=control_id,
                source_type=EvidenceSourceType.GIT_COMMIT,
                content=content,
                source_name="git_log",
                metadata={"commit_count": len(commits)},
            )
            if evidence:
                results.append(evidence)

        logger.info(
            "Git commit evidence collected",
            journey_id=str(journey_id),
            commits=len(commits),
            controls_covered=len(results),
        )
        return results

    async def auto_collect_from_cicd(
        self,
        journey_id: UUID,
        pipeline_runs: list[dict],
    ) -> list[AutoCollectedEvidence]:
        """Collect evidence from CI/CD pipeline run data.

        Each pipeline_run dict should contain: id, name, status, started_at,
        finished_at, triggered_by.
        """
        journey = next((j for j in self._journeys if j.id == journey_id), None)
        if not journey:
            return []

        target_controls = [
            cid
            for cid, sources in _AUTO_COLLECTION_MAP.items()
            if EvidenceSourceType.CI_CD_PIPELINE in sources
        ]
        framework_controls = {
            c.control_id for c in _CONTROL_REGISTRY.get(journey.framework, [])
        }
        target_controls = [c for c in target_controls if c in framework_controls]

        results: list[AutoCollectedEvidence] = []
        for control_id in target_controls:
            content = "\n".join(
                f"{r.get('started_at', '')} | {r.get('name', '')} | "
                f"{r.get('status', '')} | {r.get('triggered_by', '')}"
                for r in pipeline_runs
            )
            evidence = await self.auto_collect_evidence(
                journey_id=journey_id,
                control_id=control_id,
                source_type=EvidenceSourceType.CI_CD_PIPELINE,
                content=content,
                source_name="ci_cd_pipeline",
                metadata={"pipeline_run_count": len(pipeline_runs)},
            )
            if evidence:
                results.append(evidence)

        logger.info(
            "CI/CD evidence collected",
            journey_id=str(journey_id),
            pipeline_runs=len(pipeline_runs),
            controls_covered=len(results),
        )
        return results

    async def auto_collect_from_access_logs(
        self,
        journey_id: UUID,
        access_entries: list[dict],
    ) -> list[AutoCollectedEvidence]:
        """Collect evidence from access log entries.

        Each entry dict should contain: timestamp, user, action, resource, result.
        """
        journey = next((j for j in self._journeys if j.id == journey_id), None)
        if not journey:
            return []

        target_controls = [
            cid
            for cid, sources in _AUTO_COLLECTION_MAP.items()
            if EvidenceSourceType.ACCESS_LOG in sources
        ]
        framework_controls = {
            c.control_id for c in _CONTROL_REGISTRY.get(journey.framework, [])
        }
        target_controls = [c for c in target_controls if c in framework_controls]

        results: list[AutoCollectedEvidence] = []
        for control_id in target_controls:
            content = "\n".join(
                f"{e.get('timestamp', '')} | {e.get('user', '')} | "
                f"{e.get('action', '')} | {e.get('resource', '')} | "
                f"{e.get('result', '')}"
                for e in access_entries
            )
            evidence = await self.auto_collect_evidence(
                journey_id=journey_id,
                control_id=control_id,
                source_type=EvidenceSourceType.ACCESS_LOG,
                content=content,
                source_name="access_log",
                metadata={"entry_count": len(access_entries)},
            )
            if evidence:
                results.append(evidence)

        logger.info(
            "Access log evidence collected",
            journey_id=str(journey_id),
            entries=len(access_entries),
            controls_covered=len(results),
        )
        return results

    async def auto_collect_from_cloud_config(
        self,
        journey_id: UUID,
        config_snapshots: list[dict],
    ) -> list[AutoCollectedEvidence]:
        """Collect evidence from cloud configuration snapshots.

        Each snapshot dict should contain: service, resource_type, config, captured_at.
        """
        journey = next((j for j in self._journeys if j.id == journey_id), None)
        if not journey:
            return []

        target_controls = [
            cid
            for cid, sources in _AUTO_COLLECTION_MAP.items()
            if EvidenceSourceType.CLOUD_CONFIG in sources
        ]
        framework_controls = {
            c.control_id for c in _CONTROL_REGISTRY.get(journey.framework, [])
        }
        target_controls = [c for c in target_controls if c in framework_controls]

        results: list[AutoCollectedEvidence] = []
        for control_id in target_controls:
            content = "\n".join(
                f"{s.get('captured_at', '')} | {s.get('service', '')} | "
                f"{s.get('resource_type', '')} | {s.get('config', '')}"
                for s in config_snapshots
            )
            evidence = await self.auto_collect_evidence(
                journey_id=journey_id,
                control_id=control_id,
                source_type=EvidenceSourceType.CLOUD_CONFIG,
                content=content,
                source_name="cloud_config",
                metadata={"snapshot_count": len(config_snapshots)},
            )
            if evidence:
                results.append(evidence)

        logger.info(
            "Cloud config evidence collected",
            journey_id=str(journey_id),
            snapshots=len(config_snapshots),
            controls_covered=len(results),
        )
        return results

    # ── Auto-collection rate tracking ────────────────────────────────────

    def _compute_auto_collection_rate(self, journey_id: UUID) -> float:
        """Compute the percentage of evidence auto-collected vs total evidence.

        Target: 80%+ auto-collection rate.
        """
        jid = str(journey_id)
        auto_count = len(self._auto_collected_evidence.get(jid, []))
        journey = next((j for j in self._journeys if j.id == journey_id), None)
        if not journey:
            return 0.0
        total = journey.evidence_collected
        if total == 0:
            return 0.0
        return round((auto_count / total) * 100, 1)

    async def get_auto_collection_stats(self, journey_id: UUID) -> dict:
        """Get auto-collection rate statistics for a journey."""
        jid = str(journey_id)
        journey = next((j for j in self._journeys if j.id == journey_id), None)
        if not journey:
            return {}

        auto_evidence = self._auto_collected_evidence.get(jid, [])
        auto_rate = self._compute_auto_collection_rate(journey_id)

        by_source: dict[str, int] = {}
        for ev in auto_evidence:
            by_source[ev.source_type.value] = by_source.get(ev.source_type.value, 0) + 1

        controls = _CONTROL_REGISTRY.get(journey.framework, [])
        auto_collectible = sum(
            1 for c in controls if c.control_id in _AUTO_COLLECTION_MAP
        )

        return {
            "journey_id": jid,
            "total_evidence": journey.evidence_collected,
            "auto_collected": len(auto_evidence),
            "manual_collected": journey.evidence_collected - len(auto_evidence),
            "auto_collection_rate": auto_rate,
            "target_rate": _TARGET_AUTO_COLLECTION_RATE,
            "meets_target": auto_rate >= _TARGET_AUTO_COLLECTION_RATE,
            "by_source": by_source,
            "auto_collectible_controls": auto_collectible,
            "total_controls": len(controls),
        }

    # ── Read-only auditor portal ─────────────────────────────────────────

    async def create_auditor_session(
        self,
        journey_id: UUID,
        auditor_email: str,
        auditor_name: str,
        duration_hours: int = 72,
    ) -> AuditorPortalSession | None:
        """Create a time-limited read-only auditor portal session."""
        journey = next((j for j in self._journeys if j.id == journey_id), None)
        if not journey:
            return None

        now = datetime.now(UTC)
        session = AuditorPortalSession(
            journey_id=journey_id,
            auditor_email=auditor_email,
            auditor_name=auditor_name,
            access_token=secrets.token_urlsafe(48),
            created_at=now,
            expires_at=now + timedelta(hours=duration_hours),
            is_active=True,
        )

        jid = str(journey_id)
        self._auditor_sessions.setdefault(jid, []).append(session)

        logger.info(
            "Auditor portal session created",
            journey_id=jid,
            auditor_email=auditor_email,
            expires_at=session.expires_at.isoformat() if session.expires_at else None,
        )
        return session

    async def validate_auditor_session(
        self, access_token: str
    ) -> AuditorPortalSession | None:
        """Validate an auditor portal session token.

        Returns the session if valid and not expired, None otherwise.
        """
        for sessions in self._auditor_sessions.values():
            for session in sessions:
                if session.access_token == access_token:
                    if session.is_expired or not session.is_active:
                        return None
                    session.last_accessed_at = datetime.now(UTC)
                    return session
        return None

    async def get_auditor_view(
        self, access_token: str
    ) -> dict | None:
        """Get read-only auditor view of a journey's compliance data.

        Validates the session token and returns a sanitized, read-only view
        of gaps, evidence, and readiness information.
        """
        session = await self.validate_auditor_session(access_token)
        if not session:
            return None

        jid = str(session.journey_id)
        journey = next((j for j in self._journeys if j.id == session.journey_id), None)
        if not journey:
            return None

        gaps = self._gaps.get(jid, [])
        auto_evidence = self._auto_collected_evidence.get(jid, [])

        gap_summary = [
            {
                "control_id": g.control_id,
                "control_name": g.control_name,
                "status": g.status,
                "evidence_needed": g.evidence_needed,
            }
            for g in gaps
        ]

        evidence_summary = [
            {
                "id": str(e.id),
                "control_id": e.control_id,
                "source_type": e.source_type.value,
                "collected_at": e.collected_at.isoformat() if e.collected_at else None,
                "verified": e.verified,
                "content_hash": e.content_hash,
            }
            for e in auto_evidence
        ]

        # Track which controls the auditor viewed
        viewed = {g.control_id for g in gaps}
        session.accessed_controls = list(
            set(session.accessed_controls) | viewed
        )

        return {
            "journey_id": jid,
            "framework": journey.framework.value,
            "current_phase": journey.current_phase.value,
            "readiness_score": journey.readiness_score,
            "controls_total": journey.controls_total,
            "controls_met": journey.controls_met,
            "auto_collection_rate": self._compute_auto_collection_rate(session.journey_id),
            "gaps": gap_summary,
            "evidence": evidence_summary,
            "session_expires_at": session.expires_at.isoformat()
            if session.expires_at
            else None,
        }

    async def revoke_auditor_session(self, session_id: UUID) -> bool:
        """Revoke an auditor portal session."""
        for sessions in self._auditor_sessions.values():
            for session in sessions:
                if session.id == session_id:
                    session.is_active = False
                    logger.info(
                        "Auditor session revoked",
                        session_id=str(session_id),
                    )
                    return True
        return False

    async def list_auditor_sessions(
        self, journey_id: UUID
    ) -> list[AuditorPortalSession]:
        """List all auditor sessions for a journey."""
        return list(self._auditor_sessions.get(str(journey_id), []))

    # ── Certification readiness report ───────────────────────────────────

    async def generate_readiness_report(
        self, journey_id: UUID
    ) -> CertificationReadinessReport | None:
        """Generate a comprehensive certification readiness report.

        Includes gap summaries, remediation priorities, auto-collection
        rates, and overall readiness assessment.
        """
        journey = next((j for j in self._journeys if j.id == journey_id), None)
        if not journey:
            return None

        jid = str(journey_id)
        gaps = self._gaps.get(jid, [])
        auto_evidence = self._auto_collected_evidence.get(jid, [])
        auto_rate = self._compute_auto_collection_rate(journey_id)

        met = sum(1 for g in gaps if g.status == "met")
        partially = sum(1 for g in gaps if g.status == "partially_met")
        evidence_collected = sum(1 for g in gaps if g.status == "evidence_collected")
        not_met = sum(1 for g in gaps if g.status == "not_met")
        remaining_hours = sum(g.estimated_hours for g in gaps if g.status == "not_met")

        gap_summary = [
            {
                "control_id": g.control_id,
                "control_name": g.control_name,
                "status": g.status,
                "estimated_hours": g.estimated_hours,
                "evidence_needed": g.evidence_needed,
            }
            for g in gaps
            if g.status in ("not_met", "partially_met")
        ]

        remediation_summary = sorted(
            [
                {
                    "control_id": g.control_id,
                    "control_name": g.control_name,
                    "remediation_steps": g.remediation_steps,
                    "estimated_hours": g.estimated_hours,
                    "priority": "high" if g.estimated_hours >= 16 else (
                        "medium" if g.estimated_hours >= 10 else "low"
                    ),
                }
                for g in gaps
                if g.status == "not_met"
            ],
            key=lambda x: x["estimated_hours"],
            reverse=True,
        )

        auto_count = len(auto_evidence)
        manual_count = max(0, journey.evidence_collected - auto_count)

        report = CertificationReadinessReport(
            journey_id=journey_id,
            framework=journey.framework,
            generated_at=datetime.now(UTC),
            overall_readiness_score=journey.readiness_score,
            auto_collection_rate=auto_rate,
            controls_total=len(gaps),
            controls_met=met + evidence_collected,
            controls_partially_met=partially,
            controls_not_met=not_met,
            total_evidence_collected=journey.evidence_collected,
            auto_collected_evidence_count=auto_count,
            manual_evidence_count=manual_count,
            gap_summary=gap_summary,
            remediation_summary=remediation_summary,
            estimated_remaining_hours=round(remaining_hours, 1),
            target_auto_collection_rate=_TARGET_AUTO_COLLECTION_RATE,
            meets_auto_collection_target=auto_rate >= _TARGET_AUTO_COLLECTION_RATE,
        )

        self._readiness_reports.setdefault(jid, []).append(report)

        logger.info(
            "Readiness report generated",
            journey_id=jid,
            readiness_score=report.overall_readiness_score,
            auto_collection_rate=auto_rate,
            meets_target=report.meets_auto_collection_target,
        )
        return report

    # ── Evidence chain verification ──────────────────────────────────────

    async def verify_evidence_chain(self, journey_id: UUID) -> dict:
        """Verify the integrity of all collected evidence for a journey.

        Re-computes content hashes and checks for tampering or corruption.
        """
        jid = str(journey_id)
        auto_evidence = self._auto_collected_evidence.get(jid, [])

        if not auto_evidence:
            return {
                "journey_id": jid,
                "total_evidence": 0,
                "verified": 0,
                "failed": 0,
                "integrity_status": "no_evidence",
                "failures": [],
            }

        verified = 0
        failed = 0
        failures: list[dict] = []

        for evidence in auto_evidence:
            expected_hash = sha256(evidence.content.encode()).hexdigest()
            if evidence.content_hash == expected_hash:
                verified += 1
            else:
                failed += 1
                failures.append(
                    {
                        "evidence_id": str(evidence.id),
                        "control_id": evidence.control_id,
                        "source_type": evidence.source_type.value,
                        "expected_hash": expected_hash,
                        "actual_hash": evidence.content_hash,
                    }
                )

        status = "intact" if failed == 0 else "compromised"

        logger.info(
            "Evidence chain verification complete",
            journey_id=jid,
            total=len(auto_evidence),
            verified=verified,
            failed=failed,
            status=status,
        )

        return {
            "journey_id": jid,
            "total_evidence": len(auto_evidence),
            "verified": verified,
            "failed": failed,
            "integrity_status": status,
            "failures": failures,
        }
