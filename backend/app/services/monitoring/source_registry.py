"""Unified regulatory source initialization.

This module provides functions to initialize all regulatory sources in the database,
including both existing and new APAC, ESG, and AI Safety frameworks.
"""

from typing import Any

import structlog

from app.models.regulation import RegulatoryFramework, RegulatorySource

# Import all source definition functions
from app.services.monitoring.gdpr_sources import get_gdpr_source_definitions
from app.services.monitoring.ccpa_sources import get_ccpa_source_definitions
from app.services.monitoring.hipaa_sources import get_hipaa_source_definitions
from app.services.monitoring.eu_ai_act_sources import get_eu_ai_act_source_definitions
from app.services.monitoring.pci_dss_sources import get_pci_dss_source_definitions
from app.services.monitoring.sox_sources import get_sox_source_definitions
from app.services.monitoring.nis2_sources import get_nis2_source_definitions
from app.services.monitoring.soc2_sources import get_soc2_source_definitions
from app.services.monitoring.iso27001_sources import get_iso27001_source_definitions
# APAC sources
from app.services.monitoring.singapore_pdpa_sources import get_singapore_pdpa_source_definitions
from app.services.monitoring.india_dpdp_sources import get_india_dpdp_source_definitions
from app.services.monitoring.japan_appi_sources import get_japan_appi_source_definitions
from app.services.monitoring.korea_pipa_sources import get_korea_pipa_source_definitions
from app.services.monitoring.china_pipl_sources import get_china_pipl_source_definitions
# ESG sources
from app.services.monitoring.esg_sources import get_esg_source_definitions
# AI Safety sources
from app.services.monitoring.ai_safety_sources import get_ai_safety_source_definitions


logger = structlog.get_logger()


# Registry of all source definition functions by framework
SOURCE_REGISTRY: dict[str, callable] = {
    # Privacy & Data Protection
    "gdpr": get_gdpr_source_definitions,
    "ccpa": get_ccpa_source_definitions,
    "hipaa": get_hipaa_source_definitions,
    # Security & Compliance
    "pci_dss": get_pci_dss_source_definitions,
    "sox": get_sox_source_definitions,
    "nis2": get_nis2_source_definitions,
    "soc2": get_soc2_source_definitions,
    "iso27001": get_iso27001_source_definitions,
    # AI Regulation
    "eu_ai_act": get_eu_ai_act_source_definitions,
    "ai_safety": get_ai_safety_source_definitions,
    # APAC Privacy
    "singapore_pdpa": get_singapore_pdpa_source_definitions,
    "india_dpdp": get_india_dpdp_source_definitions,
    "japan_appi": get_japan_appi_source_definitions,
    "korea_pipa": get_korea_pipa_source_definitions,
    "china_pipl": get_china_pipl_source_definitions,
    # ESG & Sustainability
    "esg": get_esg_source_definitions,
}


# Framework categories for UI grouping
FRAMEWORK_CATEGORIES = {
    "privacy_data_protection": {
        "name": "Privacy & Data Protection",
        "description": "Privacy laws and data protection regulations",
        "frameworks": ["gdpr", "ccpa", "hipaa", "singapore_pdpa", "india_dpdp", "japan_appi", "korea_pipa", "china_pipl"],
    },
    "security_compliance": {
        "name": "Security & Compliance",
        "description": "Security standards and compliance frameworks",
        "frameworks": ["pci_dss", "sox", "nis2", "soc2", "iso27001"],
    },
    "ai_regulation": {
        "name": "AI Regulation",
        "description": "Artificial intelligence governance and safety standards",
        "frameworks": ["eu_ai_act", "ai_safety"],
    },
    "esg_sustainability": {
        "name": "ESG & Sustainability",
        "description": "Environmental, social, and governance reporting requirements",
        "frameworks": ["esg"],
    },
}


def get_all_source_definitions() -> list[dict[str, Any]]:
    """Get all regulatory source definitions from all frameworks.
    
    Returns:
        List of all source definition dictionaries
    """
    all_sources = []
    
    for framework_key, get_definitions in SOURCE_REGISTRY.items():
        try:
            sources = get_definitions()
            logger.debug(f"Loaded {len(sources)} sources for {framework_key}")
            all_sources.extend(sources)
        except Exception as e:
            logger.error(f"Error loading sources for {framework_key}: {e}")
    
    return all_sources


def get_source_definitions_by_category(category: str) -> list[dict[str, Any]]:
    """Get source definitions for a specific category.
    
    Args:
        category: Category key (e.g., 'privacy_data_protection', 'ai_regulation')
    
    Returns:
        List of source definitions for the category
    """
    if category not in FRAMEWORK_CATEGORIES:
        raise ValueError(f"Unknown category: {category}. Valid categories: {list(FRAMEWORK_CATEGORIES.keys())}")
    
    category_info = FRAMEWORK_CATEGORIES[category]
    sources = []
    
    for framework_key in category_info["frameworks"]:
        if framework_key in SOURCE_REGISTRY:
            sources.extend(SOURCE_REGISTRY[framework_key]())
    
    return sources


