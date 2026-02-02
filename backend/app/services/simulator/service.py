"""Regulatory scenario simulator service."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.copilot import CopilotClient, CopilotMessage
from app.models.codebase import CodebaseMapping, ComplianceStatus, Repository
from app.models.requirement import Requirement
from app.services.scoring import ComplianceGrade
from app.services.simulator.models import (
    ArchitectureChangeScenario,
    CodeChangeScenario,
    ComplianceDelta,
    ExpansionScenario,
    ImpactPrediction,
    RiskCategory,
    Scenario,
    ScenarioType,
    SimulationResult,
    VendorChangeScenario,
)

logger = structlog.get_logger()


class ScenarioSimulatorService:
    """Service for simulating compliance impact of proposed changes."""

    def __init__(
        self,
        db: AsyncSession,
        copilot: CopilotClient | None = None,
    ):
        self.db = db
        self.copilot = copilot

    async def simulate(self, scenario: Scenario) -> SimulationResult:
        """
        Run simulation for a scenario and predict compliance impact.
        """
        logger.info(
            "Running scenario simulation",
            scenario_id=str(scenario.id),
            scenario_type=scenario.scenario_type.value,
        )

        # Get current compliance baseline if repository specified
        baseline = {}
        if scenario.repository_id:
            baseline = await self._get_compliance_baseline(scenario.repository_id)

        # Analyze scenario based on type
        if scenario.scenario_type == ScenarioType.CODE_CHANGE:
            return await self._simulate_code_change(scenario, baseline)
        elif scenario.scenario_type == ScenarioType.ARCHITECTURE_CHANGE:
            return await self._simulate_architecture_change(scenario, baseline)
        elif scenario.scenario_type == ScenarioType.VENDOR_CHANGE:
            return await self._simulate_vendor_change(scenario, baseline)
        elif scenario.scenario_type == ScenarioType.EXPANSION:
            return await self._simulate_expansion(scenario, baseline)
        else:
            return await self._simulate_generic(scenario, baseline)

    async def _get_compliance_baseline(
        self,
        repository_id: UUID,
    ) -> dict[str, Any]:
        """Get current compliance status as baseline for comparison."""
        mappings_result = await self.db.execute(
            select(CodebaseMapping)
            .options(
                selectinload(CodebaseMapping.requirement)
                .selectinload(Requirement.regulation)
            )
            .where(CodebaseMapping.repository_id == repository_id)
        )
        mappings = list(mappings_result.scalars().all())

        # Calculate per-framework scores
        framework_stats: dict[str, dict] = {}
        for mapping in mappings:
            if not mapping.requirement or not mapping.requirement.regulation:
                continue
            
            fw = mapping.requirement.regulation.framework.value
            if fw not in framework_stats:
                framework_stats[fw] = {"total": 0, "compliant": 0, "gaps": []}
            
            framework_stats[fw]["total"] += 1
            if mapping.compliance_status == ComplianceStatus.COMPLIANT:
                framework_stats[fw]["compliant"] += 1
            else:
                framework_stats[fw]["gaps"].append({
                    "requirement_id": str(mapping.requirement_id),
                    "title": mapping.requirement.title,
                })

        return {
            fw: {
                "score": (stats["compliant"] / stats["total"] * 100) if stats["total"] > 0 else 100,
                "grade": ComplianceGrade.from_score(
                    (stats["compliant"] / stats["total"] * 100) if stats["total"] > 0 else 100
                ).value,
                "gaps": stats["gaps"],
            }
            for fw, stats in framework_stats.items()
        }

    async def _simulate_code_change(
        self,
        scenario: Scenario,
        baseline: dict,
    ) -> SimulationResult:
        """Simulate compliance impact of proposed code changes."""
        code_change = scenario.code_change
        if not code_change:
            return self._empty_result(scenario)

        impact_predictions = []
        compliance_deltas = []
        blocking_issues = []
        warnings = []

        # Analyze proposed code for compliance patterns
        analysis = await self._analyze_code_compliance(
            code_change.proposed_changes,
            code_change.language,
            scenario.target_frameworks or list(baseline.keys()),
        )

        # Build impact predictions
        for finding in analysis.get("findings", []):
            severity = finding.get("severity", "medium")
            category = self._map_to_risk_category(finding.get("category", ""))
            
            prediction = ImpactPrediction(
                category=category,
                severity=severity,
                description=finding.get("description", ""),
                affected_requirements=finding.get("requirements", []),
                mitigation_suggestions=finding.get("mitigations", []),
                confidence=finding.get("confidence", 0.7),
            )
            impact_predictions.append(prediction)

            if severity == "critical":
                blocking_issues.append({
                    "type": "compliance_violation",
                    "description": finding.get("description"),
                    "framework": finding.get("framework"),
                })
            elif severity == "high":
                warnings.append({
                    "type": "compliance_risk",
                    "description": finding.get("description"),
                    "framework": finding.get("framework"),
                })

        # Calculate compliance deltas
        for fw, base in baseline.items():
            # Estimate score impact based on findings
            fw_findings = [f for f in analysis.get("findings", []) if f.get("framework") == fw]
            score_impact = sum(
                -10 if f.get("severity") == "critical" else
                -5 if f.get("severity") == "high" else
                -2 if f.get("severity") == "medium" else 0
                for f in fw_findings
            )
            
            projected_score = max(0, min(100, base["score"] + score_impact))
            projected_grade = ComplianceGrade.from_score(projected_score).value
            
            if abs(score_impact) > 0:
                compliance_deltas.append(ComplianceDelta(
                    framework=fw,
                    current_score=base["score"],
                    projected_score=projected_score,
                    score_change=score_impact,
                    current_grade=base["grade"],
                    projected_grade=projected_grade,
                    grade_changed=base["grade"] != projected_grade,
                    new_gaps=[{"description": f.get("description")} for f in fw_findings],
                    resolved_gaps=[],
                    risk_categories_affected=[
                        self._map_to_risk_category(f.get("category", ""))
                        for f in fw_findings
                    ],
                ))

        # Determine overall recommendation
        overall_risk = "low"
        recommendation = "proceed"
        
        if blocking_issues:
            overall_risk = "critical"
            recommendation = "not_recommended"
        elif len(warnings) > 2:
            overall_risk = "high"
            recommendation = "review_required"
        elif warnings:
            overall_risk = "medium"
            recommendation = "proceed_with_caution"

        return SimulationResult(
            scenario_id=scenario.id,
            scenario_name=scenario.name,
            scenario_type=scenario.scenario_type,
            overall_risk_level=overall_risk,
            recommendation=recommendation,
            summary=self._generate_summary(scenario, impact_predictions, blocking_issues),
            compliance_deltas=compliance_deltas,
            impact_predictions=impact_predictions,
            blocking_issues=blocking_issues,
            warnings=warnings,
            required_actions=[
                f"Address {len(blocking_issues)} blocking compliance issues"
            ] if blocking_issues else [],
            recommended_actions=[
                f"Review {len(warnings)} compliance warnings before proceeding"
            ] if warnings else [],
            estimated_remediation_hours=len(blocking_issues) * 8 + len(warnings) * 2,
            estimated_timeline_days=max(1, len(blocking_issues) * 2 + len(warnings)),
            simulated_at=datetime.now(UTC),
            confidence=0.8,
        )

    async def _simulate_vendor_change(
        self,
        scenario: Scenario,
        baseline: dict,
    ) -> SimulationResult:
        """Simulate compliance impact of vendor/third-party changes."""
        vendor_change = scenario.vendor_change
        if not vendor_change:
            return self._empty_result(scenario)

        impact_predictions = []
        warnings = []
        blocking_issues = []

        # Check for cross-border data transfer issues
        if vendor_change.jurisdictions:
            for jurisdiction in vendor_change.jurisdictions:
                if jurisdiction not in ["US", "EU", "UK"]:  # Simplified check
                    impact_predictions.append(ImpactPrediction(
                        category=RiskCategory.CROSS_BORDER,
                        severity="high",
                        description=f"Data transfer to {jurisdiction} may require additional safeguards",
                        affected_requirements=["GDPR-Chapter-V"],
                        mitigation_suggestions=[
                            "Implement Standard Contractual Clauses (SCCs)",
                            "Conduct Transfer Impact Assessment",
                        ],
                        confidence=0.85,
                    ))
                    warnings.append({
                        "type": "cross_border_transfer",
                        "description": f"Data transfer to {jurisdiction} requires GDPR safeguards",
                    })

        # Check vendor certifications
        required_certs = {"SOC2", "ISO27001", "HIPAA"}  # Example requirements
        missing_certs = required_certs - set(vendor_change.certifications or [])
        
        if missing_certs:
            impact_predictions.append(ImpactPrediction(
                category=RiskCategory.VENDOR_RISK,
                severity="medium",
                description=f"Vendor missing certifications: {', '.join(missing_certs)}",
                affected_requirements=["SOC2-CC9.1", "ISO27001-A.15"],
                mitigation_suggestions=[
                    "Request vendor security questionnaire",
                    "Conduct vendor security assessment",
                ],
                confidence=0.9,
            ))

        # Check data sharing scope
        sensitive_data = ["PII", "PHI", "financial", "biometric"]
        shared_sensitive = [d for d in vendor_change.data_shared if d.lower() in sensitive_data]
        
        if shared_sensitive:
            impact_predictions.append(ImpactPrediction(
                category=RiskCategory.DATA_PRIVACY,
                severity="high",
                description=f"Sharing sensitive data types with vendor: {', '.join(shared_sensitive)}",
                affected_requirements=["GDPR-Art-28", "HIPAA-164.308"],
                mitigation_suggestions=[
                    "Execute Data Processing Agreement (DPA)",
                    "Implement data minimization",
                    "Ensure encryption in transit and at rest",
                ],
                confidence=0.9,
            ))

        # Determine recommendation
        overall_risk = "low"
        recommendation = "proceed"
        
        if any(p.severity == "critical" for p in impact_predictions):
            overall_risk = "critical"
            recommendation = "not_recommended"
        elif any(p.severity == "high" for p in impact_predictions):
            overall_risk = "high"
            recommendation = "review_required"
        elif impact_predictions:
            overall_risk = "medium"
            recommendation = "proceed_with_caution"

        return SimulationResult(
            scenario_id=scenario.id,
            scenario_name=scenario.name,
            scenario_type=scenario.scenario_type,
            overall_risk_level=overall_risk,
            recommendation=recommendation,
            summary=f"Vendor integration with {vendor_change.vendor_name} has {overall_risk} compliance risk",
            compliance_deltas=[],  # Vendor changes don't directly affect code compliance
            impact_predictions=impact_predictions,
            blocking_issues=blocking_issues,
            warnings=warnings,
            required_actions=[
                "Execute Data Processing Agreement (DPA)" if shared_sensitive else None,
                f"Obtain missing certifications: {', '.join(missing_certs)}" if missing_certs else None,
            ],
            recommended_actions=[
                "Conduct vendor security assessment",
                "Review vendor's privacy policy",
                "Document data flows to vendor",
            ],
            estimated_remediation_hours=16 if shared_sensitive else 8,
            estimated_timeline_days=14,
            simulated_at=datetime.now(UTC),
            confidence=0.85,
        )

    async def _simulate_expansion(
        self,
        scenario: Scenario,
        baseline: dict,
    ) -> SimulationResult:
        """Simulate compliance impact of geographic expansion."""
        expansion = scenario.expansion
        if not expansion:
            return self._empty_result(scenario)

        impact_predictions = []
        required_actions = []

        # Map regions to regulations
        region_regulations = {
            "EU": ["GDPR", "NIS2", "EU_AI_ACT"],
            "UK": ["UK_GDPR", "DPA_2018"],
            "US-CA": ["CCPA", "CPRA"],
            "US": ["HIPAA", "SOX", "FTC_ACT"],
            "China": ["PIPL", "CSL", "DSL"],
            "India": ["DPDP"],
            "Singapore": ["PDPA"],
            "Brazil": ["LGPD"],
            "Japan": ["APPI"],
        }

        new_frameworks = set()
        for region in expansion.target_regions:
            regulations = region_regulations.get(region, [])
            new_frameworks.update(regulations)
            
            if regulations:
                impact_predictions.append(ImpactPrediction(
                    category=RiskCategory.DATA_PRIVACY,
                    severity="high",
                    description=f"Expansion to {region} requires compliance with: {', '.join(regulations)}",
                    affected_requirements=[f"{r}-General" for r in regulations],
                    mitigation_suggestions=[
                        f"Conduct {r} gap assessment" for r in regulations
                    ],
                    confidence=0.95,
                ))
                required_actions.append(f"Achieve {', '.join(regulations)} compliance for {region}")

        # Check for data localization requirements
        localization_regions = ["China", "Russia", "India"]
        needs_localization = [r for r in expansion.target_regions if r in localization_regions]
        
        if needs_localization:
            impact_predictions.append(ImpactPrediction(
                category=RiskCategory.CROSS_BORDER,
                severity="critical",
                description=f"Data localization required in: {', '.join(needs_localization)}",
                affected_requirements=["Data-Localization"],
                mitigation_suggestions=[
                    "Deploy local data infrastructure",
                    "Implement data residency controls",
                ],
                confidence=0.95,
            ))

        overall_risk = "critical" if needs_localization else "high" if new_frameworks else "medium"
        recommendation = "review_required" if new_frameworks else "proceed_with_caution"

        return SimulationResult(
            scenario_id=scenario.id,
            scenario_name=scenario.name,
            scenario_type=scenario.scenario_type,
            overall_risk_level=overall_risk,
            recommendation=recommendation,
            summary=f"Expansion to {', '.join(expansion.target_regions)} requires {len(new_frameworks)} new regulatory frameworks",
            compliance_deltas=[],
            impact_predictions=impact_predictions,
            blocking_issues=[],
            warnings=[],
            required_actions=required_actions,
            recommended_actions=[
                "Engage local legal counsel",
                "Update privacy policy for new regions",
                "Implement region-specific consent flows",
            ],
            estimated_remediation_hours=len(new_frameworks) * 40,
            estimated_timeline_days=len(new_frameworks) * 30,
            simulated_at=datetime.now(UTC),
            confidence=0.9,
        )

    async def _simulate_architecture_change(
        self,
        scenario: Scenario,
        baseline: dict,
    ) -> SimulationResult:
        """Simulate compliance impact of architecture changes."""
        arch_change = scenario.architecture_change
        if not arch_change:
            return self._empty_result(scenario)

        impact_predictions = []
        
        # Analyze new data flows
        for flow in arch_change.new_data_flows or []:
            if flow.get("crosses_boundary"):
                impact_predictions.append(ImpactPrediction(
                    category=RiskCategory.CROSS_BORDER,
                    severity="medium",
                    description=f"New data flow crosses service boundary: {flow.get('description', '')}",
                    affected_requirements=["Data-Flow-Documentation"],
                    mitigation_suggestions=["Document data flow", "Update DPIA"],
                    confidence=0.8,
                ))

        return SimulationResult(
            scenario_id=scenario.id,
            scenario_name=scenario.name,
            scenario_type=scenario.scenario_type,
            overall_risk_level="medium",
            recommendation="proceed_with_caution",
            summary=f"Architecture change '{arch_change.component_name}' requires compliance review",
            compliance_deltas=[],
            impact_predictions=impact_predictions,
            blocking_issues=[],
            warnings=[],
            required_actions=["Update architecture documentation"],
            recommended_actions=["Update Data Protection Impact Assessment"],
            estimated_remediation_hours=8,
            estimated_timeline_days=5,
            simulated_at=datetime.now(UTC),
            confidence=0.75,
        )

    async def _simulate_generic(
        self,
        scenario: Scenario,
        baseline: dict,
    ) -> SimulationResult:
        """Generic simulation fallback."""
        return self._empty_result(scenario)

    async def _analyze_code_compliance(
        self,
        code: str,
        language: str,
        frameworks: list[str],
    ) -> dict[str, Any]:
        """Use AI to analyze code for compliance issues."""
        if not self.copilot:
            # Fallback to pattern-based analysis
            return self._pattern_based_analysis(code, language, frameworks)

        prompt = f"""Analyze this {language} code for compliance issues with {', '.join(frameworks)}.

