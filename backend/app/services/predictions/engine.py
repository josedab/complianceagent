"""Regulatory Prediction Engine."""

import random
from datetime import datetime, timezone, timedelta
from typing import Any

import structlog

from .models import (
    ComplianceTrend,
    ImpactAssessment,
    ImpactLevel,
    PredictionConfidence,
    RegulatoryDomain,
    RegulatoryPrediction,
    RegulatoryUpdate,
    RiskForecast,
    TimelineProjection,
    UpdateType,
)

logger = structlog.get_logger(__name__)


# Simulated regulatory signals database
REGULATORY_SIGNALS = {
    "GDPR": {
        "domain": RegulatoryDomain.DATA_PRIVACY,
        "recent_enforcement_trend": "increasing",
        "pending_updates": [
            "AI Act integration requirements",
            "Enhanced data portability provisions",
            "Stricter consent mechanisms",
        ],
        "typical_fine_range_eur": (50000, 20000000),
    },
    "HIPAA": {
        "domain": RegulatoryDomain.HEALTHCARE,
        "recent_enforcement_trend": "stable",
        "pending_updates": [
            "Telehealth privacy provisions",
            "AI/ML in healthcare guidance",
            "Updated breach notification timelines",
        ],
        "typical_fine_range_usd": (100, 1500000),
    },
    "PCI-DSS": {
        "domain": RegulatoryDomain.FINANCE,
        "recent_enforcement_trend": "stable",
        "pending_updates": [
            "PCI DSS 4.0 full enforcement",
            "Cloud security requirements",
            "API security standards",
        ],
    },
    "SOC2": {
        "domain": RegulatoryDomain.SECURITY,
        "recent_enforcement_trend": "increasing",
        "pending_updates": [
            "AI risk considerations",
            "Supply chain security focus",
            "Privacy criteria updates",
        ],
    },
    "AI-Act": {
        "domain": RegulatoryDomain.AI_ML,
        "recent_enforcement_trend": "new",
        "pending_updates": [
            "High-risk AI system requirements",
            "Transparency obligations",
            "Foundation model provisions",
        ],
    },
}


