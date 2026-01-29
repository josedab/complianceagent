"""ESG & Sustainability regulatory source implementations."""

import re
from typing import Any

import structlog
from bs4 import BeautifulSoup

from app.models.regulation import Jurisdiction, RegulatoryFramework, RegulatorySource
from app.services.monitoring.crawler import RegulatoryCrawler


logger = structlog.get_logger()


# ESG/Sustainability source definitions
ESG_SOURCES = [
    # EU Corporate Sustainability Reporting Directive (CSRD)
    {
        "name": "EUR-Lex CSRD",
        "description": "EU Corporate Sustainability Reporting Directive official text",
        "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022L2464",
        "jurisdiction": Jurisdiction.EU,
        "framework": RegulatoryFramework.CSRD,
        "parser_type": "html",
        "parser_config": {
            "content_selector": "#document1",
            "article_pattern": r"Article\s+(\d+)",
        },
    },
    {
        "name": "EFRAG ESRS Standards",
        "description": "European Financial Reporting Advisory Group - European Sustainability Reporting Standards",
        "url": "https://www.efrag.org/lab6",
        "jurisdiction": Jurisdiction.EU,
        "framework": RegulatoryFramework.CSRD,
        "parser_type": "html",
        "parser_config": {
            "list_selector": ".standards-list",
        },
    },
    # SEC Climate Disclosure
    {
        "name": "SEC Climate Disclosure Rules",
        "description": "SEC final rules on climate-related disclosures",
        "url": "https://www.sec.gov/rules/final/2024/33-11275.htm",
        "jurisdiction": Jurisdiction.US_FEDERAL,
        "framework": RegulatoryFramework.SEC_CLIMATE,
        "parser_type": "html",
        "parser_config": {
            "content_selector": ".rule-content",
        },
    },
    {
        "name": "SEC Climate FAQ",
        "description": "SEC climate disclosure guidance and FAQ",
        "url": "https://www.sec.gov/corpfin/climate-disclosure-guidance",
        "jurisdiction": Jurisdiction.US_FEDERAL,
        "framework": RegulatoryFramework.SEC_CLIMATE,
        "parser_type": "html",
        "parser_config": {},
    },
    # TCFD Framework
    {
        "name": "TCFD Recommendations",
        "description": "Task Force on Climate-related Financial Disclosures recommendations",
        "url": "https://www.fsb-tcfd.org/recommendations/",
        "jurisdiction": Jurisdiction.GLOBAL,
        "framework": RegulatoryFramework.TCFD,
        "parser_type": "html",
        "parser_config": {},
    },
    {
        "name": "TCFD Implementation Guidance",
        "description": "TCFD implementation guidance documents",
        "url": "https://www.fsb-tcfd.org/publications/",
        "jurisdiction": Jurisdiction.GLOBAL,
        "framework": RegulatoryFramework.TCFD,
        "parser_type": "html",
        "parser_config": {},
    },
    # GRI Standards
    {
        "name": "GRI Standards",
        "description": "Global Reporting Initiative sustainability standards",
        "url": "https://www.globalreporting.org/standards/",
        "jurisdiction": Jurisdiction.GLOBAL,
        "framework": RegulatoryFramework.CSRD,  # GRI aligns with CSRD
        "parser_type": "html",
        "parser_config": {},
    },
    # California Climate Disclosure (SB 253, SB 261)
    {
        "name": "California Climate Corporate Data Accountability Act",
        "description": "California SB 253 - Climate Corporate Data Accountability Act",
        "url": "https://leginfo.legislature.ca.gov/faces/billNavClient.xhtml?bill_id=202320240SB253",
        "jurisdiction": Jurisdiction.US_CALIFORNIA,
        "framework": RegulatoryFramework.SEC_CLIMATE,
        "parser_type": "html",
        "parser_config": {},
    },
]


