"""Models for regulatory prediction engine."""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class PredictionConfidence(str, Enum):
    """Confidence levels for predictions."""
    
    VERY_HIGH = "very_high"  # 90%+
    HIGH = "high"            # 75-89%
    MEDIUM = "medium"        # 50-74%
    LOW = "low"              # 25-49%
    VERY_LOW = "very_low"    # <25%


class RegulatoryDomain(str, Enum):
    """Regulatory domains."""
    
    DATA_PRIVACY = "data_privacy"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    SECURITY = "security"
    AI_ML = "ai_ml"
    ENVIRONMENTAL = "environmental"
    LABOR = "labor"
    CONSUMER = "consumer"


class UpdateType(str, Enum):
    """Types of regulatory updates."""
    
    NEW_REGULATION = "new_regulation"
    AMENDMENT = "amendment"
    ENFORCEMENT_ACTION = "enforcement_action"
    GUIDANCE = "guidance"
    DEADLINE = "deadline"
    COURT_RULING = "court_ruling"
    STANDARD_UPDATE = "standard_update"


class ImpactLevel(str, Enum):
    """Impact levels for regulatory changes."""
    
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


@dataclass
class RegulatoryUpdate:
    """A regulatory update or change."""
    
    id: UUID = field(default_factory=uuid4)
    
    # Update details
    title: str = ""
    description: str = ""
    update_type: UpdateType = UpdateType.NEW_REGULATION
    
    # Source
    source: str = ""
    source_url: str = ""
    jurisdiction: str = ""
    
    # Regulatory context
    domain: RegulatoryDomain = RegulatoryDomain.DATA_PRIVACY
    regulation: str = ""
    related_regulations: list[str] = field(default_factory=list)
    
    # Timing
    announced_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    effective_date: datetime | None = None
    compliance_deadline: datetime | None = None
    
    # Impact
    impact_level: ImpactLevel = ImpactLevel.MEDIUM
    affected_industries: list[str] = field(default_factory=list)
    affected_regions: list[str] = field(default_factory=list)
    
    # Analysis
    key_changes: list[str] = field(default_factory=list)
    required_actions: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "update_type": self.update_type.value,
            "source": self.source,
            "source_url": self.source_url,
            "jurisdiction": self.jurisdiction,
            "domain": self.domain.value,
            "regulation": self.regulation,
            "related_regulations": self.related_regulations,
            "announced_date": self.announced_date.isoformat(),
            "effective_date": self.effective_date.isoformat() if self.effective_date else None,
            "compliance_deadline": self.compliance_deadline.isoformat() if self.compliance_deadline else None,
            "impact_level": self.impact_level.value,
            "affected_industries": self.affected_industries,
            "affected_regions": self.affected_regions,
            "key_changes": self.key_changes,
            "required_actions": self.required_actions,
        }


@dataclass
class RegulatoryPrediction:
    """A prediction for upcoming regulatory changes."""
    
    id: UUID = field(default_factory=uuid4)
    
    # Prediction details
    title: str = ""
    description: str = ""
    domain: RegulatoryDomain = RegulatoryDomain.DATA_PRIVACY
    
    # Prediction metadata
    confidence: PredictionConfidence = PredictionConfidence.MEDIUM
    confidence_score: float = 0.5
    
    # Timing prediction
    predicted_date_range_start: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=90)
    )
    predicted_date_range_end: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=180)
    )
    
    # Impact prediction
    predicted_impact: ImpactLevel = ImpactLevel.MEDIUM
    
    # Affected areas
    affected_regulations: list[str] = field(default_factory=list)
    affected_industries: list[str] = field(default_factory=list)
    affected_regions: list[str] = field(default_factory=list)
    
    # Evidence
    supporting_signals: list[str] = field(default_factory=list)
    source_references: list[str] = field(default_factory=list)
    
    # Recommended preparations
    preparation_actions: list[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=365)
    )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "domain": self.domain.value,
            "confidence": self.confidence.value,
            "confidence_score": self.confidence_score,
            "predicted_date_range": {
                "start": self.predicted_date_range_start.isoformat(),
                "end": self.predicted_date_range_end.isoformat(),
            },
            "predicted_impact": self.predicted_impact.value,
            "affected_regulations": self.affected_regulations,
            "affected_industries": self.affected_industries,
            "affected_regions": self.affected_regions,
            "supporting_signals": self.supporting_signals,
            "source_references": self.source_references,
            "preparation_actions": self.preparation_actions,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
        }


