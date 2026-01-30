"""AI Safety and Risk Classification API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CurrentOrganization, OrgMember
from app.services.monitoring.ai_safety_sources import (
    AIRiskClassifier,
    AIRiskLevel,
    AISystemClassification,
    NIST_AI_RMF_FUNCTIONS,
    AI_SYSTEM_DETECTION_PATTERNS,
)
from app.services.monitoring.source_registry import (
    get_framework_statistics,
    get_ai_regulation_source_definitions,
    FRAMEWORK_CATEGORIES,
)


router = APIRouter()


# Request/Response schemas
class AIClassificationRequest(BaseModel):
    """Request for AI system risk classification."""
    code_content: str = Field(
        default="",
        description="Code content to analyze for AI/ML patterns",
    )
    file_names: list[str] = Field(
        default_factory=list,
        description="List of file names in the codebase",
    )
    system_description: str = Field(
        default="",
        description="Description of the AI system's purpose and functionality",
    )
    use_case: str = Field(
        default="",
        description="Primary use case or application domain",
    )
    data_types: list[str] = Field(
        default_factory=list,
        description="Types of data processed by the AI system",
    )


class AIClassificationResponse(BaseModel):
    """Response with AI system risk classification."""
    risk_level: str = Field(description="Risk level: unacceptable, high, limited, or minimal")
    confidence: float = Field(description="Confidence score (0-1)")
    reasons: list[str] = Field(description="Reasons for the classification")
    detected_patterns: list[str] = Field(description="AI/ML patterns detected in code")
    high_risk_areas: list[str] = Field(description="Identified high-risk use case areas")
    applicable_requirements: list[str] = Field(description="EU AI Act requirements that apply")
    recommendations: list[str] = Field(description="Recommended actions for compliance")


class FrameworkStatisticsResponse(BaseModel):
    """Response with framework statistics."""
    total_sources: int
    total_frameworks: int
    total_categories: int
    by_jurisdiction: dict[str, int]
    by_framework: dict[str, int]
    by_category: dict[str, int]
    categories: dict[str, dict[str, Any]]


class NISTAIRMFResponse(BaseModel):
    """Response with NIST AI RMF framework details."""
    functions: dict[str, Any]
    total_categories: int


class AIDetectionPatternsResponse(BaseModel):
    """Response with AI detection patterns."""
    ml_libraries: list[str]
    ml_file_patterns: list[str]
    ml_code_patterns: list[str]
    high_risk_indicators: list[str]
    prohibited_indicators: list[str]


# API Endpoints
@router.post("/classify", response_model=AIClassificationResponse)
async def classify_ai_system(
    request: AIClassificationRequest,
    organization: CurrentOrganization,
    member: OrgMember,
) -> AIClassificationResponse:
    """
    Classify an AI system's risk level according to the EU AI Act.
    
    Analyzes provided code content, file names, and system description to determine:
    - Risk level (Unacceptable, High, Limited, or Minimal)
    - Applicable EU AI Act requirements
    - Recommended compliance actions
    
    The classification considers:
    - Presence of ML/AI libraries and code patterns
    - High-risk use cases (biometrics, employment, healthcare, etc.)
    - Prohibited practices (social scoring, subliminal manipulation, etc.)
    """
    classifier = AIRiskClassifier()
    
    # Combine description and use case for analysis
    full_description = f"{request.system_description} {request.use_case} {' '.join(request.data_types)}"
    
    result = classifier.classify_from_code(
        code_content=request.code_content,
        file_names=request.file_names,
        description=full_description,
    )
    
    return AIClassificationResponse(
        risk_level=result.risk_level.value,
        confidence=result.confidence,
        reasons=result.reasons,
        detected_patterns=result.detected_patterns,
        high_risk_areas=result.high_risk_areas,
        applicable_requirements=result.applicable_requirements,
        recommendations=result.recommendations,
    )


@router.get("/frameworks/statistics", response_model=FrameworkStatisticsResponse)
async def get_regulatory_framework_statistics(
    organization: CurrentOrganization,
    member: OrgMember,
) -> FrameworkStatisticsResponse:
    """
    Get statistics about all available regulatory frameworks and sources.
    
    Returns counts of sources by:
    - Jurisdiction (EU, US, Singapore, India, Japan, etc.)
    - Framework (GDPR, CCPA, PDPA, CSRD, EU AI Act, etc.)
    - Category (Privacy, Security, AI Regulation, ESG)
    """
    stats = get_framework_statistics()
    return FrameworkStatisticsResponse(**stats)


@router.get("/frameworks/categories")
async def get_framework_categories(
    organization: CurrentOrganization,
    member: OrgMember,
) -> dict[str, Any]:
    """
    Get framework category definitions.
    
    Categories include:
    - privacy_data_protection: GDPR, CCPA, PDPA, DPDP, APPI, PIPA, PIPL
    - security_compliance: PCI-DSS, SOX, NIS2, SOC 2, ISO 27001
    - ai_regulation: EU AI Act, NIST AI RMF, ISO 42001
    - esg_sustainability: CSRD, SEC Climate, TCFD
    """
    return FRAMEWORK_CATEGORIES


@router.get("/nist-ai-rmf", response_model=NISTAIRMFResponse)
async def get_nist_ai_rmf_framework(
    organization: CurrentOrganization,
    member: OrgMember,
) -> NISTAIRMFResponse:
    """
    Get NIST AI Risk Management Framework details.
    
    Returns the four core functions:
    - GOVERN: Policies, accountability, workforce, culture
    - MAP: Context, categorization, capabilities, risks, impacts
    - MEASURE: Methods, metrics, evaluation, tracking
    - MANAGE: Prioritization, strategies, treatments, communication
    """
    total_categories = sum(
        len(func_data.get("categories", []))
        for func_data in NIST_AI_RMF_FUNCTIONS.values()
    )
    
    return NISTAIRMFResponse(
        functions=NIST_AI_RMF_FUNCTIONS,
        total_categories=total_categories,
    )


@router.get("/detection-patterns", response_model=AIDetectionPatternsResponse)
async def get_ai_detection_patterns(
    organization: CurrentOrganization,
    member: OrgMember,
) -> AIDetectionPatternsResponse:
    """
    Get AI/ML detection patterns used for classification.
    
    Useful for understanding what patterns trigger different risk classifications
    and for validating that your codebase analysis is complete.
    """
    return AIDetectionPatternsResponse(
        ml_libraries=AI_SYSTEM_DETECTION_PATTERNS["ml_libraries"],
        ml_file_patterns=AI_SYSTEM_DETECTION_PATTERNS["ml_file_patterns"],
        ml_code_patterns=AI_SYSTEM_DETECTION_PATTERNS["ml_code_patterns"],
        high_risk_indicators=AI_SYSTEM_DETECTION_PATTERNS["high_risk_indicators"],
        prohibited_indicators=AI_SYSTEM_DETECTION_PATTERNS["prohibited_indicators"],
    )


@router.get("/ai-sources")
async def get_ai_regulation_sources(
    organization: CurrentOrganization,
    member: OrgMember,
) -> list[dict[str, Any]]:
    """
    Get all AI regulation source definitions.
    
    Includes sources for:
    - EU AI Act
    - NIST AI RMF
    - ISO 42001
    - US State AI Laws (Colorado, Illinois)
    - UK AI Framework
    """
    sources = get_ai_regulation_source_definitions()
    
    # Convert enum values to strings for JSON serialization
    return [
        {
            "name": s["name"],
            "description": s.get("description", ""),
            "url": s["url"],
            "jurisdiction": s["jurisdiction"].value if hasattr(s["jurisdiction"], "value") else str(s["jurisdiction"]),
            "framework": s["framework"].value if hasattr(s.get("framework"), "value") else str(s.get("framework", "")),
            "parser_type": s.get("parser_type", "html"),
        }
        for s in sources
    ]
