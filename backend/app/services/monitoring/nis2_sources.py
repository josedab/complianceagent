"""NIS2 Directive regulatory source implementations."""

import re
from typing import Any

import structlog
from bs4 import BeautifulSoup

from app.models.regulation import Jurisdiction, RegulatoryFramework, RegulatorySource
from app.services.monitoring.crawler import RegulatoryCrawler


logger = structlog.get_logger()


# NIS2 source definitions
NIS2_SOURCES = [
    {
        "id": "nis2-eur-lex",
        "name": "EUR-Lex NIS2 Directive",
        "description": "Official NIS2 Directive (EU) 2022/2555 text",
        "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32022L2555",
        "jurisdiction": Jurisdiction.EU,
        "framework": RegulatoryFramework.NIS2,
        "parser_type": "html",
        "type": "official",
        "parser_config": {
            "content_selector": "#document1",
            "article_pattern": r"Article\s+(\d+)",
        },
    },
    {
        "id": "nis2-enisa-guidance",
        "name": "ENISA NIS2 Guidance",
        "description": "European Union Agency for Cybersecurity NIS2 implementation guidance",
        "url": "https://www.enisa.europa.eu/topics/nis-directive",
        "jurisdiction": Jurisdiction.EU,
        "framework": RegulatoryFramework.NIS2,
        "parser_type": "html",
        "type": "guidance",
        "parser_config": {},
    },
    {
        "id": "nis2-ec-policy",
        "name": "European Commission NIS2",
        "description": "European Commission NIS2 policy and implementation updates",
        "url": "https://digital-strategy.ec.europa.eu/en/policies/nis2-directive",
        "jurisdiction": Jurisdiction.EU,
        "framework": RegulatoryFramework.NIS2,
        "parser_type": "html",
        "type": "guidance",
        "parser_config": {},
    },
]


# NIS2 Requirements by Article (as list for test compatibility)
NIS2_REQUIREMENTS = [
    {
        "id": "NIS2-20.1",
        "article": "20",
        "name": "Management Body Approval",
        "description": "Management bodies must approve cybersecurity risk-management measures",
        "applies_to": ["essential", "important"],
    },
    {
        "id": "NIS2-20.2",
        "article": "20",
        "name": "Management Training",
        "description": "Management body members must follow training on cybersecurity",
        "applies_to": ["essential", "important"],
    },
    {
        "id": "NIS2-21.1",
        "article": "21",
        "name": "Risk Management",
        "description": "Appropriate technical, operational and organizational measures to manage risks",
        "applies_to": ["essential", "important"],
    },
    {
        "id": "NIS2-21.2.a",
        "article": "21",
        "name": "Risk Analysis Policies",
        "description": "Policies on risk analysis and information system security",
        "applies_to": ["essential", "important"],
    },
    {
        "id": "NIS2-21.2.b",
        "article": "21",
        "name": "Incident Handling",
        "description": "Incident handling procedures",
        "applies_to": ["essential", "important"],
    },
    {
        "id": "NIS2-21.2.c",
        "article": "21",
        "name": "Business Continuity",
        "description": "Business continuity including backup management and disaster recovery",
        "applies_to": ["essential", "important"],
    },
    {
        "id": "NIS2-21.2.d",
        "article": "21",
        "name": "Supply Chain Security",
        "description": "Supply chain security including security-related aspects of relationships",
        "applies_to": ["essential", "important"],
    },
    {
        "id": "NIS2-21.2.e",
        "article": "21",
        "name": "Network Security",
        "description": "Security in network and information systems acquisition and development",
        "applies_to": ["essential", "important"],
    },
    {
        "id": "NIS2-21.2.f",
        "article": "21",
        "name": "Vulnerability Handling",
        "description": "Policies and procedures for assessing effectiveness of measures",
        "applies_to": ["essential", "important"],
    },
    {
        "id": "NIS2-21.2.g",
        "article": "21",
        "name": "Cybersecurity Hygiene",
        "description": "Basic cyber hygiene practices and cybersecurity training",
        "applies_to": ["essential", "important"],
    },
    {
        "id": "NIS2-21.2.h",
        "article": "21",
        "name": "Cryptography",
        "description": "Policies and procedures regarding use of cryptography and encryption",
        "applies_to": ["essential", "important"],
    },
    {
        "id": "NIS2-21.2.i",
        "article": "21",
        "name": "Human Resources Security",
        "description": "Human resources security, access control policies and asset management",
        "applies_to": ["essential", "important"],
    },
    {
        "id": "NIS2-21.2.j",
        "article": "21",
        "name": "Multi-factor Authentication",
        "description": "Use of multi-factor authentication and secured communications",
        "applies_to": ["essential", "important"],
    },
    {
        "id": "NIS2-23.1",
        "article": "23",
        "name": "Significant Incident Notification",
        "description": "Notify competent authority of any significant incident",
        "applies_to": ["essential", "important"],
    },
    {
        "id": "NIS2-23.4.a",
        "article": "23",
        "name": "Early Warning",
        "description": "Early warning within 24 hours of becoming aware of incident",
        "applies_to": ["essential", "important"],
    },
    {
        "id": "NIS2-23.4.b",
        "article": "23",
        "name": "Incident Notification",
        "description": "Incident notification within 72 hours with initial assessment",
        "applies_to": ["essential", "important"],
    },
    {
        "id": "NIS2-23.4.c",
        "article": "23",
        "name": "Final Report",
        "description": "Final report within one month after incident notification",
        "applies_to": ["essential", "important"],
    },
    {
        "id": "NIS2-24.1",
        "article": "24",
        "name": "Certification Schemes",
        "description": "May require use of certified ICT products, services and processes",
        "applies_to": ["essential", "important"],
    },
    {
        "id": "NIS2-26.1",
        "article": "26",
        "name": "Compliance Demonstration",
        "description": "Essential entities subject to supervision measures",
        "applies_to": ["essential"],
    },
]


