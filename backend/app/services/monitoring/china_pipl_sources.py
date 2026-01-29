"""China Personal Information Protection Law (PIPL) regulatory source implementations."""

import re
from typing import Any

import structlog
from bs4 import BeautifulSoup

from app.models.regulation import Jurisdiction, RegulatoryFramework, RegulatorySource
from app.services.monitoring.crawler import RegulatoryCrawler


logger = structlog.get_logger()


# China PIPL source definitions
CHINA_PIPL_SOURCES = [
    {
        "name": "NPC China - PIPL",
        "description": "National People's Congress - PIPL official text",
        "url": "http://www.npc.gov.cn/npc/c30834/202108/a8c4e3672c74491a80b53a172bb753fe.shtml",
        "jurisdiction": Jurisdiction.CHINA,
        "framework": RegulatoryFramework.PIPL,
        "parser_type": "html",
        "parser_config": {
            "content_selector": ".article",
            "article_pattern": r"第(\d+)条",
        },
    },
    {
        "name": "CAC China - Data Security",
        "description": "Cyberspace Administration of China - Data security regulations",
        "url": "http://www.cac.gov.cn/",
        "jurisdiction": Jurisdiction.CHINA,
        "framework": RegulatoryFramework.PIPL,
        "parser_type": "html",
        "parser_config": {},
    },
    {
        "name": "China Law Translate - PIPL",
        "description": "English translation of PIPL",
        "url": "https://www.chinalawtranslate.com/en/pipl/",
        "jurisdiction": Jurisdiction.CHINA,
        "framework": RegulatoryFramework.PIPL,
        "parser_type": "html",
        "parser_config": {
            "content_selector": ".entry-content",
            "article_pattern": r"Article\s+(\d+)",
        },
    },
    {
        "name": "TC260 Standards",
        "description": "National Information Security Standardization Technical Committee",
        "url": "https://www.tc260.org.cn/",
        "jurisdiction": Jurisdiction.CHINA,
        "framework": RegulatoryFramework.PIPL,
        "parser_type": "html",
        "parser_config": {},
    },
]


# Key PIPL articles
PIPL_ARTICLES = {
    "1": {"title": "Purpose", "type": "general"},
    "2": {"title": "Scope of application", "type": "scope"},
    "3": {"title": "Extraterritorial effect", "type": "scope"},
    "4": {"title": "Definition of personal information", "type": "definitions"},
    "5": {"title": "Lawfulness principles", "type": "principles"},
    "6": {"title": "Purpose limitation", "type": "purpose_limitation"},
    "7": {"title": "Data minimization", "type": "data_minimization"},
    "8": {"title": "Data quality", "type": "data_quality"},
    "9": {"title": "Security obligation", "type": "security"},
    "13": {"title": "Lawful bases for processing", "type": "lawful_basis"},
    "14": {"title": "Consent requirements", "type": "consent"},
    "15": {"title": "Withdrawal of consent", "type": "consent"},
    "16": {"title": "Refusal of service prohibition", "type": "consent"},
    "17": {"title": "Notice requirements", "type": "transparency"},
    "23": {"title": "Entrustment of processing", "type": "processor"},
    "24": {"title": "Third party sharing", "type": "sharing"},
    "25": {"title": "Public disclosure", "type": "sharing"},
    "26": {"title": "Public places image collection", "type": "surveillance"},
    "27": {"title": "Publicly available information", "type": "public_data"},
    "28": {"title": "Sensitive personal information", "type": "sensitive_data"},
    "29": {"title": "Separate consent for sensitive data", "type": "sensitive_data"},
    "31": {"title": "Minor's personal information", "type": "children"},
    "38": {"title": "Cross-border transfer conditions", "type": "cross_border"},
    "39": {"title": "Separate consent for transfer", "type": "cross_border"},
    "40": {"title": "Critical information infrastructure", "type": "cross_border"},
    "44": {"title": "Right to know and decide", "type": "rights"},
    "45": {"title": "Right to access and copy", "type": "rights"},
    "46": {"title": "Right to correction and completion", "type": "rights"},
    "47": {"title": "Right to deletion", "type": "rights"},
    "48": {"title": "Right to explanation", "type": "rights"},
    "49": {"title": "Rights exercise by deceased persons' relatives", "type": "rights"},
    "51": {"title": "Security measures", "type": "security"},
    "52": {"title": "Data protection officer", "type": "accountability"},
    "54": {"title": "Security impact assessment", "type": "accountability"},
    "55": {"title": "Mandatory impact assessment scenarios", "type": "accountability"},
    "57": {"title": "Data breach notification", "type": "breach"},
    "66": {"title": "Penalties for violations", "type": "penalties"},
}


