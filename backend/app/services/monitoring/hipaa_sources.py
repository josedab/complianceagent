"""HIPAA (Health Insurance Portability and Accountability Act) regulatory sources."""

import re
from typing import Any

import structlog
from bs4 import BeautifulSoup

from app.models.regulation import Jurisdiction, RegulatoryFramework, RegulatorySource
from app.services.monitoring.crawler import RegulatoryCrawler


logger = structlog.get_logger()


# HIPAA source definitions
HIPAA_SOURCES = [
    {
        "name": "HHS HIPAA Regulations",
        "description": "HHS HIPAA Privacy regulations and guidance",
        "url": "https://www.hhs.gov/hipaa/for-professionals/privacy/index.html",
        "jurisdiction": Jurisdiction.US_FEDERAL,
        "framework": RegulatoryFramework.HIPAA,
        "parser_type": "html",
        "parser_config": {},
    },
    {
        "name": "HIPAA Security Rule",
        "description": "HHS HIPAA Security Rule requirements",
        "url": "https://www.hhs.gov/hipaa/for-professionals/security/index.html",
        "jurisdiction": Jurisdiction.US_FEDERAL,
        "framework": RegulatoryFramework.HIPAA,
        "parser_type": "html",
        "parser_config": {},
    },
    {
        "name": "HIPAA Breach Notification Rule",
        "description": "HHS HIPAA Breach Notification requirements",
        "url": "https://www.hhs.gov/hipaa/for-professionals/breach-notification/index.html",
        "jurisdiction": Jurisdiction.US_FEDERAL,
        "framework": RegulatoryFramework.HIPAA,
        "parser_type": "html",
        "parser_config": {},
    },
    {
        "name": "HIPAA Guidance Documents",
        "description": "HHS HIPAA FAQs and guidance",
        "url": "https://www.hhs.gov/hipaa/for-professionals/faq/index.html",
        "jurisdiction": Jurisdiction.US_FEDERAL,
        "framework": RegulatoryFramework.HIPAA,
        "parser_type": "html",
        "parser_config": {},
    },
]


# HIPAA Privacy Rule Key Requirements
HIPAA_PRIVACY_REQUIREMENTS = [
    {
        "rule": "Privacy Rule",
        "section": "164.502",
        "title": "Uses and Disclosures of PHI",
        "obligation_type": "must_not",
        "subject": "covered_entity",
        "action": "use or disclose protected health information except as permitted",
        "scope": {
            "data_types": ["PHI", "protected_health_information"],
            "exceptions": ["treatment", "payment", "healthcare_operations", "authorization"],
        },
    },
    {
        "rule": "Privacy Rule",
        "section": "164.508",
        "title": "Authorization for Disclosure",
        "obligation_type": "must",
        "subject": "covered_entity",
        "action": "obtain valid authorization before certain uses and disclosures",
        "scope": {
            "requires_authorization": ["marketing", "sale_of_PHI", "psychotherapy_notes"],
        },
    },
    {
        "rule": "Privacy Rule",
        "section": "164.520",
        "title": "Notice of Privacy Practices",
        "obligation_type": "must",
        "subject": "covered_entity",
        "action": "provide notice of privacy practices to individuals",
        "scope": {
            "notice_includes": ["uses", "disclosures", "rights", "duties"],
        },
    },
    {
        "rule": "Privacy Rule",
        "section": "164.524",
        "title": "Access to PHI",
        "obligation_type": "must",
        "subject": "covered_entity",
        "action": "permit individual to inspect and obtain copy of PHI",
        "scope": {
            "deadline": "30 days",
            "extension": "30 days with notice",
        },
    },
    {
        "rule": "Privacy Rule",
        "section": "164.526",
        "title": "Amendment of PHI",
        "obligation_type": "must",
        "subject": "covered_entity",
        "action": "permit individual to request amendment of PHI",
        "scope": {
            "deadline": "60 days",
        },
    },
    {
        "rule": "Privacy Rule",
        "section": "164.528",
        "title": "Accounting of Disclosures",
        "obligation_type": "must",
        "subject": "covered_entity",
        "action": "provide accounting of disclosures upon request",
        "scope": {
            "period": "6 years prior to request",
            "deadline": "60 days",
        },
    },
]

