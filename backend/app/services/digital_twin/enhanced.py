"""Enhanced Digital Twin - Time Travel, Drift Detection, Breach Simulation."""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from enum import Enum

import structlog

from app.services.digital_twin.snapshot import SnapshotManager, get_snapshot_manager
from app.services.digital_twin.models import ComplianceSnapshot, ComplianceIssue


logger = structlog.get_logger()


class DriftType(str, Enum):
    """Types of compliance drift."""
    SCORE_DEGRADATION = "score_degradation"
    NEW_VIOLATION = "new_violation"
    REGULATION_CHANGE = "regulation_change"
    CONTROL_WEAKENING = "control_weakening"
    DATA_FLOW_CHANGE = "data_flow_change"


class BreachScenario(str, Enum):
    """Types of breach scenarios for simulation."""
    DATA_EXFILTRATION = "data_exfiltration"
    RANSOMWARE = "ransomware"
    INSIDER_THREAT = "insider_threat"
    API_BREACH = "api_breach"
    THIRD_PARTY_COMPROMISE = "third_party_compromise"
    SUPPLY_CHAIN_ATTACK = "supply_chain_attack"


@dataclass
class DriftEvent:
    """A compliance drift event."""
    id: UUID = field(default_factory=uuid4)
    drift_type: DriftType = DriftType.SCORE_DEGRADATION
    detected_at: datetime = field(default_factory=datetime.utcnow)
    snapshot_before_id: UUID | None = None
    snapshot_after_id: UUID | None = None
    severity: str = "medium"
    description: str = ""
    affected_regulations: list[str] = field(default_factory=list)
    score_delta: float = 0.0
    auto_remediated: bool = False
    remediation_action: str | None = None


@dataclass
class BreachImpact:
    """Impact assessment for a simulated breach."""
    id: UUID = field(default_factory=uuid4)
    scenario: BreachScenario = BreachScenario.DATA_EXFILTRATION
    simulated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Data impact
    data_types_affected: list[str] = field(default_factory=list)
    records_at_risk: int = 0
    data_sensitivity: str = "medium"
    
    # Regulatory impact
    regulatory_notifications_required: list[dict[str, Any]] = field(default_factory=list)
    notification_deadline_hours: int = 72
    estimated_fine_range: tuple[float, float] = (0, 0)
    
    # Operational impact
    affected_systems: list[str] = field(default_factory=list)
    estimated_downtime_hours: float = 0.0
    recovery_time_estimate_hours: float = 0.0
    
    # Compliance implications
    compliance_score_impact: float = 0.0
    controls_failed: list[str] = field(default_factory=list)
    required_remediation: list[str] = field(default_factory=list)
    
    # Financial impact
    breach_cost_estimate: float = 0.0
    litigation_risk: str = "medium"


@dataclass
class TimelinePoint:
    """A point on the compliance timeline."""
    timestamp: datetime
    snapshot_id: UUID | None
    score: float
    status: str
    key_events: list[str] = field(default_factory=list)
    drift_events: list[UUID] = field(default_factory=list)


