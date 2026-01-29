"""SOC 2 (Service Organization Control 2) regulatory source implementations."""

import re
from typing import Any

import structlog
from bs4 import BeautifulSoup

from app.models.regulation import Jurisdiction, RegulatoryFramework, RegulatorySource
from app.services.monitoring.crawler import RegulatoryCrawler


logger = structlog.get_logger()


# SOC 2 source definitions
SOC2_SOURCES = [
    {
        "id": "soc2-aicpa-tsc",
        "name": "AICPA Trust Services Criteria",
        "description": "AICPA Trust Services Criteria for SOC 2 engagements",
        "url": "https://www.aicpa.org/interestareas/frc/assuranceadvisoryservices/sorhome",
        "jurisdiction": Jurisdiction.GLOBAL,
        "framework": RegulatoryFramework.SOC2,
        "parser_type": "html",
        "type": "official",
        "parser_config": {
            "content_selector": "#main-content",
        },
    },
    {
        "id": "soc2-aicpa-guide",
        "name": "SOC 2 Reporting Guide",
        "description": "AICPA Guide for SOC 2 examinations",
        "url": "https://www.aicpa.org/resources/download/soc-2-reporting-on-an-examination-of-controls",
        "jurisdiction": Jurisdiction.GLOBAL,
        "framework": RegulatoryFramework.SOC2,
        "parser_type": "pdf",
        "type": "guidance",
        "parser_config": {},
    },
    {
        "id": "soc2-aicpa-faq",
        "name": "SOC 2 FAQs",
        "description": "Frequently asked questions about SOC 2 reporting",
        "url": "https://www.aicpa.org/interestareas/frc/assuranceadvisoryservices/serviceorganization-smanagement",
        "jurisdiction": Jurisdiction.GLOBAL,
        "framework": RegulatoryFramework.SOC2,
        "parser_type": "html",
        "type": "faq",
        "parser_config": {},
    },
]


# SOC 2 Trust Services Categories (TSC)
SOC2_TRUST_CATEGORIES = {
    "security": {
        "name": "Security",
        "code": "CC",
        "description": "The system is protected against unauthorized access, use, or modification",
        "required": True,
    },
    "availability": {
        "name": "Availability",
        "code": "A",
        "description": "The system is available for operation and use as committed or agreed",
        "required": False,
    },
    "processing_integrity": {
        "name": "Processing Integrity",
        "code": "PI",
        "description": "System processing is complete, valid, accurate, timely, and authorized",
        "required": False,
    },
    "confidentiality": {
        "name": "Confidentiality",
        "code": "C",
        "description": "Information designated as confidential is protected as committed or agreed",
        "required": False,
    },
    "privacy": {
        "name": "Privacy",
        "code": "P",
        "description": "Personal information is collected, used, retained, disclosed, and disposed of in conformity with commitments",
        "required": False,
    },
}