def get_source_definitions_by_framework(framework_key: str) -> list[dict[str, Any]]:
    """Get source definitions for a specific framework.
    
    Args:
        framework_key: Framework key (e.g., 'gdpr', 'singapore_pdpa', 'esg')
    
    Returns:
        List of source definitions for the framework
    """
    if framework_key not in SOURCE_REGISTRY:
        raise ValueError(f"Unknown framework: {framework_key}. Valid frameworks: {list(SOURCE_REGISTRY.keys())}")
    
    return SOURCE_REGISTRY[framework_key]()


async def initialize_all_sources(db, frameworks: list[str] | None = None) -> dict[str, list[RegulatorySource]]:
    """Initialize regulatory sources in the database.
    
    Args:
        db: Database session
        frameworks: Optional list of framework keys to initialize. If None, initializes all.
    
    Returns:
        Dictionary mapping framework keys to lists of created RegulatorySource objects
    """
    results = {}
    frameworks_to_init = frameworks or list(SOURCE_REGISTRY.keys())
    
    logger.info(f"Initializing sources for {len(frameworks_to_init)} frameworks")
    
    for framework_key in frameworks_to_init:
        if framework_key not in SOURCE_REGISTRY:
            logger.warning(f"Skipping unknown framework: {framework_key}")
            continue
        
        try:
            source_defs = SOURCE_REGISTRY[framework_key]()
            sources = []
            
            for source_def in source_defs:
                # Check if source already exists
                existing = await db.execute(
                    db.query(RegulatorySource).filter(
                        RegulatorySource.name == source_def["name"]
                    )
                )
                if existing.scalar_one_or_none():
                    logger.debug(f"Source already exists: {source_def['name']}")
                    continue
                
                source = RegulatorySource(
                    name=source_def["name"],
                    description=source_def.get("description", ""),
                    url=source_def["url"],
                    jurisdiction=source_def["jurisdiction"],
                    framework=source_def.get("framework"),
                    parser_type=source_def.get("parser_type", "html"),
                    parser_config=source_def.get("parser_config", {}),
                    is_active=True,
                    check_interval_hours=source_def.get("check_interval_hours", 24),
                )
                db.add(source)
                sources.append(source)
            
            await db.flush()
            results[framework_key] = sources
            logger.info(f"Initialized {len(sources)} sources for {framework_key}")
            
        except Exception as e:
            logger.error(f"Error initializing sources for {framework_key}: {e}")
            results[framework_key] = []
    
    return results


def get_framework_statistics() -> dict[str, Any]:
    """Get statistics about available regulatory frameworks and sources.
    
    Returns:
        Dictionary with framework and source statistics
    """
    all_sources = get_all_source_definitions()
    
    # Count by jurisdiction
    by_jurisdiction = {}
    for source in all_sources:
        jurisdiction = source["jurisdiction"].value if hasattr(source["jurisdiction"], "value") else str(source["jurisdiction"])
        by_jurisdiction[jurisdiction] = by_jurisdiction.get(jurisdiction, 0) + 1
    
    # Count by framework
    by_framework = {}
    for source in all_sources:
        framework = source.get("framework")
        if framework:
            framework_val = framework.value if hasattr(framework, "value") else str(framework)
            by_framework[framework_val] = by_framework.get(framework_val, 0) + 1
    
    # Count by category
    by_category = {}
    for category_key, category_info in FRAMEWORK_CATEGORIES.items():
        count = 0
        for framework_key in category_info["frameworks"]:
            if framework_key in SOURCE_REGISTRY:
                count += len(SOURCE_REGISTRY[framework_key]())
        by_category[category_key] = count
    
    return {
        "total_sources": len(all_sources),
        "total_frameworks": len(SOURCE_REGISTRY),
        "total_categories": len(FRAMEWORK_CATEGORIES),
        "by_jurisdiction": by_jurisdiction,
        "by_framework": by_framework,
        "by_category": by_category,
        "categories": {
            key: {
                "name": info["name"],
                "description": info["description"],
                "framework_count": len(info["frameworks"]),
            }
            for key, info in FRAMEWORK_CATEGORIES.items()
        },
    }


# APAC-specific helpers
def get_apac_source_definitions() -> list[dict[str, Any]]:
    """Get all Asia-Pacific regulatory source definitions."""
    apac_frameworks = ["singapore_pdpa", "india_dpdp", "japan_appi", "korea_pipa", "china_pipl"]
    sources = []
    for framework in apac_frameworks:
        sources.extend(SOURCE_REGISTRY[framework]())
    return sources


# ESG-specific helpers
def get_sustainability_source_definitions() -> list[dict[str, Any]]:
    """Get all ESG/Sustainability regulatory source definitions."""
    return get_esg_source_definitions()


# AI Safety-specific helpers
def get_ai_regulation_source_definitions() -> list[dict[str, Any]]:
    """Get all AI regulation source definitions (EU AI Act + NIST AI RMF + ISO 42001)."""
    sources = []
    sources.extend(get_eu_ai_act_source_definitions())
    sources.extend(get_ai_safety_source_definitions())
    return sources
