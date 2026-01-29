"""Singapore Personal Data Protection Act (PDPA) regulatory source implementations."""

import re
from typing import Any

import structlog
from bs4 import BeautifulSoup

from app.models.regulation import Jurisdiction, RegulatoryFramework, RegulatorySource
from app.services.monitoring.crawler import RegulatoryCrawler


logger = structlog.get_logger()


# Singapore PDPA source definitions
SINGAPORE_PDPA_SOURCES = [
    {
        "name": "PDPC Singapore - PDPA",
        "description": "Singapore Personal Data Protection Commission - PDPA legislation and guidelines",
        "url": "https://www.pdpc.gov.sg/overview-of-pdpa/the-legislation/personal-data-protection-act",
        "jurisdiction": Jurisdiction.SINGAPORE,
        "framework": RegulatoryFramework.PDPA,
        "parser_type": "html",
        "parser_config": {
            "content_selector": ".content-area",
            "section_pattern": r"Part\s+([IVXLC]+)",
        },
    },
    {
        "name": "PDPC Advisory Guidelines",
        "description": "PDPC advisory guidelines on key PDPA concepts",
        "url": "https://www.pdpc.gov.sg/guidelines-and-consultation/advisory-guidelines",
        "jurisdiction": Jurisdiction.SINGAPORE,
        "framework": RegulatoryFramework.PDPA,
        "parser_type": "html",
        "parser_config": {
            "list_selector": ".guidelines-list",
            "item_selector": ".guideline-item",
        },
    },
    {
        "name": "Singapore Statutes Online - PDPA",
        "description": "Official PDPA text from Singapore Statutes Online",
        "url": "https://sso.agc.gov.sg/Act/PDPA2012",
        "jurisdiction": Jurisdiction.SINGAPORE,
        "framework": RegulatoryFramework.PDPA,
        "parser_type": "html",
        "parser_config": {
            "content_selector": ".act-content",
            "section_pattern": r"Section\s+(\d+)",
        },
    },
    {
        "name": "PDPC Enforcement Decisions",
        "description": "PDPC enforcement decisions and case summaries",
        "url": "https://www.pdpc.gov.sg/all-commissions-decisions",
        "jurisdiction": Jurisdiction.SINGAPORE,
        "framework": RegulatoryFramework.PDPA,
        "parser_type": "html",
        "parser_config": {},
    },
]


# Key PDPA sections and their purposes
PDPA_SECTIONS = {
    "11": {"title": "Consent required", "type": "consent"},
    "12": {"title": "Deemed consent", "type": "consent"},
    "13": {"title": "Withdrawal of consent", "type": "consent"},
    "14": {"title": "Purposes", "type": "purpose_limitation"},
    "15": {"title": "Notification of purposes", "type": "transparency"},
    "18": {"title": "Access to personal data", "type": "rights"},
    "19": {"title": "Correction of personal data", "type": "rights"},
    "22": {"title": "Accuracy of personal data", "type": "data_quality"},
    "24": {"title": "Protection of personal data", "type": "security"},
    "25": {"title": "Retention of personal data", "type": "retention"},
    "26": {"title": "Transfer of personal data outside Singapore", "type": "cross_border"},
    "26A": {"title": "Data portability", "type": "rights"},
    "26B": {"title": "Data portability request", "type": "rights"},
    "26C": {"title": "Notification of data breach", "type": "breach"},
    "26D": {"title": "Data breach assessment", "type": "breach"},
}


