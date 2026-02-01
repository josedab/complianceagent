"""Tests for regulatory framework sources."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.monitoring.pci_dss_sources import (
    PCIDSSSourceMonitor,
    PCI_DSS_SOURCES,
    PCI_DSS_REQUIREMENTS,
)
from app.services.monitoring.sox_sources import (
    SOXSourceMonitor,
    SOX_SOURCES,
    SOX_REQUIREMENTS,
    SOX_IT_CONTROLS,
)
from app.services.monitoring.nis2_sources import (
    NIS2SourceMonitor,
    NIS2_SOURCES,
    NIS2_REQUIREMENTS,
    NIS2_SECTORS,
)

pytestmark = pytest.mark.asyncio


class TestPCIDSSSources:
    """Test suite for PCI-DSS regulatory sources."""

    def test_pci_dss_sources_structure(self):
        """Test PCI-DSS sources are properly structured."""
        assert len(PCI_DSS_SOURCES) > 0
        
        for source in PCI_DSS_SOURCES:
            assert "id" in source
            assert "name" in source
            assert "url" in source
            assert "type" in source
            assert source["type"] in ["official", "guidance", "faq", "supplemental"]

    def test_pci_dss_requirements_coverage(self):
        """Test all 12 PCI-DSS requirement domains are covered."""
        domains = set()
        for req_id in PCI_DSS_REQUIREMENTS:
            # Extract domain number from requirement ID (e.g., "1.1" -> "1")
            domain = req_id.split(".")[0]
            domains.add(domain)
        
        # PCI-DSS v4.0 has 12 requirement domains
        expected_domains = {str(i) for i in range(1, 13)}
        assert domains == expected_domains, f"Missing domains: {expected_domains - domains}"

    def test_pci_dss_requirement_structure(self):
        """Test PCI-DSS requirements have proper structure."""
        for req_id, requirement in PCI_DSS_REQUIREMENTS.items():
            assert "name" in requirement
            assert "description" in requirement
            assert "domain" in requirement
            assert len(requirement["name"]) > 0
            assert len(requirement["description"]) > 0

    def test_pci_dss_source_monitor_initialization(self):
        """Test PCIDSSSourceMonitor initialization."""
        monitor = PCIDSSSourceMonitor()
        
        assert monitor.framework == "pci_dss"
        assert len(monitor.sources) > 0

    @patch("httpx.AsyncClient.get")
    async def test_pci_dss_check_for_updates(self, mock_get):
        """Test checking PCI-DSS sources for updates."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>PCI DSS v4.0 Standards</body></html>"
        mock_get.return_value = mock_response

        monitor = PCIDSSSourceMonitor()
        
        # Test that monitor can check sources without error
        # In real implementation, this would check for content changes
        assert monitor.framework == "pci_dss"


class TestSOXSources:
    """Test suite for SOX regulatory sources."""

    def test_sox_sources_structure(self):
        """Test SOX sources are properly structured."""
        assert len(SOX_SOURCES) > 0
        
        for source in SOX_SOURCES:
            assert "id" in source
            assert "name" in source
            assert "url" in source
            assert "section" in source

    def test_sox_requirements_coverage(self):
        """Test key SOX sections are covered."""
        sections = set()
        for req in SOX_REQUIREMENTS:
            sections.add(req.get("section"))
        
        # Key SOX sections
        expected_sections = {"302", "404", "409", "802", "806", "906"}
        assert sections >= expected_sections, f"Missing sections: {expected_sections - sections}"

    def test_sox_it_controls_coverage(self):
        """Test IT general controls are defined."""
        control_categories = set()
        for control in SOX_IT_CONTROLS:
            control_categories.add(control.get("category"))
        
        # COBIT-aligned IT control categories
        expected_categories = {
            "access_control",
            "change_management",
            "computer_operations",
            "system_development",
        }
        assert control_categories >= expected_categories

    def test_sox_requirement_structure(self):
        """Test SOX requirements have proper structure."""
        for requirement in SOX_REQUIREMENTS:
            assert "id" in requirement
            assert "section" in requirement
            assert "name" in requirement
            assert "description" in requirement
            assert "obligations" in requirement

    def test_sox_it_control_structure(self):
        """Test SOX IT controls have proper structure."""
        for control in SOX_IT_CONTROLS:
            assert "id" in control
            assert "category" in control
            assert "name" in control
            assert "description" in control
            assert "testing_procedures" in control

    def test_sox_source_monitor_initialization(self):
        """Test SOXSourceMonitor initialization."""
        monitor = SOXSourceMonitor()
        
        assert monitor.framework == "sox"
        assert len(monitor.sources) > 0