class RegulatoryPredictionEngine:
    """Engine for regulatory predictions and forecasting.
    
    Provides:
    - Predictions for upcoming regulatory changes
    - Compliance trend analysis
    - Risk forecasting
    - Impact assessments
    - Timeline projections
    
    Example:
        engine = RegulatoryPredictionEngine()
        
        # Get predictions for a domain
        predictions = await engine.get_predictions(domain=RegulatoryDomain.DATA_PRIVACY)
        
        # Assess impact of a regulation
        impact = await engine.assess_impact(
            regulation="GDPR",
            organization_context={"industry": "healthcare", "data_types": ["PHI", "PII"]}
        )
        
        # Forecast compliance risk
        risk = await engine.forecast_risk(regulations=["GDPR", "HIPAA"])
    """
    
    def __init__(self):
        """Initialize the prediction engine."""
        self._predictions_cache: dict[str, list[RegulatoryPrediction]] = {}
        self._trends_cache: dict[str, list[ComplianceTrend]] = {}
    
    async def get_regulatory_updates(
        self,
        domain: RegulatoryDomain | None = None,
        regulation: str | None = None,
        since: datetime | None = None,
        limit: int = 20,
    ) -> list[RegulatoryUpdate]:
        """Get recent regulatory updates.
        
        Args:
            domain: Filter by regulatory domain
            regulation: Filter by specific regulation
            since: Only updates after this date
            limit: Maximum number of updates
        
        Returns:
            List of regulatory updates
        """
        # In production, this would fetch from a regulatory tracking service
        updates = self._generate_sample_updates(domain, regulation, limit)
        
        if since:
            updates = [u for u in updates if u.announced_date >= since]
        
        logger.info(
            "regulatory_updates_fetched",
            count=len(updates),
            domain=domain.value if domain else None,
            regulation=regulation,
        )
        
        return updates
    
    async def get_predictions(
        self,
        domain: RegulatoryDomain | None = None,
        regulations: list[str] | None = None,
        time_horizon_days: int = 365,
        min_confidence: PredictionConfidence = PredictionConfidence.LOW,
    ) -> list[RegulatoryPrediction]:
        """Get predictions for upcoming regulatory changes.
        
        Args:
            domain: Filter by regulatory domain
            regulations: Filter by specific regulations
            time_horizon_days: How far ahead to predict
            min_confidence: Minimum confidence level
        
        Returns:
            List of regulatory predictions
        """
        predictions = self._generate_predictions(domain, regulations, time_horizon_days)
        
        # Filter by confidence
        confidence_order = [
            PredictionConfidence.VERY_LOW,
            PredictionConfidence.LOW,
            PredictionConfidence.MEDIUM,
            PredictionConfidence.HIGH,
            PredictionConfidence.VERY_HIGH,
        ]
        min_idx = confidence_order.index(min_confidence)
        predictions = [
            p for p in predictions
            if confidence_order.index(p.confidence) >= min_idx
        ]
        
        logger.info(
            "regulatory_predictions_generated",
            count=len(predictions),
            domain=domain.value if domain else None,
        )
        
        return predictions
    
    async def analyze_trends(
        self,
        domain: RegulatoryDomain | None = None,
        regulations: list[str] | None = None,
        lookback_days: int = 365,
    ) -> list[ComplianceTrend]:
        """Analyze compliance trends.
        
        Args:
            domain: Filter by regulatory domain
            regulations: Filter by specific regulations
            lookback_days: Historical period to analyze
        
        Returns:
            List of compliance trends
        """
        trends = self._generate_trends(domain, regulations, lookback_days)
        
        logger.info(
            "compliance_trends_analyzed",
            count=len(trends),
            domain=domain.value if domain else None,
        )
        
        return trends
    
    async def forecast_risk(
        self,
        regulations: list[str],
        current_compliance_scores: dict[str, float] | None = None,
        time_horizon_days: int = 90,
    ) -> list[RiskForecast]:
        """Forecast compliance risk.
        
        Args:
            regulations: Regulations to assess
            current_compliance_scores: Current compliance scores by regulation
            time_horizon_days: Forecast period
        
        Returns:
            List of risk forecasts
        """
        forecasts: list[RiskForecast] = []
        
        for regulation in regulations:
            current_score = (current_compliance_scores or {}).get(regulation, 0.7)
            forecast = self._generate_risk_forecast(
                regulation, current_score, time_horizon_days
            )
            forecasts.append(forecast)
        
        logger.info(
            "risk_forecast_generated",
            regulations=regulations,
            horizon_days=time_horizon_days,
        )
        
        return forecasts
    
    async def assess_impact(
        self,
        regulation: str,
        organization_context: dict[str, Any],
    ) -> ImpactAssessment:
        """Assess the impact of a regulation on an organization.
        
        Args:
            regulation: The regulation to assess
            organization_context: Organization details (industry, size, data types, etc.)
        
        Returns:
            Impact assessment
        """
        assessment = self._generate_impact_assessment(regulation, organization_context)
        
        logger.info(
            "impact_assessment_generated",
            regulation=regulation,
            overall_impact=assessment.overall_impact_score,
        )
        
        return assessment
    
    async def project_timeline(
        self,
        regulation: str,
        target_date: datetime,
        current_progress: float,
        milestones: list[dict[str, Any]] | None = None,
    ) -> TimelineProjection:
        """Project compliance timeline.
        
        Args:
            regulation: Target regulation
            target_date: Target compliance date
            current_progress: Current compliance percentage (0-1)
            milestones: Existing milestones
        
        Returns:
            Timeline projection
        """
        projection = self._generate_timeline_projection(
            regulation, target_date, current_progress, milestones
        )
        
        logger.info(
            "timeline_projection_generated",
            regulation=regulation,
            on_track=projection.on_track,
        )
        
        return projection
    
    def _generate_sample_updates(
        self,
        domain: RegulatoryDomain | None,
        regulation: str | None,
        limit: int,
    ) -> list[RegulatoryUpdate]:
        """Generate sample regulatory updates."""
        updates: list[RegulatoryUpdate] = []
        now = datetime.now(timezone.utc)
        
        sample_updates = [
            {
                "title": "EU AI Act Enters Into Force",
                "description": "The EU AI Act officially entered into force, establishing comprehensive AI regulations.",
                "update_type": UpdateType.NEW_REGULATION,
                "domain": RegulatoryDomain.AI_ML,
                "regulation": "AI-Act",
                "impact_level": ImpactLevel.CRITICAL,
                "affected_industries": ["Technology", "Healthcare", "Finance", "Manufacturing"],
                "key_changes": [
                    "Prohibited AI practices defined",
                    "High-risk AI system requirements",
                    "Transparency obligations for AI systems",
                ],
            },
            {
                "title": "GDPR Enforcement Update - Cookie Consent",
                "description": "European DPAs issue coordinated enforcement on cookie consent practices.",
                "update_type": UpdateType.ENFORCEMENT_ACTION,
                "domain": RegulatoryDomain.DATA_PRIVACY,
                "regulation": "GDPR",
                "impact_level": ImpactLevel.HIGH,
                "affected_industries": ["Technology", "E-commerce", "Media"],
                "key_changes": [
                    "Stricter consent banner requirements",
                    "Dark patterns explicitly prohibited",
                    "Enhanced user choice mechanisms",
                ],
            },
            {
                "title": "HIPAA Right of Access Initiative Update",
                "description": "OCR announces new phase of Right of Access Initiative enforcement.",
                "update_type": UpdateType.ENFORCEMENT_ACTION,
                "domain": RegulatoryDomain.HEALTHCARE,
                "regulation": "HIPAA",
                "impact_level": ImpactLevel.MEDIUM,
                "affected_industries": ["Healthcare", "Insurance"],
                "key_changes": [
                    "Faster response times required",
                    "Lower fee caps for record requests",
                    "Electronic access prioritized",
                ],
            },
            {
                "title": "PCI DSS 4.0 Requirements Now Mandatory",
                "description": "All PCI DSS 4.0 requirements now mandatory, replacing 3.2.1.",
                "update_type": UpdateType.DEADLINE,
                "domain": RegulatoryDomain.FINANCE,
                "regulation": "PCI-DSS",
                "impact_level": ImpactLevel.HIGH,
                "affected_industries": ["Finance", "E-commerce", "Retail"],
                "key_changes": [
                    "Enhanced authentication requirements",
                    "New logging and monitoring standards",
                    "Customized approach validation option",
                ],
            },
            {
                "title": "California CPRA Enforcement Begins",
                "description": "California Privacy Rights Act full enforcement commences.",
                "update_type": UpdateType.ENFORCEMENT_ACTION,
                "domain": RegulatoryDomain.DATA_PRIVACY,
                "regulation": "CCPA/CPRA",
                "impact_level": ImpactLevel.HIGH,
                "affected_industries": ["Technology", "E-commerce", "Finance"],
                "key_changes": [
                    "Data minimization requirements",
                    "Sensitive data category protections",
                    "New opt-out requirements",
                ],
            },
        ]
        
        for i, update_data in enumerate(sample_updates[:limit]):
            if domain and update_data["domain"] != domain:
                continue
            if regulation and update_data["regulation"] != regulation:
                continue
            
            update = RegulatoryUpdate(
                title=update_data["title"],
                description=update_data["description"],
                update_type=update_data["update_type"],
                domain=update_data["domain"],
                regulation=update_data["regulation"],
                impact_level=update_data["impact_level"],
                affected_industries=update_data["affected_industries"],
                key_changes=update_data["key_changes"],
                announced_date=now - timedelta(days=i * 15),
                effective_date=now + timedelta(days=30 + i * 30),
                source="Regulatory Authority",
            )
            updates.append(update)
        
        return updates
    
    def _generate_predictions(
        self,
        domain: RegulatoryDomain | None,
        regulations: list[str] | None,
        time_horizon_days: int,
    ) -> list[RegulatoryPrediction]:
        """Generate regulatory predictions."""
        predictions: list[RegulatoryPrediction] = []
        now = datetime.now(timezone.utc)
        
        prediction_templates = [
            {
                "title": "Stricter AI Transparency Requirements",
                "description": "Expected regulatory guidance requiring detailed AI model documentation and explainability.",
                "domain": RegulatoryDomain.AI_ML,
                "affected_regulations": ["AI-Act", "GDPR"],
                "confidence": PredictionConfidence.HIGH,
                "confidence_score": 0.85,
                "predicted_impact": ImpactLevel.HIGH,
                "supporting_signals": [
                    "EU AI Act implementation timeline",
                    "Increased enforcement activity",
                    "Industry consultation outcomes",
                ],
                "preparation_actions": [
                    "Document AI model training data sources",
                    "Implement explainability tools",
                    "Conduct AI impact assessments",
                ],
            },
            {
                "title": "Enhanced Data Breach Notification Requirements",
                "description": "Predicted tightening of breach notification timelines and expanded notification scope.",
                "domain": RegulatoryDomain.DATA_PRIVACY,
                "affected_regulations": ["GDPR", "CCPA/CPRA", "State Privacy Laws"],
                "confidence": PredictionConfidence.MEDIUM,
                "confidence_score": 0.65,
                "predicted_impact": ImpactLevel.MEDIUM,
                "supporting_signals": [
                    "Recent large-scale breaches",
                    "Legislative proposals in multiple states",
                    "Regulatory statements",
                ],
                "preparation_actions": [
                    "Review incident response plans",
                    "Implement faster detection systems",
                    "Update notification templates",
                ],
            },
            {
                "title": "Healthcare AI Specific Regulations",
                "description": "Expected new guidance on AI/ML usage in clinical decision support systems.",
                "domain": RegulatoryDomain.HEALTHCARE,
                "affected_regulations": ["HIPAA", "FDA"],
                "confidence": PredictionConfidence.HIGH,
                "confidence_score": 0.78,
                "predicted_impact": ImpactLevel.HIGH,
                "supporting_signals": [
                    "FDA draft guidance released",
                    "OCR statements on AI",
                    "Industry coalition recommendations",
                ],
                "preparation_actions": [
                    "Audit clinical AI systems",
                    "Document algorithm training",
                    "Establish human oversight protocols",
                ],
            },
            {
                "title": "Supply Chain Security Requirements",
                "description": "Predicted mandatory software supply chain security requirements.",
                "domain": RegulatoryDomain.SECURITY,
                "affected_regulations": ["SOC2", "NIST", "Industry Standards"],
                "confidence": PredictionConfidence.HIGH,
                "confidence_score": 0.82,
                "predicted_impact": ImpactLevel.HIGH,
                "supporting_signals": [
                    "Executive orders on cybersecurity",
                    "SBOM requirements expanding",
                    "Major supply chain incidents",
                ],
                "preparation_actions": [
                    "Implement SBOM generation",
                    "Audit vendor security",
                    "Enhance dependency scanning",
                ],
            },
            {
                "title": "Children's Data Protection Expansion",
                "description": "Expected new or expanded regulations for children's data protection.",
                "domain": RegulatoryDomain.DATA_PRIVACY,
                "affected_regulations": ["COPPA", "State Laws", "GDPR"],
                "confidence": PredictionConfidence.MEDIUM,
                "confidence_score": 0.60,
                "predicted_impact": ImpactLevel.MEDIUM,
                "supporting_signals": [
                    "State legislative activity",
                    "FTC enforcement trends",
                    "Public advocacy pressure",
                ],
                "preparation_actions": [
                    "Review age verification methods",
                    "Audit data collection practices",
                    "Update privacy notices",
                ],
            },
        ]
        
        for template in prediction_templates:
            if domain and template["domain"] != domain:
                continue
            
            if regulations:
                if not any(r in template["affected_regulations"] for r in regulations):
                    continue
            
            days_offset = random.randint(60, min(time_horizon_days, 300))
            
            prediction = RegulatoryPrediction(
                title=template["title"],
                description=template["description"],
                domain=template["domain"],
                confidence=template["confidence"],
                confidence_score=template["confidence_score"],
                predicted_impact=template["predicted_impact"],
                affected_regulations=template["affected_regulations"],
                supporting_signals=template["supporting_signals"],
                preparation_actions=template["preparation_actions"],
                predicted_date_range_start=now + timedelta(days=days_offset),
                predicted_date_range_end=now + timedelta(days=days_offset + 90),
            )
            predictions.append(prediction)
        
        return predictions
    
    def _generate_trends(
        self,
        domain: RegulatoryDomain | None,
        regulations: list[str] | None,
        lookback_days: int,
    ) -> list[ComplianceTrend]:
        """Generate compliance trends."""
        trends: list[ComplianceTrend] = []
        now = datetime.now(timezone.utc)
        
        trend_templates = [
            {
                "name": "Data Privacy Enforcement Intensity",
                "description": "Trend in regulatory enforcement actions for data privacy violations",
                "domain": RegulatoryDomain.DATA_PRIVACY,
                "direction": "increasing",
                "strength": 0.75,
                "key_drivers": [
                    "Increased regulatory budgets",
                    "High-profile breaches",
                    "Maturing regulatory frameworks",
                ],
                "potential_impacts": [
                    "Higher fine amounts",
                    "More frequent audits",
                    "Greater C-suite accountability",
                ],
            },
            {
                "name": "AI Regulation Development",
                "description": "Trend in AI-specific regulatory requirements",
                "domain": RegulatoryDomain.AI_ML,
                "direction": "increasing",
                "strength": 0.90,
                "key_drivers": [
                    "EU AI Act implementation",
                    "AI safety concerns",
                    "Rapid AI adoption",
                ],
                "potential_impacts": [
                    "New compliance requirements",
                    "AI system audits",
                    "Documentation mandates",
                ],
            },
            {
                "name": "Healthcare Data Security Focus",
                "description": "Trend in healthcare data protection enforcement",
                "domain": RegulatoryDomain.HEALTHCARE,
                "direction": "stable",
                "strength": 0.60,
                "key_drivers": [
                    "Telehealth expansion",
                    "Ransomware attacks",
                    "Data interoperability push",
                ],
                "potential_impacts": [
                    "Enhanced security requirements",
                    "Faster breach response",
                    "Cloud security guidance",
                ],
            },
        ]
        
        for template in trend_templates:
            if domain and template["domain"] != domain:
                continue
            
            # Generate data points
            data_points = []
            for i in range(12):  # Monthly data points
                date = now - timedelta(days=lookback_days - i * 30)
                base_value = 50 + i * 3 if template["direction"] == "increasing" else 50
                value = base_value + random.randint(-5, 5)
                data_points.append({
                    "date": date.isoformat(),
                    "value": value,
                })
            
            # Generate projections
            projected_values = []
            for i in range(6):  # 6-month projection
                date = now + timedelta(days=i * 30)
                last_value = data_points[-1]["value"]
                if template["direction"] == "increasing":
                    projected = last_value + i * 3 + random.randint(-2, 2)
                else:
                    projected = last_value + random.randint(-3, 3)
                projected_values.append({
                    "date": date.isoformat(),
                    "value": projected,
                    "confidence_interval": [projected - 5, projected + 5],
                })
            
            trend = ComplianceTrend(
                name=template["name"],
                description=template["description"],
                domain=template["domain"],
                direction=template["direction"],
                strength=template["strength"],
                data_points=data_points,
                projected_values=projected_values,
                key_drivers=template["key_drivers"],
                potential_impacts=template["potential_impacts"],
                start_date=now - timedelta(days=lookback_days),
                end_date=now,
            )
            trends.append(trend)
        
        return trends
    
    def _generate_risk_forecast(
        self,
        regulation: str,
        current_score: float,
        time_horizon_days: int,
    ) -> RiskForecast:
        """Generate a risk forecast for a regulation."""
        # Simulate risk factors based on regulatory signals
        signals = REGULATORY_SIGNALS.get(regulation, {})
        enforcement_trend = signals.get("recent_enforcement_trend", "stable")
        
        # Calculate projected risk
        if enforcement_trend == "increasing":
            risk_change = random.uniform(0.05, 0.15)
        elif enforcement_trend == "new":
            risk_change = random.uniform(0.10, 0.25)
        else:
            risk_change = random.uniform(-0.05, 0.05)
        
        current_risk = 1 - current_score
        projected_risk = min(1.0, current_risk + risk_change)
        
        return RiskForecast(
            title=f"{regulation} Compliance Risk Forecast",
            description=f"Risk forecast for {regulation} compliance over next {time_horizon_days} days",
            current_risk_score=round(current_risk * 100, 1),
            projected_risk_score=round(projected_risk * 100, 1),
            risk_change_percent=round(risk_change * 100, 1),
            regulations=[regulation],
            forecast_period_days=time_horizon_days,
            risk_factors=[
                {"factor": "Enforcement trend", "impact": enforcement_trend, "weight": 0.3},
                {"factor": "Regulatory updates pending", "impact": len(signals.get("pending_updates", [])), "weight": 0.3},
                {"factor": "Current compliance gap", "impact": round((1 - current_score) * 100, 1), "weight": 0.4},
            ],
            mitigating_factors=[
                {"factor": "Existing compliance program", "impact": "reduces_risk", "weight": 0.2},
                {"factor": "Recent audit completion", "impact": "reduces_risk", "weight": 0.1},
            ],
            mitigation_actions=[
                f"Review {regulation} compliance controls",
                "Update risk assessment documentation",
                "Schedule compliance audit",
                "Train staff on recent updates",
            ],
            confidence=PredictionConfidence.MEDIUM if enforcement_trend == "stable" else PredictionConfidence.HIGH,
        )
    
    def _generate_impact_assessment(
        self,
        regulation: str,
        organization_context: dict[str, Any],
    ) -> ImpactAssessment:
        """Generate an impact assessment."""
        industry = organization_context.get("industry", "technology")
        data_types = organization_context.get("data_types", ["PII"])
        company_size = organization_context.get("size", "medium")
        
        # Calculate impact scores
        base_impact = 0.5
        
        # Adjust for data types
        if "PHI" in data_types:
            base_impact += 0.2
        if "PCI" in data_types:
            base_impact += 0.15
        if "PII" in data_types:
            base_impact += 0.1
        
        # Adjust for company size
        size_multiplier = {"small": 0.7, "medium": 1.0, "large": 1.3}.get(company_size, 1.0)
        
        overall_impact = min(1.0, base_impact * size_multiplier)
        
        # Estimate effort
        base_hours = 200
        effort_hours = int(base_hours * overall_impact * size_multiplier)
        cost_per_hour = 150
        estimated_cost = effort_hours * cost_per_hour
        
        return ImpactAssessment(
            regulation=regulation,
            organization_context=organization_context,
            overall_impact_score=round(overall_impact, 2),
            technical_impact_score=round(overall_impact * 0.9, 2),
            operational_impact_score=round(overall_impact * 0.8, 2),
            financial_impact_score=round(overall_impact * 0.7, 2),
            affected_systems=["Data storage", "User authentication", "Logging systems"],
            affected_processes=["Data collection", "User consent", "Data retention"],
            affected_data_types=data_types,
            estimated_effort_hours=effort_hours,
            estimated_cost_usd=estimated_cost,
            current_compliance_level=0.6,
            target_compliance_level=1.0,
            gaps=[
                {"area": "Documentation", "gap_size": 0.3, "priority": "high"},
                {"area": "Technical controls", "gap_size": 0.2, "priority": "medium"},
                {"area": "Training", "gap_size": 0.15, "priority": "medium"},
            ],
            remediation_steps=[
                {"step": 1, "description": "Gap assessment", "effort_hours": effort_hours * 0.1},
                {"step": 2, "description": "Policy updates", "effort_hours": effort_hours * 0.2},
                {"step": 3, "description": "Technical implementation", "effort_hours": effort_hours * 0.4},
                {"step": 4, "description": "Training", "effort_hours": effort_hours * 0.15},
                {"step": 5, "description": "Audit and validation", "effort_hours": effort_hours * 0.15},
            ],
        )
    
    def _generate_timeline_projection(
        self,
        regulation: str,
        target_date: datetime,
        current_progress: float,
        milestones: list[dict[str, Any]] | None,
    ) -> TimelineProjection:
        """Generate a timeline projection."""
        now = datetime.now(timezone.utc)
        days_remaining = (target_date - now).days
        
        # Calculate projected completion
        if current_progress <= 0:
            current_progress = 0.1
        
        remaining_progress = 1.0 - current_progress
        days_needed = int(remaining_progress * days_remaining / current_progress * 1.2)  # Add buffer
        
        projected_completion = now + timedelta(days=days_needed)
        on_track = projected_completion <= target_date
        days_ahead_behind = (target_date - projected_completion).days
        
        # Calculate risk
        risk_of_missing = 0.0
        if not on_track:
            risk_of_missing = min(1.0, abs(days_ahead_behind) / 30 * 0.2)
        
        # Generate milestones if not provided
        if not milestones:
            milestones = [
                {
                    "name": "Planning Complete",
                    "target_date": (now + timedelta(days=days_remaining * 0.1)).isoformat(),
                    "status": "completed" if current_progress > 0.1 else "in_progress",
                },
                {
                    "name": "Technical Implementation",
                    "target_date": (now + timedelta(days=days_remaining * 0.5)).isoformat(),
                    "status": "completed" if current_progress > 0.5 else "pending",
                },
                {
                    "name": "Testing Complete",
                    "target_date": (now + timedelta(days=days_remaining * 0.8)).isoformat(),
                    "status": "pending",
                },
                {
                    "name": "Full Compliance",
                    "target_date": target_date.isoformat(),
                    "status": "pending",
                },
            ]
        
        return TimelineProjection(
            regulation=regulation,
            target_compliance_date=target_date,
            current_compliance_percent=round(current_progress * 100, 1),
            milestones=milestones,
            projected_completion_date=projected_completion,
            on_track=on_track,
            days_ahead_behind=days_ahead_behind,
            risk_of_missing_deadline=round(risk_of_missing, 2),
            acceleration_options=[
                "Increase team allocation",
                "Prioritize critical controls",
                "Engage external consultants",
                "Automate manual processes",
            ] if not on_track else [],
        )


# Global singleton
_prediction_engine: RegulatoryPredictionEngine | None = None


def get_prediction_engine() -> RegulatoryPredictionEngine:
    """Get the global prediction engine instance."""
    global _prediction_engine
    if _prediction_engine is None:
        _prediction_engine = RegulatoryPredictionEngine()
    return _prediction_engine
