"""AI Model Card Generator for EU AI Act compliance."""

import json
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import structlog

from app.services.model_cards.models import (
    AIRiskLevel,
    AISystemCategory,
    ModelType,
    BiasCategory,
    ModelCard,
    ModelPerformanceMetrics,
    FairnessMetrics,
    ModelLimitations,
    IntendedUse,
    TrainingData,
    EvaluationData,
    EthicalConsiderations,
    RegulatoryCompliance,
    HIGH_RISK_CATEGORIES,
    PROHIBITED_PRACTICES,
    TRANSPARENCY_REQUIREMENTS,
    HIGH_RISK_REQUIREMENTS,
)

logger = structlog.get_logger()


class ModelCardGenerator:
    """Generates and manages AI Model Cards for EU AI Act compliance."""
    
    def __init__(self) -> None:
        self._model_cards: dict[UUID, ModelCard] = {}
    
    async def create_model_card(
        self,
        model_name: str,
        model_version: str,
        model_type: ModelType,
        description: str,
        organization_id: UUID | None = None,
        **kwargs: Any,
    ) -> ModelCard:
        """Create a new model card."""
        card = ModelCard(
            model_name=model_name,
            model_version=model_version,
            model_type=model_type,
            description=description,
            organization_id=organization_id,
            **kwargs,
        )
        
        self._model_cards[card.id] = card
        return card
    
    async def get_model_card(self, card_id: UUID) -> ModelCard | None:
        """Get a model card by ID."""
        return self._model_cards.get(card_id)
    
    async def list_model_cards(
        self,
        organization_id: UUID | None = None,
    ) -> list[ModelCard]:
        """List model cards, optionally filtered by organization."""
        cards = list(self._model_cards.values())
        if organization_id:
            cards = [c for c in cards if c.organization_id == organization_id]
        return cards
    
    async def update_model_card(
        self,
        card_id: UUID,
        updates: dict[str, Any],
    ) -> ModelCard | None:
        """Update a model card."""
        card = self._model_cards.get(card_id)
        if not card:
            return None
        
        for key, value in updates.items():
            if hasattr(card, key):
                setattr(card, key, value)
        
        card.updated_at = datetime.utcnow()
        return card
    
    async def classify_ai_risk(
        self,
        card: ModelCard,
        use_case_description: str | None = None,
    ) -> dict[str, Any]:
        """Classify AI system risk level per EU AI Act."""
        # Check for prohibited practices
        prohibited = self._check_prohibited_practices(card, use_case_description)
        if prohibited:
            return {
                "risk_level": AIRiskLevel.UNACCEPTABLE,
                "category": None,
                "prohibited_practice": prohibited,
                "requirements": [],
                "can_deploy": False,
                "reason": f"This AI system involves a prohibited practice: {prohibited}",
            }
        
        # Determine category and risk level
        category = self._determine_category(card, use_case_description)
        risk_level = self._determine_risk_level(category)
        
        # Get requirements
        requirements = self._get_requirements(risk_level, category)
        
        # Update card
        card.regulatory.eu_ai_act_risk_level = risk_level
        card.regulatory.eu_ai_act_category = category
        card.regulatory.conformity_assessment_required = risk_level == AIRiskLevel.HIGH
        
        return {
            "risk_level": risk_level,
            "category": category,
            "prohibited_practice": None,
            "requirements": requirements,
            "can_deploy": True,
            "conformity_assessment_required": risk_level == AIRiskLevel.HIGH,
            "transparency_requirements": TRANSPARENCY_REQUIREMENTS.get(category),
        }
    
    def _check_prohibited_practices(
        self,
        card: ModelCard,
        use_case: str | None = None,
    ) -> str | None:
        """Check if the AI system involves prohibited practices."""
        description = (card.description + " " + (use_case or "")).lower()
        
        prohibited_keywords = {
            "subliminal": "Subliminal manipulation causing harm",
            "social scoring": "Social scoring by public authorities",
            "real-time biometric": "Real-time biometric identification in public spaces",
            "predictive policing": "Predictive policing based solely on profiling",
            "facial recognition database": "Facial recognition databases from untargeted scraping",
        }
        
        for keyword, practice in prohibited_keywords.items():
            if keyword in description:
                return practice
        
        return None
    
    def _determine_category(
        self,
        card: ModelCard,
        use_case: str | None = None,
    ) -> AISystemCategory:
        """Determine AI system category from description."""
        description = (card.description + " " + (use_case or "")).lower()
        
        # Check for high-risk categories
        category_keywords = {
            AISystemCategory.BIOMETRIC_ID: ["biometric", "face recognition", "fingerprint", "iris"],
            AISystemCategory.CRITICAL_INFRASTRUCTURE: ["power grid", "water supply", "gas", "transport", "traffic"],
            AISystemCategory.EDUCATION_TRAINING: ["student", "education", "school", "exam", "grading"],
            AISystemCategory.EMPLOYMENT: ["hiring", "recruitment", "hr", "employee", "performance review", "termination"],
            AISystemCategory.ESSENTIAL_SERVICES: ["credit score", "insurance", "healthcare access", "emergency services"],
            AISystemCategory.LAW_ENFORCEMENT: ["police", "law enforcement", "criminal", "crime prediction"],
            AISystemCategory.MIGRATION_ASYLUM: ["migration", "asylum", "visa", "border"],
            AISystemCategory.JUSTICE: ["court", "judicial", "legal", "sentencing"],
            AISystemCategory.DEMOCRATIC_PROCESS: ["election", "voting", "political"],
            AISystemCategory.CHATBOT: ["chatbot", "conversational", "chat", "assistant"],
            AISystemCategory.EMOTION_RECOGNITION: ["emotion", "sentiment", "facial expression"],
            AISystemCategory.DEEPFAKE: ["deepfake", "synthetic media", "face swap"],
            AISystemCategory.FOUNDATION_MODEL: ["llm", "large language model", "foundation model", "gpt", "bert"],
        }
        
        for category, keywords in category_keywords.items():
            if any(kw in description for kw in keywords):
                return category
        
        # Default based on model type
        model_type_mapping = {
            ModelType.GENERATIVE: AISystemCategory.GENERAL_PURPOSE,
            ModelType.NLP: AISystemCategory.CHATBOT,
            ModelType.COMPUTER_VISION: AISystemCategory.GENERAL_PURPOSE,
            ModelType.RECOMMENDATION: AISystemCategory.RECOMMENDATION,
            ModelType.FOUNDATION_MODEL: AISystemCategory.FOUNDATION_MODEL,
        }
        
        return model_type_mapping.get(card.model_type, AISystemCategory.GENERAL_PURPOSE)
    
    def _determine_risk_level(self, category: AISystemCategory) -> AIRiskLevel:
        """Determine risk level from category."""
        if category in HIGH_RISK_CATEGORIES:
            return AIRiskLevel.HIGH
        elif category in [AISystemCategory.CHATBOT, AISystemCategory.EMOTION_RECOGNITION, AISystemCategory.DEEPFAKE]:
            return AIRiskLevel.LIMITED
        else:
            return AIRiskLevel.MINIMAL
    
    def _get_requirements(
        self,
        risk_level: AIRiskLevel,
        category: AISystemCategory,
    ) -> list[str]:
        """Get applicable requirements."""
        requirements = []
        
        if risk_level == AIRiskLevel.HIGH:
            requirements.extend(HIGH_RISK_REQUIREMENTS)
        
        if category in TRANSPARENCY_REQUIREMENTS:
            requirements.append(f"Transparency: {TRANSPARENCY_REQUIREMENTS[category]}")
        
        # Foundation model requirements
        if category == AISystemCategory.FOUNDATION_MODEL:
            requirements.extend([
                "Technical documentation per Article 53",
                "Model evaluation and testing documentation",
                "Downstream provider information",
                "Training data governance documentation",
            ])
        
        return requirements
    
    async def assess_compliance_gaps(
        self,
        card: ModelCard,
    ) -> dict[str, Any]:
        """Assess compliance gaps in the model card."""
        gaps = []
        recommendations = []
        
        # Check basic information
        if not card.description or len(card.description) < 50:
            gaps.append("Insufficient model description")
            recommendations.append("Provide detailed description of model functionality")
        
        if not card.developers:
            gaps.append("No developers/maintainers listed")
            recommendations.append("Document responsible parties for the model")
        
        # Check intended use
        if not card.intended_use.primary_uses:
            gaps.append("No intended uses documented")
            recommendations.append("Document primary intended use cases")
        
        if not card.intended_use.prohibited_uses:
            gaps.append("No prohibited uses documented")
            recommendations.append("Document use cases where the model should NOT be used")
        
        if card.regulatory.eu_ai_act_risk_level == AIRiskLevel.HIGH:
            if not card.intended_use.human_oversight_required:
                gaps.append("Human oversight not documented for high-risk system")
                recommendations.append("Document human oversight mechanisms (EU AI Act Article 14)")
        
        # Check training data
        if not card.training_data.data_sources:
            gaps.append("No training data sources documented")
            recommendations.append("Document all training data sources (EU AI Act Article 10)")
        
        if card.training_data.contains_pii and not card.training_data.pii_handling:
            gaps.append("PII present but no handling procedures documented")
            recommendations.append("Document PII handling and protection measures")
        
        # Check performance
        if card.performance.accuracy is None and not card.performance.custom_metrics:
            gaps.append("No performance metrics documented")
            recommendations.append("Document model performance metrics (EU AI Act Article 15)")
        
        # Check fairness
        if not card.fairness.demographic_parity and not card.fairness.disparate_impact:
            gaps.append("No fairness metrics documented")
            recommendations.append("Conduct and document bias testing across protected groups")
        
        if card.fairness.bias_detected and not card.fairness.mitigation_techniques:
            gaps.append("Bias detected but no mitigation documented")
            recommendations.append("Document bias mitigation techniques applied")
        
        # Check limitations
        if not card.limitations.technical_limitations:
            gaps.append("No technical limitations documented")
            recommendations.append("Document known technical limitations")
        
        if not card.limitations.out_of_scope_uses:
            gaps.append("No out-of-scope uses documented")
            recommendations.append("Document scenarios where the model is not suitable")
        
        # Check ethical considerations
        if card.regulatory.eu_ai_act_risk_level == AIRiskLevel.HIGH:
            if not card.ethical_considerations.ethics_review_conducted:
                gaps.append("No ethics review for high-risk system")
                recommendations.append("Conduct ethics review before deployment")
            
            if not card.ethical_considerations.affected_stakeholders:
                gaps.append("Affected stakeholders not identified")
                recommendations.append("Identify and document affected stakeholders")
        
        # Check regulatory compliance
        if card.regulatory.eu_ai_act_risk_level == AIRiskLevel.HIGH:
            if not card.regulatory.risk_management_system:
                gaps.append("No risk management system documented")
                recommendations.append("Implement risk management system (EU AI Act Article 9)")
            
            if not card.regulatory.technical_documentation:
                gaps.append("Technical documentation incomplete")
                recommendations.append("Complete technical documentation (EU AI Act Article 11)")
            
            if not card.regulatory.conformity_assessment_completed:
                gaps.append("Conformity assessment not completed")
                recommendations.append("Complete conformity assessment before deployment (EU AI Act Article 43)")
        
        compliance_score = card.get_compliance_score()
        
        return {
            "compliance_score": compliance_score,
            "gaps_count": len(gaps),
            "gaps": gaps,
            "recommendations": recommendations,
            "ready_for_deployment": len(gaps) == 0 and compliance_score >= 80,
            "risk_level": card.regulatory.eu_ai_act_risk_level.value if card.regulatory.eu_ai_act_risk_level else None,
        }
    
    async def generate_markdown(self, card: ModelCard) -> str:
        """Generate markdown documentation from model card."""
        sections = [
            f"# Model Card: {card.model_name}",
            "",
            f"**Version:** {card.model_version}",
            f"**Model Type:** {card.model_type.value}",
            f"**Last Updated:** {card.updated_at.strftime('%Y-%m-%d')}",
            "",
            "## Model Description",
            "",
            card.description,
            "",
        ]
        
        # Developers
        if card.developers:
            sections.extend([
                "## Developers",
                "",
                ", ".join(card.developers),
                "",
            ])
        
        # EU AI Act Classification
        if card.regulatory.eu_ai_act_risk_level:
            sections.extend([
                "## EU AI Act Classification",
                "",
                f"**Risk Level:** {card.regulatory.eu_ai_act_risk_level.value.upper()}",
                f"**Category:** {card.regulatory.eu_ai_act_category.value if card.regulatory.eu_ai_act_category else 'N/A'}",
                f"**Conformity Assessment Required:** {'Yes' if card.regulatory.conformity_assessment_required else 'No'}",
                "",
            ])
        
        # Intended Use
        sections.extend([
            "## Intended Use",
            "",
        ])
        
        if card.intended_use.primary_uses:
            sections.append("### Primary Intended Uses")
            sections.append("")
            for use in card.intended_use.primary_uses:
                sections.append(f"- {use}")
            sections.append("")
        
        if card.intended_use.prohibited_uses:
            sections.append("### Out-of-Scope / Prohibited Uses")
            sections.append("")
            for use in card.intended_use.prohibited_uses:
                sections.append(f"- ⚠️ {use}")
            sections.append("")
        
        if card.intended_use.human_oversight_required:
            sections.extend([
                "### Human Oversight",
                "",
                card.intended_use.oversight_description or "Human oversight is required for this model.",
                "",
            ])
        
        # Training Data
        sections.extend([
            "## Training Data",
            "",
        ])
        
        if card.training_data.data_sources:
            sections.append("### Data Sources")
            sections.append("")
            for source in card.training_data.data_sources:
                sections.append(f"- {source}")
            sections.append("")
        
        if card.training_data.total_samples:
            sections.append(f"**Total Samples:** {card.training_data.total_samples:,}")
            sections.append("")
        
        if card.training_data.contains_pii:
            sections.extend([
                "### PII Handling",
                "",
                f"This dataset contains PII. {card.training_data.pii_handling or 'See data governance documentation.'}",
                "",
            ])
        
        # Performance
        sections.extend([
            "## Performance",
            "",
        ])
        
        if card.performance.accuracy is not None:
            sections.append(f"**Accuracy:** {card.performance.accuracy:.2%}")
        if card.performance.precision is not None:
            sections.append(f"**Precision:** {card.performance.precision:.2%}")
        if card.performance.recall is not None:
            sections.append(f"**Recall:** {card.performance.recall:.2%}")
        if card.performance.f1_score is not None:
            sections.append(f"**F1 Score:** {card.performance.f1_score:.2%}")
        
        sections.append("")
        
        # Fairness
        if card.fairness.bias_detected or card.fairness.demographic_parity:
            sections.extend([
                "## Fairness & Bias",
                "",
            ])
            
            if card.fairness.bias_detected:
                sections.append("### Bias Detected")
                sections.append("")
                for bias in card.fairness.bias_detected:
                    severity = card.fairness.bias_severity.get(bias.value, "unknown")
                    sections.append(f"- {bias.value}: {severity} severity")
                sections.append("")
            
            if card.fairness.mitigation_techniques:
                sections.append("### Mitigation Techniques")
                sections.append("")
                for technique in card.fairness.mitigation_techniques:
                    sections.append(f"- {technique}")
                sections.append("")
        
        # Limitations
        sections.extend([
            "## Limitations",
            "",
        ])
        
        if card.limitations.technical_limitations:
            sections.append("### Technical Limitations")
            sections.append("")
            for limit in card.limitations.technical_limitations:
                sections.append(f"- {limit}")
            sections.append("")
        
        if card.limitations.failure_modes:
            sections.append("### Known Failure Modes")
            sections.append("")
            for mode in card.limitations.failure_modes:
                sections.append(f"- {mode}")
            sections.append("")
        
        # Ethical Considerations
        if card.ethical_considerations.ethical_risks or card.ethical_considerations.affected_stakeholders:
            sections.extend([
                "## Ethical Considerations",
                "",
            ])
            
            if card.ethical_considerations.ethical_risks:
                sections.append("### Identified Risks")
                sections.append("")
                for risk in card.ethical_considerations.ethical_risks:
                    sections.append(f"- {risk}")
                sections.append("")
            
            if card.ethical_considerations.risk_mitigations:
                sections.append("### Risk Mitigations")
                sections.append("")
                for mitigation in card.ethical_considerations.risk_mitigations:
                    sections.append(f"- {mitigation}")
                sections.append("")
        
        # Regulatory Compliance
        sections.extend([
            "## Regulatory Compliance",
            "",
            f"**GDPR Compliant:** {'Yes' if card.regulatory.gdpr_compliant else 'No'}",
            f"**DPIA Conducted:** {'Yes' if card.regulatory.dpia_conducted else 'No'}",
        ])
        
        if card.regulatory.eu_ai_act_risk_level == AIRiskLevel.HIGH:
            sections.extend([
                "",
                "### EU AI Act High-Risk Requirements",
                "",
                f"- Risk Management System: {'✓' if card.regulatory.risk_management_system else '✗'}",
                f"- Technical Documentation: {'✓' if card.regulatory.technical_documentation else '✗'}",
                f"- Record Keeping: {'✓' if card.regulatory.record_keeping else '✗'}",
                f"- Human Oversight: {'✓' if card.regulatory.human_oversight_implemented else '✗'}",
                f"- Conformity Assessment: {'✓' if card.regulatory.conformity_assessment_completed else '✗'}",
            ])
        
        sections.extend([
            "",
            "---",
            "",
            f"*Model Card generated by ComplianceAgent on {datetime.utcnow().strftime('%Y-%m-%d')}*",
        ])
        
        return "\n".join(sections)
    
    async def export_json(self, card: ModelCard) -> dict[str, Any]:
        """Export model card as JSON (compatible with Hugging Face format)."""
        return {
            "model_details": {
                "name": card.model_name,
                "version": card.model_version,
                "type": card.model_type.value,
                "description": card.description,
                "developers": card.developers,
                "license": card.license,
                "framework": card.framework,
                "architecture": card.architecture,
            },
            "intended_use": {
                "primary_uses": card.intended_use.primary_uses,
                "primary_users": card.intended_use.primary_users,
                "out_of_scope_uses": card.intended_use.prohibited_uses,
                "human_oversight": {
                    "required": card.intended_use.human_oversight_required,
                    "description": card.intended_use.oversight_description,
                },
            },
            "training_data": {
                "sources": card.training_data.data_sources,
                "size": card.training_data.total_samples,
                "preprocessing": card.training_data.preprocessing_steps,
                "contains_pii": card.training_data.contains_pii,
                "pii_handling": card.training_data.pii_handling,
            },
            "performance": {
                "metrics": {
                    "accuracy": card.performance.accuracy,
                    "precision": card.performance.precision,
                    "recall": card.performance.recall,
                    "f1_score": card.performance.f1_score,
                    "auc_roc": card.performance.auc_roc,
                },
                "custom_metrics": card.performance.custom_metrics,
                "segment_performance": card.performance.segment_performance,
            },
            "fairness": {
                "demographic_parity": card.fairness.demographic_parity,
                "disparate_impact": card.fairness.disparate_impact,
                "bias_detected": [b.value for b in card.fairness.bias_detected],
                "mitigation_techniques": card.fairness.mitigation_techniques,
            },
            "limitations": {
                "technical": card.limitations.technical_limitations,
                "out_of_scope": card.limitations.out_of_scope_uses,
                "failure_modes": card.limitations.failure_modes,
            },
            "ethical_considerations": {
                "ethics_review": card.ethical_considerations.ethics_review_conducted,
                "risks": card.ethical_considerations.ethical_risks,
                "mitigations": card.ethical_considerations.risk_mitigations,
                "affected_stakeholders": card.ethical_considerations.affected_stakeholders,
            },
            "regulatory_compliance": {
                "eu_ai_act": {
                    "risk_level": card.regulatory.eu_ai_act_risk_level.value if card.regulatory.eu_ai_act_risk_level else None,
                    "category": card.regulatory.eu_ai_act_category.value if card.regulatory.eu_ai_act_category else None,
                    "conformity_assessment_required": card.regulatory.conformity_assessment_required,
                    "conformity_assessment_completed": card.regulatory.conformity_assessment_completed,
                },
                "gdpr": {
                    "compliant": card.regulatory.gdpr_compliant,
                    "dpia_conducted": card.regulatory.dpia_conducted,
                    "legal_basis": card.regulatory.legal_basis,
                },
            },
            "metadata": {
                "created_at": card.created_at.isoformat(),
                "updated_at": card.updated_at.isoformat(),
                "status": card.status,
                "compliance_score": card.get_compliance_score(),
            },
        }


# Singleton instance
_generator_instance: ModelCardGenerator | None = None


def get_model_card_generator() -> ModelCardGenerator:
    """Get or create the model card generator singleton."""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = ModelCardGenerator()
    return _generator_instance