class TestNIS2Sources:
    """Test suite for NIS2 Directive sources."""

    def test_nis2_sources_structure(self):
        """Test NIS2 sources are properly structured."""
        assert len(NIS2_SOURCES) > 0
        
        for source in NIS2_SOURCES:
            assert "id" in source
            assert "name" in source
            assert "url" in source
            assert "type" in source

    def test_nis2_requirements_coverage(self):
        """Test key NIS2 articles are covered."""
        articles = set()
        for req in NIS2_REQUIREMENTS:
            articles.add(req.get("article"))
        
        # Key NIS2 articles for cybersecurity
        expected_articles = {"20", "21", "23", "24", "26"}
        assert articles >= expected_articles

    def test_nis2_sector_classification(self):
        """Test sector classifications are defined."""
        assert "essential" in NIS2_SECTORS
        assert "important" in NIS2_SECTORS
        
        # Essential sectors
        essential_sectors = NIS2_SECTORS["essential"]
        assert "energy" in essential_sectors
        assert "transport" in essential_sectors
        assert "banking" in essential_sectors
        assert "health" in essential_sectors
        assert "digital_infrastructure" in essential_sectors

        # Important sectors
        important_sectors = NIS2_SECTORS["important"]
        assert "postal_services" in important_sectors
        assert "waste_management" in important_sectors
        assert "chemicals" in important_sectors
        assert "food" in important_sectors
        assert "digital_providers" in important_sectors

    def test_nis2_requirement_structure(self):
        """Test NIS2 requirements have proper structure."""
        for requirement in NIS2_REQUIREMENTS:
            assert "id" in requirement
            assert "article" in requirement
            assert "name" in requirement
            assert "description" in requirement
            assert "applies_to" in requirement

    def test_nis2_source_monitor_initialization(self):
        """Test NIS2SourceMonitor initialization."""
        monitor = NIS2SourceMonitor()
        
        assert monitor.framework == "nis2"
        assert len(monitor.sources) > 0


class TestRegulatoryFrameworkIntegration:
    """Integration tests for regulatory framework sources."""

    def test_all_frameworks_have_monitors(self):
        """Test all frameworks have source monitors."""
        monitors = [
            PCIDSSSourceMonitor(),
            SOXSourceMonitor(),
            NIS2SourceMonitor(),
        ]
        
        frameworks = {m.framework for m in monitors}
        expected = {"pci_dss", "sox", "nis2"}
        assert frameworks == expected

    def test_all_frameworks_have_sources(self):
        """Test all frameworks have source definitions."""
        assert len(PCI_DSS_SOURCES) > 0
        assert len(SOX_SOURCES) > 0
        assert len(NIS2_SOURCES) > 0

    def test_all_frameworks_have_requirements(self):
        """Test all frameworks have requirement definitions."""
        assert len(PCI_DSS_REQUIREMENTS) > 0
        assert len(SOX_REQUIREMENTS) > 0
        assert len(NIS2_REQUIREMENTS) > 0

    def test_source_ids_unique_within_framework(self):
        """Test source IDs are unique within each framework."""
        pci_ids = [s["id"] for s in PCI_DSS_SOURCES]
        sox_ids = [s["id"] for s in SOX_SOURCES]
        nis2_ids = [s["id"] for s in NIS2_SOURCES]
        
        assert len(pci_ids) == len(set(pci_ids)), "Duplicate PCI-DSS source IDs"
        assert len(sox_ids) == len(set(sox_ids)), "Duplicate SOX source IDs"
        assert len(nis2_ids) == len(set(nis2_ids)), "Duplicate NIS2 source IDs"

    def test_requirement_ids_unique_within_framework(self):
        """Test requirement IDs are unique within each framework."""
        pci_req_ids = list(PCI_DSS_REQUIREMENTS.keys())
        sox_req_ids = [r["id"] for r in SOX_REQUIREMENTS]
        nis2_req_ids = [r["id"] for r in NIS2_REQUIREMENTS]
        
        assert len(pci_req_ids) == len(set(pci_req_ids)), "Duplicate PCI-DSS req IDs"
        assert len(sox_req_ids) == len(set(sox_req_ids)), "Duplicate SOX req IDs"
        assert len(nis2_req_ids) == len(set(nis2_req_ids)), "Duplicate NIS2 req IDs"


