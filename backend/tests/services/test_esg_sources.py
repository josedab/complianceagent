"""Tests for ESG & Sustainability regulatory sources."""

import pytest
from unittest.mock import MagicMock

from app.models.regulation import Jurisdiction, RegulatoryFramework
from app.services.monitoring.esg_sources import (
    ESGParser,
    ESGSourceMonitor,
    ESG_SOURCES,
    CSRD_DISCLOSURE_TOPICS,
    SEC_CLIMATE_REQUIREMENTS,
    get_esg_source_definitions,
)


pytestmark = pytest.mark.asyncio


class TestESGSources:
    """Test suite for ESG source definitions."""

    def test_source_definitions_valid(self):
        """Test that source definitions are valid."""
        sources = get_esg_source_definitions()
        
        assert len(sources) >= 8
        
        # Check we have sources for each framework
        frameworks = {s["framework"] for s in sources}
        assert RegulatoryFramework.CSRD in frameworks
        assert RegulatoryFramework.SEC_CLIMATE in frameworks
        assert RegulatoryFramework.TCFD in frameworks

    def test_csrd_sources_present(self):
        """Test that CSRD sources are properly defined."""
        sources = get_esg_source_definitions()
        csrd_sources = [s for s in sources if s["framework"] == RegulatoryFramework.CSRD]
        
        assert len(csrd_sources) >= 2
        
        # Verify EUR-Lex source
        eurlex_source = next((s for s in csrd_sources if "EUR-Lex" in s["name"]), None)
        assert eurlex_source is not None
        assert eurlex_source["jurisdiction"] == Jurisdiction.EU

    def test_sec_climate_sources_present(self):
        """Test that SEC climate sources are properly defined."""
        sources = get_esg_source_definitions()
        sec_sources = [s for s in sources if s["framework"] == RegulatoryFramework.SEC_CLIMATE]
        
        assert len(sec_sources) >= 2
        
        # Check jurisdictions
        for source in sec_sources:
            assert source["jurisdiction"] in [Jurisdiction.US_FEDERAL, Jurisdiction.US_CALIFORNIA]

    def test_tcfd_sources_present(self):
        """Test that TCFD sources are properly defined."""
        sources = get_esg_source_definitions()
        tcfd_sources = [s for s in sources if s["framework"] == RegulatoryFramework.TCFD]
        
        assert len(tcfd_sources) >= 2
        
        # TCFD is global
        for source in tcfd_sources:
            assert source["jurisdiction"] == Jurisdiction.GLOBAL


class TestCSRDDisclosureTopics:
    """Test suite for CSRD disclosure topic definitions."""

    def test_environmental_topics_present(self):
        """Test that environmental (E) topics are defined."""
        e_topics = [k for k in CSRD_DISCLOSURE_TOPICS if k.startswith("E")]
        
        assert len(e_topics) >= 5
        assert "E1" in CSRD_DISCLOSURE_TOPICS  # Climate change
        assert "E2" in CSRD_DISCLOSURE_TOPICS  # Pollution
        
        for topic_id in e_topics:
            topic = CSRD_DISCLOSURE_TOPICS[topic_id]
            assert topic["type"] == "environmental"
            assert "title" in topic
            assert "subtopics" in topic

    def test_social_topics_present(self):
        """Test that social (S) topics are defined."""
        s_topics = [k for k in CSRD_DISCLOSURE_TOPICS if k.startswith("S")]
        
        assert len(s_topics) >= 4
        assert "S1" in CSRD_DISCLOSURE_TOPICS  # Own workforce
        assert "S4" in CSRD_DISCLOSURE_TOPICS  # Consumers
        
        for topic_id in s_topics:
            topic = CSRD_DISCLOSURE_TOPICS[topic_id]
            assert topic["type"] == "social"

    def test_governance_topics_present(self):
        """Test that governance (G) topics are defined."""
        g_topics = [k for k in CSRD_DISCLOSURE_TOPICS if k.startswith("G")]
        
        assert len(g_topics) >= 1
        assert "G1" in CSRD_DISCLOSURE_TOPICS  # Business conduct
        
        for topic_id in g_topics:
            topic = CSRD_DISCLOSURE_TOPICS[topic_id]
            assert topic["type"] == "governance"


class TestSECClimateRequirements:
    """Test suite for SEC climate disclosure requirements."""

    def test_all_tcfd_pillars_covered(self):
        """Test that all TCFD pillars are covered."""
        assert "governance" in SEC_CLIMATE_REQUIREMENTS
        assert "strategy" in SEC_CLIMATE_REQUIREMENTS
        assert "risk_management" in SEC_CLIMATE_REQUIREMENTS
        assert "metrics_targets" in SEC_CLIMATE_REQUIREMENTS

    def test_ghg_scopes_in_metrics(self):
        """Test that GHG scope requirements are included."""
        metrics = SEC_CLIMATE_REQUIREMENTS["metrics_targets"]
        requirements_text = " ".join(metrics["requirements"])
        
        assert "Scope 1" in requirements_text
        assert "Scope 2" in requirements_text
        assert "Scope 3" in requirements_text

    def test_governance_requirements(self):
        """Test governance disclosure requirements."""
        governance = SEC_CLIMATE_REQUIREMENTS["governance"]
        
        assert "title" in governance
        assert "requirements" in governance
        assert len(governance["requirements"]) >= 2
        
        # Check for board and management oversight
        requirements_text = " ".join(governance["requirements"]).lower()
        assert "board" in requirements_text
        assert "management" in requirements_text


