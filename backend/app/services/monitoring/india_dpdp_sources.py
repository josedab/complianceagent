"""India Digital Personal Data Protection Act (DPDP) regulatory source implementations."""

import re
from typing import Any

import structlog
from bs4 import BeautifulSoup

from app.models.regulation import Jurisdiction, RegulatoryFramework, RegulatorySource
from app.services.monitoring.crawler import RegulatoryCrawler


logger = structlog.get_logger()


# India DPDP source definitions
INDIA_DPDP_SOURCES = [
    {
        "name": "MeitY DPDP Act 2023",
        "description": "Ministry of Electronics and IT - Digital Personal Data Protection Act 2023",
        "url": "https://www.meity.gov.in/writereaddata/files/Digital%20Personal%20Data%20Protection%20Act%202023.pdf",
        "jurisdiction": Jurisdiction.INDIA,
        "framework": RegulatoryFramework.DPDP,
        "parser_type": "pdf",
        "parser_config": {
            "section_pattern": r"Section\s+(\d+)",
        },
    },
    {
        "name": "India Code - DPDP Act",
        "description": "DPDP Act on India Code legislative database",
        "url": "https://www.indiacode.nic.in/handle/123456789/19887",
        "jurisdiction": Jurisdiction.INDIA,
        "framework": RegulatoryFramework.DPDP,
        "parser_type": "html",
        "parser_config": {
            "content_selector": ".act-content",
        },
    },
    {
        "name": "MeitY DPDP Rules",
        "description": "Draft rules under DPDP Act",
        "url": "https://www.meity.gov.in/data-protection-framework",
        "jurisdiction": Jurisdiction.INDIA,
        "framework": RegulatoryFramework.DPDP,
        "parser_type": "html",
        "parser_config": {},
    },
    {
        "name": "Data Protection Board of India",
        "description": "Data Protection Board notices and orders",
        "url": "https://www.dpb.gov.in/",
        "jurisdiction": Jurisdiction.INDIA,
        "framework": RegulatoryFramework.DPDP,
        "parser_type": "html",
        "parser_config": {},
    },
]


# Key DPDP sections
DPDP_SECTIONS = {
    "4": {"title": "Grounds for processing personal data", "type": "lawful_basis"},
    "5": {"title": "Notice", "type": "transparency"},
    "6": {"title": "Consent", "type": "consent"},
    "7": {"title": "Certain legitimate uses", "type": "lawful_basis"},
    "8": {"title": "General obligations of Data Fiduciary", "type": "obligations"},
    "9": {"title": "Processing of personal data of children", "type": "children"},
    "10": {"title": "Additional obligations of Significant Data Fiduciary", "type": "obligations"},
    "11": {"title": "Rights of Data Principal", "type": "rights"},
    "12": {"title": "Right to access information about personal data", "type": "rights"},
    "13": {"title": "Right to correction and erasure", "type": "rights"},
    "14": {"title": "Right of grievance redressal", "type": "rights"},
    "15": {"title": "Right to nominate", "type": "rights"},
    "16": {"title": "Transfer of personal data outside India", "type": "cross_border"},
    "17": {"title": "Exemptions", "type": "exemptions"},
    "18": {"title": "Data Protection Board", "type": "enforcement"},
    "27": {"title": "Voluntary undertaking", "type": "enforcement"},
    "33": {"title": "Penalties", "type": "penalties"},
}


