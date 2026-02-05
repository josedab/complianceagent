"""Data models for AI Model Card Generator."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AIRiskLevel(str, Enum):
    """EU AI Act risk classification levels."""
    
    UNACCEPTABLE = "unacceptable"  # Banned
    HIGH = "high"  # Requires conformity assessment
    LIMITED = "limited"  # Transparency obligations
    MINIMAL = "minimal"  # No specific requirements


class AISystemCategory(str, Enum):
    """Categories of AI systems per EU AI Act."""
    
    # High-risk categories (Annex III)
    BIOMETRIC_ID = "biometric_identification"
    CRITICAL_INFRASTRUCTURE = "critical_infrastructure"
    EDUCATION_TRAINING = "education_training"
    EMPLOYMENT = "employment"
    ESSENTIAL_SERVICES = "essential_services"
    LAW_ENFORCEMENT = "law_enforcement"
    MIGRATION_ASYLUM = "migration_asylum"
    JUSTICE = "justice"
    DEMOCRATIC_PROCESS = "democratic_process"
    
    # Limited risk
    CHATBOT = "chatbot"
    EMOTION_RECOGNITION = "emotion_recognition"
    DEEPFAKE = "deepfake"
    
    # Minimal risk
    SPAM_FILTER = "spam_filter"
    RECOMMENDATION = "recommendation"
    SEARCH = "search"
    GAME_AI = "game_ai"
    
    # General purpose
    GENERAL_PURPOSE = "general_purpose"
    FOUNDATION_MODEL = "foundation_model"


class ModelType(str, Enum):
    """Types of ML models."""
    
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    NLP = "nlp"
    COMPUTER_VISION = "computer_vision"
    RECOMMENDATION = "recommendation"
    GENERATIVE = "generative"
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    TIME_SERIES = "time_series"
    ANOMALY_DETECTION = "anomaly_detection"
    FOUNDATION_MODEL = "foundation_model"


class BiasCategory(str, Enum):
    """Categories of potential bias."""
    
    GENDER = "gender"
    AGE = "age"
    RACE = "race"
    ETHNICITY = "ethnicity"
    RELIGION = "religion"
    DISABILITY = "disability"
    SOCIOECONOMIC = "socioeconomic"
    GEOGRAPHIC = "geographic"
    LANGUAGE = "language"


class ModelPerformanceMetrics(BaseModel):
    """Model performance metrics."""
    
    accuracy: float | None = None
    precision: float | None = None
    recall: float | None = None
    f1_score: float | None = None
    auc_roc: float | None = None
    mse: float | None = None
    rmse: float | None = None
    mae: float | None = None
    r_squared: float | None = None
    
    # Custom metrics
    custom_metrics: dict[str, float] = Field(default_factory=dict)
    
    # Confidence intervals
    confidence_level: float = 0.95
    accuracy_ci: tuple[float, float] | None = None
    
    # Performance by segment
    segment_performance: dict[str, dict[str, float]] = Field(default_factory=dict)


class FairnessMetrics(BaseModel):
    """Fairness and bias metrics."""
    
    # Demographic parity
    demographic_parity: dict[str, float] = Field(default_factory=dict)
    
    # Equalized odds
    equalized_odds: dict[str, float] = Field(default_factory=dict)
    
    # Disparate impact ratio
    disparate_impact: dict[str, float] = Field(default_factory=dict)
    
    # Statistical parity difference
    statistical_parity_diff: dict[str, float] = Field(default_factory=dict)
    
    # Bias detected
    bias_detected: list[BiasCategory] = Field(default_factory=list)
    bias_severity: dict[str, str] = Field(default_factory=dict)  # category -> low/medium/high
    
    # Mitigation applied
    mitigation_techniques: list[str] = Field(default_factory=list)


class ModelLimitations(BaseModel):
    """Known limitations of the model."""
    
    # Technical limitations
    technical_limitations: list[str] = Field(default_factory=list)
    
    # Out-of-scope uses
    out_of_scope_uses: list[str] = Field(default_factory=list)
    
    # Known failure modes
    failure_modes: list[str] = Field(default_factory=list)
    
    # Edge cases
    edge_cases: list[str] = Field(default_factory=list)
    
    # Environmental limitations
    environmental_constraints: list[str] = Field(default_factory=list)
    
    # Data limitations
    data_limitations: list[str] = Field(default_factory=list)


class IntendedUse(BaseModel):
    """Intended use documentation."""
    
    primary_uses: list[str] = Field(default_factory=list)
    primary_users: list[str] = Field(default_factory=list)
    
    # Use case details
    use_case_description: str | None = None
    deployment_context: str | None = None
    
    # Human oversight
    human_oversight_required: bool = True
    oversight_description: str | None = None
    
    # Prohibited uses
    prohibited_uses: list[str] = Field(default_factory=list)
    
    # Geographic scope
    geographic_scope: list[str] = Field(default_factory=list)
    
    # User requirements
    user_requirements: list[str] = Field(default_factory=list)


class TrainingData(BaseModel):
    """Training data documentation."""
    
    # Data sources
    data_sources: list[str] = Field(default_factory=list)
    
    # Data collection
    collection_method: str | None = None
    collection_date_range: str | None = None
    
    # Data size
    total_samples: int | None = None
    training_samples: int | None = None
    validation_samples: int | None = None
    test_samples: int | None = None
    
    # Demographics
    demographic_breakdown: dict[str, dict[str, float]] = Field(default_factory=dict)
    
    # Data quality
    preprocessing_steps: list[str] = Field(default_factory=list)
    data_cleaning: list[str] = Field(default_factory=list)
    
    # Labeling
    labeling_method: str | None = None
    labeler_demographics: str | None = None
    inter_annotator_agreement: float | None = None
    
    # Privacy
    contains_pii: bool = False
    pii_handling: str | None = None
    anonymization_techniques: list[str] = Field(default_factory=list)
    
    # Consent
    consent_obtained: bool = False
    consent_details: str | None = None


class EvaluationData(BaseModel):
    """Evaluation data documentation."""
    
    # Evaluation datasets
    datasets_used: list[str] = Field(default_factory=list)
    
    # Evaluation methodology
    methodology: str | None = None
    
    # Split information
    train_test_split: str | None = None
    cross_validation: bool = False
    cv_folds: int | None = None
    
    # Benchmark comparisons
    benchmark_results: dict[str, float] = Field(default_factory=dict)
    
    # Evaluation date
    evaluation_date: datetime | None = None


class EthicalConsiderations(BaseModel):
    """Ethical considerations documentation."""
    
    # Ethical review
    ethics_review_conducted: bool = False
    ethics_review_body: str | None = None
    ethics_approval_date: datetime | None = None
    
    # Identified risks
    ethical_risks: list[str] = Field(default_factory=list)
    
    # Mitigation strategies
    risk_mitigations: list[str] = Field(default_factory=list)
    
    # Stakeholder impact
    affected_stakeholders: list[str] = Field(default_factory=list)
    stakeholder_engagement: str | None = None
    
    # Environmental impact
    carbon_footprint: str | None = None
    energy_consumption: str | None = None
    
    # Social impact
    societal_impact_assessment: str | None = None
    
    # Human rights considerations
    human_rights_assessment: str | None = None


class RegulatoryCompliance(BaseModel):
    """Regulatory compliance documentation."""
    
    # EU AI Act
    eu_ai_act_risk_level: AIRiskLevel | None = None
    eu_ai_act_category: AISystemCategory | None = None
    conformity_assessment_required: bool = False
    conformity_assessment_completed: bool = False
    ce_marking: bool = False
    
    # EU AI Act specific requirements
    transparency_obligations_met: bool = False
    human_oversight_implemented: bool = False
    accuracy_robustness_cybersecurity: bool = False
    risk_management_system: bool = False
    technical_documentation: bool = False
    record_keeping: bool = False
    registration_database: bool = False
    
    # GDPR
    gdpr_compliant: bool = False
    dpia_conducted: bool = False
    legal_basis: str | None = None
    
    # Sector-specific
    sector_regulations: list[str] = Field(default_factory=list)
    sector_compliance: dict[str, bool] = Field(default_factory=dict)
    
    # Audits
    last_audit_date: datetime | None = None
    next_audit_date: datetime | None = None
    audit_findings: list[str] = Field(default_factory=list)


class ModelCard(BaseModel):
    """Complete AI Model Card."""
    
    id: UUID = Field(default_factory=uuid4)
    
    # Basic information
    model_name: str
    model_version: str
    model_type: ModelType
    organization_id: UUID | None = None
    
    # Description
    description: str
    short_description: str | None = None
    
    # Developers
    developers: list[str] = Field(default_factory=list)
    contact_info: str | None = None
    
    # Dates
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    training_date: datetime | None = None
    
    # License
    license: str | None = None
    license_url: str | None = None
    
    # Framework
    framework: str | None = None  # e.g., "PyTorch", "TensorFlow"
    framework_version: str | None = None
    
    # Model architecture
    architecture: str | None = None
    parameters_count: int | None = None
    
    # Documentation sections
    intended_use: IntendedUse = Field(default_factory=IntendedUse)
    training_data: TrainingData = Field(default_factory=TrainingData)
    evaluation_data: EvaluationData = Field(default_factory=EvaluationData)
    performance: ModelPerformanceMetrics = Field(default_factory=ModelPerformanceMetrics)
    fairness: FairnessMetrics = Field(default_factory=FairnessMetrics)
    limitations: ModelLimitations = Field(default_factory=ModelLimitations)
    ethical_considerations: EthicalConsiderations = Field(default_factory=EthicalConsiderations)
    regulatory: RegulatoryCompliance = Field(default_factory=RegulatoryCompliance)
    
    # Additional documentation
    additional_info: dict[str, Any] = Field(default_factory=dict)
    references: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    
    # Status
    status: str = "draft"  # draft, review, approved, published
    approved_by: str | None = None
    approved_at: datetime | None = None
    
    def get_compliance_score(self) -> float:
        """Calculate compliance score based on documentation completeness."""
        score = 0
        max_score = 100
        
        # Basic info (20 points)
        if self.description:
            score += 5
        if self.developers:
            score += 5
        if self.architecture:
            score += 5
        if self.license:
            score += 5
        
        # Intended use (15 points)
        if self.intended_use.primary_uses:
            score += 5
        if self.intended_use.prohibited_uses:
            score += 5
        if self.intended_use.human_oversight_required is not None:
            score += 5
        
        # Training data (15 points)
        if self.training_data.data_sources:
            score += 5
        if self.training_data.total_samples:
            score += 5
        if self.training_data.pii_handling or not self.training_data.contains_pii:
            score += 5
        
        # Performance (15 points)
        if self.performance.accuracy is not None:
            score += 5
        if self.performance.segment_performance:
            score += 5
        if self.performance.custom_metrics:
            score += 5
        
        # Fairness (15 points)
        if self.fairness.demographic_parity or self.fairness.disparate_impact:
            score += 10
        if self.fairness.mitigation_techniques:
            score += 5
        
        # Limitations (10 points)
        if self.limitations.technical_limitations:
            score += 5
        if self.limitations.out_of_scope_uses:
            score += 5
        
        # Regulatory (10 points)
        if self.regulatory.eu_ai_act_risk_level:
            score += 5
        if self.regulatory.conformity_assessment_completed or not self.regulatory.conformity_assessment_required:
            score += 5
        
        return min(score, max_score)


# ============================================================================
# EU AI Act Classification Rules
# ============================================================================

# High-risk AI systems (Article 6 + Annex III)
HIGH_RISK_CATEGORIES = [
    AISystemCategory.BIOMETRIC_ID,
    AISystemCategory.CRITICAL_INFRASTRUCTURE,
    AISystemCategory.EDUCATION_TRAINING,
    AISystemCategory.EMPLOYMENT,
    AISystemCategory.ESSENTIAL_SERVICES,
    AISystemCategory.LAW_ENFORCEMENT,
    AISystemCategory.MIGRATION_ASYLUM,
    AISystemCategory.JUSTICE,
    AISystemCategory.DEMOCRATIC_PROCESS,
]

# Prohibited AI practices (Article 5)
PROHIBITED_PRACTICES = [
    "Subliminal manipulation causing harm",
    "Exploiting vulnerabilities (age, disability) causing harm",
    "Social scoring by public authorities",
    "Real-time biometric identification in public spaces for law enforcement (with exceptions)",
    "Biometric categorization based on sensitive attributes",
    "Emotion recognition in workplace/education (with exceptions)",
    "Facial recognition databases from untargeted scraping",
    "Predictive policing based solely on profiling",
]

# Transparency requirements (Article 52)
TRANSPARENCY_REQUIREMENTS = {
    AISystemCategory.CHATBOT: "Must inform users they are interacting with AI",
    AISystemCategory.EMOTION_RECOGNITION: "Must inform subjects of the system's operation",
    AISystemCategory.DEEPFAKE: "Must label content as artificially generated or manipulated",
}

# High-risk system requirements (Chapter 2)
HIGH_RISK_REQUIREMENTS = [
    "Risk management system (Article 9)",
    "Data governance (Article 10)",
    "Technical documentation (Article 11)",
    "Record-keeping (Article 12)",
    "Transparency and information to users (Article 13)",
    "Human oversight (Article 14)",
    "Accuracy, robustness and cybersecurity (Article 15)",
    "Quality management system (Article 17)",
    "Conformity assessment (Article 43)",
    "EU database registration (Article 49)",
]
