"""Compliance simulation sandbox for what-if analysis."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

import structlog


logger = structlog.get_logger()


class SimulationType(str, Enum):
    """Types of compliance simulations."""

    CODE_CHANGE = "code_change"
    ARCHITECTURE_CHANGE = "architecture_change"
    DATA_FLOW_CHANGE = "data_flow_change"
    REGULATION_CHANGE = "regulation_change"
    VENDOR_CHANGE = "vendor_change"


@dataclass
class SimulationScenario:
    """A compliance simulation scenario."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    simulation_type: SimulationType = SimulationType.CODE_CHANGE
    parameters: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = ""


@dataclass
class SimulationResult:
    """Result of running a compliance simulation."""

    id: UUID = field(default_factory=uuid4)
    scenario_id: UUID = field(default_factory=uuid4)
    status: str = "completed"  # running, completed, failed
    compliance_before: dict[str, float] = field(default_factory=dict)
    compliance_after: dict[str, float] = field(default_factory=dict)
    new_issues: list[dict[str, Any]] = field(default_factory=list)
    resolved_issues: list[dict[str, Any]] = field(default_factory=list)
    risk_delta: float = 0.0
    recommendations: list[str] = field(default_factory=list)
    analysis_details: dict[str, Any] = field(default_factory=dict)
    simulated_at: datetime = field(default_factory=datetime.utcnow)
    duration_ms: float = 0.0