class IndiaDPDPParser:
    """Parser for India DPDP Act documents."""

    def __init__(self):
        self.section_pattern = re.compile(r"Section\s+(\d+)", re.IGNORECASE)
        self.chapter_pattern = re.compile(r"Chapter\s+([IVXLC]+)", re.IGNORECASE)

    def parse_dpdp_act(self, content: str) -> dict[str, Any]:
        """Parse DPDP Act content."""
        soup = BeautifulSoup(content, "lxml")

        result = {
            "title": "Digital Personal Data Protection Act, 2023",
            "jurisdiction": "India",
            "sections": [],
            "chapters": [],
            "schedules": [],
            "last_updated": None,
        }

        # Extract sections from content
        text_content = soup.get_text(separator="\n")
        current_section = None
        current_content = []

        for line in text_content.split("\n"):
            section_match = self.section_pattern.search(line)
            if section_match:
                # Save previous section
                if current_section:
                    section_info = DPDP_SECTIONS.get(current_section, {})
                    result["sections"].append({
                        "number": current_section,
                        "title": section_info.get("title", ""),
                        "type": section_info.get("type", "general"),
                        "content": "\n".join(current_content),
                    })

                current_section = section_match.group(1)
                current_content = [line]
            elif current_section:
                current_content.append(line)

        # Save last section
        if current_section:
            section_info = DPDP_SECTIONS.get(current_section, {})
            result["sections"].append({
                "number": current_section,
                "title": section_info.get("title", ""),
                "type": section_info.get("type", "general"),
                "content": "\n".join(current_content),
            })

        return result

    def parse_meity_updates(self, content: str) -> list[dict[str, Any]]:
        """Parse MeitY updates and announcements."""
        soup = BeautifulSoup(content, "lxml")
        updates = []

        # Multiple selector patterns for government sites
        selectors = [
            ".news-item",
            ".update-item",
            "article",
            ".content-block",
            ".list-item",
        ]

        for selector in selectors:
            items = soup.select(selector)
            if items:
                for item in items:
                    title_elem = item.select_one("h2, h3, h4, .title, a")
                    link_elem = item.select_one("a[href]")
                    date_elem = item.select_one(".date, time, .published")

                    if title_elem:
                        updates.append({
                            "title": title_elem.get_text(strip=True),
                            "url": link_elem.get("href") if link_elem else None,
                            "date": date_elem.get_text(strip=True) if date_elem else None,
                            "type": "update",
                        })
                break

        return updates

    def extract_requirements_from_section(
        self,
        section: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Extract requirements from a DPDP section."""
        requirements = []
        content = section.get("content", "")

        # DPDP-specific obligation patterns
        obligation_patterns = [
            (r"shall\s+(?:not\s+)?(\w+(?:\s+\w+){0,10})", "must"),
            (r"Data\s+Fiduciary\s+shall\s+(\w+(?:\s+\w+){0,10})", "must"),
            (r"must\s+(\w+(?:\s+\w+){0,10})", "must"),
            (r"shall\s+not\s+(\w+(?:\s+\w+){0,10})", "must_not"),
            (r"is\s+entitled\s+to\s+(\w+(?:\s+\w+){0,10})", "right"),
            (r"has\s+the\s+right\s+to\s+(\w+(?:\s+\w+){0,10})", "right"),
            (r"may\s+(\w+(?:\s+\w+){0,10})", "may"),
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
                    "title": section.get("title"),
                    "obligation_type": obligation_type,
                    "action": action,
                    "source_text": context,
                    "citation": {
                        "section": f"Section {section.get('number')}",
                        "act": "Digital Personal Data Protection Act, 2023",
                        "jurisdiction": "India",
                    },
                })

        return requirements


class IndiaDPDPSourceMonitor:
    """Monitors India DPDP regulatory sources."""

    def __init__(self):
        self.crawler = RegulatoryCrawler()
        self.parser = IndiaDPDPParser()

    async def check_dpdp_act(self, source: RegulatorySource) -> dict[str, Any]:
        """Check for DPDP Act updates."""
        async with self.crawler:
            result = await self.crawler.crawl(source)

            if result.has_changed:
                parsed = self.parser.parse_dpdp_act(result.content)
                return {
                    "changed": True,
                    "source": source.name,
                    "parsed": parsed,
                    "sections_count": len(parsed.get("sections", [])),
                }

            return {"changed": False, "source": source.name}

    async def check_meity_updates(self, source: RegulatorySource) -> dict[str, Any]:
        """Check MeitY for updates."""
        async with self.crawler:
            result = await self.crawler.crawl(source)

            if result.has_changed:
                updates = self.parser.parse_meity_updates(result.content)
                return {
                    "changed": True,
                    "source": source.name,
                    "updates": updates,
                    "updates_count": len(updates),
                }

            return {"changed": False, "source": source.name}

    async def extract_all_requirements(
        self,
        source: RegulatorySource,
        content: str,
    ) -> list[dict[str, Any]]:
        """Extract all requirements from DPDP content."""
        parsed = self.parser.parse_dpdp_act(content)
        all_requirements = []

        for section in parsed.get("sections", []):
            requirements = self.parser.extract_requirements_from_section(section)
            all_requirements.extend(requirements)

        return all_requirements


def get_india_dpdp_source_definitions() -> list[dict[str, Any]]:
    """Get predefined India DPDP source definitions."""
    return INDIA_DPDP_SOURCES


async def initialize_india_dpdp_sources(db) -> list[RegulatorySource]:
    """Initialize India DPDP sources in the database."""
    sources = []

    for source_def in INDIA_DPDP_SOURCES:
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
