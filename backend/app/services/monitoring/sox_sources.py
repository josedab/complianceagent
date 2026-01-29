"""SOX (Sarbanes-Oxley) regulatory source implementations."""

import re
from typing import Any

import structlog
from bs4 import BeautifulSoup

from app.models.regulation import Jurisdiction, RegulatoryFramework, RegulatorySource
from app.services.monitoring.crawler import RegulatoryCrawler


logger = structlog.get_logger()


# SOX source definitions
SOX_SOURCES = [
    {
        "id": "sox-sec-spotlight",
        "name": "SEC EDGAR SOX Filings",
        "description": "SEC EDGAR database for SOX-related filings and guidance",
        "url": "https://www.sec.gov/spotlight/sarbanes-oxley.htm",
        "jurisdiction": Jurisdiction.US_FEDERAL,
        "framework": RegulatoryFramework.SOX,
        "parser_type": "html",
        "section": "general",
        "parser_config": {
            "content_selector": "#main-content",
        },
    },
    {
        "id": "sox-pcaob-standards",
        "name": "PCAOB Standards",
        "description": "Public Company Accounting Oversight Board auditing standards",
        "url": "https://pcaobus.org/oversight/standards",
        "jurisdiction": Jurisdiction.US_FEDERAL,
        "framework": RegulatoryFramework.SOX,
        "parser_type": "html",
        "section": "audit",
        "parser_config": {},
    },
    {
        "id": "sox-coso-framework",
        "name": "COSO Framework",
        "description": "Committee of Sponsoring Organizations Internal Control Framework",
        "url": "https://www.coso.org/guidance-on-ic",
        "jurisdiction": Jurisdiction.GLOBAL,
        "framework": RegulatoryFramework.SOX,
        "parser_type": "html",
        "section": "internal_control",
        "parser_config": {},
    },
]


# SOX key sections and requirements (as list for test compatibility)
SOX_REQUIREMENTS = [
    {
        "id": "302.a.1",
        "section": "302",
        "name": "Review of Reports",
        "description": "Signing officers have reviewed the report",
        "obligations": ["must review financial reports"],
    },
    {
        "id": "302.a.2",
        "section": "302",
        "name": "No Untrue Statements",
        "description": "Report does not contain any untrue statement of material fact",
        "obligations": ["must not contain untrue statements"],
    },
    {
        "id": "302.a.3",
        "section": "302",
        "name": "Fair Presentation",
        "description": "Financial statements fairly present the financial condition",
        "obligations": ["must fairly present financial condition"],
    },
    {
        "id": "302.a.4",
        "section": "302",
        "name": "Internal Controls",
        "description": "Officers responsible for establishing internal controls",
        "obligations": ["must establish internal controls"],
    },
    {
        "id": "302.a.5",
        "section": "302",
        "name": "Disclosure of Deficiencies",
        "description": "Disclose significant deficiencies in internal controls",
        "obligations": ["must disclose deficiencies"],
    },
    {
        "id": "302.a.6",
        "section": "302",
        "name": "Fraud Disclosure",
        "description": "Disclose any fraud involving management or key employees",
        "obligations": ["must disclose fraud"],
    },
    {
        "id": "404.a.1",
        "section": "404",
        "name": "Management's Responsibility",
        "description": "Management responsible for internal control structure",
        "obligations": ["must maintain internal control structure"],
    },
    {
        "id": "404.a.2",
        "section": "404",
        "name": "Internal Control Assessment",
        "description": "Annual assessment of effectiveness of internal controls",
        "obligations": ["must assess internal controls annually"],
    },
    {
        "id": "404.b",
        "section": "404",
        "name": "External Auditor Attestation",
        "description": "External auditor must attest to management's assessment",
        "obligations": ["must obtain external auditor attestation"],
    },
    {
        "id": "409.a",
        "section": "409",
        "name": "Rapid Disclosure",
        "description": "Disclose material changes in financial condition on rapid basis",
        "obligations": ["must rapidly disclose material changes"],
    },
    {
        "id": "802.a.1",
        "section": "802",
        "name": "Document Retention",
        "description": "Audit workpapers retained for 5 years",
        "obligations": ["must retain audit workpapers for 5 years"],
    },
    {
        "id": "802.a.2",
        "section": "802",
        "name": "No Destruction",
        "description": "Must not destroy audit documents during investigation",
        "obligations": ["must not destroy documents during investigation"],
    },
    {
        "id": "806.a",
        "section": "806",
        "name": "Whistleblower Protection",
        "description": "No retaliation against employees reporting violations",
        "obligations": ["must not retaliate against whistleblowers"],
    },
    {
        "id": "906.a",
        "section": "906",
        "name": "Certification Accuracy",
        "description": "Periodic reports must comply with securities laws",
        "obligations": ["must certify compliance with securities laws"],
    },
    {
        "id": "906.b",
        "section": "906",
        "name": "Fair Representation",
        "description": "Financial statements must fairly present financial condition",
        "obligations": ["must fairly represent financial condition"],
    },
]


