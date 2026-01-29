"""GDPR regulatory source implementations."""

import re
from typing import Any

import structlog
from bs4 import BeautifulSoup

from app.models.regulation import Jurisdiction, RegulatoryFramework, RegulatorySource
from app.services.monitoring.crawler import RegulatoryCrawler


logger = structlog.get_logger()


# GDPR source definitions
GDPR_SOURCES = [
    {
        "name": "EUR-Lex GDPR",
        "description": "Official EU GDPR regulation text and amendments",
        "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32016R0679",
        "jurisdiction": Jurisdiction.EU,
        "framework": RegulatoryFramework.GDPR,
        "parser_type": "html",
        "parser_config": {
            "content_selector": "#document1",
            "article_pattern": r"Article\s+(\d+)",
        },
    },
    {
        "name": "EDPB Guidelines",
        "description": "European Data Protection Board guidelines and opinions",
        "url": "https://edpb.europa.eu/our-work-tools/general-guidance/gdpr-guidelines-recommendations-best-practices_en",
        "jurisdiction": Jurisdiction.EU,
        "framework": RegulatoryFramework.GDPR,
        "parser_type": "html",
        "parser_config": {
            "list_selector": ".view-content",
            "item_selector": ".views-row",
        },
    },
    {
        "name": "ICO UK Guidance",
        "description": "UK Information Commissioner's Office GDPR guidance",
        "url": "https://ico.org.uk/for-organisations/guide-to-data-protection/guide-to-the-general-data-protection-regulation-gdpr/",
        "jurisdiction": Jurisdiction.UK,
        "framework": RegulatoryFramework.UK_GDPR,
        "parser_type": "html",
        "parser_config": {},
    },
    {
        "name": "CNIL France Guidance",
        "description": "French DPA GDPR guidance and decisions",
        "url": "https://www.cnil.fr/en/gdpr-guidelines",
        "jurisdiction": Jurisdiction.EU,
        "framework": RegulatoryFramework.GDPR,
        "parser_type": "html",
        "parser_config": {},
    },
]


class GDPRParser:
    """Parser for GDPR-related documents."""

    def __init__(self):
        self.article_pattern = re.compile(r"Article\s+(\d+)", re.IGNORECASE)
        self.recital_pattern = re.compile(r"\((\d+)\)", re.IGNORECASE)

    def parse_eur_lex(self, content: str) -> dict[str, Any]:
        """Parse EUR-Lex GDPR document."""
        soup = BeautifulSoup(content, "lxml")

        result = {
            "title": "",
            "articles": [],
            "recitals": [],
            "chapters": [],
            "last_updated": None,
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

    def parse_edpb_guidelines(self, content: str) -> list[dict[str, Any]]:
        """Parse EDPB guidelines listing."""
        soup = BeautifulSoup(content, "lxml")
        guidelines = []

        for item in soup.select(".views-row"):
            title_elem = item.select_one("h3 a, .views-field-title a")
            date_elem = item.select_one(".date-display-single, .views-field-created")
            link_elem = item.select_one("a")

            if title_elem:
                guidelines.append({
                    "title": title_elem.get_text(strip=True),
                    "url": link_elem.get("href") if link_elem else None,
                    "date": date_elem.get_text(strip=True) if date_elem else None,
                })

        return guidelines

    def extract_requirements_from_article(
        self,
        article: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Extract requirements from a GDPR article."""
        requirements = []
        content = article.get("content", "")

        # Common obligation patterns
        obligation_patterns = [
            (r"shall\s+(?:be\s+)?(\w+(?:\s+\w+){0,10})", "must"),
            (r"must\s+(\w+(?:\s+\w+){0,10})", "must"),
            (r"shall\s+not\s+(\w+(?:\s+\w+){0,10})", "must_not"),
            (r"should\s+(\w+(?:\s+\w+){0,10})", "should"),
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
                    "article": article.get("number"),
                    "title": article.get("title"),
                    "obligation_type": obligation_type,
                    "action": action,
                    "source_text": context,
                    "citation": {
                        "article": f"Article {article.get('number')}",
                    },
                })

        return requirements


class GDPRSourceMonitor:
    """Monitors GDPR regulatory sources."""

    def __init__(self):
        self.crawler = RegulatoryCrawler()
        self.parser = GDPRParser()

    async def check_eur_lex(self, source: RegulatorySource) -> dict[str, Any]:
        """Check EUR-Lex for GDPR updates."""
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

    async def check_edpb(self, source: RegulatorySource) -> dict[str, Any]:
        """Check EDPB for new guidelines."""
        async with self.crawler:
            result = await self.crawler.crawl(source)

            if result.has_changed:
                guidelines = self.parser.parse_edpb_guidelines(result.content)
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
        """Extract all requirements from GDPR content."""
        parsed = self.parser.parse_eur_lex(content)
        all_requirements = []

        for article in parsed.get("articles", []):
            requirements = self.parser.extract_requirements_from_article(article)
            all_requirements.extend(requirements)

        return all_requirements


# GDPR Articles for test compatibility
GDPR_ARTICLES = {
    "5": {"title": "Principles relating to processing of personal data", "type": "principle"},
    "6": {"title": "Lawfulness of processing", "type": "lawful_basis"},
    "7": {"title": "Conditions for consent", "type": "consent"},
    "12": {"title": "Transparent information and communication", "type": "rights"},
    "13": {"title": "Information to be provided (direct collection)", "type": "rights"},
    "14": {"title": "Information to be provided (indirect collection)", "type": "rights"},
    "15": {"title": "Right of access by the data subject", "type": "rights"},
    "16": {"title": "Right to rectification", "type": "rights"},
    "17": {"title": "Right to erasure (right to be forgotten)", "type": "rights"},
    "18": {"title": "Right to restriction of processing", "type": "rights"},
    "20": {"title": "Right to data portability", "type": "rights"},
    "21": {"title": "Right to object", "type": "rights"},
    "22": {"title": "Automated individual decision-making", "type": "rights"},
    "25": {"title": "Data protection by design and by default", "type": "technical"},
    "30": {"title": "Records of processing activities", "type": "accountability"},
    "32": {"title": "Security of processing", "type": "security"},
    "33": {"title": "Notification of breach to authority", "type": "breach"},
    "34": {"title": "Communication of breach to data subject", "type": "breach"},
    "35": {"title": "Data protection impact assessment", "type": "accountability"},
    "37": {"title": "Designation of DPO", "type": "dpo"},
}


def get_gdpr_source_definitions() -> list[dict[str, Any]]:
    """Get predefined GDPR source definitions."""
    return GDPR_SOURCES


async def initialize_gdpr_sources(db) -> list[RegulatorySource]:
    """Initialize GDPR sources in the database."""
    sources = []

    for source_def in GDPR_SOURCES:
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
