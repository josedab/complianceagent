"""Relevance Scorer - ML-powered relevance scoring for regulatory updates."""

import re
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

import structlog

from app.services.intelligence.models import (
    CustomerProfile,
    RegulatoryUpdate,
    RelevanceScore,
    UpdateSeverity,
)


logger = structlog.get_logger()


# Keyword categories for relevance matching
KEYWORD_CATEGORIES = {
    "privacy": [
        "personal data", "data protection", "privacy", "consent", "data subject",
        "data controller", "data processor", "dpa", "gdpr", "ccpa", "cpra",
        "right to deletion", "right to access", "data portability", "opt-out",
    ],
    "healthcare": [
        "hipaa", "phi", "protected health information", "medical", "patient",
        "healthcare", "health data", "covered entity", "business associate",
        "hitech", "omnibus rule", "breach notification",
    ],
    "financial": [
        "sox", "sec", "financial", "audit", "internal controls", "securities",
        "pci", "pci-dss", "payment card", "cardholder", "glba", "finra",
    ],
    "ai": [
        "artificial intelligence", "ai act", "machine learning", "algorithm",
        "automated decision", "high-risk ai", "ai system", "model", "bias",
        "transparency", "explainability", "human oversight",
    ],
    "security": [
        "cybersecurity", "data breach", "security", "encryption", "access control",
        "authentication", "vulnerability", "penetration test", "nis2", "nist",
    ],
    "esg": [
        "sustainability", "esg", "climate", "carbon", "emissions", "csrd",
        "tcfd", "greenhouse gas", "environmental", "social", "governance",
    ],
}


# Jurisdiction mappings for relevance
JURISDICTION_MAPPINGS = {
    "US": ["US", "US-CA", "US-NY", "US-TX", "US-CO", "US-VA", "United States", "Federal"],
    "EU": ["EU", "European Union", "GDPR", "Europe"],
    "UK": ["UK", "United Kingdom", "Britain", "ICO"],
    "APAC": ["SG", "Singapore", "IN", "India", "JP", "Japan", "KR", "Korea", "AU", "Australia"],
    "Global": ["Global", "International", "Worldwide"],
}


