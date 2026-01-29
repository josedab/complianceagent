"""EU AI Act regulatory sources."""

import re
from typing import Any

import structlog
from bs4 import BeautifulSoup

from app.models.regulation import Jurisdiction, RegulatoryFramework, RegulatorySource
from app.services.monitoring.crawler import RegulatoryCrawler


logger = structlog.get_logger()


# EU AI Act source definitions
EU_AI_ACT_SOURCES = [
    {
        "name": "EU AI Act Official Text",
        "description": "Official EU AI Act regulation from EUR-Lex",
        "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689",
        "jurisdiction": Jurisdiction.EU,
        "framework": RegulatoryFramework.EU_AI_ACT,
        "parser_type": "html",
        "parser_config": {
            "content_selector": "#document1",
            "article_pattern": r"Article\s+(\d+)",
        },
    },
    {
        "name": "European AI Office",
        "description": "European AI Office guidance and updates",
        "url": "https://digital-strategy.ec.europa.eu/en/policies/ai-office",
        "jurisdiction": Jurisdiction.EU,
        "framework": RegulatoryFramework.EU_AI_ACT,
        "parser_type": "html",
        "parser_config": {},
    },
    {
        "name": "AI Standards and Guidelines",
        "description": "European approach to AI standards and guidelines",
        "url": "https://digital-strategy.ec.europa.eu/en/policies/european-approach-artificial-intelligence",
        "jurisdiction": Jurisdiction.EU,
        "framework": RegulatoryFramework.EU_AI_ACT,
        "parser_type": "html",
        "parser_config": {},
    },
]


# EU AI Act Risk Categories (exported as EU_AI_ACT_RISK_CATEGORIES for test compatibility)
EU_AI_ACT_RISK_CATEGORIES = AI_RISK_CATEGORIES = {
    "unacceptable": {
        "description": "AI systems that pose clear threats to safety, livelihoods, and rights",
        "prohibited": True,
        "examples": [
            "Social scoring by governments",
            "Real-time biometric identification in public spaces",
            "Emotion recognition in workplace/education",
            "AI exploiting vulnerabilities of specific groups",
            "Subliminal manipulation causing harm",
        ],
    },
    "high": {
        "description": "AI systems in high-risk areas requiring strict compliance",
        "prohibited": False,
        "areas": [
            "Biometric identification",
            "Critical infrastructure",
            "Education and training",
            "Employment and worker management",
            "Essential services (credit, insurance)",
            "Law enforcement",
            "Migration and border control",
            "Justice and democratic processes",
        ],
    },
    "limited": {
        "description": "AI systems with transparency obligations",
        "prohibited": False,
        "examples": [
            "Chatbots",
            "Emotion recognition",
            "Biometric categorization",
            "AI-generated content (deepfakes)",
        ],
    },
    "minimal": {
        "description": "AI systems with minimal or no additional obligations",
        "prohibited": False,
        "examples": [
            "AI-enabled video games",
            "Spam filters",
        ],
    },
}


