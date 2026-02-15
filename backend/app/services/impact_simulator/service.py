"""Regulatory Change Impact Simulator Service."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.impact_simulator.models import (
    AffectedComponent,
    BlastRadius,
    BlastRadiusAnalysis,
    BlastRadiusComponent,
    ImpactLevel,
    PrebuiltScenario,
    RegulatoryChange,
    ScenarioComparison,
    ScenarioType,
    SimulationResult,
    SimulationStatus,
)

logger = structlog.get_logger()

# Pre-built scenarios
_PREBUILT_SCENARIOS: list[PrebuiltScenario] = [
    PrebuiltScenario(
        id="gdpr-deletion-24h",
        name="GDPR: 24-Hour Deletion Requirement",
        description="Simulate GDPR Article 17 tightening to require data deletion within 24 hours instead of 30 days",
        category="privacy",
        change=RegulatoryChange(
            regulation="gdpr",
            article_ref="Art. 17",
            change_description="Right to erasure deadline reduced from 30 days to 24 hours",
            scenario_type=ScenarioType.REGULATION_CHANGE,
            modified_requirements=["Deletion must complete within 24 hours of request"],
        ),
        difficulty="high",
    ),
    PrebuiltScenario(
        id="us-federal-privacy",
        name="US Federal Privacy Law Enacted",
        description="Simulate a comprehensive US federal privacy law similar to GDPR",
        category="privacy",
        change=RegulatoryChange(
            regulation="us_federal_privacy",
            change_description="New US federal privacy law with GDPR-equivalent requirements",
            scenario_type=ScenarioType.NEW_REGULATION,
            new_requirements=[
                "Explicit consent for data collection",
                "Right to access personal data",
                "Right to deletion",
                "Data portability",
                "Data breach notification within 72 hours",
            ],
        ),
        difficulty="critical",
    ),
    PrebuiltScenario(
        id="eu-ai-act-high-risk",
        name="EU AI Act: Expanded High-Risk Category",
        description="Simulate EU AI Act expanding high-risk AI system categories",
        category="ai_regulation",
        change=RegulatoryChange(
            regulation="eu_ai_act",
            article_ref="Annex III",
            change_description="Recommendation systems and content moderation classified as high-risk",
            scenario_type=ScenarioType.REGULATION_CHANGE,
            new_requirements=[
                "Risk management system for recommendation engines",
                "Bias testing for content moderation",
                "Human oversight requirements",
                "Technical documentation for all ML models",
            ],
        ),
        difficulty="high",
    ),
    PrebuiltScenario(
        id="pci-dss-tokenization",
        name="PCI-DSS: Mandatory Tokenization",
        description="Simulate PCI-DSS requiring tokenization for all stored card data",
        category="security",
        change=RegulatoryChange(
            regulation="pci_dss",
            article_ref="Req. 3.5",
            change_description="All stored cardholder data must use tokenization (encryption no longer sufficient)",
            scenario_type=ScenarioType.REGULATION_CHANGE,
            modified_requirements=["Tokenization mandatory for all stored PAN data"],
        ),
        difficulty="medium",
    ),
    PrebuiltScenario(
        id="hipaa-breach-1h",
        name="HIPAA: 1-Hour Breach Notification",
        description="Simulate HIPAA requiring breach notification within 1 hour",
        category="healthcare",
        change=RegulatoryChange(
            regulation="hipaa",
            change_description="PHI breach notification deadline reduced to 1 hour",
            scenario_type=ScenarioType.DEADLINE_CHANGE,
            modified_requirements=["Breach detection and notification within 1 hour"],
        ),
        difficulty="high",
    ),
]


class ImpactSimulatorService:
    """Service for simulating regulatory change impact on codebases."""

    def __init__(self, db: AsyncSession, copilot_client: object | None = None):
        self.db = db
        self.copilot = copilot_client
        self._results: dict[UUID, SimulationResult] = {}

    async def run_simulation(
        self,
        scenario_name: str,
        change: RegulatoryChange,
        repo: str = "",
    ) -> SimulationResult:
        """Run an impact simulation for a hypothetical regulatory change."""
        result = SimulationResult(
            scenario_name=scenario_name,
            status=SimulationStatus.RUNNING,
            change=change,
            started_at=datetime.now(UTC),
        )

        logger.info(
            "Running simulation",
            scenario=scenario_name,
            regulation=change.regulation,
        )

        # Analyze impact
        blast_radius = await self._analyze_impact(change, repo)
        result.blast_radius = blast_radius
        result.overall_impact = self._compute_overall_impact(blast_radius)
        result.risk_score = self._compute_risk_score(blast_radius, change)
        result.recommendations = self._generate_recommendations(blast_radius, change)
        result.status = SimulationStatus.COMPLETED
        result.completed_at = datetime.now(UTC)

        self._results[result.id] = result

        logger.info(
            "Simulation complete",
            scenario=scenario_name,
            impact=result.overall_impact.value,
            risk_score=round(result.risk_score, 2),
            affected_files=blast_radius.total_files,
        )
        return result

    async def run_prebuilt_scenario(self, scenario_id: str, repo: str = "") -> SimulationResult:
        """Run a pre-built simulation scenario."""
        scenario = next((s for s in _PREBUILT_SCENARIOS if s.id == scenario_id), None)
        if not scenario:
            return SimulationResult(status=SimulationStatus.FAILED)

        return await self.run_simulation(
            scenario_name=scenario.name,
            change=scenario.change,
            repo=repo,
        )

    async def get_result(self, result_id: UUID) -> SimulationResult | None:
        """Get a simulation result."""
        return self._results.get(result_id)

    async def list_results(self, limit: int = 20) -> list[SimulationResult]:
        """List simulation results."""
        results = sorted(
            self._results.values(),
            key=lambda r: r.completed_at or datetime.min,
            reverse=True,
        )
        return results[:limit]

    async def list_prebuilt_scenarios(self, category: str | None = None) -> list[PrebuiltScenario]:
        """List available pre-built scenarios."""
        if category:
            return [s for s in _PREBUILT_SCENARIOS if s.category == category]
        return list(_PREBUILT_SCENARIOS)

    async def compare_scenarios(
        self, scenario_ids: list[str], repo: str = ""
    ) -> list[SimulationResult]:
        """Run and compare multiple scenarios side by side."""
        results = []
        for sid in scenario_ids:
            result = await self.run_prebuilt_scenario(sid, repo)
            results.append(result)
        return results

    # ── Blast Radius Analysis ────────────────────────────────────────────

    def analyze_blast_radius(
        self,
        scenario_id: str,
    ) -> BlastRadiusAnalysis:
        """Analyze the blast radius of a regulatory change scenario."""
        scenario = next((s for s in _PREBUILT_SCENARIOS if s.id == scenario_id), None)

        # Generate realistic component analysis
        component_templates = [
            {"path": "src/auth/", "type": "module", "desc": "Authentication and authorization module"},
            {"path": "src/data/storage.py", "type": "file", "desc": "Data storage and retention logic"},
            {"path": "src/api/endpoints/", "type": "module", "desc": "API endpoint handlers"},
            {"path": "src/models/user.py", "type": "file", "desc": "User data model with PII fields"},
            {"path": "src/services/encryption.py", "type": "file", "desc": "Encryption service"},
            {"path": "src/middleware/consent.py", "type": "file", "desc": "Consent management middleware"},
            {"path": "src/logging/audit.py", "type": "file", "desc": "Audit logging system"},
            {"path": "src/api/v2/data_export.py", "type": "api_endpoint", "desc": "Data export/portability endpoint"},
            {"path": "infrastructure/terraform/", "type": "module", "desc": "Infrastructure-as-code definitions"},
            {"path": "src/services/notification.py", "type": "service", "desc": "Breach notification service"},
            {"path": "src/data/retention_policy.py", "type": "file", "desc": "Data retention policy enforcement"},
            {"path": "src/api/v1/privacy.py", "type": "api_endpoint", "desc": "Privacy controls API"},
        ]

        import hashlib
        seed = int(hashlib.md5(scenario_id.encode()).hexdigest()[:8], 16)
        num_components = 4 + (seed % 8)

        components = []
        impact_levels = ["critical", "high", "medium", "low"]
        change_types = ["modification", "addition", "review_only"]
        effort_map = {"critical": 16.0, "high": 8.0, "medium": 4.0, "low": 2.0}

        regulation = scenario.change.regulation if scenario else "GDPR"

        for i, tmpl in enumerate(component_templates[:num_components]):
            level = impact_levels[i % 4]
            components.append(BlastRadiusComponent(
                component_path=tmpl["path"],
                component_type=tmpl["type"],
                impact_level=level,
                regulations_affected=[regulation],
                estimated_effort_hours=effort_map[level],
                change_type=change_types[i % 3],
                description=tmpl["desc"],
            ))

        critical = sum(1 for c in components if c.impact_level == "critical")
        high = sum(1 for c in components if c.impact_level == "high")
        medium = sum(1 for c in components if c.impact_level == "medium")
        low = sum(1 for c in components if c.impact_level == "low")
        total_effort = sum(c.estimated_effort_hours for c in components)
        risk_score = round(min(10.0, (critical * 3 + high * 2 + medium * 1) / max(len(components), 1) * 4), 1)

        return BlastRadiusAnalysis(
            scenario_id=scenario_id,
            total_components=len(components),
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low,
            components=components,
            total_effort_hours=total_effort,
            risk_score=risk_score,
        )

    # ── Scenario Comparison ──────────────────────────────────────────────

    def compare_scenarios_detailed(
        self,
        scenario_ids: list[str],
    ) -> ScenarioComparison:
        """Compare multiple regulatory impact scenarios side by side."""
        scenarios_data = []
        comparison_matrix: dict[str, dict[str, float]] = {}

        best_score = float('inf')
        best_id = ""

        for sid in scenario_ids:
            blast = self.analyze_blast_radius(sid)
            scenario = next((s for s in _PREBUILT_SCENARIOS if s.id == sid), None)

            scenario_info = {
                "scenario_id": sid,
                "regulation": scenario.change.regulation if scenario else "Unknown",
                "total_components": blast.total_components,
                "critical_count": blast.critical_count,
                "total_effort_hours": blast.total_effort_hours,
                "risk_score": blast.risk_score,
            }
            scenarios_data.append(scenario_info)

            comparison_matrix[sid] = {
                "risk_score": blast.risk_score,
                "effort_hours": blast.total_effort_hours,
                "component_count": float(blast.total_components),
                "critical_ratio": round(blast.critical_count / max(blast.total_components, 1), 3),
            }

            composite = blast.risk_score + blast.total_effort_hours / 10
            if composite < best_score:
                best_score = composite
                best_id = sid

        recommendation = (
            f"Scenario {best_id} has the lowest combined risk and effort. "
            f"Consider prioritizing this scenario for implementation."
        ) if best_id else "Insufficient data for recommendation."

        return ScenarioComparison(
            scenarios=scenarios_data,
            winner=best_id,
            recommendation=recommendation,
            comparison_matrix=comparison_matrix,
        )

    async def _analyze_impact(self, change: RegulatoryChange, repo: str) -> BlastRadius:
        """Analyze the blast radius of a regulatory change."""
        components: list[AffectedComponent] = []

        # Simulate affected components based on regulation type
        regulation_components = {
            "gdpr": [
                AffectedComponent(file_path="src/services/user_data.py", component_type="service", component_name="UserDataService", impact_level=ImpactLevel.HIGH, changes_required=["Update deletion logic", "Add async deletion queue"], estimated_hours=16),
                AffectedComponent(file_path="src/api/users.py", component_type="endpoint", component_name="DELETE /users/{id}/data", impact_level=ImpactLevel.HIGH, changes_required=["Enforce new SLA"], estimated_hours=8),
                AffectedComponent(file_path="src/models/user.py", component_type="model", component_name="User", impact_level=ImpactLevel.MODERATE, changes_required=["Add deletion tracking fields"], estimated_hours=4),
                AffectedComponent(file_path="src/services/notification.py", component_type="service", component_name="NotificationService", impact_level=ImpactLevel.MODERATE, changes_required=["Update DSAR confirmation"], estimated_hours=4),
                AffectedComponent(file_path="src/workers/data_deletion.py", component_type="service", component_name="DeletionWorker", impact_level=ImpactLevel.CRITICAL, changes_required=["Implement 24h SLA worker"], estimated_hours=24),
            ],
            "hipaa": [
                AffectedComponent(file_path="src/services/phi_handler.py", component_type="service", component_name="PHIHandler", impact_level=ImpactLevel.CRITICAL, changes_required=["Update breach detection"], estimated_hours=20),
                AffectedComponent(file_path="src/services/breach_notification.py", component_type="service", component_name="BreachNotifier", impact_level=ImpactLevel.CRITICAL, changes_required=["Implement 1h notification"], estimated_hours=16),
                AffectedComponent(file_path="src/config/hipaa.py", component_type="config", component_name="HIPAAConfig", impact_level=ImpactLevel.MODERATE, changes_required=["Update SLA parameters"], estimated_hours=2),
            ],
            "pci_dss": [
                AffectedComponent(file_path="src/services/payment.py", component_type="service", component_name="PaymentService", impact_level=ImpactLevel.CRITICAL, changes_required=["Replace encryption with tokenization"], estimated_hours=32),
                AffectedComponent(file_path="src/models/payment.py", component_type="model", component_name="PaymentCard", impact_level=ImpactLevel.HIGH, changes_required=["Add token fields, remove encrypted PAN"], estimated_hours=8),
                AffectedComponent(file_path="src/services/tokenization.py", component_type="service", component_name="TokenizationService", impact_level=ImpactLevel.CRITICAL, changes_required=["Implement new tokenization service"], estimated_hours=40),
            ],
        }

        regulation_key = change.regulation.lower().replace("-", "_")
        components = regulation_components.get(regulation_key, [
            AffectedComponent(
                file_path="src/services/compliance.py",
                component_type="service",
                component_name="ComplianceService",
                impact_level=ImpactLevel.HIGH,
                changes_required=change.new_requirements + change.modified_requirements,
                estimated_hours=40,
            ),
        ])

        total_hours = sum(c.estimated_hours for c in components)
        files = {c.file_path for c in components}
        services = {c.component_name for c in components if c.component_type == "service"}
        endpoints = {c.component_name for c in components if c.component_type == "endpoint"}

        return BlastRadius(
            total_files=len(files),
            total_services=len(services),
            total_endpoints=len(endpoints),
            total_data_stores=sum(1 for c in components if c.component_type == "model"),
            affected_components=components,
            estimated_total_hours=total_hours,
            estimated_person_weeks=round(total_hours / 40, 1),
        )

    def _compute_overall_impact(self, blast_radius: BlastRadius) -> ImpactLevel:
        """Compute overall impact level from blast radius."""
        if any(c.impact_level == ImpactLevel.CRITICAL for c in blast_radius.affected_components):
            return ImpactLevel.CRITICAL
        if blast_radius.estimated_person_weeks > 4:
            return ImpactLevel.HIGH
        if blast_radius.estimated_person_weeks > 1:
            return ImpactLevel.MODERATE
        return ImpactLevel.LOW

    def _compute_risk_score(self, blast_radius: BlastRadius, change: RegulatoryChange) -> float:
        """Compute a 0-10 risk score."""
        component_score = min(len(blast_radius.affected_components) / 5, 1.0) * 3
        severity_score = sum(
            {"critical": 3, "high": 2, "moderate": 1, "low": 0.5, "none": 0}.get(c.impact_level.value, 0)
            for c in blast_radius.affected_components
        )
        severity_score = min(severity_score / 5, 1.0) * 4

        new_req_score = min(len(change.new_requirements) / 3, 1.0) * 3
        return min(round(component_score + severity_score + new_req_score, 1), 10.0)

    def _generate_recommendations(
        self, blast_radius: BlastRadius, change: RegulatoryChange
    ) -> list[str]:
        """Generate actionable recommendations."""
        recs = []

        critical = [c for c in blast_radius.affected_components if c.impact_level == ImpactLevel.CRITICAL]
        if critical:
            recs.append(f"Prioritize {len(critical)} critical component(s): {', '.join(c.component_name for c in critical)}")

        if blast_radius.estimated_person_weeks > 2:
            recs.append(f"Estimated effort: {blast_radius.estimated_person_weeks} person-weeks — consider dedicated sprint allocation")

        if change.new_requirements:
            recs.append(f"Implement {len(change.new_requirements)} new requirement(s) — create tracking tickets for each")

        recs.append("Run compliance scan after implementation to verify coverage")
        recs.append("Update audit documentation with change rationale and implementation evidence")

        return recs
