"""SBOM Compliance Analyzer - Maps vulnerabilities to regulatory requirements."""

import time
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

import structlog

from app.services.sbom.models import (
    ComplianceImpact,
    ComponentComplianceIssue,
    LicenseRisk,
    LICENSE_COMPLIANCE_INFO,
    SBOMComplianceReport,
    SBOMDocument,
    VulnerabilityComplianceMapping,
    VulnerabilitySeverity,
    VULNERABILITY_REGULATION_MAPPINGS,
)


logger = structlog.get_logger()


class SBOMComplianceAnalyzer:
    """Analyzes SBOM for compliance issues and maps to regulations."""

    def __init__(self):
        self._reports: dict[UUID, SBOMComplianceReport] = {}

    async def analyze_compliance(
        self,
        sbom: SBOMDocument,
        regulations: list[str] | None = None,
    ) -> SBOMComplianceReport:
        """Analyze SBOM for compliance issues.
        
        Maps vulnerabilities and license issues to specific regulatory
        requirements, providing actionable compliance guidance.
        """
        start_time = time.perf_counter()
        
        # Default regulations
        if not regulations:
            regulations = ["PCI-DSS", "HIPAA", "SOC 2", "GDPR", "NIST CSF"]
        
        report = SBOMComplianceReport(
            sbom_id=sbom.id,
            organization_id=sbom.organization_id,
            regulation_compliance={reg: 100.0 for reg in regulations},
            issues_by_regulation={reg: [] for reg in regulations},
        )
        
        # Analyze vulnerabilities
        await self._analyze_vulnerabilities(sbom, report, regulations)
        
        # Analyze licenses
        await self._analyze_licenses(sbom, report, regulations)
        
        # Analyze supply chain
        await self._analyze_supply_chain(sbom, report, regulations)
        
        # Calculate scores
        self._calculate_scores(report, regulations)
        
        # Generate recommendations
        report.recommendations = self._generate_recommendations(report)
        
        # Generate action items
        self._generate_action_items(report)
        
        # Store
        self._reports[report.id] = report
        
        processing_time = (time.perf_counter() - start_time) * 1000
        
        logger.info(
            "SBOM compliance analysis complete",
            report_id=str(report.id),
            sbom_id=str(sbom.id),
            overall_score=report.overall_compliance_score,
            processing_time_ms=processing_time,
        )
        
        return report

    async def _analyze_vulnerabilities(
        self,
        sbom: SBOMDocument,
        report: SBOMComplianceReport,
        regulations: list[str],
    ) -> None:
        """Map vulnerabilities to compliance requirements."""
        for component in sbom.components:
            for vuln in component.vulnerabilities:
                # Map to each relevant regulation
                for regulation in regulations:
                    if regulation not in VULNERABILITY_REGULATION_MAPPINGS:
                        continue
                    
                    reg_mappings = VULNERABILITY_REGULATION_MAPPINGS[regulation]
                    severity_key = vuln.severity.value
                    
                    if severity_key not in reg_mappings:
                        continue
                    
                    mapping_info = reg_mappings[severity_key]
                    
                    # Create compliance mapping
                    mapping = VulnerabilityComplianceMapping(
                        vulnerability_id=vuln.id,
                        regulation=regulation,
                        requirement=mapping_info["requirement"],
                        article=mapping_info.get("article"),
                        impact=self._severity_to_impact(vuln.severity),
                        rationale=mapping_info["rationale"],
                        remediation_deadline_days=mapping_info.get("deadline_days"),
                        evidence_required=mapping_info.get("evidence", []),
                    )
                    
                    report.vulnerability_mappings.append(mapping)
                    vuln.compliance_mappings.append(mapping)
                    
                    # Create compliance issue
                    issue = ComponentComplianceIssue(
                        issue_type="vulnerability",
                        regulation=regulation,
                        requirement=mapping_info["requirement"],
                        article=mapping_info.get("article"),
                        impact=self._severity_to_impact(vuln.severity),
                        description=f"{vuln.id}: {vuln.description} in {component.name}@{component.version}",
                        remediation=f"Upgrade {component.name} to {vuln.fixed_in_version}" if vuln.fixed_in_version else "Review and patch vulnerability",
                        deadline=datetime.utcnow() + timedelta(days=mapping_info.get("deadline_days", 90)),
                    )
                    
                    component.compliance_issues.append(issue)
                    report.issues_by_regulation[regulation].append(issue)
                    
                    # Track risks
                    risk_msg = f"{vuln.id} in {component.name} violates {regulation} {mapping_info['requirement']}"
                    if vuln.severity == VulnerabilitySeverity.CRITICAL:
                        report.critical_risks.append(risk_msg)
                    elif vuln.severity == VulnerabilitySeverity.HIGH:
                        report.high_risks.append(risk_msg)

    async def _analyze_licenses(
        self,
        sbom: SBOMDocument,
        report: SBOMComplianceReport,
        regulations: list[str],
    ) -> None:
        """Analyze license compliance."""
        for component in sbom.components:
            license_name = component.license or "UNKNOWN"
            license_info = LICENSE_COMPLIANCE_INFO.get(license_name, {"risk": LicenseRisk.UNKNOWN})
            
            # High-risk licenses
            if component.license_risk in (LicenseRisk.HIGH, LicenseRisk.CRITICAL):
                for regulation in regulations:
                    issue = ComponentComplianceIssue(
                        issue_type="license",
                        regulation=regulation,
                        requirement="License compliance",
                        impact=ComplianceImpact.MEDIUM if component.license_risk == LicenseRisk.HIGH else ComplianceImpact.HIGH,
                        description=f"Component {component.name} uses {license_name} license which may have copyleft restrictions",
                        remediation="Review license compatibility with proprietary software distribution",
                    )
                    component.compliance_issues.append(issue)
                    report.issues_by_regulation[regulation].append(issue)
            
            # Unknown licenses
            elif component.license_risk == LicenseRisk.UNKNOWN:
                for regulation in regulations:
                    issue = ComponentComplianceIssue(
                        issue_type="license",
                        regulation=regulation,
                        requirement="License identification",
                        impact=ComplianceImpact.MEDIUM,
                        description=f"License for {component.name}@{component.version} is unknown",
                        remediation="Identify and document license for this component",
                    )
                    component.compliance_issues.append(issue)
                    report.issues_by_regulation[regulation].append(issue)

    async def _analyze_supply_chain(
        self,
        sbom: SBOMDocument,
        report: SBOMComplianceReport,
        regulations: list[str],
    ) -> None:
        """Analyze supply chain compliance."""
        # Check for missing hashes
        components_without_hash = [c for c in sbom.components if not c.hash_sha256]
        
        if len(components_without_hash) > sbom.total_components * 0.5:
            for regulation in regulations:
                if regulation in ["NIST CSF", "SOC 2"]:
                    issue = ComponentComplianceIssue(
                        issue_type="supply_chain",
                        regulation=regulation,
                        requirement="Component integrity verification",
                        impact=ComplianceImpact.MEDIUM,
                        description=f"{len(components_without_hash)} components lack integrity hashes",
                        remediation="Generate or obtain cryptographic hashes for all components",
                    )
                    report.issues_by_regulation[regulation].append(issue)
        
        # Check for missing supplier information
        components_without_supplier = [c for c in sbom.components if not c.supplier and not c.author]
        
        if len(components_without_supplier) > sbom.total_components * 0.3:
            for regulation in regulations:
                issue = ComponentComplianceIssue(
                    issue_type="supply_chain",
                    regulation=regulation,
                    requirement="Supplier identification",
                    impact=ComplianceImpact.LOW,
                    description=f"{len(components_without_supplier)} components lack supplier/author information",
                    remediation="Document supplier information for third-party components",
                )
                report.issues_by_regulation[regulation].append(issue)

    def _severity_to_impact(self, severity: VulnerabilitySeverity) -> ComplianceImpact:
        """Convert vulnerability severity to compliance impact."""
        mapping = {
            VulnerabilitySeverity.CRITICAL: ComplianceImpact.CRITICAL,
            VulnerabilitySeverity.HIGH: ComplianceImpact.HIGH,
            VulnerabilitySeverity.MEDIUM: ComplianceImpact.MEDIUM,
            VulnerabilitySeverity.LOW: ComplianceImpact.LOW,
            VulnerabilitySeverity.NONE: ComplianceImpact.INFORMATIONAL,
        }
        return mapping.get(severity, ComplianceImpact.MEDIUM)

    def _calculate_scores(
        self,
        report: SBOMComplianceReport,
        regulations: list[str],
    ) -> None:
        """Calculate compliance scores."""
        # Calculate per-regulation scores
        for regulation in regulations:
            issues = report.issues_by_regulation.get(regulation, [])
            
            penalty = 0
            for issue in issues:
                if issue.impact == ComplianceImpact.CRITICAL:
                    penalty += 25
                elif issue.impact == ComplianceImpact.HIGH:
                    penalty += 15
                elif issue.impact == ComplianceImpact.MEDIUM:
                    penalty += 8
                elif issue.impact == ComplianceImpact.LOW:
                    penalty += 3
            
            report.regulation_compliance[regulation] = max(0, 100 - penalty)
        
        # Calculate overall scores
        if regulations:
            report.overall_compliance_score = sum(report.regulation_compliance.values()) / len(regulations)
        else:
            report.overall_compliance_score = 100.0
        
        # Calculate component scores
        vuln_penalty = len(report.critical_risks) * 20 + len(report.high_risks) * 10
        report.vulnerability_score = max(0, 100 - vuln_penalty)
        
        license_issues = sum(
            1 for issues in report.issues_by_regulation.values()
            for issue in issues if issue.issue_type == "license"
        )
        report.license_score = max(0, 100 - license_issues * 5)
        
        supply_chain_issues = sum(
            1 for issues in report.issues_by_regulation.values()
            for issue in issues if issue.issue_type == "supply_chain"
        )
        report.supply_chain_score = max(0, 100 - supply_chain_issues * 10)

    def _generate_recommendations(
        self,
        report: SBOMComplianceReport,
    ) -> list[str]:
        """Generate compliance recommendations."""
        recommendations = []
        
        if report.critical_risks:
            recommendations.append(
                f"URGENT: Address {len(report.critical_risks)} critical vulnerabilities within 30 days to maintain compliance"
            )
        
        if report.high_risks:
            recommendations.append(
                f"Address {len(report.high_risks)} high-severity vulnerabilities within 90 days"
            )
        
        if report.license_score < 80:
            recommendations.append(
                "Review and document licenses for all third-party components to ensure compatibility"
            )
        
        if report.supply_chain_score < 80:
            recommendations.append(
                "Implement component integrity verification using cryptographic hashes"
            )
        
        if report.overall_compliance_score < 70:
            recommendations.append(
                "Consider a comprehensive dependency audit and upgrade strategy"
            )
        
        # Regulation-specific recommendations
        for regulation, score in report.regulation_compliance.items():
            if score < 80:
                recommendations.append(
                    f"Focus on improving {regulation} compliance (current score: {score:.0f}%)"
                )
        
        if not recommendations:
            recommendations.append("Software supply chain compliance is in good standing")
        
        return recommendations

    def _generate_action_items(
        self,
        report: SBOMComplianceReport,
    ) -> None:
        """Generate prioritized action items."""
        # Immediate (critical issues)
        for risk in report.critical_risks[:5]:
            report.immediate_actions.append(f"Remediate: {risk}")
        
        # Short-term (30 days)
        for risk in report.high_risks[:5]:
            report.short_term_actions.append(f"Address: {risk}")
        
        # Long-term (90 days)
        if report.license_score < 90:
            report.long_term_actions.append("Complete license audit for all dependencies")
        if report.supply_chain_score < 90:
            report.long_term_actions.append("Implement SBOM automation in CI/CD pipeline")
        
        report.long_term_actions.append("Establish continuous vulnerability monitoring")

    async def get_report(self, report_id: UUID) -> SBOMComplianceReport | None:
        """Retrieve a compliance report."""
        return self._reports.get(report_id)

    async def get_vulnerability_mapping(
        self,
        vulnerability_id: str,
        regulation: str | None = None,
    ) -> list[VulnerabilityComplianceMapping]:
        """Get compliance mappings for a specific vulnerability."""
        mappings = []
        
        for report in self._reports.values():
            for mapping in report.vulnerability_mappings:
                if mapping.vulnerability_id == vulnerability_id:
                    if regulation is None or mapping.regulation == regulation:
                        mappings.append(mapping)
        
        return mappings


# Global instance
_analyzer: SBOMComplianceAnalyzer | None = None


def get_sbom_analyzer() -> SBOMComplianceAnalyzer:
    """Get or create SBOM compliance analyzer."""
    global _analyzer
    if _analyzer is None:
        _analyzer = SBOMComplianceAnalyzer()
    return _analyzer