# SOC 2 Common Criteria (Security - Required for all SOC 2 reports)
SOC2_REQUIREMENTS = [
    # CC1 - Control Environment
    {
        "id": "SOC2-CC1.1",
        "category": "security",
        "criteria_code": "CC1.1",
        "name": "Commitment to Integrity and Ethics",
        "description": "The entity demonstrates a commitment to integrity and ethical values",
        "applies_to": ["all"],
    },
    {
        "id": "SOC2-CC1.2",
        "category": "security",
        "criteria_code": "CC1.2",
        "name": "Board Independence",
        "description": "The board of directors demonstrates independence from management and exercises oversight",
        "applies_to": ["all"],
    },
    {
        "id": "SOC2-CC1.3",
        "category": "security",
        "criteria_code": "CC1.3",
        "name": "Management Structure",
        "description": "Management establishes structures, reporting lines, authorities, and responsibilities",
        "applies_to": ["all"],
    },
    {
        "id": "SOC2-CC1.4",
        "category": "security",
        "criteria_code": "CC1.4",
        "name": "Competent Personnel",
        "description": "The entity demonstrates commitment to attract, develop, and retain competent individuals",
        "applies_to": ["all"],
    },
    {
        "id": "SOC2-CC1.5",
        "category": "security",
        "criteria_code": "CC1.5",
        "name": "Accountability",
        "description": "The entity holds individuals accountable for internal control responsibilities",
        "applies_to": ["all"],
    },
    # CC2 - Communication and Information
    {
        "id": "SOC2-CC2.1",
        "category": "security",
        "criteria_code": "CC2.1",
        "name": "Internal Information Quality",
        "description": "The entity obtains/generates relevant, quality information to support internal control functioning",
        "applies_to": ["all"],
    },
    {
        "id": "SOC2-CC2.2",
        "category": "security",
        "criteria_code": "CC2.2",
        "name": "Internal Communication",
        "description": "The entity internally communicates information necessary to support internal control functioning",
        "applies_to": ["all"],
    },
    {
        "id": "SOC2-CC2.3",
        "category": "security",
        "criteria_code": "CC2.3",
        "name": "External Communication",
        "description": "The entity communicates with external parties regarding matters affecting internal control functioning",
        "applies_to": ["all"],
    },
    # CC3 - Risk Assessment
    {
        "id": "SOC2-CC3.1",
        "category": "security",
        "criteria_code": "CC3.1",
        "name": "Risk Objectives",
        "description": "The entity specifies objectives with sufficient clarity to identify and assess risks",
        "applies_to": ["all"],
    },
    {
        "id": "SOC2-CC3.2",
        "category": "security",
        "criteria_code": "CC3.2",
        "name": "Risk Identification",
        "description": "The entity identifies risks to achievement of objectives and analyzes as basis for risk management",
        "applies_to": ["all"],
    },
    {
        "id": "SOC2-CC3.3",
        "category": "security",
        "criteria_code": "CC3.3",
        "name": "Fraud Risk",
        "description": "The entity considers potential for fraud in assessing risks",
        "applies_to": ["all"],
    },
    {
        "id": "SOC2-CC3.4",
        "category": "security",
        "criteria_code": "CC3.4",
        "name": "Change Identification",
        "description": "The entity identifies and assesses changes that could significantly affect internal controls",
        "applies_to": ["all"],
    },
    # CC4 - Monitoring Activities
    {
        "id": "SOC2-CC4.1",
        "category": "security",
        "criteria_code": "CC4.1",
        "name": "Ongoing Monitoring",
        "description": "The entity selects, develops, and performs ongoing evaluations to ascertain control effectiveness",
        "applies_to": ["all"],
    },
    {
        "id": "SOC2-CC4.2",
        "category": "security",
        "criteria_code": "CC4.2",
        "name": "Deficiency Communication",
        "description": "The entity evaluates and communicates internal control deficiencies to responsible parties",
        "applies_to": ["all"],
    },
    # CC5 - Control Activities
    {
        "id": "SOC2-CC5.1",
        "category": "security",
        "criteria_code": "CC5.1",
        "name": "Control Selection",
        "description": "The entity selects and develops control activities that mitigate risks",
        "applies_to": ["all"],
    },
    {
        "id": "SOC2-CC5.2",
        "category": "security",
        "criteria_code": "CC5.2",
        "name": "Technology Controls",
        "description": "The entity selects and develops general control activities over technology",
        "applies_to": ["all"],
    },
    {
        "id": "SOC2-CC5.3",
        "category": "security",
        "criteria_code": "CC5.3",
        "name": "Policy Deployment",
        "description": "The entity deploys control activities through policies and procedures",
        "applies_to": ["all"],
    },
    # CC6 - Logical and Physical Access Controls
    {
        "id": "SOC2-CC6.1",
        "category": "security",
        "criteria_code": "CC6.1",
        "name": "Security Software/Infrastructure",
        "description": "The entity implements logical access security software, infrastructure, and architectures",
        "applies_to": ["all"],
    },
    {
        "id": "SOC2-CC6.2",
        "category": "security",
        "criteria_code": "CC6.2",
        "name": "Access Credentials",
        "description": "Prior to issuing credentials and granting system access, the entity registers and authorizes users",
        "applies_to": ["all"],
    },
    {
        "id": "SOC2-CC6.3",
        "category": "security",
        "criteria_code": "CC6.3",
        "name": "Access Removal",
        "description": "The entity removes access when no longer required",
        "applies_to": ["all"],
    },
    {
        "id": "SOC2-CC6.4",
        "category": "security",
        "criteria_code": "CC6.4",
        "name": "Access Review",
        "description": "The entity restricts physical access and reviews access periodically",
        "applies_to": ["all"],
    },
    {
        "id": "SOC2-CC6.5",
        "category": "security",
        "criteria_code": "CC6.5",
        "name": "Asset Disposal",
        "description": "The entity disposes of, destroys, or removes data on assets when no longer needed",
        "applies_to": ["all"],
    },
    {
        "id": "SOC2-CC6.6",
        "category": "security",
        "criteria_code": "CC6.6",
        "name": "External Threats",
        "description": "The entity implements controls to prevent or detect and act upon unauthorized software introduction",
        "applies_to": ["all"],
    },
    {
        "id": "SOC2-CC6.7",
        "category": "security",
        "criteria_code": "CC6.7",
        "name": "Transmission Protection",
        "description": "The entity restricts transmission, movement, and removal of information to authorized parties",
        "applies_to": ["all"],
    },
    {
        "id": "SOC2-CC6.8",
        "category": "security",
        "criteria_code": "CC6.8",
        "name": "Unauthorized Access Prevention",
        "description": "The entity implements controls to prevent or detect and act upon introduction of unauthorized code",
        "applies_to": ["all"],
    },
    # CC7 - System Operations
    {
        "id": "SOC2-CC7.1",
        "category": "security",
        "criteria_code": "CC7.1",
        "name": "Vulnerability Detection",
        "description": "The entity detects and monitors security vulnerabilities",
        "applies_to": ["all"],
    },
    {
        "id": "SOC2-CC7.2",
        "category": "security",
        "criteria_code": "CC7.2",
        "name": "Incident Monitoring",
        "description": "The entity monitors system components for anomalies indicative of malicious acts",
        "applies_to": ["all"],
    },
    {
        "id": "SOC2-CC7.3",
        "category": "security",
        "criteria_code": "CC7.3",
        "name": "Security Event Evaluation",
        "description": "The entity evaluates security events to determine if they could impact the system",
        "applies_to": ["all"],
    },
    {
        "id": "SOC2-CC7.4",
        "category": "security",
        "criteria_code": "CC7.4",
        "name": "Incident Response",
        "description": "The entity responds to identified security incidents",
        "applies_to": ["all"],
    },
    {
        "id": "SOC2-CC7.5",
        "category": "security",
        "criteria_code": "CC7.5",
        "name": "Incident Recovery",
        "description": "The entity identifies, develops, and implements activities to recover from incidents",
        "applies_to": ["all"],
    },
    # CC8 - Change Management
    {
        "id": "SOC2-CC8.1",
        "category": "security",
        "criteria_code": "CC8.1",
        "name": "Change Authorization",
        "description": "The entity authorizes, designs, develops, configures, and tests changes",
        "applies_to": ["all"],
    },
    # CC9 - Risk Mitigation
    {
        "id": "SOC2-CC9.1",
        "category": "security",
        "criteria_code": "CC9.1",
        "name": "Business Disruption Risk",
        "description": "The entity identifies, selects, and develops risk mitigation activities for business disruption risks",
        "applies_to": ["all"],
    },
    {
        "id": "SOC2-CC9.2",
        "category": "security",
        "criteria_code": "CC9.2",
        "name": "Vendor Risk Management",
        "description": "The entity assesses and manages risks associated with vendors and business partners",
        "applies_to": ["all"],
    },
    # Availability Criteria
    {
        "id": "SOC2-A1.1",
        "category": "availability",
        "criteria_code": "A1.1",
        "name": "Capacity Planning",
        "description": "The entity maintains, monitors, and evaluates capacity requirements",
        "applies_to": ["availability"],
    },
    {
        "id": "SOC2-A1.2",
        "category": "availability",
        "criteria_code": "A1.2",
        "name": "Environmental Protection",
        "description": "The entity authorizes, designs, and manages environmental protections",
        "applies_to": ["availability"],
    },
    {
        "id": "SOC2-A1.3",
        "category": "availability",
        "criteria_code": "A1.3",
        "name": "Recovery Testing",
        "description": "The entity tests recovery plan procedures to achieve objectives",
        "applies_to": ["availability"],
    },
    # Processing Integrity Criteria
    {
        "id": "SOC2-PI1.1",
        "category": "processing_integrity",
        "criteria_code": "PI1.1",
        "name": "Processing Accuracy",
        "description": "The entity implements policies for defining processing activities",
        "applies_to": ["processing_integrity"],
    },
    {
        "id": "SOC2-PI1.2",
        "category": "processing_integrity",
        "criteria_code": "PI1.2",
        "name": "Input Validation",
        "description": "The entity implements policies for data input accuracy and completeness",
        "applies_to": ["processing_integrity"],
    },
    {
        "id": "SOC2-PI1.3",
        "category": "processing_integrity",
        "criteria_code": "PI1.3",
        "name": "Processing Monitoring",
        "description": "The entity implements policies for processing monitoring",
        "applies_to": ["processing_integrity"],
    },
    {
        "id": "SOC2-PI1.4",
        "category": "processing_integrity",
        "criteria_code": "PI1.4",
        "name": "Output Review",
        "description": "The entity implements policies for output completeness, accuracy, and timeliness",
        "applies_to": ["processing_integrity"],
    },
    {
        "id": "SOC2-PI1.5",
        "category": "processing_integrity",
        "criteria_code": "PI1.5",
        "name": "Data Retention",
        "description": "The entity implements policies for data storage and retention",
        "applies_to": ["processing_integrity"],
    },
    # Confidentiality Criteria
    {
        "id": "SOC2-C1.1",
        "category": "confidentiality",
        "criteria_code": "C1.1",
        "name": "Confidential Information Identification",
        "description": "The entity identifies and maintains confidential information",
        "applies_to": ["confidentiality"],
    },
    {
        "id": "SOC2-C1.2",
        "category": "confidentiality",
        "criteria_code": "C1.2",
        "name": "Confidential Information Disposal",
        "description": "The entity disposes of confidential information to meet objectives",
        "applies_to": ["confidentiality"],
    },
    # Privacy Criteria
    {
        "id": "SOC2-P1.1",
        "category": "privacy",
        "criteria_code": "P1.1",
        "name": "Privacy Notice",
        "description": "The entity provides notice to data subjects about privacy practices",
        "applies_to": ["privacy"],
    },
    {
        "id": "SOC2-P2.1",
        "category": "privacy",
        "criteria_code": "P2.1",
        "name": "Privacy Choice",
        "description": "The entity communicates choices available regarding collection and use of personal information",
        "applies_to": ["privacy"],
    },
    {
        "id": "SOC2-P3.1",
        "category": "privacy",
        "criteria_code": "P3.1",
        "name": "Collection Limitation",
        "description": "Personal information is collected consistent with entity objectives",
        "applies_to": ["privacy"],
    },
    {
        "id": "SOC2-P4.1",
        "category": "privacy",
        "criteria_code": "P4.1",
        "name": "Use Limitation",
        "description": "Personal information is limited to purposes identified in privacy notice",
        "applies_to": ["privacy"],
    },
    {
        "id": "SOC2-P5.1",
        "category": "privacy",
        "criteria_code": "P5.1",
        "name": "Retention Limitation",
        "description": "Personal information is retained only as long as necessary",
        "applies_to": ["privacy"],
    },
    {
        "id": "SOC2-P6.1",
        "category": "privacy",
        "criteria_code": "P6.1",
        "name": "Access Rights",
        "description": "The entity provides data subjects with access to their personal information",
        "applies_to": ["privacy"],
    },
    {
        "id": "SOC2-P7.1",
        "category": "privacy",
        "criteria_code": "P7.1",
        "name": "Disclosure Limitation",
        "description": "Personal information is disclosed to third parties only for identified purposes",
        "applies_to": ["privacy"],
    },
    {
        "id": "SOC2-P8.1",
        "category": "privacy",
        "criteria_code": "P8.1",
        "name": "Data Quality",
        "description": "The entity maintains accurate, complete, and relevant personal information",
        "applies_to": ["privacy"],
    },
]


