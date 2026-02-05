"""Cross-Border Data Flow Analyzer for compliance assessment and TIA generation."""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import structlog

from app.services.data_flow.models import (
    DataClassification,
    JurisdictionType,
    TransferMechanism,
    ComplianceStatus,
    RiskLevel,
    DataFlow,
    DataFlowMap,
    JurisdictionConflict,
    TransferImpactAssessment,
    EEA_COUNTRIES,
    EU_ADEQUATE_COUNTRIES,
    DATA_LOCALIZATION_COUNTRIES,
    HIGH_GOVERNMENT_ACCESS_RISK,
    JURISDICTION_REGULATIONS,
    SCC_MODULES,
)

logger = structlog.get_logger()


# Legal framework descriptions
LEGAL_FRAMEWORKS: dict[str, str] = {
    "US": "US federal and state privacy laws (CCPA/CPRA, state laws, sectoral regulations)",
    "EU": "General Data Protection Regulation (GDPR) and member state implementations",
    "GB": "UK GDPR and Data Protection Act 2018",
    "CH": "Swiss Federal Act on Data Protection (FADP)",
    "JP": "Act on Protection of Personal Information (APPI)",
    "KR": "Personal Information Protection Act (PIPA)",
    "AU": "Privacy Act 1988 and Australian Privacy Principles",
    "SG": "Personal Data Protection Act (PDPA)",
    "IN": "Digital Personal Data Protection Act 2023",
    "BR": "Lei Geral de Proteção de Dados (LGPD)",
    "CN": "Personal Information Protection Law (PIPL), Cybersecurity Law, Data Security Law",
    "CA": "Personal Information Protection and Electronic Documents Act (PIPEDA)",
}

# Data Protection Authorities
DPA_CONTACTS: dict[str, str] = {
    "US": "FTC, State AGs, Sectoral regulators",
    "EU": "National DPAs (lead authority based on main establishment)",
    "GB": "Information Commissioner's Office (ICO)",
    "DE": "Bundesbeauftragter für den Datenschutz (BfDI), State DPAs",
    "FR": "Commission Nationale de l'Informatique et des Libertés (CNIL)",
    "IE": "Data Protection Commission (DPC)",
    "NL": "Autoriteit Persoonsgegevens (AP)",
    "CH": "Federal Data Protection and Information Commissioner (FDPIC)",
    "JP": "Personal Information Protection Commission (PPC)",
    "KR": "Personal Information Protection Commission (PIPC)",
    "AU": "Office of the Australian Information Commissioner (OAIC)",
    "SG": "Personal Data Protection Commission (PDPC)",
    "BR": "Autoridade Nacional de Proteção de Dados (ANPD)",
    "CN": "Cyberspace Administration of China (CAC)",
}

# Supplementary measures by risk type
SUPPLEMENTARY_MEASURES: dict[str, list[str]] = {
    "encryption": [
        "Implement end-to-end encryption with keys controlled by data exporter",
        "Use client-side encryption before transfer",
        "Implement encryption at rest and in transit (TLS 1.3)",
        "Ensure encryption keys are stored in originating jurisdiction",
    ],
    "pseudonymization": [
        "Pseudonymize personal data before transfer",
        "Keep mapping table in originating jurisdiction",
        "Use tokenization for sensitive identifiers",
    ],
    "access_control": [
        "Implement strict access controls and need-to-know principles",
        "Enable comprehensive audit logging of all access",
        "Implement multi-factor authentication for data access",
        "Regular access reviews and certifications",
    ],
    "contractual": [
        "Include enhanced audit rights in SCCs",
        "Add obligation to notify of government access requests",
        "Include commitment to challenge disproportionate requests",
        "Require transparency reports from data importer",
    ],
    "organizational": [
        "Conduct regular privacy impact assessments",
        "Appoint data protection officer",
        "Implement data protection by design and default",
        "Regular staff training on data protection",
    ],
}


