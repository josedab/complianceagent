"""Japan Act on Protection of Personal Information (APPI) regulatory source implementations."""

import re
from typing import Any

import structlog
from bs4 import BeautifulSoup

from app.models.regulation import Jurisdiction, RegulatoryFramework, RegulatorySource
from app.services.monitoring.crawler import RegulatoryCrawler


logger = structlog.get_logger()


# Japan APPI source definitions
JAPAN_APPI_SOURCES = [
    {
        "name": "PPC Japan - APPI",
        "description": "Personal Information Protection Commission - APPI official text",
        "url": "https://www.ppc.go.jp/en/legal/",
        "jurisdiction": Jurisdiction.JAPAN,
        "framework": RegulatoryFramework.APPI,
        "parser_type": "html",
        "parser_config": {
            "content_selector": ".content-area",
            "article_pattern": r"Article\s+(\d+)",
        },
    },
    {
        "name": "PPC Guidelines",
        "description": "PPC guidelines on APPI implementation",
        "url": "https://www.ppc.go.jp/en/legal/guidelines/",
        "jurisdiction": Jurisdiction.JAPAN,
        "framework": RegulatoryFramework.APPI,
        "parser_type": "html",
        "parser_config": {
            "list_selector": ".guidelines-list",
        },
    },
    {
        "name": "e-Gov Japan - APPI",
        "description": "Official Japanese law database - APPI",
        "url": "https://elaws.e-gov.go.jp/document?lawid=415AC0000000057",
        "jurisdiction": Jurisdiction.JAPAN,
        "framework": RegulatoryFramework.APPI,
        "parser_type": "html",
        "parser_config": {
            "content_selector": ".LawBody",
            "article_pattern": r"第(\d+)条",
        },
    },
    {
        "name": "PPC Enforcement Actions",
        "description": "PPC enforcement actions and recommendations",
        "url": "https://www.ppc.go.jp/en/enforcement/",
        "jurisdiction": Jurisdiction.JAPAN,
        "framework": RegulatoryFramework.APPI,
        "parser_type": "html",
        "parser_config": {},
    },
]


# Key APPI articles
APPI_ARTICLES = {
    "1": {"title": "Purpose", "type": "general"},
    "2": {"title": "Definitions", "type": "definitions"},
    "3": {"title": "Basic principles", "type": "principles"},
    "17": {"title": "Restriction on purposes of use", "type": "purpose_limitation"},
    "18": {"title": "Specification of purposes of use", "type": "purpose_limitation"},
    "19": {"title": "Notification of purpose of use", "type": "transparency"},
    "20": {"title": "Proper acquisition", "type": "lawful_basis"},
    "21": {"title": "Acquisition of sensitive personal information", "type": "sensitive_data"},
    "22": {"title": "Accuracy of data", "type": "data_quality"},
    "23": {"title": "Security measures", "type": "security"},
    "24": {"title": "Supervision of employees", "type": "security"},
    "25": {"title": "Supervision of entrustees", "type": "processor"},
    "27": {"title": "Restriction on third-party provision", "type": "sharing"},
    "28": {"title": "Cross-border transfer", "type": "cross_border"},
    "29": {"title": "Records of third-party provision", "type": "accountability"},
    "30": {"title": "Records of receipt from third party", "type": "accountability"},
    "33": {"title": "Disclosure", "type": "rights"},
    "34": {"title": "Correction", "type": "rights"},
    "35": {"title": "Cessation of use", "type": "rights"},
    "36": {"title": "Anonymously processed information", "type": "anonymization"},
    "41": {"title": "Pseudonymously processed information", "type": "pseudonymization"},
}


