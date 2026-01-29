"""CCPA (California Consumer Privacy Act) regulatory source."""

import re
from typing import Any

import structlog
from bs4 import BeautifulSoup

from app.models.regulation import Jurisdiction, RegulatoryFramework, RegulatorySource
from app.services.monitoring.crawler import RegulatoryCrawler


logger = structlog.get_logger()


# CCPA source definitions
CCPA_SOURCES = [
    {
        "name": "CCPA Official Text",
        "description": "Official California Consumer Privacy Act legislation",
        "url": "https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?lawCode=CIV&division=3.&title=1.81.5.&part=4.&chapter=&article=",
        "jurisdiction": Jurisdiction.US_CALIFORNIA,
        "framework": RegulatoryFramework.CCPA,
        "parser_type": "html",
        "parser_config": {
            "content_selector": "#codeLawContent",
        },
    },
    {
        "name": "CPRA Regulations (CPPA)",
        "description": "California Privacy Protection Agency regulations",
        "url": "https://cppa.ca.gov/regulations/",
        "jurisdiction": Jurisdiction.US_CALIFORNIA,
        "framework": RegulatoryFramework.CCPA,
        "parser_type": "html",
        "parser_config": {},
    },
    {
        "name": "CA Attorney General CCPA Guidance",
        "description": "California Attorney General CCPA guidance documents",
        "url": "https://oag.ca.gov/privacy/ccpa",
        "jurisdiction": Jurisdiction.US_CALIFORNIA,
        "framework": RegulatoryFramework.CCPA,
        "parser_type": "html",
        "parser_config": {},
    },
]


# CCPA Key Requirements
CCPA_REQUIREMENTS = [
    {
        "article": "1798.100",
        "title": "Right to Know",
        "obligation_type": "must",
        "subject": "business",
        "action": "disclose categories and specific pieces of personal information collected",
        "scope": {
            "data_types": ["personal_information"],
            "applies_to": ["businesses meeting CCPA thresholds"],
        },
        "deadline": "45 days from request",
    },
    {
        "article": "1798.105",
        "title": "Right to Delete",
        "obligation_type": "must",
        "subject": "business",
        "action": "delete consumer personal information upon request",
        "scope": {
            "data_types": ["personal_information"],
            "exceptions": ["legal obligations", "security", "contracts"],
        },
        "deadline": "45 days from request",
    },
    {
        "article": "1798.110",
        "title": "Right to Know Categories",
        "obligation_type": "must",
        "subject": "business",
        "action": "disclose categories of personal information collected and sources",
        "scope": {
            "data_types": ["personal_information"],
            "disclosure_includes": ["categories", "sources", "purposes", "third_parties"],
        },
    },
    {
        "article": "1798.115",
        "title": "Right to Disclosure of Sales",
        "obligation_type": "must",
        "subject": "business",
        "action": "disclose if personal information is sold and to whom",
        "scope": {
            "data_types": ["personal_information"],
        },
    },
    {
        "article": "1798.120",
        "title": "Right to Opt-Out",
        "obligation_type": "must",
        "subject": "business",
        "action": "provide mechanism for consumer to opt-out of sale of personal information",
        "scope": {
            "requirement": "Do Not Sell My Personal Information link",
            "location": "homepage",
        },
    },
    {
        "article": "1798.125",
        "title": "Non-Discrimination",
        "obligation_type": "must_not",
        "subject": "business",
        "action": "discriminate against consumer for exercising CCPA rights",
        "scope": {
            "prohibited_discrimination": ["price", "service_quality", "service_level"],
        },
    },
    {
        "article": "1798.130",
        "title": "Notice at Collection",
        "obligation_type": "must",
        "subject": "business",
        "action": "provide notice at or before point of collection",
        "scope": {
            "notice_includes": ["categories", "purposes", "rights"],
        },
    },
    {
        "article": "1798.135",
        "title": "Opt-Out Methods",
        "obligation_type": "must",
        "subject": "business",
        "action": "provide multiple methods for submitting opt-out requests",
        "scope": {
            "methods": ["website link", "toll-free number"],
        },
    },
]