class SOC2Parser:
    """Parser for SOC 2-related documents."""

    def __init__(self):
        self.criteria_pattern = re.compile(r"(CC|A|PI|C|P)(\d+\.\d+)", re.IGNORECASE)

    def parse_aicpa_page(self, content: str) -> dict[str, Any]:
        """Parse AICPA SOC 2 guidance page."""
        soup = BeautifulSoup(content, "lxml")

        result = {
            "title": "",
            "documents": [],
            "updates": [],
        }

        # Extract main content
        main_content = soup.find("main") or soup.find("div", id="main-content")
        if main_content:
            title = main_content.find("h1")
            if title:
                result["title"] = title.get_text(strip=True)

            # Find document links
            for link in main_content.select("a[href*='.pdf'], a[href*='/download']"):
                text = link.get_text(strip=True)
                href = link.get("href", "")
                if text and len(text) > 5:
                    result["documents"].append({
                        "title": text,
                        "url": href if href.startswith("http") else f"https://www.aicpa.org{href}",
                        "type": "guidance",
                    })

        return result

    def get_all_requirements(self) -> list[dict[str, Any]]:
        """Get all SOC 2 requirements for database initialization."""
        return SOC2_REQUIREMENTS

    def get_requirements_by_category(self, category: str) -> list[dict[str, Any]]:
        """Get SOC 2 requirements filtered by category."""
        return [
            req for req in SOC2_REQUIREMENTS
            if req["category"] == category or "all" in req["applies_to"]
        ]


