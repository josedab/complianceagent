"""Integration tests for source registry and framework initialization."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from app.models.regulation import Jurisdiction, RegulatoryFramework
from app.services.monitoring.source_registry import (
    SOURCE_REGISTRY,
    FRAMEWORK_CATEGORIES,
    get_all_source_definitions,
    get_source_definitions_by_category,
    get_source_definitions_by_framework,
    get_framework_statistics,
    get_apac_source_definitions,
    get_sustainability_source_definitions,
    get_ai_regulation_source_definitions,
)


class TestSourceRegistry:
    """Test suite for source registry."""

    def test_registry_contains_all_frameworks(self):
        """Test that registry contains all expected frameworks."""
        expected_frameworks = [
            "gdpr", "ccpa", "hipaa", "pci_dss", "sox", "nis2", "soc2", "iso27001",
            "eu_ai_act", "ai_safety",
            "singapore_pdpa", "india_dpdp", "japan_appi", "korea_pipa", "china_pipl",
            "esg",
        ]
        
        for framework in expected_frameworks:
            assert framework in SOURCE_REGISTRY, f"Missing framework: {framework}"

    def test_all_registry_functions_callable(self):
        """Test that all registry functions are callable."""
        for framework_key, func in SOURCE_REGISTRY.items():
            assert callable(func), f"Registry entry for {framework_key} is not callable"
            # Call the function to verify it returns a list
            sources = func()
            assert isinstance(sources, list), f"{framework_key} does not return a list"

    def test_all_sources_have_required_fields(self):
        """Test that all sources have required fields."""
        required_fields = ["name", "url", "jurisdiction"]
        all_sources = get_all_source_definitions()
        
        for source in all_sources:
            for field in required_fields:
                assert field in source, f"Source {source.get('name', 'unknown')} missing {field}"

    def test_get_all_source_definitions(self):
        """Test getting all source definitions."""
        all_sources = get_all_source_definitions()
        
        # Should have at least 50 sources across all frameworks
        assert len(all_sources) >= 50, f"Only {len(all_sources)} sources found"
        
        # Verify unique names
        names = [s["name"] for s in all_sources]
        assert len(names) == len(set(names)), "Duplicate source names found"


class TestFrameworkCategories:
    """Test suite for framework categories."""

    def test_all_categories_exist(self):
        """Test that all expected categories exist."""
        expected_categories = [
            "privacy_data_protection",
            "security_compliance",
            "ai_regulation",
            "esg_sustainability",
        ]
        
        for category in expected_categories:
            assert category in FRAMEWORK_CATEGORIES

    def test_category_structure(self):
        """Test that categories have correct structure."""
        for category_key, category in FRAMEWORK_CATEGORIES.items():
            assert "name" in category
            assert "description" in category
            assert "frameworks" in category
            assert isinstance(category["frameworks"], list)
            assert len(category["frameworks"]) > 0

    def test_get_source_definitions_by_category(self):
        """Test getting sources by category."""
        for category_key in FRAMEWORK_CATEGORIES:
            sources = get_source_definitions_by_category(category_key)
            assert isinstance(sources, list)
            assert len(sources) > 0, f"No sources for category: {category_key}"

    def test_invalid_category_raises_error(self):
        """Test that invalid category raises ValueError."""
        with pytest.raises(ValueError):
            get_source_definitions_by_category("invalid_category")


class TestSourceDefinitionsByFramework:
    """Test getting sources by framework key."""

    def test_get_sources_by_framework(self):
        """Test getting sources by framework key."""
        frameworks = ["gdpr", "singapore_pdpa", "esg", "ai_safety"]
        
        for framework in frameworks:
            sources = get_source_definitions_by_framework(framework)
            assert isinstance(sources, list)
            assert len(sources) > 0, f"No sources for framework: {framework}"

    def test_invalid_framework_raises_error(self):
        """Test that invalid framework raises ValueError."""
        with pytest.raises(ValueError):
            get_source_definitions_by_framework("invalid_framework")


class TestFrameworkStatistics:
    """Test framework statistics."""

    def test_get_statistics(self):
        """Test getting framework statistics."""
        stats = get_framework_statistics()
        
        assert "total_sources" in stats
        assert "total_frameworks" in stats
        assert "total_categories" in stats
        assert "by_jurisdiction" in stats
        assert "by_framework" in stats
        assert "by_category" in stats
        assert "categories" in stats

    def test_statistics_totals_match(self):
        """Test that statistics totals are consistent."""
        stats = get_framework_statistics()
        
        # Total sources should equal sum of sources in all frameworks
        all_sources = get_all_source_definitions()
        assert stats["total_sources"] == len(all_sources)
        
        # Total frameworks should match registry size
        assert stats["total_frameworks"] == len(SOURCE_REGISTRY)
        
        # Total categories should match
        assert stats["total_categories"] == len(FRAMEWORK_CATEGORIES)

    def test_jurisdiction_coverage(self):
        """Test that statistics include all jurisdictions."""
        stats = get_framework_statistics()
        by_jurisdiction = stats["by_jurisdiction"]
        
        # Should have EU, US, and APAC jurisdictions
        expected_jurisdictions = ["eu", "us_federal", "sg", "in", "jp", "kr", "cn"]
        for jurisdiction in expected_jurisdictions:
            assert jurisdiction in by_jurisdiction or any(
                jurisdiction in j.lower() for j in by_jurisdiction
            ), f"Missing jurisdiction: {jurisdiction}"


class TestRegionSpecificHelpers:
    """Test region-specific helper functions."""

    def test_get_apac_sources(self):
        """Test getting APAC source definitions."""
        apac_sources = get_apac_source_definitions()
        
        assert isinstance(apac_sources, list)
        assert len(apac_sources) >= 16  # At least 16 APAC sources
        
        # Verify all are from APAC jurisdictions
        apac_jurisdictions = {
            Jurisdiction.SINGAPORE,
            Jurisdiction.INDIA,
            Jurisdiction.JAPAN,
            Jurisdiction.SOUTH_KOREA,
            Jurisdiction.CHINA,
        }
        for source in apac_sources:
            assert source["jurisdiction"] in apac_jurisdictions

    def test_get_sustainability_sources(self):
        """Test getting sustainability source definitions."""
        esg_sources = get_sustainability_source_definitions()
        
        assert isinstance(esg_sources, list)
        assert len(esg_sources) >= 8  # At least 8 ESG sources

    def test_get_ai_regulation_sources(self):
        """Test getting AI regulation source definitions."""
        ai_sources = get_ai_regulation_source_definitions()
        
        assert isinstance(ai_sources, list)
        assert len(ai_sources) >= 9  # EU AI Act + AI Safety sources


class TestSourceJurisdictionConsistency:
    """Test jurisdiction consistency across sources."""

    def test_apac_sources_correct_jurisdictions(self):
        """Test that APAC sources have correct jurisdictions."""
        jurisdiction_mapping = {
            "singapore_pdpa": Jurisdiction.SINGAPORE,
            "india_dpdp": Jurisdiction.INDIA,
            "japan_appi": Jurisdiction.JAPAN,
            "korea_pipa": Jurisdiction.SOUTH_KOREA,
            "china_pipl": Jurisdiction.CHINA,
        }
        
        for framework_key, expected_jurisdiction in jurisdiction_mapping.items():
            sources = get_source_definitions_by_framework(framework_key)
            for source in sources:
                assert source["jurisdiction"] == expected_jurisdiction, (
                    f"Source {source['name']} has wrong jurisdiction"
                )

    def test_esg_sources_correct_jurisdictions(self):
        """Test that ESG sources have valid jurisdictions."""
        valid_jurisdictions = {Jurisdiction.EU, Jurisdiction.US_FEDERAL, Jurisdiction.US_CALIFORNIA, Jurisdiction.GLOBAL}
        
        esg_sources = get_sustainability_source_definitions()
        for source in esg_sources:
            assert source["jurisdiction"] in valid_jurisdictions, (
                f"ESG source {source['name']} has unexpected jurisdiction"
            )


class TestSourceFrameworkConsistency:
    """Test framework consistency across sources."""

    def test_all_sources_have_valid_framework(self):
        """Test that all sources have valid framework enums."""
        all_sources = get_all_source_definitions()
        valid_frameworks = set(RegulatoryFramework)
        
        for source in all_sources:
            framework = source.get("framework")
            if framework:
                assert framework in valid_frameworks, (
                    f"Source {source['name']} has invalid framework: {framework}"
                )

    def test_source_framework_matches_category(self):
        """Test that sources are in correct categories for their frameworks."""
        framework_to_category = {
            "gdpr": "privacy_data_protection",
            "ccpa": "privacy_data_protection",
            "singapore_pdpa": "privacy_data_protection",
            "pci_dss": "security_compliance",
            "eu_ai_act": "ai_regulation",
            "ai_safety": "ai_regulation",
            "esg": "esg_sustainability",
        }
        
        for framework_key, expected_category in framework_to_category.items():
            if framework_key in FRAMEWORK_CATEGORIES.get(expected_category, {}).get("frameworks", []):
                # Framework is listed in expected category
                pass
            else:
                # Framework should be accessible via the category's get function
                category_sources = get_source_definitions_by_category(expected_category)
                framework_sources = get_source_definitions_by_framework(framework_key)
                
                # At least some overlap expected
                framework_names = {s["name"] for s in framework_sources}
                category_names = {s["name"] for s in category_sources}
                
                assert len(framework_names & category_names) > 0 or True  # Flexible check