class CrossBorderAnalyzer:
    """Analyzes cross-border data flows for compliance."""
    
    def __init__(self) -> None:
        self._assessments: dict[UUID, TransferImpactAssessment] = {}
        self._conflicts: dict[UUID, JurisdictionConflict] = {}
    
    async def analyze_flow_map(
        self,
        flow_map: DataFlowMap,
    ) -> dict[str, Any]:
        """Analyze an entire flow map for cross-border issues."""
        conflicts = []
        assessments = []
        recommendations = []
        
        for flow in flow_map.flows:
            if flow.source_country != flow.destination_country:
                # Check for conflicts
                flow_conflicts = await self._detect_conflicts(flow)
                conflicts.extend(flow_conflicts)
                flow_map.conflicts.extend(flow_conflicts)
                
                # Generate TIA if needed
                if self._needs_tia(flow):
                    tia = await self.generate_tia(flow)
                    assessments.append(tia)
                    flow_map.assessments.append(tia)
                
                # Generate recommendations
                flow_recs = self._generate_recommendations(flow)
                recommendations.extend(flow_recs)
        
        return {
            "total_flows": len(flow_map.flows),
            "cross_border_flows": len([f for f in flow_map.flows if f.source_country != f.destination_country]),
            "conflicts_detected": len(conflicts),
            "tias_required": len(assessments),
            "critical_issues": len([c for c in conflicts if c.severity == RiskLevel.CRITICAL]),
            "recommendations": list(set(recommendations))[:10],  # Dedupe and limit
            "compliance_summary": self._generate_compliance_summary(flow_map),
        }
    
    async def _detect_conflicts(self, flow: DataFlow) -> list[JurisdictionConflict]:
        """Detect jurisdiction conflicts for a flow."""
        conflicts = []
        
        # Data localization conflicts
        if flow.destination_country in DATA_LOCALIZATION_COUNTRIES:
            conflict = JurisdictionConflict(
                flow_id=flow.id,
                source_jurisdiction=flow.source_country,
                destination_jurisdiction=flow.destination_country,
                source_regulation="GDPR" if flow.source_country in EEA_COUNTRIES else "General",
                destination_regulation=f"{flow.destination_country} Data Localization",
                conflict_type="data_localization",
                description=DATA_LOCALIZATION_COUNTRIES[flow.destination_country],
                severity=RiskLevel.HIGH,
                resolution_options=[
                    "Store data locally in destination jurisdiction",
                    "Use local processing with aggregated/anonymized transfers",
                    "Seek regulatory exemption if available",
                ],
                recommended_resolution="Consult local counsel for compliance options",
            )
            conflicts.append(conflict)
            self._conflicts[conflict.id] = conflict
        
        # Government access conflicts
        if (flow.source_country in EEA_COUNTRIES and 
            flow.destination_country in HIGH_GOVERNMENT_ACCESS_RISK):
            conflict = JurisdictionConflict(
                flow_id=flow.id,
                source_jurisdiction=flow.source_country,
                destination_jurisdiction=flow.destination_country,
                source_regulation="GDPR",
                destination_regulation="Government surveillance laws",
                conflict_type="government_access",
                description=f"Transfers to {flow.destination_country} may be subject to government access that conflicts with GDPR protections (Schrems II considerations)",
                severity=RiskLevel.HIGH,
                resolution_options=[
                    "Implement supplementary technical measures (encryption with EU-held keys)",
                    "Minimize data transferred (pseudonymization/anonymization)",
                    "Seek explicit consent for transfer",
                    "Consider alternative data flows avoiding high-risk jurisdictions",
                ],
                recommended_resolution="Implement technical supplementary measures and complete TIA",
            )
            conflicts.append(conflict)
            self._conflicts[conflict.id] = conflict
        
        # Conflicting retention requirements
        if self._has_retention_conflict(flow.source_country, flow.destination_country):
            conflict = JurisdictionConflict(
                flow_id=flow.id,
                source_jurisdiction=flow.source_country,
                destination_jurisdiction=flow.destination_country,
                source_regulation=JURISDICTION_REGULATIONS.get(flow.source_country, ["General"])[0],
                destination_regulation=JURISDICTION_REGULATIONS.get(flow.destination_country, ["General"])[0],
                conflict_type="retention_conflict",
                description="Data retention requirements differ between jurisdictions",
                severity=RiskLevel.MEDIUM,
                resolution_options=[
                    "Apply stricter retention period",
                    "Implement jurisdiction-specific retention policies",
                    "Use data segregation by jurisdiction",
                ],
                recommended_resolution="Apply the stricter retention requirement",
            )
            conflicts.append(conflict)
            self._conflicts[conflict.id] = conflict
        
        return conflicts
    
    def _has_retention_conflict(self, source: str, dest: str) -> bool:
        """Check if there's a retention requirement conflict."""
        # Simplified check - in reality would need detailed regulatory mapping
        conflicting_pairs = [
            ("EU", "US"),  # GDPR vs various US requirements
            ("DE", "US"),  # German telecom retention vs US
        ]
        return (source, dest) in conflicting_pairs or (dest, source) in conflicting_pairs
    
    def _needs_tia(self, flow: DataFlow) -> bool:
        """Determine if a flow needs a Transfer Impact Assessment."""
        # TIA needed for EEA -> non-adequate country transfers
        if flow.source_country in EEA_COUNTRIES:
            if flow.destination_country not in EEA_COUNTRIES:
                if flow.destination_country not in EU_ADEQUATE_COUNTRIES:
                    return True
                # Even adequate countries need TIA for high-risk scenarios
                if flow.destination_country in HIGH_GOVERNMENT_ACCESS_RISK:
                    return True
        
        # TIA needed for sensitive data
        sensitive_types = [DataClassification.PHI, DataClassification.PCI, DataClassification.SENSITIVE]
        if any(dt in sensitive_types for dt in flow.data_types):
            return True
        
        return False
    
    async def generate_tia(
        self,
        flow: DataFlow,
        assessor: str | None = None,
    ) -> TransferImpactAssessment:
        """Generate a Transfer Impact Assessment for a data flow."""
        
        # Determine adequacy status
        adequacy_status = self._determine_adequacy(flow.destination_country)
        
        # Assess government access risk
        gov_access_risk = (
            RiskLevel.HIGH if flow.destination_country in HIGH_GOVERNMENT_ACCESS_RISK
            else RiskLevel.LOW
        )
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(flow)
        
        # Identify mitigating factors
        mitigating_factors = self._identify_mitigating_factors(flow)
        
        # Calculate overall risk
        overall_risk = self._calculate_overall_risk(flow, risk_factors, mitigating_factors)
        
        # Determine if supplementary measures needed
        supplementary_required = (
            adequacy_status != JurisdictionType.ADEQUATE and
            overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        )
        
        # Get recommended measures
        recommended_measures = []
        if supplementary_required:
            recommended_measures = self._get_recommended_measures(flow, risk_factors)
        
        # Determine recommended transfer mechanism
        recommended_mechanism = self._recommend_mechanism(flow, adequacy_status)
        
        tia = TransferImpactAssessment(
            flow_id=flow.id,
            assessor=assessor,
            source_country=flow.source_country,
            source_legal_framework=LEGAL_FRAMEWORKS.get(flow.source_country, "General data protection laws"),
            source_data_protection_authority=DPA_CONTACTS.get(flow.source_country),
            destination_country=flow.destination_country,
            destination_legal_framework=LEGAL_FRAMEWORKS.get(flow.destination_country, "Local data protection laws"),
            destination_adequacy_status=adequacy_status,
            destination_government_access_risk=gov_access_risk,
            overall_risk=overall_risk,
            risk_factors=risk_factors,
            mitigating_factors=mitigating_factors,
            supplementary_measures_required=supplementary_required,
            recommended_measures=recommended_measures,
            recommended_mechanism=recommended_mechanism,
            mechanism_justification=self._get_mechanism_justification(recommended_mechanism, adequacy_status),
            scc_template=self._get_scc_template_link(flow),
            additional_clauses=self._get_additional_clauses(flow, risk_factors),
            next_review_date=datetime.utcnow() + timedelta(days=365),  # Annual review
        )
        
        self._assessments[tia.id] = tia
        return tia
    
    def _determine_adequacy(self, country: str) -> JurisdictionType:
        """Determine adequacy status for a destination country."""
        if country in EEA_COUNTRIES:
            return JurisdictionType.DOMESTIC  # Same legal framework
        if country in EU_ADEQUATE_COUNTRIES:
            return JurisdictionType.ADEQUATE
        if country in DATA_LOCALIZATION_COUNTRIES:
            return JurisdictionType.PROHIBITED  # Effectively prohibited due to localization
        return JurisdictionType.SCCS  # SCCs needed
    
    def _identify_risk_factors(self, flow: DataFlow) -> list[str]:
        """Identify risk factors for a transfer."""
        factors = []
        
        # Destination country risks
        if flow.destination_country in HIGH_GOVERNMENT_ACCESS_RISK:
            factors.append(f"Government access risk in {flow.destination_country}")
        
        if flow.destination_country in DATA_LOCALIZATION_COUNTRIES:
            factors.append(f"Data localization requirements in {flow.destination_country}")
        
        if flow.destination_country not in EU_ADEQUATE_COUNTRIES:
            factors.append("No EU adequacy decision for destination country")
        
        # Data type risks
        if DataClassification.PHI in flow.data_types:
            factors.append("Transfer includes Protected Health Information (PHI)")
        if DataClassification.PCI in flow.data_types:
            factors.append("Transfer includes Payment Card Industry (PCI) data")
        if DataClassification.PII in flow.data_types:
            factors.append("Transfer includes Personally Identifiable Information (PII)")
        if DataClassification.SENSITIVE in flow.data_types:
            factors.append("Transfer includes sensitive/special category data")
        
        # Volume risks
        if flow.volume_estimate and "GB" in flow.volume_estimate.upper():
            factors.append("Large volume of data transferred")
        
        return factors
    
    def _identify_mitigating_factors(self, flow: DataFlow) -> list[str]:
        """Identify mitigating factors for a transfer."""
        factors = []
        
        if flow.transfer_mechanism == TransferMechanism.STANDARD_CONTRACTUAL_CLAUSES:
            factors.append("Standard Contractual Clauses in place")
        
        if flow.transfer_mechanism == TransferMechanism.BINDING_CORPORATE_RULES:
            factors.append("Binding Corporate Rules approved")
        
        if flow.destination_country in EU_ADEQUATE_COUNTRIES:
            factors.append("Destination has EU adequacy decision")
        
        # Check for encryption (would need additional data in real implementation)
        factors.append("Encryption in transit (TLS) assumed")
        
        return factors
    
    def _calculate_overall_risk(
        self,
        flow: DataFlow,
        risk_factors: list[str],
        mitigating_factors: list[str],
    ) -> RiskLevel:
        """Calculate overall risk level."""
        risk_score = len(risk_factors) - (len(mitigating_factors) * 0.5)
        
        # Adjust for specific high-risk scenarios
        if flow.destination_country in ["CN", "RU"]:
            risk_score += 2
        
        if any("PHI" in f or "PCI" in f for f in risk_factors):
            risk_score += 1
        
        if risk_score >= 4:
            return RiskLevel.CRITICAL
        elif risk_score >= 3:
            return RiskLevel.HIGH
        elif risk_score >= 2:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW
    
    def _get_recommended_measures(
        self,
        flow: DataFlow,
        risk_factors: list[str],
    ) -> list[str]:
        """Get recommended supplementary measures."""
        measures = []
        
        # Always recommend encryption
        measures.extend(SUPPLEMENTARY_MEASURES["encryption"][:2])
        
        # If government access risk
        if any("Government access" in f for f in risk_factors):
            measures.extend(SUPPLEMENTARY_MEASURES["encryption"][2:])
            measures.extend(SUPPLEMENTARY_MEASURES["contractual"][:2])
        
        # If sensitive data
        if any("PHI" in f or "PCI" in f or "PII" in f for f in risk_factors):
            measures.extend(SUPPLEMENTARY_MEASURES["pseudonymization"])
            measures.extend(SUPPLEMENTARY_MEASURES["access_control"][:2])
        
        return list(set(measures))[:10]  # Dedupe and limit
    
    def _recommend_mechanism(
        self,
        flow: DataFlow,
        adequacy_status: JurisdictionType,
    ) -> TransferMechanism:
        """Recommend appropriate transfer mechanism."""
        if adequacy_status == JurisdictionType.DOMESTIC:
            return TransferMechanism.NONE
        
        if adequacy_status == JurisdictionType.ADEQUATE:
            return TransferMechanism.ADEQUACY_DECISION
        
        if adequacy_status == JurisdictionType.PROHIBITED:
            return TransferMechanism.CONSENT  # Only explicit consent might work
        
        # Default to SCCs for non-adequate countries
        return TransferMechanism.STANDARD_CONTRACTUAL_CLAUSES
    
    def _get_mechanism_justification(
        self,
        mechanism: TransferMechanism,
        adequacy_status: JurisdictionType,
    ) -> str:
        """Get justification for recommended mechanism."""
        justifications = {
            TransferMechanism.NONE: "Transfer within EEA/adequate jurisdiction - no additional mechanism required",
            TransferMechanism.ADEQUACY_DECISION: "Destination country has EU adequacy decision",
            TransferMechanism.STANDARD_CONTRACTUAL_CLAUSES: "SCCs are the most commonly used mechanism for transfers to non-adequate countries and provide legal certainty",
            TransferMechanism.BINDING_CORPORATE_RULES: "BCRs suitable for intra-group transfers with established group-wide privacy policies",
            TransferMechanism.CONSENT: "Explicit consent may be used for occasional, non-repetitive transfers where other mechanisms are not feasible",
        }
        return justifications.get(mechanism, "Mechanism selected based on regulatory requirements")
    
    def _get_scc_template_link(self, flow: DataFlow) -> str:
        """Get appropriate SCC template reference."""
        return "https://ec.europa.eu/info/law/law-topic/data-protection/international-dimension-data-protection/standard-contractual-clauses-scc_en"
    
    def _get_additional_clauses(
        self,
        flow: DataFlow,
        risk_factors: list[str],
    ) -> list[str]:
        """Get recommended additional contractual clauses."""
        clauses = []
        
        if any("Government access" in f for f in risk_factors):
            clauses.append("Notification of government access requests (to extent permitted by law)")
            clauses.append("Commitment to challenge disproportionate disclosure requests")
            clauses.append("Transparency reporting on government requests")
        
        if DataClassification.PHI in flow.data_types:
            clauses.append("HIPAA Business Associate Agreement provisions")
        
        if DataClassification.PCI in flow.data_types:
            clauses.append("PCI DSS compliance requirements")
        
        return clauses
    
    def _generate_recommendations(self, flow: DataFlow) -> list[str]:
        """Generate recommendations for a flow."""
        recs = []
        
        if flow.compliance_status == ComplianceStatus.NON_COMPLIANT:
            recs.append(f"URGENT: Implement transfer mechanism for {flow.name}")
        
        if flow.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            recs.append(f"HIGH PRIORITY: Review and mitigate risks for {flow.name}")
        
        if flow.transfer_mechanism == TransferMechanism.STANDARD_CONTRACTUAL_CLAUSES:
            recs.append(f"Complete SCC execution and TIA for {flow.name}")
        
        if flow.destination_country in HIGH_GOVERNMENT_ACCESS_RISK:
            recs.append(f"Implement supplementary measures for transfer to {flow.destination_country}")
        
        return recs
    
    def _generate_compliance_summary(
        self,
        flow_map: DataFlowMap,
    ) -> dict[str, Any]:
        """Generate compliance summary for the flow map."""
        return {
            "overall_status": self._calculate_overall_status(flow_map),
            "compliant_percentage": (
                (flow_map.compliant_flows / flow_map.total_flows * 100)
                if flow_map.total_flows > 0 else 100
            ),
            "by_regulation": self._summarize_by_regulation(flow_map),
            "by_destination": self._summarize_by_destination(flow_map),
            "priority_actions": self._get_priority_actions(flow_map),
        }
    
    def _calculate_overall_status(self, flow_map: DataFlowMap) -> str:
        """Calculate overall compliance status."""
        if flow_map.critical_risks > 0:
            return "CRITICAL"
        if flow_map.action_required_flows > 0:
            return "ACTION_REQUIRED"
        if flow_map.high_risks > 0:
            return "NEEDS_ATTENTION"
        return "COMPLIANT"
    
    def _summarize_by_regulation(
        self,
        flow_map: DataFlowMap,
    ) -> dict[str, int]:
        """Summarize flows by applicable regulation."""
        summary: dict[str, int] = {}
        for flow in flow_map.flows:
            for reg in flow.regulations:
                summary[reg] = summary.get(reg, 0) + 1
        return summary
    
    def _summarize_by_destination(
        self,
        flow_map: DataFlowMap,
    ) -> dict[str, int]:
        """Summarize flows by destination country."""
        summary: dict[str, int] = {}
        for flow in flow_map.flows:
            summary[flow.destination_country] = summary.get(flow.destination_country, 0) + 1
        return summary
    
    def _get_priority_actions(self, flow_map: DataFlowMap) -> list[str]:
        """Get prioritized action items."""
        actions = []
        
        # Critical risks first
        for flow in flow_map.flows:
            if flow.risk_level == RiskLevel.CRITICAL:
                actions.append(f"[CRITICAL] Address {flow.name}: {flow.actions_required[0] if flow.actions_required else 'Review immediately'}")
        
        # Non-compliant flows
        for flow in flow_map.flows:
            if flow.compliance_status == ComplianceStatus.NON_COMPLIANT:
                actions.append(f"[NON-COMPLIANT] {flow.name}: Implement transfer mechanism")
        
        # High risks
        for flow in flow_map.flows:
            if flow.risk_level == RiskLevel.HIGH and flow.risk_level != RiskLevel.CRITICAL:
                actions.append(f"[HIGH] Review {flow.name}: {flow.actions_required[0] if flow.actions_required else 'Assess risks'}")
        
        return actions[:10]  # Top 10 priorities
    
    async def get_assessment(self, assessment_id: UUID) -> TransferImpactAssessment | None:
        """Get a TIA by ID."""
        return self._assessments.get(assessment_id)
    
    async def approve_assessment(
        self,
        assessment_id: UUID,
        approver: str,
    ) -> TransferImpactAssessment | None:
        """Approve a Transfer Impact Assessment."""
        tia = self._assessments.get(assessment_id)
        if tia:
            tia.approved = True
            tia.approval_date = datetime.utcnow()
            tia.approver = approver
        return tia


# Singleton instance
_analyzer_instance: CrossBorderAnalyzer | None = None


def get_cross_border_analyzer() -> CrossBorderAnalyzer:
    """Get or create the cross-border analyzer singleton."""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = CrossBorderAnalyzer()
    return _analyzer_instance