class RelevanceScorer:
    """ML-powered relevance scoring for regulatory updates."""

    def __init__(
        self,
        base_threshold: float = 0.3,
        urgency_boost: float = 0.2,
    ):
        self.base_threshold = base_threshold
        self.urgency_boost = urgency_boost

    def score_update(
        self,
        update: RegulatoryUpdate,
        profile: CustomerProfile,
    ) -> RelevanceScore:
        """Score the relevance of an update for a customer profile.
        
        Uses multiple signals:
        - Jurisdiction match
        - Industry/framework match
        - Keyword matching
        - Urgency/deadline proximity
        - Historical interest patterns
        
        Returns a RelevanceScore with detailed breakdown.
        """
        matched_criteria = []
        
        # Jurisdiction matching (0-1)
        jurisdiction_score = self._score_jurisdiction(
            update.jurisdiction, profile.jurisdictions
        )
        if jurisdiction_score > 0.5:
            matched_criteria.append(f"Jurisdiction: {update.jurisdiction}")
        
        # Industry/regulation match (0-1)
        regulation_score = self._score_regulation(
            update.framework, update.affected_regulations, profile.applicable_regulations
        )
        if regulation_score > 0.5:
            matched_criteria.append(f"Regulation: {update.framework}")
        
        # Industry match (0-1)
        industry_score = self._score_industry(update, profile.industries)
        if industry_score > 0.5:
            matched_criteria.append(f"Industry match")
        
        # Keyword matching (0-1)
        keyword_score = self._score_keywords(
            update.title + " " + update.summary + " " + " ".join(update.keywords),
            profile.keywords_of_interest,
            profile.data_types_processed,
        )
        if keyword_score > 0.3:
            matched_criteria.append(f"Keyword relevance: {keyword_score:.0%}")
        
        # Urgency factor (0-1)
        urgency_score = self._score_urgency(update)
        if urgency_score > 0.5:
            matched_criteria.append(f"Urgency: {update.severity.value}")
        
        # Historical interest (placeholder - would use ML model)
        historical_score = 0.5  # Default neutral
        
        # Weighted combination
        weights = {
            "jurisdiction": 0.25,
            "regulation": 0.25,
            "industry": 0.15,
            "keyword": 0.15,
            "urgency": 0.10,
            "historical": 0.10,
        }
        
        overall = (
            jurisdiction_score * weights["jurisdiction"] +
            regulation_score * weights["regulation"] +
            industry_score * weights["industry"] +
            keyword_score * weights["keyword"] +
            urgency_score * weights["urgency"] +
            historical_score * weights["historical"]
        )
        
        # Apply urgency boost for critical/high severity
        if update.severity in (UpdateSeverity.CRITICAL, UpdateSeverity.HIGH):
            overall = min(1.0, overall + self.urgency_boost)
        
        # Generate explanation
        explanation = self._generate_explanation(
            update, profile, overall, matched_criteria
        )
        
        return RelevanceScore(
            update_id=update.id,
            organization_id=profile.organization_id,
            overall_score=overall,
            jurisdiction_match=jurisdiction_score,
            industry_match=industry_score,
            regulation_match=regulation_score,
            keyword_match=keyword_score,
            historical_interest=historical_score,
            urgency_factor=urgency_score,
            confidence=self._calculate_confidence(update, profile),
            explanation=explanation,
            matched_criteria=matched_criteria,
        )

    def batch_score(
        self,
        updates: list[RegulatoryUpdate],
        profile: CustomerProfile,
        min_score: float | None = None,
    ) -> list[tuple[RegulatoryUpdate, RelevanceScore]]:
        """Score multiple updates and optionally filter by minimum score."""
        results = []
        threshold = min_score or self.base_threshold
        
        for update in updates:
            score = self.score_update(update, profile)
            if score.overall_score >= threshold:
                results.append((update, score))
        
        # Sort by relevance (highest first)
        results.sort(key=lambda x: x[1].overall_score, reverse=True)
        return results

    def predict_impact(
        self,
        update: RegulatoryUpdate,
        profile: CustomerProfile,
    ) -> dict[str, Any]:
        """Predict the impact of an update on an organization."""
        relevance = self.score_update(update, profile)
        
        # Estimate effort based on update type and severity
        effort_map = {
            (UpdateSeverity.CRITICAL, "new_regulation"): "high",
            (UpdateSeverity.CRITICAL, "amendment"): "high",
            (UpdateSeverity.HIGH, "new_regulation"): "high",
            (UpdateSeverity.HIGH, "amendment"): "medium",
            (UpdateSeverity.MEDIUM, "new_regulation"): "medium",
            (UpdateSeverity.MEDIUM, "amendment"): "low",
        }
        effort = effort_map.get(
            (update.severity, update.update_type.value), "low"
        )
        
        # Calculate days until action required
        days_to_action = None
        if update.effective_date:
            delta = update.effective_date - datetime.utcnow()
            days_to_action = max(0, delta.days)
        
        return {
            "relevance_score": relevance.overall_score,
            "estimated_effort": effort,
            "days_to_action": days_to_action,
            "affected_areas": self._identify_affected_areas(update, profile),
            "recommended_actions": self._generate_recommendations(update, relevance),
            "risk_level": self._assess_risk(update, relevance, profile),
        }

    def _score_jurisdiction(
        self,
        update_jurisdiction: str,
        profile_jurisdictions: list[str],
    ) -> float:
        """Score jurisdiction match."""
        if not profile_jurisdictions:
            return 0.5  # Neutral if no jurisdictions specified
        
        update_jur = update_jurisdiction.upper()
        
        # Direct match
        if update_jur in [j.upper() for j in profile_jurisdictions]:
            return 1.0
        
        # Check mappings
        for group, members in JURISDICTION_MAPPINGS.items():
            members_upper = [m.upper() for m in members]
            if update_jur in members_upper:
                for profile_jur in profile_jurisdictions:
                    if profile_jur.upper() in members_upper or profile_jur.upper() == group:
                        return 0.8
        
        # Global applies to everyone
        if update_jur in ["GLOBAL", "INTERNATIONAL"]:
            return 0.6
        
        return 0.0

    def _score_regulation(
        self,
        update_framework: str,
        affected_regulations: list[str],
        profile_regulations: list[str],
    ) -> float:
        """Score regulation/framework match."""
        if not profile_regulations:
            return 0.5
        
        profile_regs_lower = [r.lower() for r in profile_regulations]
        
        # Direct framework match
        if update_framework.lower() in profile_regs_lower:
            return 1.0
        
        # Check affected regulations
        for reg in affected_regulations:
            if reg.lower() in profile_regs_lower:
                return 0.9
        
        # Fuzzy matching for common variations
        framework_lower = update_framework.lower()
        for profile_reg in profile_regs_lower:
            # Handle variations like "GDPR" vs "EU GDPR"
            if framework_lower in profile_reg or profile_reg in framework_lower:
                return 0.7
        
        return 0.0

    def _score_industry(
        self,
        update: RegulatoryUpdate,
        profile_industries: list[str],
    ) -> float:
        """Score industry relevance."""
        if not profile_industries:
            return 0.5
        
        # Map frameworks to industries
        framework_industry_map = {
            "hipaa": ["healthcare", "medical", "pharma"],
            "pci-dss": ["retail", "ecommerce", "fintech", "payments"],
            "sox": ["financial", "fintech", "banking"],
            "gdpr": ["technology", "saas", "retail", "healthcare", "fintech"],
            "eu ai act": ["technology", "ai", "saas", "healthcare", "fintech"],
        }
        
        framework_lower = update.framework.lower()
        relevant_industries = framework_industry_map.get(framework_lower, [])
        
        profile_industries_lower = [i.lower() for i in profile_industries]
        
        for industry in relevant_industries:
            if industry in profile_industries_lower:
                return 1.0
        
        # Partial matches
        for industry in relevant_industries:
            for profile_ind in profile_industries_lower:
                if industry in profile_ind or profile_ind in industry:
                    return 0.6
        
        return 0.3  # Base relevance

    def _score_keywords(
        self,
        text: str,
        profile_keywords: list[str],
        data_types: list[str],
    ) -> float:
        """Score keyword relevance."""
        text_lower = text.lower()
        matches = 0
        total_keywords = len(profile_keywords) + len(data_types)
        
        if total_keywords == 0:
            return 0.5
        
        # Check profile keywords
        for keyword in profile_keywords:
            if keyword.lower() in text_lower:
                matches += 1
        
        # Check data types
        for data_type in data_types:
            if data_type.lower() in text_lower:
                matches += 1
        
        # Check category keywords
        for category, keywords in KEYWORD_CATEGORIES.items():
            category_matches = sum(1 for k in keywords if k.lower() in text_lower)
            if category_matches >= 2:
                matches += 0.5
        
        return min(1.0, matches / max(total_keywords, 1))

    def _score_urgency(self, update: RegulatoryUpdate) -> float:
        """Score urgency based on severity and deadlines."""
        severity_scores = {
            UpdateSeverity.CRITICAL: 1.0,
            UpdateSeverity.HIGH: 0.8,
            UpdateSeverity.MEDIUM: 0.5,
            UpdateSeverity.LOW: 0.3,
            UpdateSeverity.INFO: 0.1,
        }
        
        base_score = severity_scores.get(update.severity, 0.5)
        
        # Boost for upcoming deadlines
        if update.effective_date:
            days_until = (update.effective_date - datetime.utcnow()).days
            if days_until <= 30:
                base_score = min(1.0, base_score + 0.3)
            elif days_until <= 90:
                base_score = min(1.0, base_score + 0.15)
        
        return base_score

    def _calculate_confidence(
        self,
        update: RegulatoryUpdate,
        profile: CustomerProfile,
    ) -> float:
        """Calculate confidence in the relevance score."""
        confidence = 0.7  # Base confidence
        
        # Higher confidence with more profile data
        if profile.jurisdictions:
            confidence += 0.05
        if profile.applicable_regulations:
            confidence += 0.05
        if profile.industries:
            confidence += 0.05
        if profile.keywords_of_interest:
            confidence += 0.05
        
        # Higher confidence with more update data
        if update.summary:
            confidence += 0.03
        if update.keywords:
            confidence += 0.02
        if update.effective_date:
            confidence += 0.02
        
        return min(0.95, confidence)

    def _generate_explanation(
        self,
        update: RegulatoryUpdate,
        profile: CustomerProfile,
        score: float,
        matched_criteria: list[str],
    ) -> str:
        """Generate human-readable explanation of the relevance score."""
        if score >= 0.8:
            level = "highly relevant"
        elif score >= 0.5:
            level = "moderately relevant"
        elif score >= 0.3:
            level = "potentially relevant"
        else:
            level = "low relevance"
        
        explanation = f"This update is {level} to your organization. "
        
        if matched_criteria:
            explanation += f"Key factors: {', '.join(matched_criteria[:3])}."
        
        if update.effective_date:
            days = (update.effective_date - datetime.utcnow()).days
            if days > 0:
                explanation += f" Action required within {days} days."
        
        return explanation

    def _identify_affected_areas(
        self,
        update: RegulatoryUpdate,
        profile: CustomerProfile,
    ) -> list[str]:
        """Identify which areas of the organization are affected."""
        areas = []
        
        # Based on framework
        framework_areas = {
            "gdpr": ["Data Privacy", "Customer Data", "Marketing"],
            "hipaa": ["Healthcare Operations", "Patient Records", "IT Security"],
            "pci-dss": ["Payment Processing", "E-commerce", "Customer Data"],
            "sox": ["Financial Reporting", "Internal Controls", "Audit"],
            "eu ai act": ["AI/ML Systems", "Product Development", "Compliance"],
        }
        
        areas.extend(framework_areas.get(update.framework.lower(), []))
        
        # Based on keywords
        if any(k in update.summary.lower() for k in ["breach", "notification", "incident"]):
            areas.append("Incident Response")
        if any(k in update.summary.lower() for k in ["consent", "opt-in", "opt-out"]):
            areas.append("Consent Management")
        if any(k in update.summary.lower() for k in ["transfer", "cross-border", "international"]):
            areas.append("International Operations")
        
        return list(set(areas))

    def _generate_recommendations(
        self,
        update: RegulatoryUpdate,
        relevance: RelevanceScore,
    ) -> list[str]:
        """Generate recommended actions based on the update."""
        recommendations = []
        
        if relevance.overall_score >= 0.7:
            recommendations.append("Review this update with compliance team immediately")
        
        if update.severity == UpdateSeverity.CRITICAL:
            recommendations.append("Schedule emergency compliance review meeting")
        elif update.severity == UpdateSeverity.HIGH:
            recommendations.append("Add to compliance review agenda within 7 days")
        
        if update.effective_date:
            days = (update.effective_date - datetime.utcnow()).days
            if days <= 90:
                recommendations.append(f"Create compliance project plan (deadline: {update.effective_date.date()})")
        
        if update.update_type.value == "new_regulation":
            recommendations.append("Conduct gap analysis against current practices")
        elif update.update_type.value == "amendment":
            recommendations.append("Review changes against current implementation")
        
        return recommendations

    def _assess_risk(
        self,
        update: RegulatoryUpdate,
        relevance: RelevanceScore,
        profile: CustomerProfile,
    ) -> str:
        """Assess risk level of non-compliance."""
        risk_score = relevance.overall_score * 0.4
        
        # Severity factor
        severity_risk = {
            UpdateSeverity.CRITICAL: 0.4,
            UpdateSeverity.HIGH: 0.3,
            UpdateSeverity.MEDIUM: 0.2,
            UpdateSeverity.LOW: 0.1,
            UpdateSeverity.INFO: 0.0,
        }
        risk_score += severity_risk.get(update.severity, 0.1)
        
        # Deadline proximity factor
        if update.effective_date:
            days = (update.effective_date - datetime.utcnow()).days
            if days <= 30:
                risk_score += 0.2
            elif days <= 90:
                risk_score += 0.1
        
        if risk_score >= 0.7:
            return "high"
        elif risk_score >= 0.4:
            return "medium"
        return "low"


# Global scorer instance
_scorer_instance: RelevanceScorer | None = None


def get_relevance_scorer() -> RelevanceScorer:
    """Get or create the relevance scorer instance."""
    global _scorer_instance
    if _scorer_instance is None:
        _scorer_instance = RelevanceScorer()
    return _scorer_instance