# CSRD disclosure topics
CSRD_DISCLOSURE_TOPICS = {
    "E1": {
        "title": "Climate change",
        "type": "environmental",
        "subtopics": ["climate_mitigation", "climate_adaptation", "energy"],
    },
    "E2": {
        "title": "Pollution",
        "type": "environmental",
        "subtopics": ["air", "water", "soil", "substances_of_concern"],
    },
    "E3": {
        "title": "Water and marine resources",
        "type": "environmental",
        "subtopics": ["water_consumption", "water_discharge", "marine_resources"],
    },
    "E4": {
        "title": "Biodiversity and ecosystems",
        "type": "environmental",
        "subtopics": ["direct_drivers", "impacts_on_ecosystems"],
    },
    "E5": {
        "title": "Resource use and circular economy",
        "type": "environmental",
        "subtopics": ["resource_inflows", "resource_outflows", "waste"],
    },
    "S1": {
        "title": "Own workforce",
        "type": "social",
        "subtopics": ["working_conditions", "equal_treatment", "health_safety"],
    },
    "S2": {
        "title": "Workers in the value chain",
        "type": "social",
        "subtopics": ["working_conditions", "equal_treatment", "health_safety"],
    },
    "S3": {
        "title": "Affected communities",
        "type": "social",
        "subtopics": ["communities_rights", "indigenous_peoples"],
    },
    "S4": {
        "title": "Consumers and end-users",
        "type": "social",
        "subtopics": ["information_privacy", "health_safety", "social_inclusion"],
    },
    "G1": {
        "title": "Business conduct",
        "type": "governance",
        "subtopics": ["corporate_culture", "corruption_bribery", "political_engagement"],
    },
}


# SEC Climate Disclosure Requirements
SEC_CLIMATE_REQUIREMENTS = {
    "governance": {
        "title": "Governance of climate-related risks",
        "requirements": [
            "Board oversight of climate-related risks",
            "Management role in assessing and managing climate-related risks",
        ],
    },
    "strategy": {
        "title": "Strategy for climate-related risks",
        "requirements": [
            "Climate-related risks and opportunities identification",
            "Impact on business model and strategy",
            "Resilience of strategy under different climate scenarios",
        ],
    },
    "risk_management": {
        "title": "Risk management processes",
        "requirements": [
            "Processes for identifying climate-related risks",
            "Processes for managing climate-related risks",
            "Integration into overall risk management",
        ],
    },
    "metrics_targets": {
        "title": "Metrics and targets",
        "requirements": [
            "Scope 1 GHG emissions",
            "Scope 2 GHG emissions",
            "Scope 3 GHG emissions (if material)",
            "Climate-related targets",
            "Progress against targets",
        ],
    },
}


