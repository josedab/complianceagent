"""PCI-DSS regulatory source implementations."""

import re
from typing import Any

import structlog
from bs4 import BeautifulSoup

from app.models.regulation import Jurisdiction, RegulatoryFramework, RegulatorySource
from app.services.monitoring.crawler import RegulatoryCrawler


logger = structlog.get_logger()


# PCI-DSS source definitions
PCI_DSS_SOURCES = [
    {
        "id": "pci-dss-standards-library",
        "name": "PCI SSC Standards Library",
        "description": "Official PCI Security Standards Council documents",
        "url": "https://www.pcisecuritystandards.org/document_library/",
        "jurisdiction": Jurisdiction.GLOBAL,
        "framework": RegulatoryFramework.PCI_DSS,
        "parser_type": "html",
        "type": "official",
        "parser_config": {
            "content_selector": ".document-library",
            "document_selector": ".document-item",
        },
    },
    {
        "id": "pci-dss-v4-qrg",
        "name": "PCI DSS v4.0 Quick Reference",
        "description": "PCI DSS v4.0 requirements quick reference guide",
        "url": "https://www.pcisecuritystandards.org/documents/PCI_DSS-QRG-v4_0.pdf",
        "jurisdiction": Jurisdiction.GLOBAL,
        "framework": RegulatoryFramework.PCI_DSS,
        "parser_type": "pdf",
        "type": "guidance",
        "parser_config": {},
    },
    {
        "id": "pci-dss-faq",
        "name": "PCI DSS FAQs",
        "description": "Frequently asked questions about PCI DSS compliance",
        "url": "https://www.pcisecuritystandards.org/faqs",
        "jurisdiction": Jurisdiction.GLOBAL,
        "framework": RegulatoryFramework.PCI_DSS,
        "parser_type": "html",
        "type": "faq",
        "parser_config": {},
    },
    {
        "id": "pci-dss-supplemental",
        "name": "PCI DSS Supplemental Guidance",
        "description": "Supplemental guidance and information supplements",
        "url": "https://www.pcisecuritystandards.org/document_library/?category=guidance",
        "jurisdiction": Jurisdiction.GLOBAL,
        "framework": RegulatoryFramework.PCI_DSS,
        "parser_type": "html",
        "type": "supplemental",
        "parser_config": {},
    },
]