# HIPAA Security Rule Key Requirements
HIPAA_SECURITY_REQUIREMENTS = [
    {
        "rule": "Security Rule",
        "section": "164.308(a)(1)",
        "title": "Security Management Process",
        "obligation_type": "must",
        "subject": "covered_entity",
        "action": "implement policies and procedures to prevent, detect, contain, and correct security violations",
        "scope": {
            "includes": ["risk_analysis", "risk_management", "sanction_policy", "information_system_activity_review"],
        },
    },
    {
        "rule": "Security Rule",
        "section": "164.308(a)(3)",
        "title": "Workforce Security",
        "obligation_type": "must",
        "subject": "covered_entity",
        "action": "implement policies and procedures for authorization and supervision of workforce access",
        "scope": {
            "addressable": ["authorization_procedures", "workforce_clearance", "termination_procedures"],
        },
    },
    {
        "rule": "Security Rule",
        "section": "164.308(a)(5)",
        "title": "Security Awareness Training",
        "obligation_type": "must",
        "subject": "covered_entity",
        "action": "implement security awareness and training program for workforce",
        "scope": {
            "addressable": ["security_reminders", "malicious_software_protection", "login_monitoring", "password_management"],
        },
    },
    {
        "rule": "Security Rule",
        "section": "164.312(a)(1)",
        "title": "Access Control",
        "obligation_type": "must",
        "subject": "covered_entity",
        "action": "implement technical policies and procedures for access control",
        "scope": {
            "includes": ["unique_user_identification", "emergency_access", "automatic_logoff", "encryption"],
        },
    },
    {
        "rule": "Security Rule",
        "section": "164.312(b)",
        "title": "Audit Controls",
        "obligation_type": "must",
        "subject": "covered_entity",
        "action": "implement hardware, software, and procedural mechanisms for recording and examining activity",
        "scope": {
            "data_types": ["ePHI", "electronic_protected_health_information"],
        },
    },
    {
        "rule": "Security Rule",
        "section": "164.312(c)(1)",
        "title": "Integrity Controls",
        "obligation_type": "must",
        "subject": "covered_entity",
        "action": "implement policies and procedures to protect ePHI from improper alteration or destruction",
        "scope": {
            "addressable": ["mechanism_to_authenticate_ePHI"],
        },
    },
    {
        "rule": "Security Rule",
        "section": "164.312(d)",
        "title": "Person or Entity Authentication",
        "obligation_type": "must",
        "subject": "covered_entity",
        "action": "implement procedures to verify identity of person or entity seeking access to ePHI",
    },
    {
        "rule": "Security Rule",
        "section": "164.312(e)(1)",
        "title": "Transmission Security",
        "obligation_type": "must",
        "subject": "covered_entity",
        "action": "implement technical security measures to guard against unauthorized access during transmission",
        "scope": {
            "addressable": ["integrity_controls", "encryption"],
        },
    },
]

# HIPAA Breach Notification Requirements
HIPAA_BREACH_REQUIREMENTS = [
    {
        "rule": "Breach Notification Rule",
        "section": "164.404",
        "title": "Notification to Individuals",
        "obligation_type": "must",
        "subject": "covered_entity",
        "action": "notify affected individuals of breach of unsecured PHI",
        "scope": {
            "deadline": "60 days from discovery",
            "method": "written notice",
        },
    },
    {
        "rule": "Breach Notification Rule",
        "section": "164.406",
        "title": "Notification to Media",
        "obligation_type": "must",
        "subject": "covered_entity",
        "action": "notify prominent media outlets if breach affects more than 500 residents of a state",
        "scope": {
            "threshold": "500 individuals in state",
            "deadline": "60 days",
        },
    },
    {
        "rule": "Breach Notification Rule",
        "section": "164.408",
        "title": "Notification to HHS",
        "obligation_type": "must",
        "subject": "covered_entity",
        "action": "notify Secretary of HHS of breach",
        "scope": {
            "if_over_500": "concurrent with individual notification",
            "if_under_500": "annual log within 60 days of calendar year end",
        },
    },
]