# High-Risk AI System Requirements
HIGH_RISK_REQUIREMENTS = [
    {
        "article": "Article 9",
        "title": "Risk Management System",
        "obligation_type": "must",
        "subject": "provider",
        "action": "establish, implement, document and maintain a risk management system",
        "scope": {
            "includes": [
                "identification and analysis of known and foreseeable risks",
                "estimation and evaluation of risks",
                "adoption of risk management measures",
                "testing to identify appropriate measures",
            ],
        },
    },
    {
        "article": "Article 10",
        "title": "Data and Data Governance",
        "obligation_type": "must",
        "subject": "provider",
        "action": "ensure training, validation and testing data sets meet quality criteria",
        "scope": {
            "criteria": [
                "relevant",
                "sufficiently representative",
                "free of errors",
                "complete",
            ],
            "includes": ["data governance practices", "bias examination"],
        },
    },
    {
        "article": "Article 11",
        "title": "Technical Documentation",
        "obligation_type": "must",
        "subject": "provider",
        "action": "draw up technical documentation before placing on market",
        "scope": {
            "includes": [
                "general description of AI system",
                "detailed description of elements",
                "monitoring, functioning, control",
                "risk management system description",
            ],
        },
    },
    {
        "article": "Article 12",
        "title": "Record-Keeping",
        "obligation_type": "must",
        "subject": "provider",
        "action": "ensure automatic recording of events (logs)",
        "scope": {
            "logs_must_include": [
                "operation period",
                "reference database",
                "input data",
                "identification of natural persons involved in verification",
            ],
            "retention": "appropriate to intended purpose",
        },
    },
    {
        "article": "Article 13",
        "title": "Transparency and Information",
        "obligation_type": "must",
        "subject": "provider",
        "action": "ensure AI system operation is sufficiently transparent for deployers",
        "scope": {
            "includes": [
                "instructions for use",
                "characteristics, capabilities, limitations",
                "intended purpose",
                "level of accuracy, robustness, cybersecurity",
            ],
        },
    },
    {
        "article": "Article 14",
        "title": "Human Oversight",
        "obligation_type": "must",
        "subject": "provider",
        "action": "design and develop AI systems to be effectively overseen by natural persons",
        "scope": {
            "measures": [
                "human-machine interface",
                "ability to understand capabilities and limitations",
                "ability to interpret output",
                "ability to decide not to use or override",
                "ability to intervene or interrupt",
            ],
        },
    },
    {
        "article": "Article 15",
        "title": "Accuracy, Robustness, Cybersecurity",
        "obligation_type": "must",
        "subject": "provider",
        "action": "design and develop AI systems to achieve appropriate levels of accuracy, robustness, and cybersecurity",
        "scope": {
            "includes": [
                "accuracy metrics declared in documentation",
                "resilience to errors and inconsistencies",
                "protection against manipulation",
            ],
        },
    },
    {
        "article": "Article 16",
        "title": "Quality Management System",
        "obligation_type": "must",
        "subject": "provider",
        "action": "put in place a quality management system",
        "scope": {
            "includes": [
                "compliance strategy",
                "design and development procedures",
                "testing and validation",
                "data management",
                "risk management",
                "post-market monitoring",
            ],
        },
    },
    {
        "article": "Article 17",
        "title": "EU Declaration of Conformity",
        "obligation_type": "must",
        "subject": "provider",
        "action": "draw up EU declaration of conformity",
        "scope": {
            "before": "placing on market or putting into service",
            "content": ["provider identification", "AI system identification", "conformity assessment body"],
        },
    },
    {
        "article": "Article 49",
        "title": "CE Marking",
        "obligation_type": "must",
        "subject": "provider",
        "action": "affix CE marking to high-risk AI system",
        "scope": {
            "when": "before placing on market",
            "requirements": ["visible", "legible", "indelible"],
        },
    },
]

# GPAI (General Purpose AI) Model Requirements
GPAI_REQUIREMENTS = [
    {
        "article": "Article 53",
        "title": "GPAI Model Documentation",
        "obligation_type": "must",
        "subject": "provider_of_gpai",
        "action": "draw up and keep up-to-date technical documentation",
        "scope": {
            "includes": [
                "model description",
                "training processes",
                "evaluation results",
                "capabilities and limitations",
            ],
        },
    },
    {
        "article": "Article 53",
        "title": "GPAI Information for Downstream",
        "obligation_type": "must",
        "subject": "provider_of_gpai",
        "action": "provide information and documentation to downstream providers",
        "scope": {
            "purpose": "enable compliance with AI Act requirements",
        },
    },
    {
        "article": "Article 53",
        "title": "GPAI Copyright Compliance",
        "obligation_type": "must",
        "subject": "provider_of_gpai",
        "action": "put in place policy to comply with EU copyright law",
        "scope": {
            "includes": ["identify and respect opt-outs under Article 4(3) DSM Directive"],
        },
    },
    {
        "article": "Article 53",
        "title": "GPAI Training Data Summary",
        "obligation_type": "must",
        "subject": "provider_of_gpai",
        "action": "draw up and make publicly available sufficiently detailed summary of training data",
        "scope": {
            "template": "provided by AI Office",
        },
    },
]


