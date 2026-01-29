"""Regulatory monitoring services."""

from app.services.monitoring.ccpa_sources import (
    CCPAParser,
    CCPASourceMonitor,
    get_ccpa_source_definitions,
    initialize_ccpa_sources,
)
from app.services.monitoring.crawler import CrawlerResult, RegulatoryCrawler
from app.services.monitoring.eu_ai_act_sources import (
    EUAIActParser,
    EUAIActSourceMonitor,
    get_eu_ai_act_source_definitions,
    initialize_eu_ai_act_sources,
)
from app.services.monitoring.gdpr_sources import (
    GDPRParser,
    GDPRSourceMonitor,
    get_gdpr_source_definitions,
    initialize_gdpr_sources,
)
from app.services.monitoring.hipaa_sources import (
    HIPAAParser,
    HIPAASourceMonitor,
    get_hipaa_source_definitions,
    initialize_hipaa_sources,
)
from app.services.monitoring.iso27001_sources import (
    ISO27001Parser,
    ISO27001SourceMonitor,
    get_iso27001_source_definitions,
    initialize_iso27001_sources,
)
from app.services.monitoring.nis2_sources import (
    NIS2Parser,
    NIS2SourceMonitor,
    get_nis2_source_definitions,
    initialize_nis2_sources,
)
from app.services.monitoring.pci_dss_sources import (
    PCIDSSParser,
    PCIDSSSourceMonitor,
    get_pci_dss_source_definitions,
    initialize_pci_dss_sources,
)
from app.services.monitoring.service import MonitoringService
from app.services.monitoring.soc2_sources import (
    SOC2Parser,
    SOC2SourceMonitor,
    get_soc2_source_definitions,
    initialize_soc2_sources,
)
from app.services.monitoring.sox_sources import (
    SOXParser,
    SOXSourceMonitor,
    get_sox_source_definitions,
    initialize_sox_sources,
)
# Asia-Pacific sources
from app.services.monitoring.singapore_pdpa_sources import (
    SingaporePDPAParser,
    SingaporePDPASourceMonitor,
    get_singapore_pdpa_source_definitions,
    initialize_singapore_pdpa_sources,
)
from app.services.monitoring.india_dpdp_sources import (
    IndiaDPDPParser,
    IndiaDPDPSourceMonitor,
    get_india_dpdp_source_definitions,
    initialize_india_dpdp_sources,
)
from app.services.monitoring.japan_appi_sources import (
    JapanAPPIParser,
    JapanAPPISourceMonitor,
    get_japan_appi_source_definitions,
    initialize_japan_appi_sources,
)
from app.services.monitoring.korea_pipa_sources import (
    KoreaPIPAParser,
    KoreaPIPASourceMonitor,
    get_korea_pipa_source_definitions,
    initialize_korea_pipa_sources,
)
from app.services.monitoring.china_pipl_sources import (
    ChinaPIPLParser,
    ChinaPIPLSourceMonitor,
    get_china_pipl_source_definitions,
    initialize_china_pipl_sources,
)
# ESG sources
from app.services.monitoring.esg_sources import (
    ESGParser,
    ESGSourceMonitor,
    get_esg_source_definitions,
    initialize_esg_sources,
)
# AI Safety sources
from app.services.monitoring.ai_safety_sources import (
    AISafetyParser,
    AISafetySourceMonitor,
    AIRiskClassifier,
    AIRiskLevel,
    AISystemClassification,
    get_ai_safety_source_definitions,
    initialize_ai_safety_sources,
)


__all__ = [
    # CCPA
    "CCPAParser",
    "CCPASourceMonitor",
    "CrawlerResult",
    # EU AI Act
    "EUAIActParser",
    "EUAIActSourceMonitor",
    # GDPR
    "GDPRParser",
    "GDPRSourceMonitor",
    # HIPAA
    "HIPAAParser",
    "HIPAASourceMonitor",
    # ISO 27001
    "ISO27001Parser",
    "ISO27001SourceMonitor",
    # Main services
    "MonitoringService",
    # NIS2
    "NIS2Parser",
    "NIS2SourceMonitor",
    # PCI-DSS
    "PCIDSSParser",
    "PCIDSSSourceMonitor",
    "RegulatoryCrawler",
    # SOC 2
    "SOC2Parser",
    "SOC2SourceMonitor",
    # SOX
    "SOXParser",
    "SOXSourceMonitor",
    # Singapore PDPA
    "SingaporePDPAParser",
    "SingaporePDPASourceMonitor",
    # India DPDP
    "IndiaDPDPParser",
    "IndiaDPDPSourceMonitor",
    # Japan APPI
    "JapanAPPIParser",
    "JapanAPPISourceMonitor",
    # Korea PIPA
    "KoreaPIPAParser",
    "KoreaPIPASourceMonitor",
    # China PIPL
    "ChinaPIPLParser",
    "ChinaPIPLSourceMonitor",
    # ESG
    "ESGParser",
    "ESGSourceMonitor",
    # AI Safety
    "AISafetyParser",
    "AISafetySourceMonitor",
    "AIRiskClassifier",
    "AIRiskLevel",
    "AISystemClassification",
    # Source definitions
    "get_ccpa_source_definitions",
    "get_eu_ai_act_source_definitions",
    "get_gdpr_source_definitions",
    "get_hipaa_source_definitions",
    "get_iso27001_source_definitions",
    "get_nis2_source_definitions",
    "get_pci_dss_source_definitions",
    "get_soc2_source_definitions",
    "get_sox_source_definitions",
    "get_singapore_pdpa_source_definitions",
    "get_india_dpdp_source_definitions",
    "get_japan_appi_source_definitions",
    "get_korea_pipa_source_definitions",
    "get_china_pipl_source_definitions",
    "get_esg_source_definitions",
    "get_ai_safety_source_definitions",
    # Initialization functions
    "initialize_ccpa_sources",
    "initialize_eu_ai_act_sources",
    "initialize_gdpr_sources",
    "initialize_hipaa_sources",
    "initialize_iso27001_sources",
    "initialize_nis2_sources",
    "initialize_pci_dss_sources",
    "initialize_soc2_sources",
    "initialize_sox_sources",
    "initialize_singapore_pdpa_sources",
    "initialize_india_dpdp_sources",
    "initialize_japan_appi_sources",
    "initialize_korea_pipa_sources",
    "initialize_china_pipl_sources",
    "initialize_esg_sources",
    "initialize_ai_safety_sources",
]