# PCI-DSS v4.0 Requirements structure (dict keyed by requirement ID for test compatibility)
PCI_DSS_REQUIREMENTS = {
    "1.1": {"name": "Processes and mechanisms for network security controls", "description": "Processes and mechanisms for installing and maintaining network security controls are defined and understood.", "domain": "1"},
    "1.2": {"name": "Network security controls configured", "description": "Network security controls are configured and maintained.", "domain": "1"},
    "1.3": {"name": "Network access restricted", "description": "Network access to and from the cardholder data environment is restricted.", "domain": "1"},
    "1.4": {"name": "Network connections controlled", "description": "Network connections between trusted and untrusted networks are controlled.", "domain": "1"},
    "1.5": {"name": "CDE risks mitigated", "description": "Risks to the CDE from computing devices connecting to untrusted networks are mitigated.", "domain": "1"},
    "2.1": {"name": "Secure configuration processes", "description": "Processes for applying secure configurations are defined and understood.", "domain": "2"},
    "2.2": {"name": "System components secured", "description": "System components are configured and managed securely.", "domain": "2"},
    "2.3": {"name": "Wireless environments secured", "description": "Wireless environments are configured and managed securely.", "domain": "2"},
    "3.1": {"name": "Stored account data processes", "description": "Processes for protecting stored account data are defined and understood.", "domain": "3"},
    "3.2": {"name": "Data storage minimized", "description": "Storage of account data is kept to a minimum.", "domain": "3"},
    "3.3": {"name": "SAD not stored", "description": "Sensitive authentication data (SAD) is not stored after authorization.", "domain": "3"},
    "3.4": {"name": "PAN display restricted", "description": "Access to displays of full PAN and ability to copy cardholder data are restricted.", "domain": "3"},
    "3.5": {"name": "PAN secured", "description": "PAN is secured wherever it is stored.", "domain": "3"},
    "3.6": {"name": "Cryptographic keys secured", "description": "Cryptographic keys used to protect stored account data are secured.", "domain": "3"},
    "3.7": {"name": "Key management implemented", "description": "Where cryptography is used to protect stored account data, key management processes are defined and implemented.", "domain": "3"},
    "4.1": {"name": "Transmission protection processes", "description": "Processes for protecting cardholder data with strong cryptography during transmission are defined.", "domain": "4"},
    "4.2": {"name": "PAN transmission protected", "description": "PAN is protected with strong cryptography during transmission.", "domain": "4"},
    "5.1": {"name": "Malware protection processes", "description": "Processes for protecting systems from malware are defined and understood.", "domain": "5"},
    "5.2": {"name": "Malware prevented or detected", "description": "Malware is prevented or detected and addressed.", "domain": "5"},
    "5.3": {"name": "Anti-malware maintained", "description": "Anti-malware mechanisms and processes are active, maintained, and monitored.", "domain": "5"},
    "5.4": {"name": "Anti-phishing implemented", "description": "Anti-phishing mechanisms protect users against phishing attacks.", "domain": "5"},
    "6.1": {"name": "Secure development processes", "description": "Processes for developing secure systems and software are defined and understood.", "domain": "6"},
    "6.2": {"name": "Custom software secured", "description": "Bespoke and custom software is developed securely.", "domain": "6"},
    "6.3": {"name": "Vulnerabilities addressed", "description": "Security vulnerabilities are identified and addressed.", "domain": "6"},
    "6.4": {"name": "Web applications protected", "description": "Public-facing web applications are protected against attacks.", "domain": "6"},
    "6.5": {"name": "Changes managed securely", "description": "Changes to all system components are managed securely.", "domain": "6"},
    "7.1": {"name": "Access restriction processes", "description": "Processes for restricting access to system components are defined and understood.", "domain": "7"},
    "7.2": {"name": "Access appropriately assigned", "description": "Access to system components and data is appropriately defined and assigned.", "domain": "7"},
    "7.3": {"name": "Access control system used", "description": "Access to system components and data is managed via an access control system.", "domain": "7"},
    "8.1": {"name": "User identification processes", "description": "Processes for identifying users and authenticating access are defined and understood.", "domain": "8"},
    "8.2": {"name": "User accounts managed", "description": "User identification and related accounts are strictly managed.", "domain": "8"},
    "8.3": {"name": "Strong authentication established", "description": "Strong authentication for users and administrators is established and managed.", "domain": "8"},
    "8.4": {"name": "MFA implemented", "description": "Multi-factor authentication is implemented to secure access to the CDE.", "domain": "8"},
    "8.5": {"name": "MFA systems configured", "description": "Multi-factor authentication systems are configured to prevent misuse.", "domain": "8"},
    "8.6": {"name": "Application accounts managed", "description": "Use of application and system accounts is strictly managed.", "domain": "8"},
    "9.1": {"name": "Physical access processes", "description": "Processes for restricting physical access are defined and understood.", "domain": "9"},
    "9.2": {"name": "Physical controls manage entry", "description": "Physical access controls manage entry into facilities and systems containing cardholder data.", "domain": "9"},
    "9.3": {"name": "Physical access authorized", "description": "Physical access for personnel and visitors is authorized and managed.", "domain": "9"},
    "9.4": {"name": "Media securely handled", "description": "Media with cardholder data is securely stored, accessed, distributed, and destroyed.", "domain": "9"},
    "9.5": {"name": "POI devices protected", "description": "POI devices are protected from tampering and unauthorized substitution.", "domain": "9"},
    "10.1": {"name": "Logging processes defined", "description": "Processes for logging and monitoring all access are defined and understood.", "domain": "10"},
    "10.2": {"name": "Audit logs implemented", "description": "Audit logs are implemented to support the detection of anomalies.", "domain": "10"},
    "10.3": {"name": "Audit logs protected", "description": "Audit logs are protected from destruction and unauthorized modifications.", "domain": "10"},
    "10.4": {"name": "Audit logs reviewed", "description": "Audit logs are reviewed to identify anomalies or suspicious activity.", "domain": "10"},
    "10.5": {"name": "Audit log history retained", "description": "Audit log history is retained and available for analysis.", "domain": "10"},
    "10.6": {"name": "Time synchronization used", "description": "Time-synchronization mechanisms support consistent time across systems.", "domain": "10"},
    "10.7": {"name": "Security control failures detected", "description": "Failures of critical security control systems are detected, reported, and responded to.", "domain": "10"},
    "11.1": {"name": "Security testing processes", "description": "Processes for testing security are defined and understood.", "domain": "11"},
    "11.2": {"name": "Wireless access points monitored", "description": "Wireless access points are identified and monitored.", "domain": "11"},
    "11.3": {"name": "Vulnerabilities regularly addressed", "description": "External and internal vulnerabilities are regularly identified and addressed.", "domain": "11"},
    "11.4": {"name": "Penetration testing performed", "description": "External and internal penetration testing is regularly performed.", "domain": "11"},
    "11.5": {"name": "Intrusions detected", "description": "Network intrusions and unexpected file changes are detected and responded to.", "domain": "11"},
    "11.6": {"name": "Payment page changes detected", "description": "Unauthorized changes on payment pages are detected and responded to.", "domain": "11"},
    "12.1": {"name": "Security policy in place", "description": "A comprehensive information security policy is known and in place.", "domain": "12"},
    "12.2": {"name": "Acceptable use policies defined", "description": "Acceptable use policies for end-user technologies are defined and implemented.", "domain": "12"},
    "12.3": {"name": "Risks formally managed", "description": "Risks to the cardholder data environment are formally identified and managed.", "domain": "12"},
    "12.4": {"name": "Compliance managed", "description": "PCI DSS compliance is managed throughout the year.", "domain": "12"},
    "12.5": {"name": "Scope documented", "description": "PCI DSS scope is documented and validated.", "domain": "12"},
    "12.6": {"name": "Security awareness ongoing", "description": "Security awareness education is an ongoing activity.", "domain": "12"},
    "12.7": {"name": "Personnel screened", "description": "Personnel are screened to reduce risks from insider threats.", "domain": "12"},
    "12.8": {"name": "Third-party risk managed", "description": "Risk to information assets from third-party service provider relationships is managed.", "domain": "12"},
    "12.9": {"name": "TPSPs support compliance", "description": "Third-party service providers support their customers' PCI DSS compliance.", "domain": "12"},
    "12.10": {"name": "Security incidents responded to", "description": "Suspected and confirmed security incidents are responded to immediately.", "domain": "12"},
}


