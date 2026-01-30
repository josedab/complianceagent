"""Risk Scorer - Calculates compliance risk for vendors."""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

import structlog

from app.services.vendor_risk.models import (
    ComplianceInheritance,
    ComplianceTier,
    KNOWN_VENDORS,
    RiskAssessment,
    RiskLevel,
    Vendor,
    VendorGraph,
    VendorType,
)


logger = structlog.get_logger()


# Risk weights by factor
RISK_WEIGHTS = {
    "no_certifications": 30,
    "unknown_vendor": 20,
    "processes_pii": 15,
    "processes_payment": 20,
    "processes_health": 25,
    "no_security_audit": 10,
    "vulnerabilities": 15,
    "outdated_version": 10,
    "no_maintenance": 15,
    "cross_border_data": 10,
}

# Compliance requirements by regulation and data type
COMPLIANCE_REQUIREMENTS = {
    "GDPR": {
        "triggers": ["personal_data", "behavior", "location"],
        "requirements": [
            "Data Processing Agreement (DPA) required",
            "Article 28 processor requirements",
            "Data transfer assessment for non-EU vendors",
            "Record of processing activities",
        ],
    },
    "HIPAA": {
        "triggers": ["health", "phi", "medical"],
        "requirements": [
            "Business Associate Agreement (BAA) required",
            "Technical safeguards verification",
            "Security assessment of vendor",
            "Breach notification procedures",
        ],
    },
    "PCI-DSS": {
        "triggers": ["payment", "card", "financial"],
        "requirements": [
            "PCI-DSS compliance attestation",
            "Tokenization or encryption verification",
            "Secure key management",
            "Regular vulnerability scans",
        ],
    },
    "SOC2": {
        "triggers": ["all"],
        "requirements": [
            "SOC2 report review",
            "Vendor management policy compliance",
            "Security questionnaire completion",
            "Annual review cycle",
        ],
    },
}