class EnhancedDigitalTwin:
    """Enhanced digital twin with time-travel and breach simulation."""
    
    def __init__(self, snapshot_manager: SnapshotManager | None = None):
        self.snapshot_manager = snapshot_manager or get_snapshot_manager()
        self._drift_events: dict[UUID, DriftEvent] = {}
        self._drift_by_org: dict[UUID, list[UUID]] = {}
        self._breach_simulations: dict[UUID, BreachImpact] = {}
        self._auto_remediation_enabled: dict[UUID, bool] = {}
    
    # =========================
    # TIME TRAVEL FUNCTIONALITY
    # =========================
    
    async def get_compliance_at_point_in_time(
        self,
        organization_id: UUID,
        target_time: datetime,
    ) -> ComplianceSnapshot | None:
        """Get compliance state at a specific point in time."""
        snapshots = await self.snapshot_manager.list_snapshots(organization_id, limit=1000)
        
        # Find closest snapshot at or before target time
        candidates = [s for s in snapshots if s.created_at <= target_time]
        if not candidates:
            return None
        
        return max(candidates, key=lambda s: s.created_at)
    
    async def get_compliance_timeline(
        self,
        organization_id: UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        granularity: str = "daily",
    ) -> list[TimelinePoint]:
        """Get compliance timeline showing score evolution."""
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=90)
        
        snapshots = await self.snapshot_manager.list_snapshots(organization_id, limit=1000)
        snapshots = [s for s in snapshots if start_date <= s.created_at <= end_date]
        
        # Get drift events in range
        org_drift_ids = self._drift_by_org.get(organization_id, [])
        drift_events = [
            self._drift_events[did] for did in org_drift_ids
            if did in self._drift_events and start_date <= self._drift_events[did].detected_at <= end_date
        ]
        
        timeline = []
        for snapshot in sorted(snapshots, key=lambda s: s.created_at):
            # Find drift events near this snapshot
            nearby_drifts = [
                d.id for d in drift_events
                if abs((d.detected_at - snapshot.created_at).total_seconds()) < 86400
            ]
            
            timeline.append(TimelinePoint(
                timestamp=snapshot.created_at,
                snapshot_id=snapshot.id,
                score=snapshot.overall_score,
                status=snapshot.overall_status.value if snapshot.overall_status else "unknown",
                key_events=[],  # Would be populated from audit log
                drift_events=nearby_drifts,
            ))
        
        return timeline
    
    async def compare_time_periods(
        self,
        organization_id: UUID,
        period1_start: datetime,
        period1_end: datetime,
        period2_start: datetime,
        period2_end: datetime,
    ) -> dict[str, Any]:
        """Compare compliance between two time periods."""
        # Get snapshots for each period
        p1_snapshot = await self.get_compliance_at_point_in_time(organization_id, period1_end)
        p2_snapshot = await self.get_compliance_at_point_in_time(organization_id, period2_end)
        
        if not p1_snapshot or not p2_snapshot:
            return {"error": "Insufficient snapshot data for comparison"}
        
        return await self.snapshot_manager.compare_snapshots(p1_snapshot.id, p2_snapshot.id)
    
    # =======================
    # DRIFT DETECTION
    # =======================
    
    async def detect_drift(
        self,
        organization_id: UUID,
        threshold: float = 0.05,
    ) -> list[DriftEvent]:
        """Detect compliance drift by comparing recent snapshots."""
        snapshots = await self.snapshot_manager.list_snapshots(organization_id, limit=10)
        
        if len(snapshots) < 2:
            return []
        
        drift_events = []
        latest = snapshots[0]
        previous = snapshots[1]
        
        # Score degradation
        score_delta = latest.overall_score - previous.overall_score
        if score_delta < -threshold:
            event = DriftEvent(
                drift_type=DriftType.SCORE_DEGRADATION,
                snapshot_before_id=previous.id,
                snapshot_after_id=latest.id,
                severity="high" if score_delta < -0.15 else "medium",
                description=f"Compliance score dropped by {abs(score_delta)*100:.1f}%",
                score_delta=score_delta,
            )
            drift_events.append(event)
            self._store_drift_event(organization_id, event)
        
        # New violations
        prev_codes = {i.code for i in previous.issues}
        for issue in latest.issues:
            if issue.code not in prev_codes:
                event = DriftEvent(
                    drift_type=DriftType.NEW_VIOLATION,
                    snapshot_after_id=latest.id,
                    severity=issue.severity,
                    description=f"New violation: {issue.message}",
                    affected_regulations=[issue.regulation] if issue.regulation else [],
                )
                drift_events.append(event)
                self._store_drift_event(organization_id, event)
        
        # Regulation score changes
        prev_regs = {r.regulation: r for r in previous.regulations}
        for reg in latest.regulations:
            if reg.regulation in prev_regs:
                prev_reg = prev_regs[reg.regulation]
                if reg.score < prev_reg.score - threshold:
                    event = DriftEvent(
                        drift_type=DriftType.CONTROL_WEAKENING,
                        severity="high" if reg.score < 0.6 else "medium",
                        description=f"{reg.regulation} compliance dropped from {prev_reg.score*100:.0f}% to {reg.score*100:.0f}%",
                        affected_regulations=[reg.regulation],
                        score_delta=reg.score - prev_reg.score,
                    )
                    drift_events.append(event)
                    self._store_drift_event(organization_id, event)
        
        logger.info("Drift detection completed", org_id=str(organization_id), drift_count=len(drift_events))
        return drift_events
    
    def _store_drift_event(self, organization_id: UUID, event: DriftEvent) -> None:
        """Store a drift event."""
        self._drift_events[event.id] = event
        if organization_id not in self._drift_by_org:
            self._drift_by_org[organization_id] = []
        self._drift_by_org[organization_id].append(event.id)
    
    async def get_drift_history(
        self,
        organization_id: UUID,
        limit: int = 50,
    ) -> list[DriftEvent]:
        """Get drift event history for an organization."""
        event_ids = self._drift_by_org.get(organization_id, [])
        events = [self._drift_events[eid] for eid in event_ids if eid in self._drift_events]
        events.sort(key=lambda e: e.detected_at, reverse=True)
        return events[:limit]
    
    async def enable_auto_remediation(
        self,
        organization_id: UUID,
        enabled: bool = True,
    ) -> bool:
        """Enable or disable automatic drift remediation."""
        self._auto_remediation_enabled[organization_id] = enabled
        return enabled
    
    # =======================
    # BREACH SIMULATION
    # =======================
    
    async def simulate_breach(
        self,
        organization_id: UUID,
        scenario: BreachScenario,
        parameters: dict[str, Any] | None = None,
    ) -> BreachImpact:
        """Simulate a breach scenario and assess impact."""
        params = parameters or {}
        
        # Get current compliance state
        current_snapshot = await self.snapshot_manager.get_latest_snapshot(organization_id)
        
        # Scenario-specific impact calculation
        if scenario == BreachScenario.DATA_EXFILTRATION:
            impact = self._simulate_data_exfiltration(current_snapshot, params)
        elif scenario == BreachScenario.RANSOMWARE:
            impact = self._simulate_ransomware(current_snapshot, params)
        elif scenario == BreachScenario.INSIDER_THREAT:
            impact = self._simulate_insider_threat(current_snapshot, params)
        elif scenario == BreachScenario.API_BREACH:
            impact = self._simulate_api_breach(current_snapshot, params)
        elif scenario == BreachScenario.THIRD_PARTY_COMPROMISE:
            impact = self._simulate_third_party_compromise(current_snapshot, params)
        elif scenario == BreachScenario.SUPPLY_CHAIN_ATTACK:
            impact = self._simulate_supply_chain_attack(current_snapshot, params)
        else:
            raise ValueError(f"Unknown breach scenario: {scenario}")
        
        impact.scenario = scenario
        self._breach_simulations[impact.id] = impact
        
        logger.info(
            "Breach simulation completed",
            scenario=scenario.value,
            records_at_risk=impact.records_at_risk,
            cost_estimate=impact.breach_cost_estimate,
        )
        
        return impact
    
    def _simulate_data_exfiltration(
        self,
        snapshot: ComplianceSnapshot | None,
        params: dict[str, Any],
    ) -> BreachImpact:
        """Simulate data exfiltration breach."""
        records = params.get("records_affected", 10000)
        data_types = params.get("data_types", ["PII", "email", "name"])
        
        # Calculate regulatory notifications
        notifications = []
        if any(dt in ["PII", "personal_data", "email"] for dt in data_types):
            notifications.append({
                "regulation": "GDPR",
                "authority": "Data Protection Authority",
                "deadline_hours": 72,
                "required": True,
            })
            notifications.append({
                "regulation": "CCPA",
                "authority": "California AG",
                "deadline_hours": 72,
                "required": records > 500,
            })
        
        if any(dt in ["PHI", "health", "medical"] for dt in data_types):
            notifications.append({
                "regulation": "HIPAA",
                "authority": "HHS/OCR",
                "deadline_hours": 60 * 24,  # 60 days
                "required": True,
            })
        
        # Cost calculation (based on IBM cost of data breach)
        cost_per_record = 165 if "PHI" in data_types else 150
        base_cost = records * cost_per_record
        
        return BreachImpact(
            data_types_affected=data_types,
            records_at_risk=records,
            data_sensitivity="high" if "PHI" in data_types else "medium",
            regulatory_notifications_required=notifications,
            notification_deadline_hours=72,
            estimated_fine_range=(base_cost * 0.1, base_cost * 0.5),
            affected_systems=params.get("systems", ["database", "api"]),
            estimated_downtime_hours=24,
            recovery_time_estimate_hours=168,  # 1 week
            compliance_score_impact=-0.2,
            controls_failed=["access_control", "encryption_at_rest", "monitoring"],
            required_remediation=[
                "Conduct forensic investigation",
                "Notify affected individuals",
                "Submit regulatory notifications",
                "Implement additional access controls",
                "Enhance monitoring capabilities",
            ],
            breach_cost_estimate=base_cost,
            litigation_risk="high" if records > 10000 else "medium",
        )
    
    def _simulate_ransomware(
        self,
        snapshot: ComplianceSnapshot | None,
        params: dict[str, Any],
    ) -> BreachImpact:
        """Simulate ransomware attack."""
        systems_affected = params.get("systems", ["all_production"])
        
        return BreachImpact(
            data_types_affected=["all_data"],
            records_at_risk=params.get("records", 100000),
            data_sensitivity="high",
            regulatory_notifications_required=[
                {"regulation": "GDPR", "authority": "DPA", "deadline_hours": 72, "required": True},
                {"regulation": "HIPAA", "authority": "HHS", "deadline_hours": 72, "required": True},
            ],
            notification_deadline_hours=72,
            estimated_fine_range=(100000, 5000000),
            affected_systems=systems_affected,
            estimated_downtime_hours=72,
            recovery_time_estimate_hours=336,  # 2 weeks
            compliance_score_impact=-0.35,
            controls_failed=["backup_integrity", "endpoint_protection", "network_segmentation"],
            required_remediation=[
                "Isolate affected systems",
                "Restore from clean backups",
                "Conduct full security audit",
                "Implement network segmentation",
                "Deploy EDR solution",
                "Train staff on phishing awareness",
            ],
            breach_cost_estimate=params.get("ransom_demand", 500000) + 2000000,  # Ransom + recovery
            litigation_risk="high",
        )
    
    def _simulate_insider_threat(
        self,
        snapshot: ComplianceSnapshot | None,
        params: dict[str, Any],
    ) -> BreachImpact:
        """Simulate insider threat scenario."""
        return BreachImpact(
            data_types_affected=params.get("data_types", ["proprietary", "customer_data"]),
            records_at_risk=params.get("records", 5000),
            data_sensitivity="medium",
            regulatory_notifications_required=[
                {"regulation": "GDPR", "authority": "DPA", "deadline_hours": 72, "required": True},
            ],
            notification_deadline_hours=72,
            estimated_fine_range=(10000, 500000),
            affected_systems=["internal_databases", "file_shares"],
            estimated_downtime_hours=4,
            recovery_time_estimate_hours=48,
            compliance_score_impact=-0.15,
            controls_failed=["access_control", "data_loss_prevention", "user_monitoring"],
            required_remediation=[
                "Revoke access for involved parties",
                "Audit all privileged access",
                "Implement DLP controls",
                "Enhance user activity monitoring",
            ],
            breach_cost_estimate=750000,
            litigation_risk="medium",
        )
    
    def _simulate_api_breach(
        self,
        snapshot: ComplianceSnapshot | None,
        params: dict[str, Any],
    ) -> BreachImpact:
        """Simulate API security breach."""
        return BreachImpact(
            data_types_affected=["API_responses", "authentication_tokens", "user_data"],
            records_at_risk=params.get("records", 25000),
            data_sensitivity="high",
            regulatory_notifications_required=[
                {"regulation": "GDPR", "authority": "DPA", "deadline_hours": 72, "required": True},
                {"regulation": "PCI-DSS", "authority": "Card brands", "deadline_hours": 24, "required": True},
            ],
            notification_deadline_hours=24,
            estimated_fine_range=(50000, 2000000),
            affected_systems=["api_gateway", "authentication_service", "user_service"],
            estimated_downtime_hours=8,
            recovery_time_estimate_hours=96,
            compliance_score_impact=-0.25,
            controls_failed=["api_authentication", "rate_limiting", "input_validation"],
            required_remediation=[
                "Rotate all API keys and tokens",
                "Implement API rate limiting",
                "Add input validation",
                "Deploy API security gateway",
                "Implement API monitoring",
            ],
            breach_cost_estimate=1200000,
            litigation_risk="high",
        )
    
    def _simulate_third_party_compromise(
        self,
        snapshot: ComplianceSnapshot | None,
        params: dict[str, Any],
    ) -> BreachImpact:
        """Simulate third-party/vendor compromise."""
        vendor_name = params.get("vendor", "Analytics Provider")
        
        return BreachImpact(
            data_types_affected=["shared_data", "integration_data"],
            records_at_risk=params.get("records", 50000),
            data_sensitivity="medium",
            regulatory_notifications_required=[
                {"regulation": "GDPR", "authority": "DPA", "deadline_hours": 72, "required": True},
            ],
            notification_deadline_hours=72,
            estimated_fine_range=(25000, 1000000),
            affected_systems=[f"{vendor_name}_integration", "data_sharing_pipeline"],
            estimated_downtime_hours=12,
            recovery_time_estimate_hours=120,
            compliance_score_impact=-0.18,
            controls_failed=["vendor_risk_management", "data_sharing_controls", "third_party_monitoring"],
            required_remediation=[
                f"Disable {vendor_name} integration",
                "Audit all third-party data sharing",
                "Review vendor security assessments",
                "Implement vendor monitoring",
                "Update Data Processing Agreements",
            ],
            breach_cost_estimate=900000,
            litigation_risk="medium",
        )
    
    def _simulate_supply_chain_attack(
        self,
        snapshot: ComplianceSnapshot | None,
        params: dict[str, Any],
    ) -> BreachImpact:
        """Simulate supply chain attack (e.g., compromised dependency)."""
        return BreachImpact(
            data_types_affected=["source_code", "build_artifacts", "secrets"],
            records_at_risk=params.get("records", 0),  # May not involve data
            data_sensitivity="critical",
            regulatory_notifications_required=[
                {"regulation": "GDPR", "authority": "DPA", "deadline_hours": 72, "required": True},
                {"regulation": "CISA", "authority": "CISA", "deadline_hours": 24, "required": True},
            ],
            notification_deadline_hours=24,
            estimated_fine_range=(100000, 10000000),
            affected_systems=["build_pipeline", "all_deployments", "developer_workstations"],
            estimated_downtime_hours=48,
            recovery_time_estimate_hours=504,  # 3 weeks
            compliance_score_impact=-0.4,
            controls_failed=["sbom_verification", "dependency_scanning", "build_integrity"],
            required_remediation=[
                "Audit all dependencies (SBOM)",
                "Rotate all secrets and credentials",
                "Rebuild all artifacts from clean sources",
                "Implement dependency verification",
                "Add software composition analysis",
                "Implement signed commits and builds",
            ],
            breach_cost_estimate=5000000,
            litigation_risk="critical",
        )
    
    async def get_breach_simulation(self, simulation_id: UUID) -> BreachImpact | None:
        """Get a breach simulation by ID."""
        return self._breach_simulations.get(simulation_id)
    
    async def list_breach_simulations(self, limit: int = 20) -> list[BreachImpact]:
        """List recent breach simulations."""
        simulations = list(self._breach_simulations.values())
        simulations.sort(key=lambda s: s.simulated_at, reverse=True)
        return simulations[:limit]


# Singleton instance
_enhanced_twin: EnhancedDigitalTwin | None = None


def get_enhanced_digital_twin() -> EnhancedDigitalTwin:
    """Get or create the enhanced digital twin singleton."""
    global _enhanced_twin
    if _enhanced_twin is None:
        _enhanced_twin = EnhancedDigitalTwin()
    return _enhanced_twin