class TestESGParser:
    """Test suite for ESG parser."""

    def test_parser_extract_csrd_requirements(self):
        """Test extracting requirements from CSRD article."""
        parser = ESGParser()
        
        article = {
            "number": "1",
            "title": "Sustainability reporting standards",
            "content": """
            Large undertakings and listed SMEs shall report in accordance with 
            sustainability reporting standards adopted by the Commission. Companies 
            shall disclose information on environmental, social, and governance matters.
            The sustainability report shall include information necessary to understand
            the undertaking's impacts on sustainability matters.
            """,
        }
        
        requirements = parser.extract_requirements_from_csrd(article)
        
        assert len(requirements) > 0
        assert any(r["obligation_type"] == "must" for r in requirements)
        assert all(r["category"] == "sustainability_reporting" for r in requirements)
        assert all(r["citation"]["directive"] == "Directive (EU) 2022/2464 (CSRD)" for r in requirements)

    def test_parser_extract_ghg_requirements(self):
        """Test extracting GHG emissions requirements."""
        parser = ESGParser()
        
        content = """
        Companies shall disclose their Scope 1 GHG emissions from direct operations.
        Companies shall also disclose Scope 2 GHG emissions from purchased electricity.
        Where material, companies should disclose Scope 3 emissions from their value chain.
        """
        
        requirements = parser.extract_ghg_requirements(content)
        
        assert len(requirements) >= 3
        
        # Check all scopes are captured
        scopes = {r["scope"] for r in requirements}
        assert "Scope 1" in scopes
        assert "Scope 2" in scopes
        assert "Scope 3" in scopes

    def test_parser_scope_pattern_matching(self):
        """Test that scope pattern correctly identifies emissions scopes."""
        parser = ESGParser()
        
        test_cases = [
            ("Scope 1 emissions", "1"),
            ("Scope 2 emissions", "2"),
            ("Scope 3 value chain", "3"),
            ("Scope 1 and Scope 2", "1"),  # First match
        ]
        
        for text, expected_scope in test_cases:
            match = parser.scope_pattern.search(text)
            assert match is not None, f"Failed to match: {text}"
            assert match.group(1) == expected_scope

    def test_parser_esrs_pattern_matching(self):
        """Test ESRS standard pattern matching."""
        parser = ESGParser()
        
        test_cases = [
            "ESRS E1 Climate Change",
            "ESRS S1 Own Workforce",
            "ESRS G1 Business Conduct",
        ]
        
        for text in test_cases:
            match = parser.esrs_pattern.search(text)
            assert match is not None, f"Failed to match: {text}"

    def test_parse_csrd_directive(self):
        """Test parsing CSRD directive HTML."""
        parser = ESGParser()
        
        html_content = """
        <html>
        <body>
        <p class="oj-doc-ti">Directive (EU) 2022/2464 - Corporate Sustainability Reporting</p>
        <div class="eli-subdivision" id="art_1">
            <p class="oj-ti-art">Article 1 - Subject matter and scope</p>
            <div class="eli-subdivision">
                This Directive lays down rules on sustainability reporting.
            </div>
        </div>
        </body>
        </html>
        """
        
        result = parser.parse_csrd_directive(html_content)
        
        assert result["jurisdiction"] == "EU"
        assert len(result["articles"]) > 0


class TestESGSourceMonitor:
    """Test suite for ESG source monitor."""

    def test_monitor_initialization(self):
        """Test that monitor initializes correctly."""
        monitor = ESGSourceMonitor()
        
        assert monitor.crawler is not None
        assert monitor.parser is not None

    async def test_extract_requirements_from_csrd_content(self):
        """Test extracting requirements from CSRD-like content."""
        monitor = ESGSourceMonitor()
        
        source = MagicMock()
        source.framework = RegulatoryFramework.CSRD
        
        content = """
        <html>
        <body>
        <div class="eli-subdivision" id="art_1">
            <p class="oj-ti-art">Article 1</p>
            <div class="eli-subdivision">
                Undertakings shall report on sustainability matters. 
                Companies shall disclose their Scope 1 and Scope 2 emissions.
            </div>
        </div>
        </body>
        </html>
        """
        
        requirements = await monitor.extract_all_requirements(source, content)
        
        assert isinstance(requirements, list)


class TestESGRequirementCategories:
    """Test ESG-related requirement categories."""

    def test_esg_categories_in_enum(self):
        """Test that ESG categories are defined in RequirementCategory."""
        from app.models.requirement import RequirementCategory
        
        # Check sustainability categories exist
        assert hasattr(RequirementCategory, "SUSTAINABILITY_REPORTING")
        assert hasattr(RequirementCategory, "GHG_EMISSIONS")
        assert hasattr(RequirementCategory, "CLIMATE_RISK")
        assert hasattr(RequirementCategory, "ENVIRONMENTAL_IMPACT")
        assert hasattr(RequirementCategory, "SOCIAL_IMPACT")
        assert hasattr(RequirementCategory, "GOVERNANCE_DISCLOSURE")

    def test_esg_category_values(self):
        """Test ESG category enum values."""
        from app.models.requirement import RequirementCategory
        
        assert RequirementCategory.SUSTAINABILITY_REPORTING.value == "sustainability_reporting"
        assert RequirementCategory.GHG_EMISSIONS.value == "ghg_emissions"
        assert RequirementCategory.CLIMATE_RISK.value == "climate_risk"