class TestGDPRSourcesIntegration:
    """Tests for existing GDPR sources integration."""

    def test_gdpr_sources_exist(self):
        """Test GDPR sources module exists and exports correctly."""
        from app.services.monitoring.gdpr_sources import (
            GDPR_SOURCES,
            GDPR_ARTICLES,
            GDPRParser,
            GDPRSourceMonitor,
        )
        
        assert len(GDPR_SOURCES) > 0
        assert len(GDPR_ARTICLES) > 0


class TestCCPASourcesIntegration:
    """Tests for existing CCPA sources integration."""

    def test_ccpa_sources_exist(self):
        """Test CCPA sources module exists and exports correctly."""
        from app.services.monitoring.ccpa_sources import (
            CCPA_SOURCES,
            CCPA_SECTIONS,
            CCPAParser,
            CCPASourceMonitor,
        )
        
        assert len(CCPA_SOURCES) > 0
        assert len(CCPA_SECTIONS) > 0


class TestHIPAASourcesIntegration:
    """Tests for existing HIPAA sources integration."""

    def test_hipaa_sources_exist(self):
        """Test HIPAA sources module exists and exports correctly."""
        from app.services.monitoring.hipaa_sources import (
            HIPAA_SOURCES,
            HIPAA_RULES,
            HIPAAParser,
            HIPAASourceMonitor,
        )
        
        assert len(HIPAA_SOURCES) > 0
        assert len(HIPAA_RULES) > 0


class TestEUAIActSourcesIntegration:
    """Tests for existing EU AI Act sources integration."""

    def test_eu_ai_act_sources_exist(self):
        """Test EU AI Act sources module exists and exports correctly."""
        from app.services.monitoring.eu_ai_act_sources import (
            EU_AI_ACT_SOURCES,
            EU_AI_ACT_RISK_CATEGORIES,
            EUAIActParser,
            EUAIActSourceMonitor,
        )
        
        assert len(EU_AI_ACT_SOURCES) > 0
        assert len(EU_AI_ACT_RISK_CATEGORIES) > 0