# NIS2 Sector categories (flat structure for test compatibility)
NIS2_SECTORS = {
    "essential": {
        "energy": "Energy (electricity, oil, gas, hydrogen, district heating)",
        "transport": "Transport (air, rail, water, road)",
        "banking": "Banking",
        "financial_market": "Financial market infrastructures",
        "health": "Health",
        "drinking_water": "Drinking water",
        "waste_water": "Waste water",
        "digital_infrastructure": "Digital infrastructure",
        "ict_service_management": "ICT service management (B2B)",
        "public_administration": "Public administration",
        "space": "Space",
    },
    "important": {
        "postal_services": "Postal and courier services",
        "waste_management": "Waste management",
        "chemicals": "Manufacture of chemicals",
        "food": "Food production and distribution",
        "manufacturing": "Manufacturing (medical devices, computers, electronics, machinery, motor vehicles)",
        "digital_providers": "Digital providers (online marketplaces, search engines, social networks)",
        "research": "Research",
    },
}


class NIS2Parser:
    """Parser for NIS2-related documents."""

    def __init__(self):
        self.article_pattern = re.compile(r"Article\s+(\d+)", re.IGNORECASE)

    def parse_eur_lex(self, content: str) -> dict[str, Any]:
        """Parse EUR-Lex NIS2 document."""
        soup = BeautifulSoup(content, "lxml")

        result = {
            "title": "",
            "articles": [],
            "annexes": [],
        }

        # Extract title
        title_elem = soup.find("p", class_="oj-doc-ti")
        if title_elem:
            result["title"] = title_elem.get_text(strip=True)

        # Extract articles
        for article in soup.find_all("div", class_="eli-subdivision"):
            article_id = article.get("id", "")
            if article_id.startswith("art_"):
                article_num = article_id.replace("art_", "")
                article_title = ""
                article_content = ""

                title_elem = article.find("p", class_="oj-ti-art")
                if title_elem:
                    article_title = title_elem.get_text(strip=True)

                content_elem = article.find("div", class_="eli-subdivision")
                if content_elem:
                    article_content = content_elem.get_text(separator="\n", strip=True)

                result["articles"].append({
                    "number": article_num,
                    "title": article_title,
                    "content": article_content,
                })

        return result

    def parse_enisa_guidance(self, content: str) -> list[dict[str, Any]]:
        """Parse ENISA NIS2 guidance page."""
        soup = BeautifulSoup(content, "lxml")
        guidance = []

        for item in soup.select("article, .content-item, .publication-item"):
            title_elem = item.select_one("h2, h3, .title, a")
            date_elem = item.select_one(".date, time, .published-date")
            link_elem = item.select_one("a")

            if title_elem:
                guidance.append({
                    "title": title_elem.get_text(strip=True),
                    "url": link_elem.get("href") if link_elem else None,
                    "date": date_elem.get_text(strip=True) if date_elem else None,
                    "type": "guidance",
                })

        return guidance

    def get_all_requirements(self) -> list[dict[str, Any]]:
        """Get all NIS2 requirements for database initialization."""
        all_requirements = []

        for article_num, article in NIS2_REQUIREMENTS.items():
            for req in article["requirements"]:
                requirement = {
                    "requirement_id": f"NIS2-{req['id']}",
                    "article": article_num,
                    "article_title": article["title"],
                    "title": req["title"],
                    "description": req["description"],
                    "obligation_type": req["obligation"],
                    "category": req["category"],
                    "framework": "NIS2",
                    "citation": {
                        "article": f"Article {article_num}",
                    },
                }

                if "timeframe" in req:
                    requirement["timeframe"] = req["timeframe"]

                all_requirements.append(requirement)

        return all_requirements

    def get_sector_requirements(self) -> dict[str, Any]:
        """Get NIS2 sector classifications."""
        return NIS2_SECTORS