class ChinaPIPLParser:
    """Parser for China PIPL documents."""

    def __init__(self):
        self.article_pattern_en = re.compile(r"Article\s+(\d+)", re.IGNORECASE)
        self.article_pattern_cn = re.compile(r"第(\d+)条")
        self.chapter_pattern = re.compile(r"Chapter\s+(\d+)|第(\d+)章", re.IGNORECASE)

    def parse_pipl_statute(self, content: str) -> dict[str, Any]:
        """Parse PIPL statute content."""
        soup = BeautifulSoup(content, "lxml")

        result = {
            "title": "Personal Information Protection Law of the People's Republic of China",
            "jurisdiction": "China",
            "articles": [],
            "chapters": [],
            "supplementary_provisions": [],
            "last_updated": None,
        }

        # Extract title
        title_elem = soup.find("h1") or soup.find("title")
        if title_elem:
            title_text = title_elem.get_text(strip=True)
            if "个人信息" in title_text or "Personal Information" in title_text:
                result["title"] = title_text

        # Extract articles
        text_content = soup.get_text(separator="\n")
        current_article = None
        current_content = []

        for line in text_content.split("\n"):
            # Check for article match (English or Chinese)
            article_match = self.article_pattern_en.search(line)
            chinese_match = self.article_pattern_cn.search(line)

            if article_match or chinese_match:
                # Save previous article
                if current_article:
                    article_info = PIPL_ARTICLES.get(current_article, {})
                    result["articles"].append({
                        "number": current_article,
                        "title": article_info.get("title", ""),
                        "type": article_info.get("type", "general"),
                        "content": "\n".join(current_content),
                    })

                current_article = (article_match or chinese_match).group(1)
                current_content = [line]
            elif current_article:
                current_content.append(line)

        # Save last article
        if current_article:
            article_info = PIPL_ARTICLES.get(current_article, {})
            result["articles"].append({
                "number": current_article,
                "title": article_info.get("title", ""),
                "type": article_info.get("type", "general"),
                "content": "\n".join(current_content),
            })

        return result

    def parse_cac_updates(self, content: str) -> list[dict[str, Any]]:
        """Parse CAC updates and announcements."""
        soup = BeautifulSoup(content, "lxml")
        updates = []

        selectors = [
            ".news-list li",
            ".list-item",
            ".content-item",
            "article",
            "ul li a",
        ]

        for selector in selectors:
            items = soup.select(selector)
            if items:
                for item in items:
                    title_elem = item.select_one("a, h3, .title") or item
                    link_elem = item.select_one("a[href]") or (item if item.name == "a" else None)
                    date_elem = item.select_one(".date, time, span")

                    if title_elem:
                        title_text = title_elem.get_text(strip=True)
                        if title_text and len(title_text) > 5:
                            updates.append({
                                "title": title_text,
                                "url": link_elem.get("href") if link_elem else None,
                                "date": date_elem.get_text(strip=True) if date_elem else None,
                                "type": "update",
                            })
                break

        return updates

    def extract_requirements_from_article(
        self,
        article: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Extract requirements from a PIPL article."""
        requirements = []
        content = article.get("content", "")

        # PIPL-specific obligation patterns
        obligation_patterns = [
            (r"shall\s+(?:not\s+)?(\w+(?:\s+\w+){0,10})", "must"),
            (r"must\s+(\w+(?:\s+\w+){0,10})", "must"),
            (r"shall\s+not\s+(\w+(?:\s+\w+){0,10})", "must_not"),
            (r"may\s+not\s+(\w+(?:\s+\w+){0,10})", "must_not"),
            (r"is\s+prohibited\s+from\s+(\w+(?:\s+\w+){0,10})", "must_not"),
            (r"may\s+(\w+(?:\s+\w+){0,10})", "may"),
            (r"is\s+required\s+to\s+(\w+(?:\s+\w+){0,10})", "must"),
            (r"has\s+the\s+right\s+to\s+(\w+(?:\s+\w+){0,10})", "right"),
            (r"have\s+the\s+right\s+to\s+(\w+(?:\s+\w+){0,10})", "right"),
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
                        "act": "Personal Information Protection Law",
                        "jurisdiction": "China",
                    },
                })

        return requirements


class ChinaPIPLSourceMonitor:
    """Monitors China PIPL regulatory sources."""

    def __init__(self):
        self.crawler = RegulatoryCrawler()
        self.parser = ChinaPIPLParser()

    async def check_pipl_statute(self, source: RegulatorySource) -> dict[str, Any]:
        """Check for PIPL statute updates."""
        async with self.crawler:
            result = await self.crawler.crawl(source)

            if result.has_changed:
                parsed = self.parser.parse_pipl_statute(result.content)
                return {
                    "changed": True,
                    "source": source.name,
                    "parsed": parsed,
                    "articles_count": len(parsed.get("articles", [])),
                }

            return {"changed": False, "source": source.name}

    async def check_cac_updates(self, source: RegulatorySource) -> dict[str, Any]:
        """Check CAC for updates."""
        async with self.crawler:
            result = await self.crawler.crawl(source)

            if result.has_changed:
                updates = self.parser.parse_cac_updates(result.content)
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
        """Extract all requirements from PIPL content."""
        parsed = self.parser.parse_pipl_statute(content)
        all_requirements = []

        for article in parsed.get("articles", []):
            requirements = self.parser.extract_requirements_from_article(article)
            all_requirements.extend(requirements)

        return all_requirements


def get_china_pipl_source_definitions() -> list[dict[str, Any]]:
    """Get predefined China PIPL source definitions."""
    return CHINA_PIPL_SOURCES


async def initialize_china_pipl_sources(db) -> list[RegulatorySource]:
    """Initialize China PIPL sources in the database."""
    sources = []

    for source_def in CHINA_PIPL_SOURCES:
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