# IT-specific SOX controls (COBIT-aligned) - as list for test compatibility
SOX_IT_CONTROLS = [
    {
        "id": "IT-AC-01",
        "category": "access_control",
        "name": "User Access Management",
        "description": "Formal user registration and de-registration procedure",
        "testing_procedures": ["Review user provisioning process", "Sample user access requests"],
    },
    {
        "id": "IT-AC-02",
        "category": "access_control",
        "name": "Privileged Access Management",
        "description": "Restricted allocation and use of privileged access",
        "testing_procedures": ["Review privileged accounts", "Test access controls"],
    },
    {
        "id": "IT-AC-03",
        "category": "access_control",
        "name": "Access Reviews",
        "description": "Regular review of user access rights",
        "testing_procedures": ["Review access review documentation", "Sample access certifications"],
    },
    {
        "id": "IT-AC-04",
        "category": "access_control",
        "name": "Segregation of Duties",
        "description": "Conflicting duties are segregated",
        "testing_procedures": ["Review SoD matrix", "Test conflicting access"],
    },
    {
        "id": "IT-CM-01",
        "category": "change_management",
        "name": "Change Control Procedures",
        "description": "Formal change management procedures",
        "testing_procedures": ["Review change management policy", "Sample change tickets"],
    },
    {
        "id": "IT-CM-02",
        "category": "change_management",
        "name": "Testing Requirements",
        "description": "Changes tested before production deployment",
        "testing_procedures": ["Review test documentation", "Sample test results"],
    },
    {
        "id": "IT-CM-03",
        "category": "change_management",
        "name": "Change Authorization",
        "description": "Changes authorized by appropriate management",
        "testing_procedures": ["Review approval workflow", "Sample change approvals"],
    },
    {
        "id": "IT-CM-04",
        "category": "change_management",
        "name": "Emergency Changes",
        "description": "Emergency change procedures documented",
        "testing_procedures": ["Review emergency change process", "Sample emergency changes"],
    },
    {
        "id": "IT-CO-01",
        "category": "computer_operations",
        "name": "Job Scheduling",
        "description": "Automated job scheduling with monitoring",
        "testing_procedures": ["Review job schedules", "Test job monitoring alerts"],
    },
    {
        "id": "IT-CO-02",
        "category": "computer_operations",
        "name": "Backup and Recovery",
        "description": "Regular backup and tested recovery procedures",
        "testing_procedures": ["Review backup logs", "Test restoration procedures"],
    },
    {
        "id": "IT-CO-03",
        "category": "computer_operations",
        "name": "Incident Management",
        "description": "IT incident management procedures",
        "testing_procedures": ["Review incident tickets", "Test escalation procedures"],
    },
    {
        "id": "IT-SD-01",
        "category": "system_development",
        "name": "SDLC Methodology",
        "description": "Formal system development methodology",
        "testing_procedures": ["Review SDLC documentation", "Sample project artifacts"],
    },
    {
        "id": "IT-SD-02",
        "category": "system_development",
        "name": "Security in SDLC",
        "description": "Security requirements in development lifecycle",
        "testing_procedures": ["Review security requirements", "Sample security testing"],
    },
    {
        "id": "IT-SD-03",
        "category": "system_development",
        "name": "Code Review",
        "description": "Code review before deployment",
        "testing_procedures": ["Review code review process", "Sample code review records"],
    },
]


class SOXParser:
    """Parser for SOX-related documents."""

    def __init__(self):
        self.section_pattern = re.compile(r"Section\s+(\d+)", re.IGNORECASE)

    def parse_sec_page(self, content: str) -> list[dict[str, Any]]:
        """Parse SEC SOX guidance page."""
        soup = BeautifulSoup(content, "lxml")
        documents = []

        for link in soup.select("a[href*='.pdf'], a[href*='/rules/'], a[href*='/interps/']"):
            href = link.get("href", "")
            text = link.get_text(strip=True)
            if text and len(text) > 10:
                documents.append({
                    "title": text,
                    "url": href if href.startswith("http") else f"https://www.sec.gov{href}",
                    "type": "guidance",
                })

        return documents

    def get_all_requirements(self) -> list[dict[str, Any]]:
        """Get all SOX requirements for database initialization."""
        all_requirements = []

        # Section-based requirements
        for section_num, section in SOX_REQUIREMENTS.items():
            for req in section["requirements"]:
                all_requirements.append({
                    "requirement_id": f"SOX-{req['id']}",
                    "section": section_num,
                    "section_title": section["title"],
                    "title": req["title"],
                    "description": req["description"],
                    "obligation_type": req["obligation"],
                    "control_type": req["control_type"],
                    "framework": "SOX",
                    "citation": {
                        "section": f"Section {section_num}",
                    },
                })

        # IT controls
        for category_key, category in SOX_IT_CONTROLS.items():
            for control in category["controls"]:
                all_requirements.append({
                    "requirement_id": f"SOX-{control['id']}",
                    "section": "IT",
                    "section_title": category["title"],
                    "title": control["title"],
                    "description": control["description"],
                    "obligation_type": control["obligation"],
                    "control_type": "it_control",
                    "framework": "SOX",
                    "citation": {
                        "control_id": control["id"],
                        "category": category_key,
                    },
                })

        return all_requirements


class SOXSourceMonitor:
    """Monitors SOX regulatory sources."""

    def __init__(self):
        self.crawler = RegulatoryCrawler()
        self.parser = SOXParser()
        self.framework = "sox"
        self.sources = SOX_SOURCES

    async def check_sec_guidance(self, source: RegulatorySource) -> dict[str, Any]:
        """Check SEC for SOX updates."""
        async with self.crawler:
            result = await self.crawler.crawl(source)

            if result.has_changed:
                documents = self.parser.parse_sec_page(result.content)
                return {
                    "changed": True,
                    "source": source.name,
                    "documents": documents,
                    "documents_count": len(documents),
                }

            return {"changed": False, "source": source.name}

    def get_all_requirements(self) -> list[dict[str, Any]]:
        """Get all SOX requirements for database initialization."""
        return self.parser.get_all_requirements()


def get_sox_source_definitions() -> list[dict[str, Any]]:
    """Get predefined SOX source definitions."""
    return SOX_SOURCES


async def initialize_sox_sources(db) -> list[RegulatorySource]:
    """Initialize SOX sources in the database."""
    sources = []

    for source_def in SOX_SOURCES:
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