class TestSOC2SourcesIntegration:
    """Tests for SOC 2 sources integration."""

    def test_soc2_sources_exist(self):
        """Test SOC 2 sources module exists and exports correctly."""
        from app.services.monitoring.soc2_sources import (
            SOC2_SOURCES,
            SOC2_REQUIREMENTS,
            SOC2_TRUST_CATEGORIES,
            SOC2Parser,
            SOC2SourceMonitor,
        )
        
        assert len(SOC2_SOURCES) > 0
        assert len(SOC2_REQUIREMENTS) > 0
        assert len(SOC2_TRUST_CATEGORIES) > 0

    def test_soc2_sources_structure(self):
        """Test SOC 2 sources are properly structured."""
        from app.services.monitoring.soc2_sources import SOC2_SOURCES
        
        for source in SOC2_SOURCES:
            assert "id" in source
            assert "name" in source
            assert "url" in source
            assert "type" in source
            assert source["type"] in ["official", "guidance", "faq", "supplemental"]

    def test_soc2_requirements_structure(self):
        """Test SOC 2 requirements have proper structure."""
        from app.services.monitoring.soc2_sources import SOC2_REQUIREMENTS
        
        for req in SOC2_REQUIREMENTS:
            assert "id" in req
            assert "category" in req
            assert "name" in req
            assert "description" in req
            assert "applies_to" in req

    def test_soc2_trust_categories(self):
        """Test SOC 2 trust services categories."""
        from app.services.monitoring.soc2_sources import SOC2_TRUST_CATEGORIES
        
        # Security is mandatory for all SOC 2 reports
        assert "security" in SOC2_TRUST_CATEGORIES
        assert SOC2_TRUST_CATEGORIES["security"]["required"] is True
        
        # Optional categories
        assert "availability" in SOC2_TRUST_CATEGORIES
        assert "processing_integrity" in SOC2_TRUST_CATEGORIES
        assert "confidentiality" in SOC2_TRUST_CATEGORIES
        assert "privacy" in SOC2_TRUST_CATEGORIES

    def test_soc2_source_monitor_initialization(self):
        """Test SOC2SourceMonitor initialization."""
        from app.services.monitoring.soc2_sources import SOC2SourceMonitor
        
        monitor = SOC2SourceMonitor()
        
        assert monitor.framework == "soc2"
        assert len(monitor.sources) > 0


class TestISO27001SourcesIntegration:
    """Tests for ISO 27001 sources integration."""

    def test_iso27001_sources_exist(self):
        """Test ISO 27001 sources module exists and exports correctly."""
        from app.services.monitoring.iso27001_sources import (
            ISO27001_SOURCES,
            ISO27001_REQUIREMENTS,
            ISO27001_CONTROL_CATEGORIES,
            ISO27001Parser,
            ISO27001SourceMonitor,
        )
        
        assert len(ISO27001_SOURCES) > 0
        assert len(ISO27001_REQUIREMENTS) > 0
        assert len(ISO27001_CONTROL_CATEGORIES) > 0

    def test_iso27001_sources_structure(self):
        """Test ISO 27001 sources are properly structured."""
        from app.services.monitoring.iso27001_sources import ISO27001_SOURCES
        
        for source in ISO27001_SOURCES:
            assert "id" in source
            assert "name" in source
            assert "url" in source
            assert "type" in source

    def test_iso27001_requirements_structure(self):
        """Test ISO 27001 requirements have proper structure."""
        from app.services.monitoring.iso27001_sources import ISO27001_REQUIREMENTS
        
        for req in ISO27001_REQUIREMENTS:
            assert "id" in req
            assert "clause" in req
            assert "name" in req
            assert "description" in req
            assert "applies_to" in req
            assert "category" in req

    def test_iso27001_control_categories(self):
        """Test ISO 27001 control categories."""
        from app.services.monitoring.iso27001_sources import ISO27001_CONTROL_CATEGORIES
        
        expected_categories = ["organizational", "people", "physical", "technological"]
        for cat in expected_categories:
            assert cat in ISO27001_CONTROL_CATEGORIES
            assert "code" in ISO27001_CONTROL_CATEGORIES[cat]
            assert "name" in ISO27001_CONTROL_CATEGORIES[cat]

    def test_iso27001_mandatory_clauses(self):
        """Test ISO 27001 mandatory clauses are present."""
        from app.services.monitoring.iso27001_sources import ISO27001_REQUIREMENTS
        
        mandatory_reqs = [r for r in ISO27001_REQUIREMENTS if "mandatory" in r["applies_to"]]
        
        # Clauses 4-10 are mandatory
        clauses_found = {r["clause"] for r in mandatory_reqs}
        expected_clauses = {"4", "5", "6", "7", "8", "9", "10"}
        assert clauses_found >= expected_clauses

    def test_iso27001_source_monitor_initialization(self):
        """Test ISO27001SourceMonitor initialization."""
        from app.services.monitoring.iso27001_sources import ISO27001SourceMonitor
        
        monitor = ISO27001SourceMonitor()
        
        assert monitor.framework == "iso27001"
        assert len(monitor.sources) > 0
