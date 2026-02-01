"""Tests for Asia-Pacific regulatory sources."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from app.models.regulation import Jurisdiction, RegulatoryFramework
from app.services.monitoring.singapore_pdpa_sources import (
    SingaporePDPAParser,
    SingaporePDPASourceMonitor,
    SINGAPORE_PDPA_SOURCES,
    PDPA_SECTIONS,
    get_singapore_pdpa_source_definitions,
)
from app.services.monitoring.india_dpdp_sources import (
    IndiaDPDPParser,
    IndiaDPDPSourceMonitor,
    INDIA_DPDP_SOURCES,
    DPDP_SECTIONS,
    get_india_dpdp_source_definitions,
)
from app.services.monitoring.japan_appi_sources import (
    JapanAPPIParser,
    JapanAPPISourceMonitor,
    JAPAN_APPI_SOURCES,
    APPI_ARTICLES,
    get_japan_appi_source_definitions,
)
from app.services.monitoring.korea_pipa_sources import (
    KoreaPIPAParser,
    KoreaPIPASourceMonitor,
    KOREA_PIPA_SOURCES,
    PIPA_ARTICLES,
    get_korea_pipa_source_definitions,
)
from app.services.monitoring.china_pipl_sources import (
    ChinaPIPLParser,
    ChinaPIPLSourceMonitor,
    CHINA_PIPL_SOURCES,
    PIPL_ARTICLES,
    get_china_pipl_source_definitions,
)


pytestmark = pytest.mark.asyncio


class TestSingaporePDPA:
    """Test suite for Singapore PDPA sources."""

    def test_source_definitions_valid(self):
        """Test that source definitions are valid."""
        sources = get_singapore_pdpa_source_definitions()
        
        assert len(sources) >= 4
        for source in sources:
            assert "name" in source
            assert "url" in source
            assert source["jurisdiction"] == Jurisdiction.SINGAPORE
            assert source["framework"] == RegulatoryFramework.PDPA

    def test_pdpa_sections_coverage(self):
        """Test that key PDPA sections are defined."""
        # Verify key sections
        assert "11" in PDPA_SECTIONS  # Consent required
        assert "18" in PDPA_SECTIONS  # Access to personal data
        assert "26C" in PDPA_SECTIONS  # Notification of data breach
        
        for section_num, section_info in PDPA_SECTIONS.items():
            assert "title" in section_info
            assert "type" in section_info

    def test_parser_extract_requirements(self):
        """Test requirement extraction from PDPA section."""
        parser = SingaporePDPAParser()
        
        section = {
            "number": "11",
            "title": "Consent required",
            "type": "consent",
            "content": """
            An organisation shall not collect, use or disclose personal data about 
            an individual unless the individual gives or is deemed to have given 
            consent under this Act.
            """,
        }
        
        requirements = parser.extract_requirements_from_section(section)
        
        assert len(requirements) > 0
        assert requirements[0]["obligation_type"] == "must"
        assert requirements[0]["citation"]["jurisdiction"] == "Singapore"

    def test_parser_parse_statute(self):
        """Test parsing PDPA statute HTML."""
        parser = SingaporePDPAParser()
        
        html_content = """
        <html>
        <body>
        <h1>Personal Data Protection Act 2012</h1>
        <div class="section">
            Section 11 - Consent required
            An organisation shall not collect personal data without consent.
        </div>
        </body>
        </html>
        """
        
        result = parser.parse_pdpa_statute(html_content)
        
        assert result["title"] == "Personal Data Protection Act 2012"
        assert result["jurisdiction"] == "Singapore"


class TestIndiaDPDP:
    """Test suite for India DPDP sources."""

    def test_source_definitions_valid(self):
        """Test that source definitions are valid."""
        sources = get_india_dpdp_source_definitions()
        
        assert len(sources) >= 4
        for source in sources:
            assert "name" in source
            assert "url" in source
            assert source["jurisdiction"] == Jurisdiction.INDIA
            assert source["framework"] == RegulatoryFramework.DPDP

    def test_dpdp_sections_coverage(self):
        """Test that key DPDP sections are defined."""
        # Verify key sections
        assert "6" in DPDP_SECTIONS  # Consent
        assert "11" in DPDP_SECTIONS  # Rights of Data Principal
        assert "16" in DPDP_SECTIONS  # Transfer outside India
        
        for section_num, section_info in DPDP_SECTIONS.items():
            assert "title" in section_info
            assert "type" in section_info

    def test_parser_extract_requirements(self):
        """Test requirement extraction from DPDP section."""
        parser = IndiaDPDPParser()
        
        section = {
            "number": "8",
            "title": "General obligations of Data Fiduciary",
            "type": "obligations",
            "content": """
            The Data Fiduciary shall ensure the completeness, accuracy and 
            consistency of personal data, particularly where such personal data 
            is likely to be used to make a decision that affects the Data Principal.
            """,
        }
        
        requirements = parser.extract_requirements_from_section(section)
        
        assert len(requirements) > 0
        assert requirements[0]["citation"]["act"] == "Digital Personal Data Protection Act, 2023"
        assert requirements[0]["citation"]["jurisdiction"] == "India"


class TestJapanAPPI:
    """Test suite for Japan APPI sources."""

    def test_source_definitions_valid(self):
        """Test that source definitions are valid."""
        sources = get_japan_appi_source_definitions()
        
        assert len(sources) >= 4
        for source in sources:
            assert "name" in source
            assert "url" in source
            assert source["jurisdiction"] == Jurisdiction.JAPAN
            assert source["framework"] == RegulatoryFramework.APPI

    def test_appi_articles_coverage(self):
        """Test that key APPI articles are defined."""
        # Verify key articles
        assert "17" in APPI_ARTICLES  # Restriction on purposes
        assert "23" in APPI_ARTICLES  # Security measures
        assert "28" in APPI_ARTICLES  # Cross-border transfer
        assert "33" in APPI_ARTICLES  # Disclosure
        
        for article_num, article_info in APPI_ARTICLES.items():
            assert "title" in article_info
            assert "type" in article_info

    def test_parser_extract_requirements(self):
        """Test requirement extraction from APPI article."""
        parser = JapanAPPIParser()
        
        article = {
            "number": "23",
            "title": "Security measures",
            "type": "security",
            "content": """
            A personal information handling business operator shall take necessary 
            and appropriate action for the security control of personal data including 
            prevention of the leakage, loss, or damage of the personal data.
            """,
        }
        
        requirements = parser.extract_requirements_from_article(article)
        
        assert len(requirements) > 0
        assert requirements[0]["citation"]["act"] == "Act on the Protection of Personal Information"
        assert requirements[0]["citation"]["jurisdiction"] == "Japan"

    def test_parser_handles_japanese_article_format(self):
        """Test that parser handles Japanese article numbering."""
        parser = JapanAPPIParser()
        
        # Japanese format: 第X条
        assert parser.article_pattern_jp.search("第23条") is not None
        # English format: Article X
        assert parser.article_pattern_en.search("Article 23") is not None


class TestKoreaPIPA:
    """Test suite for South Korea PIPA sources."""

    def test_source_definitions_valid(self):
        """Test that source definitions are valid."""
        sources = get_korea_pipa_source_definitions()
        
        assert len(sources) >= 4
        for source in sources:
            assert "name" in source
            assert "url" in source
            assert source["jurisdiction"] == Jurisdiction.SOUTH_KOREA
            assert source["framework"] == RegulatoryFramework.PIPA

    def test_pipa_articles_coverage(self):
        """Test that key PIPA articles are defined."""
        # Verify key articles
        assert "15" in PIPA_ARTICLES  # Collection and use
        assert "29" in PIPA_ARTICLES  # Safety measures
        assert "34" in PIPA_ARTICLES  # Notification of breach
        assert "35" in PIPA_ARTICLES  # Right of access
        
        for article_num, article_info in PIPA_ARTICLES.items():
            assert "title" in article_info
            assert "type" in article_info

    def test_parser_extract_requirements(self):
        """Test requirement extraction from PIPA article."""
        parser = KoreaPIPAParser()
        
        article = {
            "number": "29",
            "title": "Safety measures",
            "type": "security",
            "content": """
            A personal information controller shall take technical, administrative, 
            and physical measures necessary to ensure the safety of personal information 
            in order to prevent the loss, theft, leakage, falsification, or damage of 
            personal information.
            """,
        }
        
        requirements = parser.extract_requirements_from_article(article)
        
        assert len(requirements) > 0
        assert requirements[0]["citation"]["jurisdiction"] == "South Korea"

    def test_parser_handles_korean_article_format(self):
        """Test that parser handles Korean article numbering."""
        parser = KoreaPIPAParser()
        
        # Korean format: 제X조 or 제X조의Y
        assert parser.korean_article_pattern.search("제29조") is not None
        match = parser.korean_article_pattern.search("제37조의2")
        assert match is not None


class TestChinaPIPL:
    """Test suite for China PIPL sources."""

    def test_source_definitions_valid(self):
        """Test that source definitions are valid."""
        sources = get_china_pipl_source_definitions()
        
        assert len(sources) >= 4
        for source in sources:
            assert "name" in source
            assert "url" in source
            assert source["jurisdiction"] == Jurisdiction.CHINA
            assert source["framework"] == RegulatoryFramework.PIPL

    def test_pipl_articles_coverage(self):
        """Test that key PIPL articles are defined."""
        # Verify key articles
        assert "13" in PIPL_ARTICLES  # Lawful bases
        assert "38" in PIPL_ARTICLES  # Cross-border transfer
        assert "45" in PIPL_ARTICLES  # Right to access
        assert "57" in PIPL_ARTICLES  # Data breach notification
        
        for article_num, article_info in PIPL_ARTICLES.items():
            assert "title" in article_info
            assert "type" in article_info

    def test_parser_extract_requirements(self):
        """Test requirement extraction from PIPL article."""
        parser = ChinaPIPLParser()
        
        article = {
            "number": "51",
            "title": "Security measures",
            "type": "security",
            "content": """
            Personal information handlers shall take the following measures to ensure 
            that personal information handling activities comply with the provisions 
            of laws and administrative regulations, and to prevent unauthorized access 
            as well as personal information leakage, distortion, or loss.
            """,
        }
        
        requirements = parser.extract_requirements_from_article(article)
        
        assert len(requirements) > 0
        assert requirements[0]["citation"]["act"] == "Personal Information Protection Law"
        assert requirements[0]["citation"]["jurisdiction"] == "China"

    def test_parser_handles_chinese_article_format(self):
        """Test that parser handles Chinese article numbering."""
        parser = ChinaPIPLParser()
        
        # Chinese format: 第X条
        assert parser.article_pattern_cn.search("第51条") is not None
        # English format: Article X
        assert parser.article_pattern_en.search("Article 51") is not None


class TestAPACConflictResolution:
    """Test APAC jurisdiction conflict resolution."""

    def test_apac_jurisdictions_in_strictness_ranking(self):
        """Test that APAC jurisdictions are included in strictness ranking."""
        from app.services.conflict_resolution import JurisdictionConflictResolver
        
        resolver = JurisdictionConflictResolver()
        
        # Verify all APAC jurisdictions are ranked
        assert Jurisdiction.SINGAPORE in resolver.STRICTNESS_RANKING
        assert Jurisdiction.SOUTH_KOREA in resolver.STRICTNESS_RANKING
        assert Jurisdiction.CHINA in resolver.STRICTNESS_RANKING
        assert Jurisdiction.INDIA in resolver.STRICTNESS_RANKING
        assert Jurisdiction.JAPAN in resolver.STRICTNESS_RANKING

    def test_china_strictness_reflects_pipl(self):
        """Test that China's strictness reflects PIPL's comprehensive requirements."""
        from app.services.conflict_resolution import JurisdictionConflictResolver
        
        resolver = JurisdictionConflictResolver()
        
        # China PIPL is relatively strict
        assert resolver.STRICTNESS_RANKING[Jurisdiction.CHINA] >= 7

    def test_resolve_apac_conflict(self):
        """Test resolving conflict between APAC jurisdictions."""
        from app.services.conflict_resolution import (
            JurisdictionConflictResolver,
            ConflictResolutionStrategy,
        )
        from app.models.requirement import Requirement, ObligationType, RequirementCategory
        
        resolver = JurisdictionConflictResolver()
        
        # Create conflicting requirements between Singapore and China
        req_sg = MagicMock(spec=Requirement)
        req_sg.reference_id = "SG-001"
        req_sg.title = "Singapore Breach Notification"
        req_sg.description = "Notify within 3 days"
        req_sg.category = RequirementCategory.BREACH_NOTIFICATION
        req_sg.obligation_type = ObligationType.MUST
        req_sg.deadline_days = 3
        req_sg.action = "notify PDPC of breach"
        req_sg.data_types = ["personal_data"]
        req_sg.processes = ["breach_notification"]
        req_sg.regulation = MagicMock()
        req_sg.regulation.jurisdiction = Jurisdiction.SINGAPORE
        
        req_cn = MagicMock(spec=Requirement)
        req_cn.reference_id = "CN-001"
        req_cn.title = "China Breach Notification"
        req_cn.description = "Notify immediately"
        req_cn.category = RequirementCategory.BREACH_NOTIFICATION
        req_cn.obligation_type = ObligationType.MUST
        req_cn.deadline_days = 1  # Stricter
        req_cn.action = "notify authority of breach immediately"
        req_cn.data_types = ["personal_data"]
        req_cn.processes = ["breach_notification"]
        req_cn.regulation = MagicMock()
        req_cn.regulation.jurisdiction = Jurisdiction.CHINA
        
        result = resolver.resolve_conflict(
            [req_sg, req_cn],
            strategy=ConflictResolutionStrategy.MOST_RESTRICTIVE,
        )
        
        assert result.has_conflict is True
        assert result.resolved_requirement is not None
        # China requirement should be chosen (stricter deadline)
        assert result.resolved_requirement["deadline_days"] == 1
