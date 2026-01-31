"""Compliance Simulator - What-if analysis for compliance changes."""

import time
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import structlog

from app.services.digital_twin.models import (
    ComplianceIssue,
    ComplianceSnapshot,
    ComplianceStatus,
    RegulationCompliance,
    ScenarioType,
    SimulationResult,
    SimulationScenario,
)
from app.services.digital_twin.snapshot import SnapshotManager, get_snapshot_manager


logger = structlog.get_logger()


class ComplianceSimulator:
    """Simulates compliance impact of proposed changes."""

    def __init__(self, snapshot_manager: SnapshotManager | None = None):
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
        
        # Calculate final metrics
        result.score_delta = result.simulated_score - result.baseline_score
        result.risk_delta = self._calculate_risk_delta(result)
        result.passed = result.new_critical_issues == 0 and result.score_delta >= -0.05
        
        # Generate recommendations
        result.recommendations = self._generate_recommendations(scenario, result)
        
        # Timing
        result.completed_at = datetime.utcnow()
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
            if change_type == "modify" or change_type == "delete":
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
                result.new_issues.append(ComplianceIssue(
                    code="ARCH-DATA-001",
                    message=f"New data storage component '{component}' requires data protection assessment",
                    severity="medium",
                    regulation="GDPR",
                    category="architecture",
                ))
            
            if any(kw in component_lower for kw in ["ml", "ai", "model", "inference"]):
                result.new_issues.append(ComplianceIssue(
                    code="ARCH-AI-001",
                    message=f"New AI component '{component}' may require EU AI Act compliance",
                    severity="high",
                    regulation="EU AI Act",
                    category="architecture",
                ))
            
            if any(kw in component_lower for kw in ["payment", "billing", "checkout"]):
                result.new_issues.append(ComplianceIssue(
                    code="ARCH-PCI-001",
                    message=f"New payment component '{component}' requires PCI-DSS compliance",
                    severity="critical",
                    regulation="PCI-DSS",
                    category="architecture",
                ))
        
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
            vendor_type = vendor.get("type", "saas")
            data_access = vendor.get("data_access", [])
            certifications = vendor.get("certifications", [])
            
            # Check for compliance gaps
            if "personal_data" in data_access or "pii" in data_access:
                if "SOC2" not in certifications and "ISO27001" not in certifications:
                    result.new_issues.append(ComplianceIssue(
                        code="VENDOR-CERT-001",
                        message=f"Vendor '{vendor_name}' handles personal data without SOC2/ISO27001 certification",
                        severity="high",
                        regulation="GDPR",
                        category="vendor",
                    ))
                
                result.new_issues.append(ComplianceIssue(
                    code="VENDOR-DPA-001",
                    message=f"Data Processing Agreement required for vendor '{vendor_name}'",
                    severity="medium",
                    regulation="GDPR",
                    category="vendor",
                ))
            
            if "payment" in data_access or "card" in data_access:
                if "PCI-DSS" not in certifications:
                    result.new_issues.append(ComplianceIssue(
                        code="VENDOR-PCI-001",
                        message=f"Vendor '{vendor_name}' handles payment data without PCI-DSS certification",
                        severity="critical",
                        regulation="PCI-DSS",
                        category="vendor",
                    ))
        
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
            result.new_issues.append(ComplianceIssue(
                code=f"{reg.upper()[:4]}-GAP-001",
                message=f"Gap analysis required for {reg} compliance",
                severity="high",
                regulation=reg,
                category="regulation_adoption",
            ))
            
            # Estimate initial compliance score for new regulation
            result.compliance_after[reg] = 0.3  # Initial assumption: 30% compliant
            
            result.warnings.append(f"Adopting {reg} will require comprehensive compliance assessment")
        
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
                result.new_issues.append(ComplianceIssue(
                    code="DATA-TRANSFER-001",
                    message=f"Cross-border data transfer from {source} to {destination} requires legal basis",
                    severity="high",
                    regulation="GDPR",
                    category="data_transfer",
                ))
            
            # Sensitive data flows
            if any(dt in ["health", "medical", "phi"] for dt in data_types):
                result.new_issues.append(ComplianceIssue(
                    code="DATA-PHI-001",
                    message=f"PHI data flow to {destination} requires HIPAA safeguards",
                    severity="critical",
                    regulation="HIPAA",
                    category="data_flow",
                ))
        
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
                    result.new_issues.append(ComplianceIssue(
                        code="INFRA-PIPL-001",
                        message=f"Deployment in China requires PIPL compliance",
                        severity="high",
                        regulation="PIPL",
                        category="infrastructure",
                    ))
            
            if change_type == "encryption_change":
                if not change.get("at_rest") or not change.get("in_transit"):
                    result.new_issues.append(ComplianceIssue(
                        code="INFRA-CRYPTO-001",
                        message="Encryption must be enabled at rest and in transit",
                        severity="critical",
                        regulation="HIPAA",
                        category="infrastructure",
                    ))
        
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
                issues.append(ComplianceIssue(
                    code=code,
                    message=message,
                    severity=severity,
                    file_path=file_path,
                    category="security",
                ))
        
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

    async def get_scenario(self, scenario_id: UUID) -> SimulationScenario | None:
        """Get a scenario by ID."""
        return self._scenarios.get(scenario_id)

    async def get_result(self, result_id: UUID) -> SimulationResult | None:
        """Get a simulation result by ID."""
        return self._results.get(result_id)


# Global instance
_simulator: ComplianceSimulator | None = None


def get_compliance_simulator() -> ComplianceSimulator:
    """Get or create compliance simulator."""
    global _simulator
    if _simulator is None:
        _simulator = ComplianceSimulator()
    return _simulator