class SingaporePDPAParser:
    """Parser for Singapore PDPA documents."""

    def __init__(self):
        self.section_pattern = re.compile(r"Section\s+(\d+[A-Z]?)", re.IGNORECASE)
        self.part_pattern = re.compile(r"Part\s+([IVXLC]+)", re.IGNORECASE)

    def parse_pdpa_statute(self, content: str) -> dict[str, Any]:
        """Parse PDPA statute from Singapore Statutes Online."""
        soup = BeautifulSoup(content, "lxml")

        result = {
            "title": "Personal Data Protection Act 2012",
            "jurisdiction": "Singapore",
            "sections": [],
            "parts": [],
            "schedules": [],
            "last_updated": None,
        }

        # Extract act title
        title_elem = soup.find("h1", class_="act-title") or soup.find("title")
        if title_elem:
            result["title"] = title_elem.get_text(strip=True)

        # Extract sections
        for section in soup.find_all(["div", "p"], class_=re.compile(r"section|provision")):
            section_match = self.section_pattern.search(section.get_text())
            if section_match:
                section_num = section_match.group(1)
                section_info = PDPA_SECTIONS.get(section_num, {})

                result["sections"].append({
                    "number": section_num,
                    "title": section_info.get("title", ""),
                    "type": section_info.get("type", "general"),
                    "content": section.get_text(separator="\n", strip=True),
                })

        return result

    def parse_pdpc_guidelines(self, content: str) -> list[dict[str, Any]]:
        """Parse PDPC advisory guidelines listing."""
        soup = BeautifulSoup(content, "lxml")
        guidelines = []

        # Try multiple selector patterns
        selectors = [
            ".guidelines-list .guideline-item",
            ".card-list .card",
            "article.guideline",
            ".content-item",
        ]

        for selector in selectors:
            items = soup.select(selector)
            if items:
                for item in items:
                    title_elem = item.select_one("h2, h3, .title, a")
                    link_elem = item.select_one("a[href]")
                    date_elem = item.select_one(".date, time, .published")

                    if title_elem:
                        guidelines.append({
                            "title": title_elem.get_text(strip=True),
                            "url": link_elem.get("href") if link_elem else None,
                            "date": date_elem.get_text(strip=True) if date_elem else None,
                            "type": "guideline",
                        })
                break

        return guidelines

    def extract_requirements_from_section(
        self,
        section: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Extract requirements from a PDPA section."""
        requirements = []
        content = section.get("content", "")

        # PDPA-specific obligation patterns
        obligation_patterns = [
            (r"shall\s+(?:not\s+)?(?:be\s+)?(\w+(?:\s+\w+){0,10})", "must"),
            (r"must\s+(\w+(?:\s+\w+){0,10})", "must"),
            (r"shall\s+not\s+(\w+(?:\s+\w+){0,10})", "must_not"),
            (r"is\s+required\s+to\s+(\w+(?:\s+\w+){0,10})", "must"),
            (r"may\s+(?:only\s+)?(\w+(?:\s+\w+){0,10})", "may"),
            (r"is\s+prohibited\s+from\s+(\w+(?:\s+\w+){0,10})", "must_not"),
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
                        "act": "Personal Data Protection Act 2012",
                        "jurisdiction": "Singapore",
                    },
                })

        return requirements


class SingaporePDPASourceMonitor:
    """Monitors Singapore PDPA regulatory sources."""

    def __init__(self):
        self.crawler = RegulatoryCrawler()
        self.parser = SingaporePDPAParser()

    async def check_pdpa_statute(self, source: RegulatorySource) -> dict[str, Any]:
        """Check for PDPA statute updates."""
        async with self.crawler:
            result = await self.crawler.crawl(source)

            if result.has_changed:
                parsed = self.parser.parse_pdpa_statute(result.content)
                return {
                    "changed": True,
                    "source": source.name,
                    "parsed": parsed,
                    "sections_count": len(parsed.get("sections", [])),
                }

            return {"changed": False, "source": source.name}

    async def check_pdpc_guidelines(self, source: RegulatorySource) -> dict[str, Any]:
        """Check PDPC for new guidelines."""
        async with self.crawler:
            result = await self.crawler.crawl(source)

            if result.has_changed:
                guidelines = self.parser.parse_pdpc_guidelines(result.content)
                return {
                    "changed": True,
                    "source": source.name,
                    "guidelines": guidelines,
                    "new_guidelines_count": len(guidelines),
                }

            return {"changed": False, "source": source.name}

    async def extract_all_requirements(
        self,
        source: RegulatorySource,
        content: str,
    ) -> list[dict[str, Any]]:
        """Extract all requirements from PDPA content."""
        parsed = self.parser.parse_pdpa_statute(content)
        all_requirements = []

        for section in parsed.get("sections", []):
            requirements = self.parser.extract_requirements_from_section(section)
            all_requirements.extend(requirements)

        return all_requirements


def get_singapore_pdpa_source_definitions() -> list[dict[str, Any]]:
    """Get predefined Singapore PDPA source definitions."""
    return SINGAPORE_PDPA_SOURCES


async def initialize_singapore_pdpa_sources(db) -> list[RegulatorySource]:
    """Initialize Singapore PDPA sources in the database."""
    sources = []

    for source_def in SINGAPORE_PDPA_SOURCES:
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