class ComplianceSandbox:
    """Sandbox for compliance what-if analysis.

    Allows testing proposed changes against compliance requirements
    before implementing them.
    """

    def __init__(self):
        self._scenarios: dict[UUID, SimulationScenario] = {}
        self._results: dict[UUID, SimulationResult] = {}

    async def create_scenario(
        self,
        name: str,
        simulation_type: SimulationType,
        parameters: dict[str, Any],
        description: str = "",
        created_by: str = "",
    ) -> SimulationScenario:
        """Create a new simulation scenario."""
        scenario = SimulationScenario(
            name=name,
            description=description,
            simulation_type=simulation_type,
            parameters=parameters,
            created_by=created_by,
        )
        self._scenarios[scenario.id] = scenario
        return scenario

    async def run_simulation(
        self,
        scenario_id: UUID,
        current_state: dict[str, Any],
    ) -> SimulationResult:
        """Run a compliance simulation.

        Args:
            scenario_id: ID of the scenario to simulate
            current_state: Current compliance state including code, regulations, etc.

        Returns:
            Simulation result with compliance impact analysis
        """
        import time

        start_time = time.perf_counter()

        scenario = self._scenarios.get(scenario_id)
        if not scenario:
            raise ValueError(f"Scenario {scenario_id} not found")

        # Get current compliance scores
        compliance_before = current_state.get("compliance_scores", {
            "GDPR": 85.0,
            "CCPA": 90.0,
            "HIPAA": 80.0,
            "SOX": 75.0,
        })

        # Simulate based on scenario type
        if scenario.simulation_type == SimulationType.CODE_CHANGE:
            result = await self._simulate_code_change(scenario, current_state, compliance_before)
        elif scenario.simulation_type == SimulationType.ARCHITECTURE_CHANGE:
            result = await self._simulate_architecture_change(scenario, current_state, compliance_before)
        elif scenario.simulation_type == SimulationType.DATA_FLOW_CHANGE:
            result = await self._simulate_data_flow_change(scenario, current_state, compliance_before)
        elif scenario.simulation_type == SimulationType.REGULATION_CHANGE:
            result = await self._simulate_regulation_change(scenario, current_state, compliance_before)
        elif scenario.simulation_type == SimulationType.VENDOR_CHANGE:
            result = await self._simulate_vendor_change(scenario, current_state, compliance_before)
        else:
            raise ValueError(f"Unknown simulation type: {scenario.simulation_type}")

        result.scenario_id = scenario_id
        result.duration_ms = (time.perf_counter() - start_time) * 1000

        self._results[result.id] = result
        return result

    async def _simulate_code_change(
        self,
        scenario: SimulationScenario,
        current_state: dict[str, Any],
        compliance_before: dict[str, float],
    ) -> SimulationResult:
        """Simulate impact of code changes on compliance."""
        from app.services.ide import IDEComplianceAnalyzer

        params = scenario.parameters
        code_changes = params.get("code_changes", [])
        language = params.get("language", "python")

        analyzer = IDEComplianceAnalyzer()
        new_issues = []
        resolved_issues = []

        # Analyze proposed code
        for change in code_changes:
            file_path = change.get("file")
            new_content = change.get("content", "")
            old_content = change.get("old_content", "")

            # Analyze new code
            new_result = analyzer.analyze_document(file_path, new_content, language)
            new_codes = {d.code for d in new_result.diagnostics}

            # Analyze old code if provided
            if old_content:
                old_result = analyzer.analyze_document(file_path, old_content, language)
                old_codes = {d.code for d in old_result.diagnostics}

                # Find new issues
                for diag in new_result.diagnostics:
                    if diag.code not in old_codes:
                        new_issues.append({
                            "file": file_path,
                            "code": diag.code,
                            "message": diag.message,
                            "severity": diag.severity.value,
                            "regulation": diag.regulation,
                        })

                # Find resolved issues
                for diag in old_result.diagnostics:
                    if diag.code not in new_codes:
                        resolved_issues.append({
                            "file": file_path,
                            "code": diag.code,
                            "message": diag.message,
                            "regulation": diag.regulation,
                        })
            else:
                for diag in new_result.diagnostics:
                    new_issues.append({
                        "file": file_path,
                        "code": diag.code,
                        "message": diag.message,
                        "severity": diag.severity.value,
                        "regulation": diag.regulation,
                    })

        # Calculate compliance impact
        compliance_after = compliance_before.copy()
        for issue in new_issues:
            reg = issue.get("regulation")
            if reg and reg in compliance_after:
                compliance_after[reg] = max(0, compliance_after[reg] - 5)

        for issue in resolved_issues:
            reg = issue.get("regulation")
            if reg and reg in compliance_after:
                compliance_after[reg] = min(100, compliance_after[reg] + 3)

        # Calculate risk delta
        before_avg = sum(compliance_before.values()) / len(compliance_before) if compliance_before else 0
        after_avg = sum(compliance_after.values()) / len(compliance_after) if compliance_after else 0
        risk_delta = before_avg - after_avg  # Positive = increased risk

        # Generate recommendations
        recommendations = []
        if new_issues:
            recommendations.append(f"Address {len(new_issues)} new compliance issues before merging")
            if any(i.get("severity") == "error" for i in new_issues):
                recommendations.append("Critical issues detected - consider revising approach")
        if resolved_issues:
            recommendations.append(f"This change resolves {len(resolved_issues)} existing issues")

        return SimulationResult(
            compliance_before=compliance_before,
            compliance_after=compliance_after,
            new_issues=new_issues,
            resolved_issues=resolved_issues,
            risk_delta=risk_delta,
            recommendations=recommendations,
            analysis_details={
                "files_analyzed": len(code_changes),
                "language": language,
            },
        )

    async def _simulate_architecture_change(
        self,
        scenario: SimulationScenario,
        current_state: dict[str, Any],
        compliance_before: dict[str, float],
    ) -> SimulationResult:
        """Simulate impact of architecture changes."""
        params = scenario.parameters
        new_components = params.get("new_components", [])
        removed_components = params.get("removed_components", [])
        data_flows = params.get("data_flows", [])

        new_issues = []
        recommendations = []
        compliance_after = compliance_before.copy()

        # Check new component implications
        for component in new_components:
            component_type = component.get("type", "")
            location = component.get("location", "")

            if "database" in component_type.lower():
                if "eu" not in location.lower():
                    new_issues.append({
                        "code": "ARCH-DR-001",
                        "message": f"Database {component.get('name')} not in EU region",
                        "severity": "warning",
                        "regulation": "GDPR",
                    })
                    compliance_after["GDPR"] = max(0, compliance_after.get("GDPR", 100) - 10)

            if "third-party" in component_type.lower() or "external" in component_type.lower():
                new_issues.append({
                    "code": "ARCH-VND-001",
                    "message": f"Third-party component {component.get('name')} requires vendor assessment",
                    "severity": "info",
                    "regulation": "SOC 2",
                })
                recommendations.append(f"Complete vendor risk assessment for {component.get('name')}")

        # Check data flow implications
        for flow in data_flows:
            if flow.get("crosses_border"):
                new_issues.append({
                    "code": "ARCH-XB-001",
                    "message": f"Data flow '{flow.get('name')}' crosses borders",
                    "severity": "warning",
                    "regulation": "GDPR",
                })
                recommendations.append("Implement Standard Contractual Clauses for cross-border transfer")

        risk_delta = sum(compliance_before.values()) - sum(compliance_after.values())

        return SimulationResult(
            compliance_before=compliance_before,
            compliance_after=compliance_after,
            new_issues=new_issues,
            resolved_issues=[],
            risk_delta=risk_delta / len(compliance_before) if compliance_before else 0,
            recommendations=recommendations,
            analysis_details={
                "new_components": len(new_components),
                "removed_components": len(removed_components),
                "data_flows_analyzed": len(data_flows),
            },
        )

    async def _simulate_data_flow_change(
        self,
        scenario: SimulationScenario,
        current_state: dict[str, Any],
        compliance_before: dict[str, float],
    ) -> SimulationResult:
        """Simulate impact of data flow changes."""
        params = scenario.parameters
        compliance_after = compliance_before.copy()
        new_issues = []
        recommendations = []

        new_data_types = params.get("new_data_types", [])
        new_processors = params.get("new_processors", [])
        new_destinations = params.get("new_destinations", [])

        # Check sensitive data types
        sensitive_types = ["PII", "PHI", "financial", "biometric"]
        for dt in new_data_types:
            if dt in sensitive_types:
                new_issues.append({
                    "code": "DATA-SENS-001",
                    "message": f"New sensitive data type '{dt}' requires additional controls",
                    "severity": "warning",
                    "regulation": "GDPR",
                })
                recommendations.append(f"Implement data protection impact assessment for {dt}")

        # Check new processors
        for processor in new_processors:
            new_issues.append({
                "code": "DATA-PROC-001",
                "message": f"New data processor '{processor}' requires DPA",
                "severity": "info",
                "regulation": "GDPR",
            })
            recommendations.append(f"Execute Data Processing Agreement with {processor}")

        # Check destinations
        non_adequate = ["US", "CN", "IN"]  # Simplified
        for dest in new_destinations:
            if dest.get("country") in non_adequate:
                compliance_after["GDPR"] = max(0, compliance_after.get("GDPR", 100) - 15)
                new_issues.append({
                    "code": "DATA-XFR-001",
                    "message": f"Transfer to {dest.get('country')} requires adequacy measures",
                    "severity": "error",
                    "regulation": "GDPR",
                })

        return SimulationResult(
            compliance_before=compliance_before,
            compliance_after=compliance_after,
            new_issues=new_issues,
            resolved_issues=[],
            risk_delta=(sum(compliance_before.values()) - sum(compliance_after.values())) / len(compliance_before) if compliance_before else 0,
            recommendations=recommendations,
        )

    async def _simulate_regulation_change(
        self,
        scenario: SimulationScenario,
        current_state: dict[str, Any],
        compliance_before: dict[str, float],
    ) -> SimulationResult:
        """Simulate impact of new regulations."""
        params = scenario.parameters
        new_regulations = params.get("new_regulations", [])
        compliance_after = compliance_before.copy()
        new_issues = []
        recommendations = []

        for reg in new_regulations:
            reg_name = reg.get("name", "Unknown")
            requirements = reg.get("requirements", [])

            # Add new regulation with estimated compliance
            compliance_after[reg_name] = reg.get("estimated_initial_compliance", 50.0)

            for req in requirements:
                new_issues.append({
                    "code": f"{reg_name[:4].upper()}-NEW-{requirements.index(req)+1:03d}",
                    "message": req,
                    "severity": "warning",
                    "regulation": reg_name,
                })

            recommendations.append(f"Begin {reg_name} compliance assessment")
            recommendations.append(f"Allocate resources for {len(requirements)} new requirements")

        return SimulationResult(
            compliance_before=compliance_before,
            compliance_after=compliance_after,
            new_issues=new_issues,
            resolved_issues=[],
            risk_delta=0,  # Risk concept changes with new regulations
            recommendations=recommendations,
            analysis_details={
                "new_regulations": len(new_regulations),
                "new_requirements": sum(len(r.get("requirements", [])) for r in new_regulations),
            },
        )

    async def _simulate_vendor_change(
        self,
        scenario: SimulationScenario,
        current_state: dict[str, Any],
        compliance_before: dict[str, float],
    ) -> SimulationResult:
        """Simulate impact of vendor changes."""
        params = scenario.parameters
        compliance_after = compliance_before.copy()
        new_issues = []
        resolved_issues = []
        recommendations = []

        old_vendor = params.get("old_vendor", {})
        new_vendor = params.get("new_vendor", {})

        # Compare certifications
        old_certs = set(old_vendor.get("certifications", []))
        new_certs = set(new_vendor.get("certifications", []))

        lost_certs = old_certs - new_certs
        gained_certs = new_certs - old_certs

        for cert in lost_certs:
            new_issues.append({
                "code": "VND-CERT-001",
                "message": f"New vendor lacks {cert} certification",
                "severity": "warning",
                "regulation": cert,
            })
            if cert in compliance_after:
                compliance_after[cert] = max(0, compliance_after[cert] - 10)

        for cert in gained_certs:
            resolved_issues.append({
                "code": "VND-CERT-002",
                "message": f"New vendor adds {cert} certification",
                "regulation": cert,
            })

        # Check data location
        if new_vendor.get("data_location") != old_vendor.get("data_location"):
            recommendations.append("Review data residency requirements for new vendor location")

        return SimulationResult(
            compliance_before=compliance_before,
            compliance_after=compliance_after,
            new_issues=new_issues,
            resolved_issues=resolved_issues,
            risk_delta=(sum(compliance_before.values()) - sum(compliance_after.values())) / len(compliance_before) if compliance_before else 0,
            recommendations=recommendations,
        )

    def get_scenario(self, scenario_id: UUID) -> SimulationScenario | None:
        """Get a scenario by ID."""
        return self._scenarios.get(scenario_id)

    def get_result(self, result_id: UUID) -> SimulationResult | None:
        """Get a result by ID."""
        return self._results.get(result_id)

    def list_scenarios(self, created_by: str | None = None) -> list[SimulationScenario]:
        """List all scenarios, optionally filtered by creator."""
        scenarios = list(self._scenarios.values())
        if created_by:
            scenarios = [s for s in scenarios if s.created_by == created_by]
        return sorted(scenarios, key=lambda s: s.created_at, reverse=True)


# Global sandbox instance
_sandbox: ComplianceSandbox | None = None


def get_compliance_sandbox() -> ComplianceSandbox:
    """Get or create the global compliance sandbox."""
    global _sandbox
    if _sandbox is None:
        _sandbox = ComplianceSandbox()
    return _sandbox