Code:
```{language}
{code[:4000]}
```

Return JSON with:
- findings: array of {{framework, category, severity, description, requirements, mitigations, confidence}}

Focus on:
- Data handling and privacy
- Security practices
- Logging of sensitive data
- Access control
- Encryption usage

Return only valid JSON."""

        try:
            async with self.copilot as client:
                response = await client.chat(
                    messages=[CopilotMessage(role="user", content=prompt)],
                    system_message="You are a compliance analyst reviewing code for regulatory issues.",
                    temperature=0.3,
                    max_tokens=2048,
                )
            
            import json
            return json.loads(response.content.strip().strip("```json").strip("```"))
        except Exception as e:
            logger.warning("AI code analysis failed", error=str(e))
            return self._pattern_based_analysis(code, language, frameworks)

    def _pattern_based_analysis(
        self,
        code: str,
        language: str,
        frameworks: list[str],
    ) -> dict[str, Any]:
        """Fallback pattern-based compliance analysis."""
        findings = []
        code_lower = code.lower()

        # Check for common compliance patterns
        if "password" in code_lower and ("log" in code_lower or "print" in code_lower):
            findings.append({
                "framework": "SOC2",
                "category": "data_security",
                "severity": "critical",
                "description": "Potential logging of password/credentials",
                "requirements": ["SOC2-CC6.1"],
                "mitigations": ["Remove sensitive data from logs"],
                "confidence": 0.8,
            })

        if "personal" in code_lower and "encrypt" not in code_lower:
            findings.append({
                "framework": "GDPR",
                "category": "data_privacy",
                "severity": "high",
                "description": "Personal data handling without apparent encryption",
                "requirements": ["GDPR-Art-32"],
                "mitigations": ["Implement encryption for personal data"],
                "confidence": 0.6,
            })

        return {"findings": findings}

    def _map_to_risk_category(self, category: str) -> RiskCategory:
        """Map string category to RiskCategory enum."""
        mapping = {
            "data_privacy": RiskCategory.DATA_PRIVACY,
            "data_security": RiskCategory.DATA_SECURITY,
            "access_control": RiskCategory.ACCESS_CONTROL,
            "audit_logging": RiskCategory.AUDIT_LOGGING,
            "data_retention": RiskCategory.DATA_RETENTION,
            "consent": RiskCategory.CONSENT_MANAGEMENT,
            "cross_border": RiskCategory.CROSS_BORDER,
            "vendor_risk": RiskCategory.VENDOR_RISK,
            "ai_compliance": RiskCategory.AI_COMPLIANCE,
        }
        return mapping.get(category.lower(), RiskCategory.DATA_PRIVACY)

    def _generate_summary(
        self,
        scenario: Scenario,
        predictions: list[ImpactPrediction],
        blocking: list[dict],
    ) -> str:
        """Generate human-readable summary."""
        if blocking:
            return f"Scenario '{scenario.name}' has {len(blocking)} blocking compliance issues that must be resolved"
        elif predictions:
            high_count = sum(1 for p in predictions if p.severity in ["critical", "high"])
            return f"Scenario '{scenario.name}' has {high_count} high-priority compliance considerations"
        return f"Scenario '{scenario.name}' appears to have minimal compliance impact"

    def _empty_result(self, scenario: Scenario) -> SimulationResult:
        """Return empty result for invalid scenarios."""
        return SimulationResult(
            scenario_id=scenario.id,
            scenario_name=scenario.name,
            scenario_type=scenario.scenario_type,
            overall_risk_level="low",
            recommendation="proceed",
            summary="No compliance impact detected",
            simulated_at=datetime.now(UTC),
            confidence=0.5,
        )