@dataclass
class ComplianceTrend:
    """A compliance trend analysis."""
    
    id: UUID = field(default_factory=uuid4)
    
    # Trend details
    name: str = ""
    description: str = ""
    domain: RegulatoryDomain = RegulatoryDomain.DATA_PRIVACY
    
    # Trend direction
    direction: str = "increasing"  # increasing, decreasing, stable
    strength: float = 0.5  # 0-1
    
    # Time series data
    data_points: list[dict[str, Any]] = field(default_factory=list)
    
    # Projections
    projected_values: list[dict[str, Any]] = field(default_factory=list)
    
    # Analysis
    key_drivers: list[str] = field(default_factory=list)
    potential_impacts: list[str] = field(default_factory=list)
    
    # Time range
    start_date: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc) - timedelta(days=365)
    )
    end_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "domain": self.domain.value,
            "direction": self.direction,
            "strength": self.strength,
            "data_points": self.data_points,
            "projected_values": self.projected_values,
            "key_drivers": self.key_drivers,
            "potential_impacts": self.potential_impacts,
            "time_range": {
                "start": self.start_date.isoformat(),
                "end": self.end_date.isoformat(),
            },
        }


@dataclass
class RiskForecast:
    """A compliance risk forecast."""
    
    id: UUID = field(default_factory=uuid4)
    
    # Risk details
    title: str = ""
    description: str = ""
    
    # Risk assessment
    current_risk_score: float = 0.0
    projected_risk_score: float = 0.0
    risk_change_percent: float = 0.0
    
    # Risk factors
    risk_factors: list[dict[str, Any]] = field(default_factory=list)
    mitigating_factors: list[dict[str, Any]] = field(default_factory=list)
    
    # Affected regulations
    regulations: list[str] = field(default_factory=list)
    
    # Time horizon
    forecast_period_days: int = 90
    
    # Recommendations
    mitigation_actions: list[str] = field(default_factory=list)
    
    # Confidence
    confidence: PredictionConfidence = PredictionConfidence.MEDIUM
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "current_risk_score": self.current_risk_score,
            "projected_risk_score": self.projected_risk_score,
            "risk_change_percent": self.risk_change_percent,
            "risk_factors": self.risk_factors,
            "mitigating_factors": self.mitigating_factors,
            "regulations": self.regulations,
            "forecast_period_days": self.forecast_period_days,
            "mitigation_actions": self.mitigation_actions,
            "confidence": self.confidence.value,
        }


@dataclass
class ImpactAssessment:
    """Assessment of regulatory impact on an organization."""
    
    id: UUID = field(default_factory=uuid4)
    
    # Target
    regulation: str = ""
    organization_context: dict[str, Any] = field(default_factory=dict)
    
    # Impact scores
    overall_impact_score: float = 0.0
    technical_impact_score: float = 0.0
    operational_impact_score: float = 0.0
    financial_impact_score: float = 0.0
    
    # Detailed impacts
    affected_systems: list[str] = field(default_factory=list)
    affected_processes: list[str] = field(default_factory=list)
    affected_data_types: list[str] = field(default_factory=list)
    
    # Effort estimation
    estimated_effort_hours: int = 0
    estimated_cost_usd: int = 0
    
    # Gap analysis
    current_compliance_level: float = 0.0
    target_compliance_level: float = 1.0
    gaps: list[dict[str, Any]] = field(default_factory=list)
    
    # Remediation plan
    remediation_steps: list[dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "regulation": self.regulation,
            "organization_context": self.organization_context,
            "impact_scores": {
                "overall": self.overall_impact_score,
                "technical": self.technical_impact_score,
                "operational": self.operational_impact_score,
                "financial": self.financial_impact_score,
            },
            "affected_areas": {
                "systems": self.affected_systems,
                "processes": self.affected_processes,
                "data_types": self.affected_data_types,
            },
            "effort_estimation": {
                "hours": self.estimated_effort_hours,
                "cost_usd": self.estimated_cost_usd,
            },
            "gap_analysis": {
                "current_level": self.current_compliance_level,
                "target_level": self.target_compliance_level,
                "gaps": self.gaps,
            },
            "remediation_steps": self.remediation_steps,
        }


@dataclass
class TimelineProjection:
    """Timeline projection for regulatory compliance."""
    
    id: UUID = field(default_factory=uuid4)
    
    # Context
    regulation: str = ""
    target_compliance_date: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=180)
    )
    
    # Current state
    current_compliance_percent: float = 0.0
    
    # Milestones
    milestones: list[dict[str, Any]] = field(default_factory=list)
    
    # Projections
    projected_completion_date: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=180)
    )
    on_track: bool = True
    days_ahead_behind: int = 0
    
    # Risk assessment
    risk_of_missing_deadline: float = 0.0
    
    # Recommendations
    acceleration_options: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "regulation": self.regulation,
            "target_compliance_date": self.target_compliance_date.isoformat(),
            "current_compliance_percent": self.current_compliance_percent,
            "milestones": self.milestones,
            "projected_completion_date": self.projected_completion_date.isoformat(),
            "on_track": self.on_track,
            "days_ahead_behind": self.days_ahead_behind,
            "risk_of_missing_deadline": self.risk_of_missing_deadline,
            "acceleration_options": self.acceleration_options,
        }
