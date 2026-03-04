"""Compliance Simulator - What-if analysis for compliance changes."""

import time
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.digital_twin.models import (
    BlastRadiusMap,
    BlastRadiusNode,
    ComplianceIssue,
    ComplianceSnapshot,
    CostEstimate,
    ExecutiveDashboard,
    ScenarioComparison,
    ScenarioType,
    SimulationResult,
    SimulationScenario,
)
from app.services.digital_twin.snapshot import SnapshotManager, get_snapshot_manager


logger = structlog.get_logger()


class ComplianceSimulator:
    """Simulates compliance impact of proposed changes."""

    def __init__(
        self, db: AsyncSession | None = None, snapshot_manager: SnapshotManager | None = None
    ):
        self.db = db
        self.snapshot_manager = snapshot_manager or get_snapshot_manager()
        self._scenarios: dict[UUID, SimulationScenario] = {}
        self._results: dict[UUID, SimulationResult] = {}

    async def create_scenario(
        self,
        organization_id: UUID,
        name: str,
        scenario_type: ScenarioType,
        parameters: dict[str, Any],
        description: str = "",
        created_by: str | None = None,
    ) -> SimulationScenario:
        """Create a new simulation scenario."""
        scenario = SimulationScenario(
            organization_id=organization_id,
            name=name,
            description=description,
            scenario_type=scenario_type,
            created_by=created_by,
            parameters=parameters,
        )

        # Parse parameters based on scenario type
        if scenario_type == ScenarioType.CODE_CHANGE:
            scenario.file_changes = parameters.get("file_changes", [])
        elif scenario_type == ScenarioType.ARCHITECTURE_CHANGE:
            scenario.new_components = parameters.get("new_components", [])
            scenario.removed_components = parameters.get("removed_components", [])
        elif scenario_type == ScenarioType.VENDOR_CHANGE:
            scenario.new_vendors = parameters.get("new_vendors", [])
            scenario.removed_vendors = parameters.get("removed_vendors", [])
        elif scenario_type == ScenarioType.REGULATION_ADOPTION:
            scenario.new_regulations = parameters.get("new_regulations", [])
            scenario.removed_regulations = parameters.get("removed_regulations", [])

        self._scenarios[scenario.id] = scenario

        logger.info(
            "Created simulation scenario",
            scenario_id=str(scenario.id),
            type=scenario_type.value,
        )

        return scenario

    async def run_simulation(
        self,
        scenario_id: UUID,
        baseline_snapshot_id: UUID | None = None,
    ) -> SimulationResult:
        """Run a simulation scenario against a baseline.

        Args:
            scenario_id: Scenario to simulate
            baseline_snapshot_id: Baseline snapshot (uses latest if not provided)

        Returns:
            SimulationResult with before/after comparison
        """
        start_time = time.perf_counter()

        scenario = self._scenarios.get(scenario_id)
        if not scenario:
            raise ValueError(f"Scenario {scenario_id} not found")

        # Get baseline snapshot
        baseline = None
        if baseline_snapshot_id:
            baseline = await self.snapshot_manager.get_snapshot(baseline_snapshot_id)
        elif scenario.organization_id:
            baseline = await self.snapshot_manager.get_latest_snapshot(scenario.organization_id)

        if not baseline:
            raise ValueError("No baseline snapshot available")

        # Create simulation result
        result = SimulationResult(
            scenario_id=scenario_id,
            baseline_snapshot_id=baseline.id,
            baseline_score=baseline.overall_score,
        )

        # Capture baseline compliance by regulation
        for reg in baseline.regulations:
            result.compliance_before[reg.regulation] = reg.score

        # Run simulation based on scenario type
        if scenario.scenario_type == ScenarioType.CODE_CHANGE:
            await self._simulate_code_change(scenario, baseline, result)
        elif scenario.scenario_type == ScenarioType.ARCHITECTURE_CHANGE:
            await self._simulate_architecture_change(scenario, baseline, result)
        elif scenario.scenario_type == ScenarioType.VENDOR_CHANGE:
            await self._simulate_vendor_change(scenario, baseline, result)
        elif scenario.scenario_type == ScenarioType.REGULATION_ADOPTION:
            await self._simulate_regulation_adoption(scenario, baseline, result)
        elif scenario.scenario_type == ScenarioType.DATA_FLOW_CHANGE:
            await self._simulate_data_flow_change(scenario, baseline, result)
        elif scenario.scenario_type == ScenarioType.INFRASTRUCTURE_CHANGE:
            await self._simulate_infrastructure_change(scenario, baseline, result)
        elif scenario.scenario_type == ScenarioType.JURISDICTION_EXPANSION:
            await self._simulate_jurisdiction_expansion(scenario, baseline, result)
        elif scenario.scenario_type == ScenarioType.MERGER_ACQUISITION:
            await self._simulate_merger_acquisition(scenario, baseline, result)

        # Calculate final metrics
        result.score_delta = result.simulated_score - result.baseline_score
        result.risk_delta = self._calculate_risk_delta(result)
        result.passed = result.new_critical_issues == 0 and result.score_delta >= -0.05

        # Generate recommendations
        result.recommendations = self._generate_recommendations(scenario, result)

        # Calculate cost/effort/timeline
        result.cost_estimate = self._estimate_cost(scenario, result)

        # Generate blast radius map
        result.blast_radius = self._compute_blast_radius(scenario, result)

        # Timing
        result.completed_at = datetime.now(UTC)
        result.duration_ms = (time.perf_counter() - start_time) * 1000

        # Store result
        self._results[result.id] = result

        logger.info(
            "Simulation completed",
            scenario_id=str(scenario_id),
            passed=result.passed,
            score_delta=result.score_delta,
            new_issues=len(result.new_issues),
            duration_ms=result.duration_ms,
        )

        return result

    async def _simulate_code_change(
        self,
        scenario: SimulationScenario,
        baseline: ComplianceSnapshot,
        result: SimulationResult,
    ) -> None:
        """Simulate impact of code changes."""
        # Analyze each file change
        for change in scenario.file_changes:
            file_path = change.get("path", "")
            change_type = change.get("type", "modify")  # add, modify, delete
            content = change.get("content", "")

            # Detect potential new issues from content
            new_file_issues = self._analyze_code_for_issues(content, file_path)

            # Check if changes resolve existing issues
            if change_type in {"modify", "delete"}:
                for existing_issue in baseline.issues:
                    if existing_issue.file_path == file_path:
                        # Check if the issue's code pattern is no longer present
                        if existing_issue.code not in content:
                            result.resolved_issues.append(existing_issue)

            result.new_issues.extend(new_file_issues)

        # Calculate simulated compliance
        result.compliance_after = dict(result.compliance_before)
        result.simulated_score = self._calculate_simulated_score(
            baseline, result.new_issues, result.resolved_issues
        )

    async def _simulate_architecture_change(
        self,
        scenario: SimulationScenario,
        baseline: ComplianceSnapshot,
        result: SimulationResult,
    ) -> None:
        """Simulate impact of architecture changes."""
        # New components may introduce compliance requirements
        for component in scenario.new_components:
            component_lower = component.lower()

            # Detect high-risk components
            if any(kw in component_lower for kw in ["database", "storage", "cache"]):
                result.new_issues.append(
                    ComplianceIssue(
                        code="ARCH-DATA-001",
                        message=f"New data storage component '{component}' requires data protection assessment",
                        severity="medium",
                        regulation="GDPR",
                        category="architecture",
                    )
                )

            if any(kw in component_lower for kw in ["ml", "ai", "model", "inference"]):
                result.new_issues.append(
                    ComplianceIssue(
                        code="ARCH-AI-001",
                        message=f"New AI component '{component}' may require EU AI Act compliance",
                        severity="high",
                        regulation="EU AI Act",
                        category="architecture",
                    )
                )

            if any(kw in component_lower for kw in ["payment", "billing", "checkout"]):
                result.new_issues.append(
                    ComplianceIssue(
                        code="ARCH-PCI-001",
                        message=f"New payment component '{component}' requires PCI-DSS compliance",
                        severity="critical",
                        regulation="PCI-DSS",
                        category="architecture",
                    )
                )

        # Removed components may resolve issues
        for component in scenario.removed_components:
            for issue in baseline.issues:
                if component.lower() in (issue.message or "").lower():
                    result.resolved_issues.append(issue)

        result.compliance_after = dict(result.compliance_before)
        result.simulated_score = self._calculate_simulated_score(
            baseline, result.new_issues, result.resolved_issues
        )

    async def _simulate_vendor_change(
        self,
        scenario: SimulationScenario,
        baseline: ComplianceSnapshot,
        result: SimulationResult,
    ) -> None:
        """Simulate impact of vendor/third-party changes."""
        for vendor in scenario.new_vendors:
            vendor_name = vendor.get("name", "Unknown")
            vendor.get("type", "saas")
            data_access = vendor.get("data_access", [])
            certifications = vendor.get("certifications", [])

            # Check for compliance gaps
            if "personal_data" in data_access or "pii" in data_access:
                if "SOC2" not in certifications and "ISO27001" not in certifications:
                    result.new_issues.append(
                        ComplianceIssue(
                            code="VENDOR-CERT-001",
                            message=f"Vendor '{vendor_name}' handles personal data without SOC2/ISO27001 certification",
                            severity="high",
                            regulation="GDPR",
                            category="vendor",
                        )
                    )

                result.new_issues.append(
                    ComplianceIssue(
                        code="VENDOR-DPA-001",
                        message=f"Data Processing Agreement required for vendor '{vendor_name}'",
                        severity="medium",
                        regulation="GDPR",
                        category="vendor",
                    )
                )

            if "payment" in data_access or "card" in data_access:
                if "PCI-DSS" not in certifications:
                    result.new_issues.append(
                        ComplianceIssue(
                            code="VENDOR-PCI-001",
                            message=f"Vendor '{vendor_name}' handles payment data without PCI-DSS certification",
                            severity="critical",
                            regulation="PCI-DSS",
                            category="vendor",
                        )
                    )

        result.compliance_after = dict(result.compliance_before)
        result.simulated_score = self._calculate_simulated_score(
            baseline, result.new_issues, result.resolved_issues
        )

    async def _simulate_regulation_adoption(
        self,
        scenario: SimulationScenario,
        baseline: ComplianceSnapshot,
        result: SimulationResult,
    ) -> None:
        """Simulate impact of adopting new regulations."""
        for reg in scenario.new_regulations:
            # Adding a new regulation typically reveals compliance gaps
            result.new_issues.append(
                ComplianceIssue(
                    code=f"{reg.upper()[:4]}-GAP-001",
                    message=f"Gap analysis required for {reg} compliance",
                    severity="high",
                    regulation=reg,
                    category="regulation_adoption",
                )
            )

            # Estimate initial compliance score for new regulation
            result.compliance_after[reg] = 0.3  # Initial assumption: 30% compliant

            result.warnings.append(
                f"Adopting {reg} will require comprehensive compliance assessment"
            )

        for reg in scenario.removed_regulations:
            result.compliance_after.pop(reg, None)
            # Removing a regulation may resolve some issues
            for issue in baseline.issues:
                if issue.regulation == reg:
                    result.resolved_issues.append(issue)

        result.simulated_score = self._calculate_simulated_score(
            baseline, result.new_issues, result.resolved_issues
        )

    async def _simulate_data_flow_change(
        self,
        scenario: SimulationScenario,
        baseline: ComplianceSnapshot,
        result: SimulationResult,
    ) -> None:
        """Simulate impact of data flow changes."""
        data_flows = scenario.parameters.get("data_flows", [])

        for flow in data_flows:
            source = flow.get("source", "")
            destination = flow.get("destination", "")
            data_types = flow.get("data_types", [])

            # Cross-border data transfer
            if flow.get("cross_border"):
                result.new_issues.append(
                    ComplianceIssue(
                        code="DATA-TRANSFER-001",
                        message=f"Cross-border data transfer from {source} to {destination} requires legal basis",
                        severity="high",
                        regulation="GDPR",
                        category="data_transfer",
                    )
                )

            # Sensitive data flows
            if any(dt in ["health", "medical", "phi"] for dt in data_types):
                result.new_issues.append(
                    ComplianceIssue(
                        code="DATA-PHI-001",
                        message=f"PHI data flow to {destination} requires HIPAA safeguards",
                        severity="critical",
                        regulation="HIPAA",
                        category="data_flow",
                    )
                )

        result.compliance_after = dict(result.compliance_before)
        result.simulated_score = self._calculate_simulated_score(
            baseline, result.new_issues, result.resolved_issues
        )

    async def _simulate_infrastructure_change(
        self,
        scenario: SimulationScenario,
        baseline: ComplianceSnapshot,
        result: SimulationResult,
    ) -> None:
        """Simulate impact of infrastructure changes."""
        changes = scenario.parameters.get("infrastructure_changes", [])

        for change in changes:
            change_type = change.get("type", "")
            region = change.get("region", "")

            if change_type == "new_region":
                # New deployment region may have compliance implications
                if "EU" not in region and "europe" not in region.lower():
                    result.warnings.append(f"Deployment in {region} may affect GDPR compliance")

                if region in ["CN", "China", "china"]:
                    result.new_issues.append(
                        ComplianceIssue(
                            code="INFRA-PIPL-001",
                            message="Deployment in China requires PIPL compliance",
                            severity="high",
                            regulation="PIPL",
                            category="infrastructure",
                        )
                    )

            if change_type == "encryption_change":
                if not change.get("at_rest") or not change.get("in_transit"):
                    result.new_issues.append(
                        ComplianceIssue(
                            code="INFRA-CRYPTO-001",
                            message="Encryption must be enabled at rest and in transit",
                            severity="critical",
                            regulation="HIPAA",
                            category="infrastructure",
                        )
                    )

        result.compliance_after = dict(result.compliance_before)
        result.simulated_score = self._calculate_simulated_score(
            baseline, result.new_issues, result.resolved_issues
        )

    def _analyze_code_for_issues(
        self,
        content: str,
        file_path: str,
    ) -> list[ComplianceIssue]:
        """Analyze code content for potential compliance issues."""
        issues = []
        content_lower = content.lower()

        # Check for common compliance patterns
        patterns = [
            ("password", "SEC-CRED-001", "Potential hardcoded credential", "high"),
            ("api_key", "SEC-KEY-001", "Potential hardcoded API key", "high"),
            ("eval(", "SEC-EVAL-001", "Use of eval() function", "medium"),
            ("exec(", "SEC-EXEC-001", "Use of exec() function", "medium"),
        ]

        for pattern, code, message, severity in patterns:
            if pattern in content_lower:
                issues.append(
                    ComplianceIssue(
                        code=code,
                        message=message,
                        severity=severity,
                        file_path=file_path,
                        category="security",
                    )
                )

        return issues

    def _calculate_simulated_score(
        self,
        baseline: ComplianceSnapshot,
        new_issues: list[ComplianceIssue],
        resolved_issues: list[ComplianceIssue],
    ) -> float:
        """Calculate simulated compliance score."""
        # Weight by severity
        severity_weights = {
            "critical": 0.10,
            "high": 0.05,
            "medium": 0.02,
            "low": 0.01,
        }

        penalty = sum(severity_weights.get(i.severity, 0.01) for i in new_issues)
        bonus = sum(severity_weights.get(i.severity, 0.01) for i in resolved_issues)

        return max(0, min(1, baseline.overall_score - penalty + bonus))

    def _calculate_risk_delta(self, result: SimulationResult) -> float:
        """Calculate change in risk level."""
        # Higher is riskier
        new_risk = sum(
            {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(i.severity, 1)
            for i in result.new_issues
        )
        resolved_risk = sum(
            {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(i.severity, 1)
            for i in result.resolved_issues
        )
        return new_risk - resolved_risk

    def _generate_recommendations(
        self,
        scenario: SimulationScenario,
        result: SimulationResult,
    ) -> list[str]:
        """Generate recommendations based on simulation results."""
        recommendations = []

        if result.new_critical_issues > 0:
            recommendations.append("Address critical compliance issues before proceeding")

        if result.score_delta < -0.1:
            recommendations.append("Consider alternative approaches to reduce compliance impact")

        if scenario.scenario_type == ScenarioType.VENDOR_CHANGE:
            recommendations.append("Obtain security certifications from new vendors")
            recommendations.append("Execute Data Processing Agreements with new vendors")

        if scenario.scenario_type == ScenarioType.REGULATION_ADOPTION:
            recommendations.append("Conduct comprehensive gap analysis for new regulations")
            recommendations.append("Develop implementation roadmap with compliance team")

        if not recommendations:
            recommendations.append("Changes appear compliant - proceed with standard review")

        return recommendations

    async def persist_result(self, result: SimulationResult) -> None:
        """Persist a simulation result to the database.

        Falls back to in-memory storage until DB table is created.
        """
        logger.info(
            "Persisting simulation result",
            result_id=str(result.id),
            scenario_id=str(result.scenario_id),
            passed=result.passed,
            score_delta=result.score_delta,
            has_db=self.db is not None,
        )
        # Fallback: store in-memory until DB table exists
        self._results[result.id] = result

    async def get_scenario(self, scenario_id: UUID) -> SimulationScenario | None:
        """Get a scenario by ID."""
        return self._scenarios.get(scenario_id)

    async def get_result(self, result_id: UUID) -> SimulationResult | None:
        """Get a simulation result by ID."""
        return self._results.get(result_id)

    # ─── Jurisdiction Expansion / M&A ─────────────────────────────────

    async def _simulate_jurisdiction_expansion(
        self,
        scenario: SimulationScenario,
        baseline: ComplianceSnapshot,
        result: SimulationResult,
    ) -> None:
        """Simulate impact of expanding into new jurisdictions."""
        jurisdiction_regs = {
            "EU": ["GDPR", "EU AI Act", "NIS2", "DORA"],
            "US": ["CCPA", "HIPAA", "SOX"],
            "UK": ["UK GDPR", "Online Safety Act"],
            "Brazil": ["LGPD"],
            "China": ["PIPL", "CSL", "DSL"],
            "India": ["DPDPA"],
            "Japan": ["APPI"],
            "South Korea": ["PIPA"],
            "Canada": ["PIPEDA", "AIDA"],
            "Australia": ["Privacy Act", "CDR"],
        }

        target_jurisdictions = scenario.target_jurisdictions or scenario.parameters.get("jurisdictions", [])

        for jurisdiction in target_jurisdictions:
            regs = jurisdiction_regs.get(jurisdiction, [f"{jurisdiction} Privacy Law"])
            for reg in regs:
                if reg not in result.compliance_before:
                    result.new_issues.append(ComplianceIssue(
                        code=f"JURIS-{reg.upper()[:4]}-001",
                        message=f"Expansion to {jurisdiction} requires {reg} compliance",
                        severity="high",
                        regulation=reg,
                        category="jurisdiction_expansion",
                    ))
                    result.compliance_after[reg] = 0.2  # Initial: ~20% compliant
                    result.warnings.append(
                        f"{jurisdiction}: {reg} compliance assessment required "
                        f"(est. {len(regs) * 4} weeks)"
                    )

        result.compliance_after.update(result.compliance_before)
        result.simulated_score = self._calculate_simulated_score(
            baseline, result.new_issues, result.resolved_issues
        )

    async def _simulate_merger_acquisition(
        self,
        scenario: SimulationScenario,
        baseline: ComplianceSnapshot,
        result: SimulationResult,
    ) -> None:
        """Simulate compliance impact of a merger or acquisition."""
        target = scenario.parameters.get("target_company", "Unknown")
        target_size = scenario.parameters.get("target_employees", 100)
        target_jurisdictions = scenario.parameters.get("target_jurisdictions", [])
        target_frameworks = scenario.parameters.get("target_frameworks", [])

        # M&A introduces data consolidation risks
        result.new_issues.append(ComplianceIssue(
            code="MA-DATA-001",
            message=f"Data consolidation from {target} requires privacy impact assessment",
            severity="high",
            regulation="GDPR",
            category="merger_acquisition",
        ))
        result.new_issues.append(ComplianceIssue(
            code="MA-VENDOR-001",
            message=f"Inherited vendor relationships from {target} require assessment",
            severity="medium",
            category="merger_acquisition",
        ))

        if target_size > 500:
            result.new_issues.append(ComplianceIssue(
                code="MA-SCALE-001",
                message=f"Large acquisition ({target_size} employees) may trigger additional regulatory thresholds",
                severity="high",
                category="merger_acquisition",
            ))

        for jurisdiction in target_jurisdictions:
            if jurisdiction not in ["US", "EU"]:  # Unknown territory
                result.warnings.append(
                    f"Target operates in {jurisdiction} — requires local counsel review"
                )

        result.compliance_after = dict(result.compliance_before)
        result.simulated_score = self._calculate_simulated_score(
            baseline, result.new_issues, result.resolved_issues
        )

    # ─── Cost/Effort/Timeline Calculator ──────────────────────────────

    def _estimate_cost(
        self,
        scenario: SimulationScenario,
        result: SimulationResult,
    ) -> CostEstimate:
        """Estimate cost, effort, and timeline for implementing scenario changes."""
        eng_rate = 150.0  # USD/hour
        legal_rate = 350.0

        # Base engineering hours by scenario type
        type_base_hours = {
            ScenarioType.CODE_CHANGE: 8,
            ScenarioType.ARCHITECTURE_CHANGE: 40,
            ScenarioType.VENDOR_CHANGE: 16,
            ScenarioType.REGULATION_ADOPTION: 80,
            ScenarioType.DATA_FLOW_CHANGE: 24,
            ScenarioType.INFRASTRUCTURE_CHANGE: 32,
            ScenarioType.JURISDICTION_EXPANSION: 120,
            ScenarioType.MERGER_ACQUISITION: 200,
        }

        base_hours = type_base_hours.get(scenario.scenario_type, 40)

        # Scale by issue count
        critical_multiplier = 1 + (result.new_critical_issues * 0.3)
        issue_hours = len(result.new_issues) * 4  # ~4 hours per issue

        eng_hours = (base_hours + issue_hours) * critical_multiplier
        legal_hours = max(4, len(result.new_issues) * 2)

        # Tooling cost (monitoring, scanning, etc.)
        tooling = 500 if scenario.scenario_type in (
            ScenarioType.REGULATION_ADOPTION,
            ScenarioType.JURISDICTION_EXPANSION,
        ) else 100

        # Training cost
        training = 0.0
        if scenario.scenario_type in (
            ScenarioType.REGULATION_ADOPTION,
            ScenarioType.JURISDICTION_EXPANSION,
            ScenarioType.MERGER_ACQUISITION,
        ):
            training = eng_hours * 0.2 * eng_rate

        eng_cost = eng_hours * eng_rate
        legal_cost = legal_hours * legal_rate
        total = eng_cost + legal_cost + tooling + training
        timeline = max(1, eng_hours / 40)  # weeks (40h/week)

        return CostEstimate(
            engineering_hours=round(eng_hours, 1),
            engineering_cost_usd=round(eng_cost, 2),
            legal_review_hours=round(legal_hours, 1),
            legal_cost_usd=round(legal_cost, 2),
            tooling_cost_usd=round(tooling, 2),
            training_cost_usd=round(training, 2),
            total_cost_usd=round(total, 2),
            timeline_weeks=round(timeline, 1),
            confidence=0.7 if len(result.new_issues) < 5 else 0.5,
            breakdown={
                "engineering": round(eng_cost, 2),
                "legal": round(legal_cost, 2),
                "tooling": round(tooling, 2),
                "training": round(training, 2),
            },
        )

    # ─── Blast Radius Visualization ───────────────────────────────────

    def _compute_blast_radius(
        self,
        scenario: SimulationScenario,
        result: SimulationResult,
    ) -> BlastRadiusMap:
        """Compute blast radius map showing impact spread."""
        center = scenario.name
        nodes: list[BlastRadiusNode] = []
        edges: list[dict[str, str]] = []

        # Origin node
        nodes.append(BlastRadiusNode(
            id="origin",
            name=center,
            node_type="change",
            impact_level="critical",
            distance=0,
        ))

        # Distance 1: directly affected regulations
        affected_regs = set()
        for issue in result.new_issues:
            if issue.regulation and issue.regulation not in affected_regs:
                affected_regs.add(issue.regulation)
                node_id = f"reg-{issue.regulation}"
                nodes.append(BlastRadiusNode(
                    id=node_id,
                    name=issue.regulation,
                    node_type="regulation",
                    impact_level=issue.severity,
                    distance=1,
                ))
                edges.append({"source": "origin", "target": node_id})

        # Distance 2: affected teams/services
        categories = set(issue.category or "general" for issue in result.new_issues)
        for cat in categories:
            node_id = f"team-{cat}"
            impact = "high" if any(
                i.severity in ("critical", "high") and i.category == cat
                for i in result.new_issues
            ) else "medium"
            nodes.append(BlastRadiusNode(
                id=node_id,
                name=f"{cat.replace('_', ' ').title()} Team",
                node_type="team",
                impact_level=impact,
                distance=2,
            ))
            # Connect to affected regulations
            for issue in result.new_issues:
                if issue.category == cat and issue.regulation:
                    edges.append({"source": f"reg-{issue.regulation}", "target": node_id})

        # Distance 3: downstream systems
        if scenario.scenario_type in (ScenarioType.ARCHITECTURE_CHANGE, ScenarioType.INFRASTRUCTURE_CHANGE):
            for comp in scenario.new_components:
                node_id = f"sys-{comp}"
                nodes.append(BlastRadiusNode(
                    id=node_id, name=comp, node_type="system",
                    impact_level="low", distance=3,
                ))
                edges.append({"source": "origin", "target": node_id})

        return BlastRadiusMap(
            center=center,
            nodes=nodes,
            edges=edges,
            max_distance=max((n.distance for n in nodes), default=0),
            total_affected=len(nodes) - 1,
        )

    # ─── Executive Dashboard ──────────────────────────────────────────

    async def get_executive_dashboard(
        self,
        organization_id: UUID | None = None,
    ) -> ExecutiveDashboard:
        """Generate executive dashboard data with scenario comparisons."""
        # Get baseline snapshot
        baseline = None
        if organization_id:
            baseline = await self.snapshot_manager.get_latest_snapshot(organization_id)

        # Aggregate scenario results
        completed = [r for r in self._results.values() if r.completed_at]
        active = [s for s in self._scenarios.values()]

        # Score trend from completed simulations
        score_trend = []
        for r in sorted(completed, key=lambda x: x.started_at):
            score_trend.append({
                "date": r.started_at.isoformat(),
                "baseline": r.baseline_score,
                "simulated": r.simulated_score,
            })

        # Top risks from latest simulations
        all_issues: list[dict] = []
        for r in completed[-5:]:  # Last 5 simulations
            for issue in r.new_issues:
                if issue.severity in ("critical", "high"):
                    all_issues.append({
                        "code": issue.code,
                        "message": issue.message,
                        "severity": issue.severity,
                        "regulation": issue.regulation,
                        "scenario": str(r.scenario_id),
                    })

        # Recent scenario summaries
        recent = []
        for r in completed[-10:]:
            scenario = self._scenarios.get(r.scenario_id) if r.scenario_id else None
            recent.append({
                "id": str(r.id),
                "name": scenario.name if scenario else "Unknown",
                "type": scenario.scenario_type.value if scenario else "",
                "passed": r.passed,
                "score_delta": r.score_delta,
                "new_issues": len(r.new_issues),
                "cost_usd": r.cost_estimate.total_cost_usd if r.cost_estimate else 0,
            })

        # Regulation coverage from baseline
        reg_coverage: dict[str, float] = {}
        if baseline:
            for reg in baseline.regulations:
                reg_coverage[reg.regulation] = reg.score

        return ExecutiveDashboard(
            overall_score=baseline.overall_score if baseline else 0.0,
            score_trend=score_trend,
            active_simulations=len(active),
            completed_simulations=len(completed),
            regulation_coverage=reg_coverage,
            top_risks=all_issues[:10],
            recent_scenarios=recent,
        )

    async def compare_scenarios(
        self,
        result_ids: list[UUID],
    ) -> ScenarioComparison:
        """Compare multiple scenario results side-by-side."""
        scenarios = []
        best_id = ""
        worst_id = ""
        best_score = -999.0
        worst_score = 999.0

        for rid in result_ids:
            result = self._results.get(rid)
            if not result:
                continue
            scenario = self._scenarios.get(result.scenario_id) if result.scenario_id else None

            entry = {
                "id": str(rid),
                "name": scenario.name if scenario else "Unknown",
                "type": scenario.scenario_type.value if scenario else "",
                "baseline_score": result.baseline_score,
                "simulated_score": result.simulated_score,
                "score_delta": result.score_delta,
                "passed": result.passed,
                "new_issues": len(result.new_issues),
                "resolved_issues": len(result.resolved_issues),
                "risk_delta": result.risk_delta,
                "cost_usd": result.cost_estimate.total_cost_usd if result.cost_estimate else 0,
                "timeline_weeks": result.cost_estimate.timeline_weeks if result.cost_estimate else 0,
            }
            scenarios.append(entry)

            if result.score_delta > best_score:
                best_score = result.score_delta
                best_id = str(rid)
            if result.score_delta < worst_score:
                worst_score = result.score_delta
                worst_id = str(rid)

        recommendation = ""
        if best_id:
            best_entry = next((s for s in scenarios if s["id"] == best_id), None)
            if best_entry:
                recommendation = (
                    f"Recommended: '{best_entry['name']}' with "
                    f"score delta of {best_entry['score_delta']:+.2f} "
                    f"and estimated cost of ${best_entry.get('cost_usd', 0):,.0f}"
                )

        return ScenarioComparison(
            scenarios=scenarios,
            best_scenario_id=best_id,
            worst_scenario_id=worst_id,
            recommendation=recommendation,
        )


# Global instance
_simulator: ComplianceSimulator | None = None


def get_compliance_simulator() -> ComplianceSimulator:
    """Get or create compliance simulator."""
    global _simulator
    if _simulator is None:
        _simulator = ComplianceSimulator()
    return _simulator