class PCIDSSParser:
    """Parser for PCI-DSS documents."""

    def __init__(self):
        self.requirement_pattern = re.compile(r"(\d+\.\d+(?:\.\d+)?)\s+(.*)")

    def parse_standards_library(self, content: str) -> list[dict[str, Any]]:
        """Parse PCI SSC Standards Library page."""
        soup = BeautifulSoup(content, "lxml")
        documents = []

        for item in soup.select(".document-item, .resource-item, article"):
            title_elem = item.select_one("h3, h4, .title, a")
            date_elem = item.select_one(".date, time, .published-date")
            link_elem = item.select_one("a[href*='.pdf'], a[href*='document']")

            if title_elem:
                documents.append({
                    "title": title_elem.get_text(strip=True),
                    "url": link_elem.get("href") if link_elem else None,
                    "date": date_elem.get_text(strip=True) if date_elem else None,
                    "type": "standard" if "standard" in title_elem.get_text().lower() else "guidance",
                })

        return documents

    def get_all_requirements(self) -> list[dict[str, Any]]:
        """Get all PCI-DSS v4.0 requirements."""
        all_requirements = []

        for domain_num, domain in PCI_DSS_REQUIREMENTS.items():
            for req in domain["requirements"]:
                all_requirements.append({
                    "requirement_id": f"PCI-DSS-{req['id']}",
                    "domain": domain_num,
                    "domain_title": domain["title"],
                    "title": req["title"],
                    "obligation_type": req["obligation"],
                    "framework": "PCI_DSS",
                    "version": "4.0",
                    "citation": {
                        "requirement": req["id"],
                        "domain": f"Requirement {domain_num}",
                    },
                })

        return all_requirements


class PCIDSSSourceMonitor:
    """Monitors PCI-DSS regulatory sources."""

    def __init__(self):
        self.crawler = RegulatoryCrawler()
        self.parser = PCIDSSParser()
        self.framework = "pci_dss"
        self.sources = PCI_DSS_SOURCES

    async def check_standards_library(self, source: RegulatorySource) -> dict[str, Any]:
        """Check PCI SSC for updates."""
        async with self.crawler:
            result = await self.crawler.crawl(source)

            if result.has_changed:
                documents = self.parser.parse_standards_library(result.content)
                return {
                    "changed": True,
                    "source": source.name,
                    "documents": documents,
                    "documents_count": len(documents),
                }

            return {"changed": False, "source": source.name}

    def get_all_requirements(self) -> list[dict[str, Any]]:
        """Get all PCI-DSS requirements for database initialization."""
        return self.parser.get_all_requirements()


def get_pci_dss_source_definitions() -> list[dict[str, Any]]:
    """Get predefined PCI-DSS source definitions."""
    return PCI_DSS_SOURCES


async def initialize_pci_dss_sources(db) -> list[RegulatorySource]:
    """Initialize PCI-DSS sources in the database."""
    sources = []

    for source_def in PCI_DSS_SOURCES:
        source = RegulatorySource(
            name=source_def["name"],
            description=source_def["description"],
            url=source_def["url"],
            jurisdiction=source_def["jurisdiction"],
            framework=source_def["framework"],
            parser_type=source_def["parser_type"],
            parser_config=source_def["parser_config"],
            is_active=True,
            check_interval_hours=168,  # Weekly for PCI
        )
        db.add(source)
        sources.append(source)

    await db.flush()
    return sources