class JapanAPPIParser:
    """Parser for Japan APPI documents."""

    def __init__(self):
        # Support both English and Japanese article patterns
        self.article_pattern_en = re.compile(r"Article\s+(\d+)", re.IGNORECASE)
        self.article_pattern_jp = re.compile(r"第(\d+)条")
        self.chapter_pattern = re.compile(r"Chapter\s+(\d+)|第(\d+)章", re.IGNORECASE)

    def parse_appi_statute(self, content: str) -> dict[str, Any]:
        """Parse APPI statute content."""
        soup = BeautifulSoup(content, "lxml")

        result = {
            "title": "Act on the Protection of Personal Information",
            "jurisdiction": "Japan",
            "articles": [],
            "chapters": [],
            "supplements": [],
            "last_updated": None,
        }

        # Extract title if available
        title_elem = soup.find("h1") or soup.find("title")
        if title_elem:
            title_text = title_elem.get_text(strip=True)
            if "個人情報" in title_text or "Personal Information" in title_text:
                result["title"] = title_text

        # Extract articles
        text_content = soup.get_text(separator="\n")
        current_article = None
        current_content = []

        for line in text_content.split("\n"):
            # Check for article match (English or Japanese)
            article_match = self.article_pattern_en.search(line) or self.article_pattern_jp.search(line)
            if article_match:
                # Save previous article
                if current_article:
                    article_info = APPI_ARTICLES.get(current_article, {})
                    result["articles"].append({
                        "number": current_article,
                        "title": article_info.get("title", ""),
                        "type": article_info.get("type", "general"),
                        "content": "\n".join(current_content),
                    })

                current_article = article_match.group(1)
                current_content = [line]
            elif current_article:
                current_content.append(line)

        # Save last article
        if current_article:
            article_info = APPI_ARTICLES.get(current_article, {})
            result["articles"].append({
                "number": current_article,
                "title": article_info.get("title", ""),
                "type": article_info.get("type", "general"),
                "content": "\n".join(current_content),
            })

        return result

    def parse_ppc_guidelines(self, content: str) -> list[dict[str, Any]]:
        """Parse PPC guidelines listing."""
        soup = BeautifulSoup(content, "lxml")
        guidelines = []

        selectors = [
            ".guidelines-list li",
            ".content-list .item",
            "article",
            ".list-group-item",
            "ul li a",
        ]

        for selector in selectors:
            items = soup.select(selector)
            if items:
                for item in items:
                    title_elem = item.select_one("a, h3, .title") or item
                    link_elem = item.select_one("a[href]") or (item if item.name == "a" else None)
                    date_elem = item.select_one(".date, time")

                    title_text = title_elem.get_text(strip=True) if title_elem else ""
                    if title_text and len(title_text) > 5:  # Filter out empty/short items
                        guidelines.append({
                            "title": title_text,
                            "url": link_elem.get("href") if link_elem else None,
                            "date": date_elem.get_text(strip=True) if date_elem else None,
                            "type": "guideline",
                        })
                break

        return guidelines

    def extract_requirements_from_article(
        self,
        article: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Extract requirements from an APPI article."""
        requirements = []
        content = article.get("content", "")

        # APPI-specific obligation patterns (English)
        obligation_patterns = [
            (r"shall\s+(?:not\s+)?(\w+(?:\s+\w+){0,10})", "must"),
            (r"must\s+(\w+(?:\s+\w+){0,10})", "must"),
            (r"shall\s+not\s+(\w+(?:\s+\w+){0,10})", "must_not"),
            (r"is\s+prohibited\s+from\s+(\w+(?:\s+\w+){0,10})", "must_not"),
            (r"may\s+not\s+(\w+(?:\s+\w+){0,10})", "must_not"),
            (r"may\s+(\w+(?:\s+\w+){0,10})", "may"),
            (r"is\s+required\s+to\s+(\w+(?:\s+\w+){0,10})", "must"),
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
                        "act": "Act on the Protection of Personal Information",
                        "jurisdiction": "Japan",
                    },
                })

        return requirements


class JapanAPPISourceMonitor:
    """Monitors Japan APPI regulatory sources."""

    def __init__(self):
        self.crawler = RegulatoryCrawler()
        self.parser = JapanAPPIParser()

    async def check_appi_statute(self, source: RegulatorySource) -> dict[str, Any]:
        """Check for APPI statute updates."""
        async with self.crawler:
            result = await self.crawler.crawl(source)

            if result.has_changed:
                parsed = self.parser.parse_appi_statute(result.content)
                return {
                    "changed": True,
                    "source": source.name,
                    "parsed": parsed,
                    "articles_count": len(parsed.get("articles", [])),
                }

            return {"changed": False, "source": source.name}

    async def check_ppc_guidelines(self, source: RegulatorySource) -> dict[str, Any]:
        """Check PPC for new guidelines."""
        async with self.crawler:
            result = await self.crawler.crawl(source)

            if result.has_changed:
                guidelines = self.parser.parse_ppc_guidelines(result.content)
                return {
                    "changed": True,
                    "source": source.name,
                    "guidelines": guidelines,
                    "guidelines_count": len(guidelines),
                }

            return {"changed": False, "source": source.name}

    async def extract_all_requirements(
        self,
        source: RegulatorySource,
        content: str,
    ) -> list[dict[str, Any]]:
        """Extract all requirements from APPI content."""
        parsed = self.parser.parse_appi_statute(content)
        all_requirements = []

        for article in parsed.get("articles", []):
            requirements = self.parser.extract_requirements_from_article(article)
            all_requirements.extend(requirements)

        return all_requirements


def get_japan_appi_source_definitions() -> list[dict[str, Any]]:
    """Get predefined Japan APPI source definitions."""
    return JAPAN_APPI_SOURCES


async def initialize_japan_appi_sources(db) -> list[RegulatorySource]:
    """Initialize Japan APPI sources in the database."""
    sources = []

    for source_def in JAPAN_APPI_SOURCES:
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