class SOC2SourceMonitor:
    """Monitors SOC 2 regulatory sources."""

    def __init__(self):
        self.crawler = RegulatoryCrawler()
        self.parser = SOC2Parser()
        self.framework = "soc2"
        self.sources = SOC2_SOURCES

    async def check_aicpa_updates(self, source: RegulatorySource) -> dict[str, Any]:
        """Check AICPA for SOC 2 updates."""
        async with self.crawler:
            result = await self.crawler.crawl(source)

            if result.has_changed:
                parsed = self.parser.parse_aicpa_page(result.content)
                return {
                    "changed": True,
                    "source": source.name,
                    "parsed": parsed,
                    "documents_count": len(parsed.get("documents", [])),
                }

            return {"changed": False, "source": source.name}

    def get_all_requirements(self) -> list[dict[str, Any]]:
        """Get all SOC 2 requirements for database initialization."""
        return self.parser.get_all_requirements()

    def get_trust_categories(self) -> dict[str, Any]:
        """Get SOC 2 Trust Services Categories."""
        return SOC2_TRUST_CATEGORIES


def get_soc2_source_definitions() -> list[dict[str, Any]]:
    """Get predefined SOC 2 source definitions."""
    return SOC2_SOURCES


async def initialize_soc2_sources(db) -> list[RegulatorySource]:
    """Initialize SOC 2 sources in the database."""
    sources = []

    for source_def in SOC2_SOURCES:
        source = RegulatorySource(
            name=source_def["name"],
            description=source_def["description"],
            url=source_def["url"],
            jurisdiction=source_def["jurisdiction"],
            framework=source_def["framework"],
            parser_type=source_def["parser_type"],
            parser_config=source_def["parser_config"],
            is_active=True,
            check_interval_hours=168,  # Weekly
        )
        db.add(source)
        sources.append(source)

    await db.flush()
    return sources