class RiskScorer:
    """Calculates compliance risk scores for vendors."""

    def __init__(self):
        self._assessments: dict[UUID, RiskAssessment] = {}

    async def assess_vendor(
        self,
        vendor: Vendor,
        organization_regulations: list[str] | None = None,
    ) -> RiskAssessment:
        """Assess risk for a single vendor.
        
        Args:
            vendor: Vendor to assess
            organization_regulations: Regulations the org must comply with
            
        Returns:
            RiskAssessment with scores and recommendations
        """
        assessment = RiskAssessment(
            vendor_id=vendor.id,
            vendor_name=vendor.name,
        )
        
        risk_factors = []
        risk_score = 0.0
        
        # Check certification status
        if vendor.compliance_tier == ComplianceTier.UNCERTIFIED:
            risk_factors.append({
                "factor": "no_certifications",
                "description": "Vendor has no compliance certifications",
                "weight": RISK_WEIGHTS["no_certifications"],
            })
            risk_score += RISK_WEIGHTS["no_certifications"]
        elif vendor.compliance_tier == ComplianceTier.UNKNOWN:
            risk_factors.append({
                "factor": "unknown_vendor",
                "description": "Vendor compliance status is unknown",
                "weight": RISK_WEIGHTS["unknown_vendor"],
            })
            risk_score += RISK_WEIGHTS["unknown_vendor"]
        
        # Check data processing
        if "personal_data" in vendor.data_processing or "pii" in vendor.data_processing:
            risk_factors.append({
                "factor": "processes_pii",
                "description": "Vendor processes personal/PII data",
                "weight": RISK_WEIGHTS["processes_pii"],
            })
            risk_score += RISK_WEIGHTS["processes_pii"]
        
        if "payment" in vendor.data_processing:
            risk_factors.append({
                "factor": "processes_payment",
                "description": "Vendor processes payment data",
                "weight": RISK_WEIGHTS["processes_payment"],
            })
            risk_score += RISK_WEIGHTS["processes_payment"]
        
        if "health" in vendor.data_processing or "phi" in vendor.data_processing:
            risk_factors.append({
                "factor": "processes_health",
                "description": "Vendor processes health/PHI data",
                "weight": RISK_WEIGHTS["processes_health"],
            })
            risk_score += RISK_WEIGHTS["processes_health"]
        
        # Check security
        if vendor.known_vulnerabilities > 0:
            risk_factors.append({
                "factor": "vulnerabilities",
                "description": f"Vendor has {vendor.known_vulnerabilities} known vulnerabilities",
                "weight": RISK_WEIGHTS["vulnerabilities"],
            })
            risk_score += RISK_WEIGHTS["vulnerabilities"]
        
        if not vendor.last_security_audit:
            risk_factors.append({
                "factor": "no_security_audit",
                "description": "No recent security audit information",
                "weight": RISK_WEIGHTS["no_security_audit"],
            })
            risk_score += RISK_WEIGHTS["no_security_audit"]
        
        # Mitigating factors
        mitigating = []
        if vendor.compliance_tier == ComplianceTier.FULLY_CERTIFIED:
            mitigating.append("Fully certified with compliance standards")
            risk_score = max(0, risk_score - 20)
        
        if vendor.name.lower() in KNOWN_VENDORS:
            known_risk = KNOWN_VENDORS[vendor.name.lower()].get("risk_level")
            if known_risk == RiskLevel.LOW:
                mitigating.append("Well-known vendor with established security track record")
                risk_score = max(0, risk_score - 15)
        
        # Calculate component scores
        assessment.security_score = max(0, 100 - risk_score * 0.5)
        assessment.compliance_score = 100 if vendor.compliance_tier == ComplianceTier.FULLY_CERTIFIED else (
            70 if vendor.compliance_tier == ComplianceTier.PARTIALLY_CERTIFIED else 30
        )
        assessment.maintenance_score = 70 if vendor.vendor_type == VendorType.PACKAGE else 85
        assessment.transparency_score = 80 if vendor.name.lower() in KNOWN_VENDORS else 50
        
        # Overall score
        assessment.risk_score = min(100, risk_score)
        assessment.risk_factors = risk_factors
        assessment.mitigating_factors = mitigating
        
        # Determine risk level
        if risk_score >= 60:
            assessment.overall_risk = RiskLevel.CRITICAL
        elif risk_score >= 40:
            assessment.overall_risk = RiskLevel.HIGH
        elif risk_score >= 20:
            assessment.overall_risk = RiskLevel.MEDIUM
        elif risk_score > 0:
            assessment.overall_risk = RiskLevel.LOW
        else:
            assessment.overall_risk = RiskLevel.MINIMAL
        
        # Generate recommendations
        assessment.recommendations = self._generate_recommendations(vendor, risk_factors)
        assessment.required_actions = self._generate_required_actions(
            vendor, organization_regulations or []
        )
        
        # Store
        self._assessments[assessment.vendor_id] = assessment
        
        return assessment

    async def assess_graph(
        self,
        graph: VendorGraph,
        organization_regulations: list[str] | None = None,
    ) -> dict[str, Any]:
        """Assess all vendors in a graph.
        
        Returns aggregate assessment.
        """
        assessments = []
        total_score = 0.0
        
        for vendor in graph.vendors.values():
            assessment = await self.assess_vendor(vendor, organization_regulations)
            assessments.append(assessment)
            total_score += assessment.risk_score
        
        avg_score = total_score / len(assessments) if assessments else 0
        
        # Count by risk level
        by_risk = {level.value: 0 for level in RiskLevel}
        for a in assessments:
            by_risk[a.overall_risk.value] += 1
        
        # Overall risk
        if by_risk.get(RiskLevel.CRITICAL.value, 0) > 0:
            overall = RiskLevel.CRITICAL
        elif by_risk.get(RiskLevel.HIGH.value, 0) > 0:
            overall = RiskLevel.HIGH
        elif by_risk.get(RiskLevel.MEDIUM.value, 0) > 0:
            overall = RiskLevel.MEDIUM
        else:
            overall = RiskLevel.LOW
        
        return {
            "graph_id": str(graph.id),
            "total_vendors": len(assessments),
            "average_risk_score": round(avg_score, 2),
            "overall_risk": overall.value,
            "by_risk_level": by_risk,
            "critical_vendors": [
                {"name": a.vendor_name, "score": a.risk_score}
                for a in assessments if a.overall_risk == RiskLevel.CRITICAL
            ],
            "high_risk_vendors": [
                {"name": a.vendor_name, "score": a.risk_score}
                for a in assessments if a.overall_risk == RiskLevel.HIGH
            ],
            "top_recommendations": self._aggregate_recommendations(assessments),
        }

    def calculate_inheritance(
        self,
        vendor: Vendor,
        organization_regulations: list[str],
    ) -> ComplianceInheritance:
        """Calculate compliance requirements inherited from vendor."""
        inheritance = ComplianceInheritance(vendor_name=vendor.name)
        
        for reg, config in COMPLIANCE_REQUIREMENTS.items():
            if reg not in organization_regulations:
                continue
            
            triggers = config["triggers"]
            
            # Check if vendor triggers this regulation
            triggered = False
            if "all" in triggers:
                triggered = True
            else:
                for trigger in triggers:
                    if trigger in vendor.data_processing:
                        triggered = True
                        break
            
            if triggered:
                inheritance.affected_regulations.append(reg)
                inheritance.inherited_requirements.extend(config["requirements"])
                
                # Check specific requirements
                if reg == "GDPR":
                    inheritance.dpa_required = True
                    inheritance.subprocessor_notification = True
                if reg == "HIPAA":
                    inheritance.audit_rights = True
        
        # Generate gaps
        if vendor.compliance_tier != ComplianceTier.FULLY_CERTIFIED:
            if "GDPR" in inheritance.affected_regulations:
                inheritance.compliance_gaps.append("Missing GDPR DPA with vendor")
            if "HIPAA" in inheritance.affected_regulations:
                inheritance.compliance_gaps.append("Missing BAA with vendor")
            if "PCI-DSS" in inheritance.affected_regulations:
                inheritance.compliance_gaps.append("PCI-DSS compliance not verified")
        
        inheritance.impact_summary = (
            f"Vendor affects {len(inheritance.affected_regulations)} regulations with "
            f"{len(inheritance.inherited_requirements)} requirements"
        )
        
        return inheritance

    def _generate_recommendations(
        self,
        vendor: Vendor,
        risk_factors: list[dict[str, Any]],
    ) -> list[str]:
        """Generate recommendations based on risk factors."""
        recommendations = []
        
        factor_names = {f["factor"] for f in risk_factors}
        
        if "no_certifications" in factor_names or "unknown_vendor" in factor_names:
            recommendations.append("Request compliance certifications from vendor")
            recommendations.append("Complete vendor security questionnaire")
        
        if "processes_pii" in factor_names:
            recommendations.append("Execute Data Processing Agreement (DPA)")
            recommendations.append("Review vendor's privacy policy")
        
        if "processes_payment" in factor_names:
            recommendations.append("Verify PCI-DSS compliance")
            recommendations.append("Review cardholder data handling")
        
        if "vulnerabilities" in factor_names:
            recommendations.append("Update to latest patched version")
            recommendations.append("Review security advisories")
        
        if not recommendations:
            recommendations.append("Continue regular vendor monitoring")
        
        return recommendations[:5]  # Top 5

    def _generate_required_actions(
        self,
        vendor: Vendor,
        regulations: list[str],
    ) -> list[str]:
        """Generate required actions for compliance."""
        actions = []
        
        if "GDPR" in regulations and any(
            d in vendor.data_processing for d in ["personal_data", "pii", "behavior"]
        ):
            actions.append("Execute GDPR-compliant DPA")
        
        if "HIPAA" in regulations and any(
            d in vendor.data_processing for d in ["health", "phi"]
        ):
            actions.append("Execute Business Associate Agreement")
        
        if "PCI-DSS" in regulations and "payment" in vendor.data_processing:
            actions.append("Obtain PCI-DSS attestation of compliance")
        
        return actions

    def _aggregate_recommendations(
        self,
        assessments: list[RiskAssessment],
    ) -> list[str]:
        """Aggregate recommendations from all assessments."""
        all_recs = []
        for a in assessments:
            all_recs.extend(a.recommendations)
        
        # Count frequency
        from collections import Counter
        counts = Counter(all_recs)
        
        return [rec for rec, _ in counts.most_common(5)]


# Global instance
_scorer: RiskScorer | None = None


def get_risk_scorer() -> RiskScorer:
    """Get or create risk scorer."""
    global _scorer
    if _scorer is None:
        _scorer = RiskScorer()
    return _scorer