class CCPAParser:
    """Parser for CCPA-related documents."""

    def __init__(self):
        self.section_pattern = re.compile(r"Section\s+(\d+\.\d+)", re.IGNORECASE)

    def parse_california_legislature(self, content: str) -> dict[str, Any]:
        """Parse California Legislature CCPA document."""
        soup = BeautifulSoup(content, "lxml")

        result = {
            "title": "California Consumer Privacy Act",
            "sections": [],
            "requirements": [],
        }

        # Extract sections
        for section in soup.find_all("div", class_="law-section"):
            section_num = ""
            section_content = ""

            header = section.find("div", class_="law-section-header")
            if header:
                section_num = header.get_text(strip=True)

            body = section.find("div", class_="law-section-body")
            if body:
                section_content = body.get_text(separator="\n", strip=True)

            if section_num:
                result["sections"].append({
                    "number": section_num,
                    "content": section_content,
                })

        return result

    def extract_requirements_from_section(
        self,
        section: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Extract requirements from a CCPA section."""
        requirements = []
        content = section.get("content", "")

        # CCPA obligation patterns
        obligation_patterns = [
            (r"shall\s+(?:be\s+)?(\w+(?:\s+\w+){0,10})", "must"),
            (r"must\s+(\w+(?:\s+\w+){0,10})", "must"),
            (r"shall\s+not\s+(\w+(?:\s+\w+){0,10})", "must_not"),
            (r"may\s+not\s+(\w+(?:\s+\w+){0,10})", "must_not"),
        ]

        for pattern, obligation_type in obligation_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                action = match.group(1).strip()
                context_start = max(0, match.start() - 100)
                context_end = min(len(content), match.end() + 100)
                context = content[context_start:context_end]

                requirements.append({
                    "section": section.get("number"),
                    "obligation_type": obligation_type,
                    "action": action,
                    "source_text": context,
                    "framework": "ccpa",
                    "jurisdiction": "US-CA",
                })

        return requirements


class CCPASourceMonitor:
    """Monitors CCPA regulatory sources."""

    def __init__(self):
        self.crawler = RegulatoryCrawler()
        self.parser = CCPAParser()

    async def check_source(self, source: RegulatorySource) -> dict[str, Any]:
        """Check a CCPA source for updates."""
        async with self.crawler:
            result = await self.crawler.crawl(source)

            if result.has_changed:
                parsed = self.parser.parse_california_legislature(result.content)
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
        """Extract all requirements from CCPA content."""
        parsed = self.parser.parse_california_legislature(content)
        all_requirements = []

        for section in parsed.get("sections", []):
            requirements = self.parser.extract_requirements_from_section(section)
            all_requirements.extend(requirements)

        return all_requirements


# CCPA Sections for test compatibility
CCPA_SECTIONS = {
    "1798.100": {"title": "Right to Know", "obligation": "must"},
    "1798.105": {"title": "Right to Delete", "obligation": "must"},
    "1798.110": {"title": "Right to Know Categories", "obligation": "must"},
    "1798.115": {"title": "Right to Disclosure of Sales", "obligation": "must"},
    "1798.120": {"title": "Right to Opt-Out", "obligation": "must"},
    "1798.125": {"title": "Non-Discrimination", "obligation": "must_not"},
    "1798.130": {"title": "Notice at Collection", "obligation": "must"},
    "1798.135": {"title": "Opt-Out Methods", "obligation": "must"},
}


def get_ccpa_source_definitions() -> list[dict[str, Any]]:
    """Get predefined CCPA source definitions."""
    return CCPA_SOURCES


async def initialize_ccpa_sources(db) -> list[RegulatorySource]:
    """Initialize CCPA sources in the database."""
    sources = []

    for source_def in CCPA_SOURCES:
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


def parse_ccpa_text(content: str) -> dict[str, Any]:
    """Parse CCPA legislative text to extract requirements."""
    requirements = []

    # CCPA-specific parsing logic
    import re

    # Find section references
    sections = re.findall(r"Section (\d+\.\d+)", content, re.IGNORECASE)

    # Find "shall" obligations (California legal language)
    obligations = re.findall(r"(?:shall|must|required to)\s+([^.]+\.)", content, re.IGNORECASE)

    for i, obligation in enumerate(obligations[:20]):  # Limit to first 20
        requirements.append({
            "id": f"ccpa-{i+1}",
            "obligation_type": "must",
            "action": obligation.strip(),
            "source_text": obligation,
            "confidence": 0.75,
        })

    return {
        "framework": "ccpa",
        "jurisdiction": "US-CA",
        "requirements": requirements,
        "sections_found": list(set(sections)),
    }