class ESGParser:
    """Parser for ESG/Sustainability documents."""

    def __init__(self):
        self.article_pattern = re.compile(r"Article\s+(\d+)", re.IGNORECASE)
        self.esrs_pattern = re.compile(r"ESRS\s+([A-Z]\d+)", re.IGNORECASE)
        self.scope_pattern = re.compile(r"Scope\s+(\d+)", re.IGNORECASE)

    def parse_csrd_directive(self, content: str) -> dict[str, Any]:
        """Parse CSRD directive content."""
        soup = BeautifulSoup(content, "lxml")

        result = {
            "title": "Corporate Sustainability Reporting Directive (CSRD)",
            "jurisdiction": "EU",
            "articles": [],
            "recitals": [],
            "annexes": [],
            "last_updated": None,
        }

        # Extract title
        title_elem = soup.find("p", class_="oj-doc-ti") or soup.find("title")
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

    def parse_esrs_standard(self, content: str) -> dict[str, Any]:
        """Parse European Sustainability Reporting Standard."""
        soup = BeautifulSoup(content, "lxml")

        result = {
            "title": "",
            "standard_id": "",
            "disclosure_requirements": [],
            "datapoints": [],
            "application_guidance": [],
        }

        # Extract standard ID
        text_content = soup.get_text()
        esrs_match = self.esrs_pattern.search(text_content)
        if esrs_match:
            result["standard_id"] = esrs_match.group(1)

        return result

    def parse_sec_climate_rule(self, content: str) -> dict[str, Any]:
        """Parse SEC climate disclosure rule."""
        soup = BeautifulSoup(content, "lxml")

        result = {
            "title": "SEC Climate-Related Disclosures",
            "jurisdiction": "US Federal",
            "sections": [],
            "requirements": SEC_CLIMATE_REQUIREMENTS,
            "effective_dates": [],
        }

        # Extract title
        title_elem = soup.find("h1") or soup.find("title")
        if title_elem:
            result["title"] = title_elem.get_text(strip=True)

        return result

    def parse_tcfd_recommendations(self, content: str) -> dict[str, Any]:
        """Parse TCFD recommendations."""
        soup = BeautifulSoup(content, "lxml")

        result = {
            "title": "TCFD Recommendations",
            "pillars": ["governance", "strategy", "risk_management", "metrics_targets"],
            "recommendations": [],
            "guidance": [],
        }

        return result

    def extract_requirements_from_csrd(
        self,
        article: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Extract requirements from CSRD article."""
        requirements = []
        content = article.get("content", "")

        # ESG-specific obligation patterns
        obligation_patterns = [
            (r"shall\s+(?:be\s+required\s+to\s+)?(\w+(?:\s+\w+){0,10})", "must"),
            (r"shall\s+disclose\s+(\w+(?:\s+\w+){0,10})", "must"),
            (r"shall\s+report\s+(\w+(?:\s+\w+){0,10})", "must"),
            (r"shall\s+include\s+(\w+(?:\s+\w+){0,10})", "must"),
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
                    "category": "sustainability_reporting",
                    "citation": {
                        "article": f"Article {article.get('number')}",
                        "directive": "Directive (EU) 2022/2464 (CSRD)",
                        "jurisdiction": "EU",
                    },
                })

        return requirements

    def extract_ghg_requirements(self, content: str) -> list[dict[str, Any]]:
        """Extract GHG emissions reporting requirements."""
        requirements = []

        # Find Scope 1, 2, 3 references
        scope_matches = self.scope_pattern.finditer(content)
        for match in scope_matches:
            scope_num = match.group(1)
            context_start = max(0, match.start() - 150)
            context_end = min(len(content), match.end() + 150)
            context = content[context_start:context_end]

            scope_descriptions = {
                "1": "direct GHG emissions from owned or controlled sources",
                "2": "indirect GHG emissions from purchased energy",
                "3": "all other indirect GHG emissions in value chain",
            }

            requirements.append({
                "scope": f"Scope {scope_num}",
                "description": scope_descriptions.get(scope_num, ""),
                "source_text": context,
                "category": "ghg_emissions",
                "obligation_type": "must" if scope_num in ["1", "2"] else "conditional",
            })

        return requirements


class ESGSourceMonitor:
    """Monitors ESG/Sustainability regulatory sources."""

    def __init__(self):
        self.crawler = RegulatoryCrawler()
        self.parser = ESGParser()

    async def check_csrd(self, source: RegulatorySource) -> dict[str, Any]:
        """Check for CSRD updates."""
        async with self.crawler:
            result = await self.crawler.crawl(source)

            if result.has_changed:
                parsed = self.parser.parse_csrd_directive(result.content)
                return {
                    "changed": True,
                    "source": source.name,
                    "parsed": parsed,
                    "articles_count": len(parsed.get("articles", [])),
                }

            return {"changed": False, "source": source.name}

    async def check_sec_climate(self, source: RegulatorySource) -> dict[str, Any]:
        """Check SEC climate rules for updates."""
        async with self.crawler:
            result = await self.crawler.crawl(source)

            if result.has_changed:
                parsed = self.parser.parse_sec_climate_rule(result.content)
                return {
                    "changed": True,
                    "source": source.name,
                    "parsed": parsed,
                }

            return {"changed": False, "source": source.name}

    async def extract_all_requirements(
        self,
        source: RegulatorySource,
        content: str,
    ) -> list[dict[str, Any]]:
        """Extract all ESG requirements from content."""
        all_requirements = []

        if source.framework == RegulatoryFramework.CSRD:
            parsed = self.parser.parse_csrd_directive(content)
            for article in parsed.get("articles", []):
                requirements = self.parser.extract_requirements_from_csrd(article)
                all_requirements.extend(requirements)

        # Add GHG requirements
        ghg_requirements = self.parser.extract_ghg_requirements(content)
        all_requirements.extend(ghg_requirements)

        return all_requirements


def get_esg_source_definitions() -> list[dict[str, Any]]:
    """Get predefined ESG source definitions."""
    return ESG_SOURCES


async def initialize_esg_sources(db) -> list[RegulatorySource]:
    """Initialize ESG sources in the database."""
    sources = []

    for source_def in ESG_SOURCES:
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
