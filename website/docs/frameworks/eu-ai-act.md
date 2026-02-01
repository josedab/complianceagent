---
sidebar_position: 5
title: EU AI Act
description: European Union AI Act compliance with ComplianceAgent
---

# EU AI Act Compliance

The EU AI Act is the world's first comprehensive legal framework for AI. ComplianceAgent helps you navigate these requirements.

## Overview

| Attribute | Value |
|-----------|-------|
| **Jurisdiction** | European Union |
| **Effective Date** | August 2024 (phased implementation) |
| **Applies To** | Providers and deployers of AI systems |
| **Maximum Penalty** | €35M or 7% global revenue |
| **Requirements Tracked** | 94 |

## Timeline

```
Aug 2024: Entry into force
Feb 2025: Prohibited AI practices apply
Aug 2025: GPAI rules apply
Aug 2026: High-risk AI rules (Annex III) apply
Aug 2027: High-risk AI rules (Annex II) apply
```

## Risk Categories

### Prohibited AI (Article 5)

Banned AI practices include:

```python
PROHIBITED_AI_SYSTEMS = [
    "subliminal_manipulation",           # Distorts behavior detrimentally
    "exploitation_of_vulnerabilities",   # Targets age, disability, etc.
    "social_scoring_by_government",      # Chinese-style social credit
    "real_time_biometric_identification", # In public spaces (with exceptions)
    "emotion_recognition_workplace",     # Workplace/education inference
    "biometric_categorization",          # Sensitive attribute inference
    "facial_recognition_databases"       # Untargeted scraping
]

async def check_prohibited_ai(system: AISystem) -> ComplianceResult:
    """Check if AI system falls into prohibited category."""
    for prohibited in PROHIBITED_AI_SYSTEMS:
        if system.matches_category(prohibited):
            return ComplianceResult(
                compliant=False,
                severity="critical",
                message=f"System matches prohibited category: {prohibited}",
                action="System must be discontinued in EU"
            )
    return ComplianceResult(compliant=True)
```

### High-Risk AI (Annex III)

Systems requiring full compliance:

```yaml
high_risk_categories:
  biometrics:
    - remote_biometric_identification
    - emotion_recognition
    - biometric_categorization
  
  critical_infrastructure:
    - traffic_management
    - utilities_supply
    - digital_infrastructure
  
  education:
    - admission_decisions
    - assessment_and_grading
    - proctoring_systems
  
  employment:
    - recruitment_tools
    - performance_evaluation
    - task_allocation
    - termination_decisions
  
  essential_services:
    - credit_scoring
    - insurance_pricing
    - emergency_services
  
  law_enforcement:
    - risk_assessment
    - polygraph_ai
    - evidence_analysis
  
  migration:
    - document_verification
    - application_assessment
    - risk_assessment
```

### Limited-Risk AI

Transparency requirements only:

```typescript
// Chatbots and similar systems
interface LimitedRiskAI {
  type: 'chatbot' | 'emotion_detection' | 'deepfake' | 'synthetic_content';
  transparencyMeasures: TransparencyMeasure[];
}

// Required: Inform users they're interacting with AI
function enforceTransparency(aiSystem: LimitedRiskAI): void {
  switch (aiSystem.type) {
    case 'chatbot':
      displayAIDisclosure("You are interacting with an AI assistant");
      break;
    case 'synthetic_content':
      labelContent("AI-generated content");
      break;
    case 'deepfake':
      watermarkContent();
      displayDisclosure();
      break;
  }
}
```

### Minimal-Risk AI

No specific requirements (spam filters, inventory management, etc.).

## High-Risk Requirements

### Technical Documentation (Article 11)

```yaml
# Required technical documentation
technical_documentation:
  general_description:
    - intended_purpose
    - provider_information
    - system_version
    - hardware_requirements
    - software_components
    
  risk_management:
    - identified_risks
    - mitigation_measures
    - residual_risks
    
  data_governance:
    - training_data_description
    - data_preparation_methods
    - data_quality_metrics
    - bias_analysis
    
  design_specifications:
    - architecture_overview
    - computational_resources
    - human_oversight_measures
    
  monitoring:
    - performance_metrics
    - logging_capabilities
    - accuracy_degradation_detection
```

### Risk Management System (Article 9)

```python
class AIRiskManagementSystem:
    """EU AI Act compliant risk management."""
    
    async def establish(self, ai_system: AISystem) -> RiskManagementPlan:
        # 1. Identify risks
        risks = await self.identify_risks(ai_system)
        
        # 2. Estimate and evaluate risks
        evaluated_risks = []
        for risk in risks:
            evaluation = RiskEvaluation(
                risk=risk,
                likelihood=self.assess_likelihood(risk),
                severity=self.assess_severity(risk),
                affected_groups=self.identify_affected_groups(risk)
            )
            evaluated_risks.append(evaluation)
        
        # 3. Adopt risk management measures
        mitigations = await self.develop_mitigations(evaluated_risks)
        
        # 4. Test effectiveness
        test_results = await self.test_mitigations(mitigations)
        
        # 5. Document residual risks
        residual_risks = self.calculate_residual_risks(
            evaluated_risks, 
            mitigations, 
            test_results
        )
        
        return RiskManagementPlan(
            identified_risks=risks,
            evaluations=evaluated_risks,
            mitigations=mitigations,
            test_results=test_results,
            residual_risks=residual_risks,
            iteration_process="continuous"
        )
```

### Data Governance (Article 10)