class EUAIActParser:
    """Parser for EU AI Act documents."""

    def __init__(self):
        self.article_pattern = re.compile(r"Article\s+(\d+)", re.IGNORECASE)

    def parse_eur_lex(self, content: str) -> dict[str, Any]:
        """Parse EUR-Lex EU AI Act document."""
        soup = BeautifulSoup(content, "lxml")

        result = {
            "title": "",
            "articles": [],
            "recitals": [],
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

    def extract_requirements_from_article(
        self,
        article: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Extract requirements from an EU AI Act article."""
        requirements = []
        content = article.get("content", "")

        obligation_patterns = [
            (r"shall\s+(?:be\s+)?(\w+(?:\s+\w+){0,10})", "must"),
            (r"must\s+(\w+(?:\s+\w+){0,10})", "must"),
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
                    "article": article.get("number"),
                    "title": article.get("title"),
                    "obligation_type": obligation_type,
                    "action": action,
                    "source_text": context,
                    "framework": "eu_ai_act",
                    "jurisdiction": "EU",
                })

        return requirements


class EUAIActSourceMonitor:
    """Monitors EU AI Act regulatory sources."""

    def __init__(self):
        self.crawler = RegulatoryCrawler()
        self.parser = EUAIActParser()

    async def check_source(self, source: RegulatorySource) -> dict[str, Any]:
        """Check an EU AI Act source for updates."""
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

    async def extract_all_requirements(
        self,
        source: RegulatorySource,
        content: str,
    ) -> list[dict[str, Any]]:
        """Extract all requirements from EU AI Act content."""
        parsed = self.parser.parse_eur_lex(content)
        all_requirements = []

        for article in parsed.get("articles", []):
            requirements = self.parser.extract_requirements_from_article(article)
            all_requirements.extend(requirements)

        return all_requirements


def get_eu_ai_act_source_definitions() -> list[dict[str, Any]]:
    """Get predefined EU AI Act source definitions."""
    return EU_AI_ACT_SOURCES


async def initialize_eu_ai_act_sources(db) -> list[RegulatorySource]:
    """Initialize EU AI Act sources in the database."""
    sources = []

    for source_def in EU_AI_ACT_SOURCES:
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


def parse_eu_ai_act_text(content: str) -> dict[str, Any]:
    """Parse EU AI Act text to extract requirements."""
    requirements = []

    import re

    # Find article references
    articles = re.findall(r"Article\s+(\d+)", content)

    # Find shall/must obligations
    obligations = re.findall(r"(?:shall|must|required to)\s+([^.]+\.)", content, re.IGNORECASE)

    # Find provider obligations
    provider_obligations = re.findall(
        r"provider[s]?\s+(?:of\s+(?:high-risk|general-purpose)\s+AI\s+systems?\s+)?(?:shall|must)\s+([^.]+\.)",
        content,
        re.IGNORECASE
    )

    all_obligations = obligations + provider_obligations

    for i, obligation in enumerate(all_obligations[:30]):
        requirements.append({
            "id": f"eu-ai-act-{i+1}",
            "obligation_type": "must",
            "action": obligation.strip(),
            "source_text": obligation,
            "confidence": 0.75,
        })

    return {
        "framework": "eu_ai_act",
        "jurisdiction": "EU",
        "requirements": requirements,
        "articles_found": list(set(articles)),
    }


def classify_ai_system_risk(system_description: str, use_case: str) -> dict[str, Any]:
    """Classify an AI system's risk level under the EU AI Act."""
    # This would use AI to analyze the system description
    # For now, return a placeholder
    return {
        "risk_level": "high",
        "confidence": 0.8,
        "reasons": [
            "System involves biometric data processing",
            "Use case is in employment context",
        ],
        "requirements_applicable": HIGH_RISK_REQUIREMENTS,
    }
