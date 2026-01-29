"""South Korea Personal Information Protection Act (PIPA) regulatory source implementations."""

import re
from typing import Any

import structlog
from bs4 import BeautifulSoup

from app.models.regulation import Jurisdiction, RegulatoryFramework, RegulatorySource
from app.services.monitoring.crawler import RegulatoryCrawler


logger = structlog.get_logger()


# South Korea PIPA source definitions
KOREA_PIPA_SOURCES = [
    {
        "name": "PIPC Korea - PIPA",
        "description": "Personal Information Protection Commission - PIPA official information",
        "url": "https://www.pipc.go.kr/eng/user/ltn/lawInfo.do",
        "jurisdiction": Jurisdiction.SOUTH_KOREA,
        "framework": RegulatoryFramework.PIPA,
        "parser_type": "html",
        "parser_config": {
            "content_selector": ".content-area",
            "article_pattern": r"Article\s+(\d+)",
        },
    },
    {
        "name": "Korea Law Translation - PIPA",
        "description": "Official English translation of PIPA",
        "url": "https://elaw.klri.re.kr/eng_service/lawView.do?hseq=53044",
        "jurisdiction": Jurisdiction.SOUTH_KOREA,
        "framework": RegulatoryFramework.PIPA,
        "parser_type": "html",
        "parser_config": {
            "content_selector": ".lawCon",
            "article_pattern": r"Article\s+(\d+)",
        },
    },
    {
        "name": "PIPC Guidelines",
        "description": "PIPC guidelines and interpretations",
        "url": "https://www.pipc.go.kr/eng/user/ltn/guideInfo.do",
        "jurisdiction": Jurisdiction.SOUTH_KOREA,
        "framework": RegulatoryFramework.PIPA,
        "parser_type": "html",
        "parser_config": {},
    },
    {
        "name": "PIPC Enforcement",
        "description": "PIPC enforcement decisions",
        "url": "https://www.pipc.go.kr/eng/user/csc/notice.do",
        "jurisdiction": Jurisdiction.SOUTH_KOREA,
        "framework": RegulatoryFramework.PIPA,
        "parser_type": "html",
        "parser_config": {},
    },
]


# Key PIPA articles
PIPA_ARTICLES = {
    "1": {"title": "Purpose", "type": "general"},
    "2": {"title": "Definitions", "type": "definitions"},
    "3": {"title": "Principles of personal information protection", "type": "principles"},
    "15": {"title": "Collection and use of personal information", "type": "lawful_basis"},
    "16": {"title": "Limitation on collection of personal information", "type": "data_minimization"},
    "17": {"title": "Provision of personal information", "type": "sharing"},
    "18": {"title": "Limitations on use and provision", "type": "purpose_limitation"},
    "20": {"title": "Notification of sources", "type": "transparency"},
    "21": {"title": "Deletion of personal information", "type": "retention"},
    "22": {"title": "Consent", "type": "consent"},
    "23": {"title": "Processing of sensitive information", "type": "sensitive_data"},
    "24": {"title": "Limitations on processing of unique identifiers", "type": "sensitive_data"},
    "24-2": {"title": "Processing of pseudonymized information", "type": "pseudonymization"},
    "28-2": {"title": "Processing of pseudonymized information for research", "type": "research"},
    "28-7": {"title": "Transfer to third country", "type": "cross_border"},
    "29": {"title": "Safety measures", "type": "security"},
    "30": {"title": "Privacy policy", "type": "transparency"},
    "34": {"title": "Notification of breach", "type": "breach"},
    "35": {"title": "Right of access", "type": "rights"},
    "36": {"title": "Right to correction or deletion", "type": "rights"},
    "37": {"title": "Right to suspend processing", "type": "rights"},
    "37-2": {"title": "Right to data portability", "type": "rights"},
    "39-3": {"title": "Collection and use of information in online services", "type": "online"},
}