```python
class AIDataGovernance:
    """EU AI Act data governance requirements."""
    
    async def assess_training_data(self, dataset: Dataset) -> DataAssessment:
        return DataAssessment(
            relevance=await self.check_relevance(dataset),
            representativeness=await self.check_representativeness(dataset),
            error_free=await self.check_data_quality(dataset),
            completeness=await self.check_completeness(dataset),
            bias_analysis=await self.analyze_bias(dataset),
            statistical_properties=await self.analyze_statistics(dataset)
        )
    
    async def analyze_bias(self, dataset: Dataset) -> BiasAnalysis:
        """Detect biases in training data."""
        protected_attributes = [
            "gender", "race", "ethnicity", "religion",
            "disability", "age", "sexual_orientation"
        ]
        
        biases = []
        for attr in protected_attributes:
            if attr in dataset.columns:
                distribution = dataset[attr].value_counts(normalize=True)
                expected = self.get_expected_distribution(attr)
                
                if self.significant_deviation(distribution, expected):
                    biases.append(BiasReport(
                        attribute=attr,
                        observed=distribution,
                        expected=expected,
                        severity=self.calculate_severity(distribution, expected)
                    ))
        
        return BiasAnalysis(biases=biases)
```

### Human Oversight (Article 14)

```python
class HumanOversightMeasures:
    """Enable human oversight of AI systems."""
    
    def implement(self, ai_system: AISystem) -> OversightConfiguration:
        return OversightConfiguration(
            # Understand AI capabilities and limitations
            documentation=self.generate_user_documentation(ai_system),
            
            # Monitor operations
            monitoring_dashboard=self.create_monitoring_ui(),
            
            # Interpret outputs
            explainability=self.enable_explainability(ai_system),
            
            # Override decisions
            override_mechanism=self.implement_override(),
            
            # Stop operation
            emergency_stop=self.implement_emergency_stop()
        )
    
    def implement_override(self) -> OverrideMechanism:
        """Allow human to override AI decisions."""
        return OverrideMechanism(
            enabled=True,
            required_confirmation=True,
            audit_trail=True,
            response_time_ms=100  # Fast enough for real-time
        )
```

### Conformity Assessment (Article 43)

```yaml
conformity_assessment:
  self_assessment:
    # For most Annex III high-risk systems
    applicable_to:
      - biometrics_not_for_identification
      - critical_infrastructure
      - education_not_admission
      - employment_not_recruitment
      - essential_services
    
    requirements:
      - quality_management_system
      - technical_documentation
      - conformity_declaration
      - ce_marking
  
  third_party_assessment:
    # For more sensitive high-risk systems
    applicable_to:
      - biometric_identification
      - admission_decisions
      - recruitment_tools
    
    requirements:
      - notified_body_audit
      - certification
      - ongoing_surveillance
```

## General Purpose AI (GPAI)

### Transparency Requirements

```python
class GPAICompliance:
    """GPAI model compliance requirements."""
    
    async def ensure_compliance(self, model: GPAIModel):
        # Technical documentation
        await self.document_model(model)
        
        # Training data summary
        await self.document_training_data(model)
        
        # Copyright compliance
        await self.document_copyright_policy(model)
        
        # EU AI Office registration
        await self.register_with_ai_office(model)
    
    async def document_training_data(self, model: GPAIModel):
        """Document training data per Article 53."""
        return TrainingDataSummary(
            data_sources=model.training_sources,
            web_scraping_methods=model.scraping_methodology,
            copyright_assessment=model.copyright_analysis,
            data_volume=model.training_data_size
        )
```

### Systemic Risk Models

Additional requirements for large models:

```yaml
systemic_risk_requirements:
  threshold: "10^25 FLOPS training compute"
  
  obligations:
    - model_evaluation
    - adversarial_testing
    - systemic_risk_tracking
    - incident_reporting
    - cybersecurity_measures
```

## Configuration

```yaml
# .complianceagent/config.yml
frameworks:
  eu_ai_act:
    enabled: true
    
    ai_systems:
      - name: "recommendation-engine"
        risk_category: "minimal"
        
      - name: "resume-screener"
        risk_category: "high"
        high_risk_category: "employment.recruitment"
        
      - name: "customer-chatbot"
        risk_category: "limited"
        requires_transparency: true
    
    gpai_models:
      - name: "internal-llm"
        systemic_risk: false
        training_compute_flops: "1e22"
```

## Templates

| Template | Description |
|----------|-------------|
| `eu-ai-technical-doc` | Technical documentation template |
| `eu-ai-risk-management` | Risk management system |
| `eu-ai-data-governance` | Training data governance |
| `eu-ai-human-oversight` | Override and monitoring controls |
| `eu-ai-transparency` | AI disclosure components |

## Compliance Checklist

```python
EU_AI_ACT_CHECKLIST = {
    "all_ai_systems": [
        "identify_risk_category",
        "check_prohibited_practices",
        "register_eu_database"  # If high-risk
    ],
    "high_risk": [
        "risk_management_system",
        "data_governance",
        "technical_documentation",
        "record_keeping",
        "transparency_to_users",
        "human_oversight",
        "accuracy_robustness_cybersecurity",
        "quality_management_system",
        "conformity_assessment",
        "eu_declaration_conformity",
        "ce_marking"
    ],
    "limited_risk": [
        "ai_disclosure",
        "deepfake_labeling"
    ],
    "gpai": [
        "technical_documentation",
        "copyright_policy",
        "training_data_summary"
    ]
}
```

---

See also: [GDPR](./gdpr) | [Frameworks Overview](./overview) | [AI Parsing](../core-concepts/ai-parsing)