class HIPAAParser:
    """Parser for HIPAA-related documents."""

    def __init__(self):
        self.cfr_pattern = re.compile(r"§?\s*164\.(\d+)", re.IGNORECASE)

    def parse_hhs_hipaa(self, content: str) -> dict[str, Any]:
        """Parse HHS HIPAA document."""
        soup = BeautifulSoup(content, "lxml")

        result = {
            "title": "",
            "sections": [],
            "requirements": [],
        }

        # Extract main content
        main_content = soup.find("main") or soup.find("div", class_="content")
        if main_content:
            for section in main_content.find_all(["h2", "h3"]):
                section_title = section.get_text(strip=True)
                section_content = ""

                # Get content until next heading
                sibling = section.find_next_sibling()
                while sibling and sibling.name not in ["h2", "h3"]:
                    if sibling.name == "p":
                        section_content += sibling.get_text(strip=True) + "\n"
                    sibling = sibling.find_next_sibling()

                if section_title:
                    result["sections"].append({
                        "title": section_title,
                        "content": section_content,
                    })

        return result

    def extract_requirements_from_section(
        self,
        section: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Extract requirements from a HIPAA section."""
        requirements = []
        content = section.get("content", "")

        obligation_patterns = [
            (r"shall\s+(?:be\s+)?(\w+(?:\s+\w+){0,10})", "must"),
            (r"must\s+(\w+(?:\s+\w+){0,10})", "must"),
            (r"required\s+to\s+(\w+(?:\s+\w+){0,10})", "must"),
            (r"shall\s+not\s+(\w+(?:\s+\w+){0,10})", "must_not"),
        ]

        for pattern, obligation_type in obligation_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                action = match.group(1).strip()
                context_start = max(0, match.start() - 100)
                context_end = min(len(content), match.end() + 100)
                context = content[context_start:context_end]

                requirements.append({
                    "section": section.get("title"),
                    "obligation_type": obligation_type,
                    "action": action,
                    "source_text": context,
                    "framework": "hipaa",
                    "jurisdiction": "US-Federal",
                })

        return requirements


class HIPAASourceMonitor:
    """Monitors HIPAA regulatory sources."""

    def __init__(self):
        self.crawler = RegulatoryCrawler()
        self.parser = HIPAAParser()

    async def check_source(self, source: RegulatorySource) -> dict[str, Any]:
        """Check a HIPAA source for updates."""
        async with self.crawler:
            result = await self.crawler.crawl(source)

            if result.has_changed:
                parsed = self.parser.parse_hhs_hipaa(result.content)
                return {
                    "changed": True,
                    "source": source.name,
                    "parsed": parsed,
                    "sections_count": len(parsed.get("sections", [])),
                }

            return {"changed": False, "source": source.name}

    async def extract_all_requirements(
        self,
        source: RegulatorySource,
        content: str,
    ) -> list[dict[str, Any]]:
        """Extract all requirements from HIPAA content."""
        parsed = self.parser.parse_hhs_hipaa(content)
        all_requirements = []

        for section in parsed.get("sections", []):
            requirements = self.parser.extract_requirements_from_section(section)
            all_requirements.extend(requirements)

        return all_requirements


# HIPAA Rules for test compatibility
HIPAA_RULES = {
    "privacy": {
        "title": "Privacy Rule",
        "cfr": "45 CFR Part 160 and Part 164 Subparts A and E",
        "requirements": HIPAA_PRIVACY_REQUIREMENTS,
    },
    "security": {
        "title": "Security Rule",
        "cfr": "45 CFR Part 160 and Part 164 Subparts A and C",
        "requirements": HIPAA_SECURITY_REQUIREMENTS,
    },
    "breach": {
        "title": "Breach Notification Rule",
        "cfr": "45 CFR Part 164 Subpart D",
        "requirements": HIPAA_BREACH_REQUIREMENTS,
    },
}


def get_hipaa_source_definitions() -> list[dict[str, Any]]:
    """Get predefined HIPAA source definitions."""
    return HIPAA_SOURCES


async def initialize_hipaa_sources(db) -> list[RegulatorySource]:
    """Initialize HIPAA sources in the database."""
    sources = []

    for source_def in HIPAA_SOURCES:
        source = RegulatorySource(
            name=source_def["name"],
            description=source_def["description"],
            url=source_def["url"],
            jurisdiction=source_def["jurisdiction"],
            framework=source_def["framework"],
            parser_type=source_def["parser_type"],
            parser_config=source_def["parser_config"],
            is_active=True,
            check_interval_hours=24,
        )
        db.add(source)
        sources.append(source)

    await db.flush()
    return sources


def parse_hipaa_text(content: str) -> dict[str, Any]:
    """Parse HIPAA regulatory text to extract requirements."""
    requirements = []

    import re

    # Find CFR references (45 CFR Part 164)
    cfr_refs = re.findall(r"§?\s*164\.(\d+)", content)

    # Find shall/must obligations
    obligations = re.findall(r"(?:shall|must|required to)\s+([^.]+\.)", content, re.IGNORECASE)

    for i, obligation in enumerate(obligations[:20]):
        requirements.append({
            "id": f"hipaa-{i+1}",
            "obligation_type": "must",
            "action": obligation.strip(),
            "source_text": obligation,
            "confidence": 0.75,
        })

    return {
        "framework": "hipaa",
        "jurisdiction": "US-Federal",
        "requirements": requirements,
        "cfr_sections": list(set(cfr_refs)),
    }