class NIS2SourceMonitor:
    """Monitors NIS2 regulatory sources."""

    def __init__(self):
        self.crawler = RegulatoryCrawler()
        self.parser = NIS2Parser()
        self.framework = "nis2"
        self.sources = NIS2_SOURCES

    async def check_eur_lex(self, source: RegulatorySource) -> dict[str, Any]:
        """Check EUR-Lex for NIS2 updates."""
        async with self.crawler:
            result = await self.crawler.crawl(source)

            if result.has_changed:
                parsed = self.parser.parse_eur_lex(result.content)
                return {
                    "changed": True,
                    "source": source.name,
                    "parsed": parsed,
                    "articles_count": len(parsed.get("articles", [])),
                }

            return {"changed": False, "source": source.name}

    async def check_enisa(self, source: RegulatorySource) -> dict[str, Any]:
        """Check ENISA for NIS2 guidance updates."""
        async with self.crawler:
            result = await self.crawler.crawl(source)

            if result.has_changed:
                guidance = self.parser.parse_enisa_guidance(result.content)
                return {
                    "changed": True,
                    "source": source.name,
                    "guidance": guidance,
                    "guidance_count": len(guidance),
                }

            return {"changed": False, "source": source.name}

    def get_all_requirements(self) -> list[dict[str, Any]]:
        """Get all NIS2 requirements for database initialization."""
        return self.parser.get_all_requirements()


def get_nis2_source_definitions() -> list[dict[str, Any]]:
    """Get predefined NIS2 source definitions."""
    return NIS2_SOURCES


async def initialize_nis2_sources(db) -> list[RegulatorySource]:
    """Initialize NIS2 sources in the database."""
    sources = []

    for source_def in NIS2_SOURCES:
        source = RegulatorySource(
            name=source_def["name"],
            description=source_def["description"],
            url=source_def["url"],
            jurisdiction=source_def["jurisdiction"],
            framework=source_def["framework"],
            parser_type=source_def["parser_type"],
            parser_config=source_def["parser_config"],
            is_active=True,
            check_interval_hours=24,  # Daily for EU regulations
        )
        db.add(source)
        sources.append(source)

    await db.flush()
    return sources