class KoreaPIPAParser:
    """Parser for South Korea PIPA documents."""

    def __init__(self):
        self.article_pattern = re.compile(r"Article\s+(\d+(?:-\d+)?)", re.IGNORECASE)
        self.korean_article_pattern = re.compile(r"제(\d+)조(?:의(\d+))?")
        self.chapter_pattern = re.compile(r"Chapter\s+(\d+)|제(\d+)장", re.IGNORECASE)

    def parse_pipa_statute(self, content: str) -> dict[str, Any]:
        """Parse PIPA statute content."""
        soup = BeautifulSoup(content, "lxml")

        result = {
            "title": "Personal Information Protection Act",
            "jurisdiction": "South Korea",
            "articles": [],
            "chapters": [],
            "supplementary_provisions": [],
            "last_updated": None,
        }

        # Extract title
        title_elem = soup.find("h1") or soup.find("title")
        if title_elem:
            title_text = title_elem.get_text(strip=True)
            if "Personal Information" in title_text or "개인정보" in title_text:
                result["title"] = title_text

        # Extract articles
        text_content = soup.get_text(separator="\n")
        current_article = None
        current_content = []

        for line in text_content.split("\n"):
            # Check for article match
            article_match = self.article_pattern.search(line)
            korean_match = self.korean_article_pattern.search(line)

            if article_match or korean_match:
                # Save previous article
                if current_article:
                    article_info = PIPA_ARTICLES.get(current_article, {})
                    result["articles"].append({
                        "number": current_article,
                        "title": article_info.get("title", ""),
                        "type": article_info.get("type", "general"),
                        "content": "\n".join(current_content),
                    })

                if article_match:
                    current_article = article_match.group(1)
                else:
                    # Convert Korean format to standard format
                    main = korean_match.group(1)
                    sub = korean_match.group(2)
                    current_article = f"{main}-{sub}" if sub else main

                current_content = [line]
            elif current_article:
                current_content.append(line)

        # Save last article
        if current_article:
            article_info = PIPA_ARTICLES.get(current_article, {})
            result["articles"].append({
                "number": current_article,
                "title": article_info.get("title", ""),
                "type": article_info.get("type", "general"),
                "content": "\n".join(current_content),
            })

        return result

    def parse_pipc_guidelines(self, content: str) -> list[dict[str, Any]]:
        """Parse PIPC guidelines listing."""
        soup = BeautifulSoup(content, "lxml")
        guidelines = []

        selectors = [
            ".board-list tbody tr",
            ".list-table tbody tr",
            ".content-list .item",
            "article",
            "ul.list li",
        ]

        for selector in selectors:
            items = soup.select(selector)
            if items:
                for item in items:
                    title_elem = item.select_one("td.title a, .title a, a")
                    link_elem = item.select_one("a[href]")
                    date_elem = item.select_one("td.date, .date, time")

                    if title_elem:
                        title_text = title_elem.get_text(strip=True)
                        if title_text and len(title_text) > 5:
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
        """Extract requirements from a PIPA article."""
        requirements = []
        content = article.get("content", "")

        # PIPA-specific obligation patterns
        obligation_patterns = [
            (r"shall\s+(?:not\s+)?(\w+(?:\s+\w+){0,10})", "must"),
            (r"must\s+(\w+(?:\s+\w+){0,10})", "must"),
            (r"shall\s+not\s+(\w+(?:\s+\w+){0,10})", "must_not"),
            (r"may\s+not\s+(\w+(?:\s+\w+){0,10})", "must_not"),
            (r"is\s+prohibited\s+from\s+(\w+(?:\s+\w+){0,10})", "must_not"),
            (r"may\s+(\w+(?:\s+\w+){0,10})", "may"),
            (r"is\s+required\s+to\s+(\w+(?:\s+\w+){0,10})", "must"),
            (r"has\s+the\s+right\s+to\s+(\w+(?:\s+\w+){0,10})", "right"),
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
                        "act": "Personal Information Protection Act",
                        "jurisdiction": "South Korea",
                    },
                })

        return requirements


class KoreaPIPASourceMonitor:
    """Monitors South Korea PIPA regulatory sources."""

    def __init__(self):
        self.crawler = RegulatoryCrawler()
        self.parser = KoreaPIPAParser()

    async def check_pipa_statute(self, source: RegulatorySource) -> dict[str, Any]:
        """Check for PIPA statute updates."""
        async with self.crawler:
            result = await self.crawler.crawl(source)

            if result.has_changed:
                parsed = self.parser.parse_pipa_statute(result.content)
                return {
                    "changed": True,
                    "source": source.name,
                    "parsed": parsed,
                    "articles_count": len(parsed.get("articles", [])),
                }

            return {"changed": False, "source": source.name}

    async def check_pipc_guidelines(self, source: RegulatorySource) -> dict[str, Any]:
        """Check PIPC for new guidelines."""
        async with self.crawler:
            result = await self.crawler.crawl(source)

            if result.has_changed:
                guidelines = self.parser.parse_pipc_guidelines(result.content)
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
        """Extract all requirements from PIPA content."""
        parsed = self.parser.parse_pipa_statute(content)
        all_requirements = []

        for article in parsed.get("articles", []):
            requirements = self.parser.extract_requirements_from_article(article)
            all_requirements.extend(requirements)

        return all_requirements


def get_korea_pipa_source_definitions() -> list[dict[str, Any]]:
    """Get predefined South Korea PIPA source definitions."""
    return KOREA_PIPA_SOURCES


async def initialize_korea_pipa_sources(db) -> list[RegulatorySource]:
    """Initialize South Korea PIPA sources in the database."""
    sources = []

    for source_def in KOREA_PIPA_SOURCES:
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
