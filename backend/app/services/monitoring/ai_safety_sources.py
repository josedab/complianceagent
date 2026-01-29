"""AI Safety Standards regulatory sources and risk classification service."""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog
from bs4 import BeautifulSoup

from app.models.regulation import Jurisdiction, RegulatoryFramework, RegulatorySource
from app.services.monitoring.crawler import RegulatoryCrawler


logger = structlog.get_logger()


class AIRiskLevel(str, Enum):
    """AI system risk classification levels per EU AI Act."""
    UNACCEPTABLE = "unacceptable"
    HIGH = "high"
    LIMITED = "limited"
    MINIMAL = "minimal"


# AI Safety Standards source definitions (extends existing EU AI Act sources)
AI_SAFETY_SOURCES = [
    # NIST AI Risk Management Framework
    {
        "name": "NIST AI RMF",
        "description": "NIST AI Risk Management Framework - official documentation",
        "url": "https://www.nist.gov/itl/ai-risk-management-framework",
        "jurisdiction": Jurisdiction.US_FEDERAL,
        "framework": RegulatoryFramework.NIST_AI_RMF,
        "parser_type": "html",
        "parser_config": {},
    },
    {
        "name": "NIST AI RMF Playbook",
        "description": "NIST AI RMF implementation playbook",
        "url": "https://airc.nist.gov/AI_RMF_Knowledge_Base/Playbook",
        "jurisdiction": Jurisdiction.US_FEDERAL,
        "framework": RegulatoryFramework.NIST_AI_RMF,
        "parser_type": "html",
        "parser_config": {},
    },
    # ISO 42001 AI Management System
    {
        "name": "ISO 42001 Overview",
        "description": "ISO/IEC 42001 AI Management System standard overview",
        "url": "https://www.iso.org/standard/81230.html",
        "jurisdiction": Jurisdiction.GLOBAL,
        "framework": RegulatoryFramework.ISO42001,
        "parser_type": "html",
        "parser_config": {},
    },
    # US State AI Laws
    {
        "name": "Colorado AI Act",
        "description": "Colorado SB 21-169 - Concerning Consumer Protections for AI",
        "url": "https://leg.colorado.gov/bills/sb21-169",
        "jurisdiction": Jurisdiction.US_FEDERAL,  # US state
        "framework": RegulatoryFramework.EU_AI_ACT,  # Similar framework type
        "parser_type": "html",
        "parser_config": {},
    },
    {
        "name": "Illinois BIPA AI Provisions",
        "description": "Illinois Biometric Information Privacy Act AI-related provisions",
        "url": "https://www.ilga.gov/legislation/ilcs/ilcs3.asp?ActID=3004",
        "jurisdiction": Jurisdiction.US_FEDERAL,  # US state
        "framework": RegulatoryFramework.EU_AI_ACT,
        "parser_type": "html",
        "parser_config": {},
    },
    # UK AI Framework
    {
        "name": "UK AI Regulation Framework",
        "description": "UK pro-innovation approach to AI regulation",
        "url": "https://www.gov.uk/government/publications/ai-regulation-a-pro-innovation-approach",
        "jurisdiction": Jurisdiction.UK,
        "framework": RegulatoryFramework.EU_AI_ACT,
        "parser_type": "html",
        "parser_config": {},
    },
]


# NIST AI RMF Core Functions
NIST_AI_RMF_FUNCTIONS = {
    "govern": {
        "description": "Cultivate and implement a culture of risk management",
        "categories": [
            {
                "id": "govern_1",
                "title": "Policies, processes, procedures, and practices",
                "description": "Policies, processes, procedures, and practices across the organization related to the mapping, measuring, and managing of AI risks are in place, transparent, and implemented effectively.",
            },
            {
                "id": "govern_2",
                "title": "Accountability structures",
                "description": "Accountability structures are in place so that the appropriate teams and individuals are empowered, responsible, and trained for mapping, measuring, and managing AI risks.",
            },
            {
                "id": "govern_3",
                "title": "Workforce diversity, equity, inclusion, accessibility",
                "description": "Workforce diversity, equity, inclusion, and accessibility processes are prioritized in the mapping, measuring, and managing of AI risks throughout the lifecycle.",
            },
            {
                "id": "govern_4",
                "title": "Organizational teams",
                "description": "Organizational teams are committed to a culture that considers and communicates AI risk.",
            },
            {
                "id": "govern_5",
                "title": "Processes and practices",
                "description": "Processes are in place for robust engagement with relevant AI actors.",
            },
            {
                "id": "govern_6",
                "title": "Policies and practices",
                "description": "Policies and procedures are in place to address AI risks and benefits arising from third-party software and data and other supply chain issues.",
            },
        ],
    },
    "map": {
        "description": "Context and characterize risks",
        "categories": [
            {
                "id": "map_1",
                "title": "Context is established",
                "description": "Context is established and understood.",
            },
            {
                "id": "map_2",
                "title": "Categorization",
                "description": "Categorization of the AI system is performed.",
            },
            {
                "id": "map_3",
                "title": "AI capabilities",
                "description": "AI capabilities, targeted usage, goals, and expected benefits and costs compared with appropriate benchmarks are understood.",
            },
            {
                "id": "map_4",
                "title": "Risks and benefits",
                "description": "Risks and benefits are mapped for all components of the AI system.",
            },
            {
                "id": "map_5",
                "title": "Impacts",
                "description": "Impacts to individuals, groups, communities, organizations, and society are characterized.",
            },
        ],
    },
    "measure": {
        "description": "Assess, analyze, and track AI risks",
        "categories": [
            {
                "id": "measure_1",
                "title": "Appropriate methods",
                "description": "Appropriate methods and metrics are identified and applied.",
            },
            {
                "id": "measure_2",
                "title": "AI systems evaluated",
                "description": "AI systems are evaluated for trustworthy characteristics.",
            },
            {
                "id": "measure_3",
                "title": "Mechanisms for tracking",
                "description": "Mechanisms for tracking identified AI risks over time are in place.",
            },
            {
                "id": "measure_4",
                "title": "Feedback gathered",
                "description": "Feedback about efficacy of measurement is gathered and assessed.",
            },
        ],
    },
    "manage": {
        "description": "Prioritize, respond to, and manage AI risks",
        "categories": [
            {
                "id": "manage_1",
                "title": "AI risks prioritized",
                "description": "AI risks based on assessments and other analytical output from the MAP and MEASURE functions are prioritized, responded to, and managed.",
            },
            {
                "id": "manage_2",
                "title": "Strategies to maximize",
                "description": "Strategies to maximize AI benefits and minimize negative impacts are planned, prepared, implemented, documented, and informed by input from relevant AI actors.",
            },
            {
                "id": "manage_3",
                "title": "AI risk treatments",
                "description": "AI risk treatment are documented and monitored regularly.",
            },
            {
                "id": "manage_4",
                "title": "Risk treatments communicated",
                "description": "Residual risk is documented and risk treatments are communicated.",
            },
        ],
    },
}


# AI System Detection Patterns
AI_SYSTEM_DETECTION_PATTERNS = {
    "ml_libraries": [
        "tensorflow",
        "torch",
        "pytorch",
        "keras",
        "scikit-learn",
        "sklearn",
        "xgboost",
        "lightgbm",
        "catboost",
        "transformers",
        "huggingface",
        "openai",
        "anthropic",
        "langchain",
        "llama",
        "ollama",
        "mlflow",
        "wandb",
        "weights & biases",
    ],
    "ml_file_patterns": [
        r"\.pt$",  # PyTorch model
        r"\.pth$",  # PyTorch model
        r"\.h5$",  # Keras/HDF5 model
        r"\.keras$",  # Keras model
        r"\.onnx$",  # ONNX model
        r"\.pkl$",  # Pickled model (may be ML)
        r"\.joblib$",  # Joblib model
        r"model.*\.json$",  # Model config
        r"weights.*\.",  # Model weights
        r"checkpoint",  # Training checkpoint
    ],
    "ml_code_patterns": [
        r"\.fit\(",  # Model training
        r"\.predict\(",  # Model inference
        r"\.train\(",  # Training call
        r"model\.forward\(",  # PyTorch forward
        r"tf\.keras\.",  # TensorFlow Keras
        r"torch\.nn\.",  # PyTorch neural network
        r"GPT|BERT|Transformer",  # LLM architectures
        r"embedding|Embedding",  # Embeddings
        r"neural.?network",  # Neural network mentions
        r"machine.?learning|ML\b",  # ML mentions
        r"inference|Inference",  # Inference code
        r"pipeline\(.*model",  # HuggingFace pipeline
    ],
    "high_risk_indicators": [
        # Biometric
        r"biometric",
        r"face.?recognition",
        r"facial.?detection",
        r"fingerprint",
        r"voice.?recognition",
        r"emotion.?detection",
        r"emotion.?recognition",
        # Critical infrastructure
        r"power.?grid",
        r"water.?treatment",
        r"traffic.?control",
        r"infrastructure",
        # Employment
        r"hiring|recruitment",
        r"cv.?screening|resume.?screening",
        r"employee.?monitoring",
        r"worker.?management",
        r"performance.?evaluation",
        # Credit/Finance
        r"credit.?scor",
        r"loan.?decision",
        r"insurance.?pricing",
        r"fraud.?detection",
        # Healthcare
        r"diagnosis|diagnostic",
        r"medical.?device",
        r"patient.?risk",
        r"healthcare.?ai",
        # Law enforcement
        r"predictive.?policing",
        r"crime.?prediction",
        r"recidivism",
        # Education
        r"grading|assessment",
        r"admission",
        r"student.?evaluation",
    ],
    "prohibited_indicators": [
        r"social.?scoring",
        r"real.?time.*biometric.*public",
        r"subliminal",
        r"exploit.*vulnerabilit",
        r"manipulation.?technique",
    ],
}


@dataclass
class AISystemClassification:
    """Result of AI system risk classification."""
    risk_level: AIRiskLevel
    confidence: float
    reasons: list[str]
    detected_patterns: list[str]
    high_risk_areas: list[str]
    applicable_requirements: list[str]
    recommendations: list[str]


class AIRiskClassifier:
    """Classifies AI systems according to EU AI Act risk levels."""

    def __init__(self):
        self.patterns = AI_SYSTEM_DETECTION_PATTERNS
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for efficiency."""
        self.compiled_high_risk = [
            re.compile(p, re.IGNORECASE) for p in self.patterns["high_risk_indicators"]
        ]
        self.compiled_prohibited = [
            re.compile(p, re.IGNORECASE) for p in self.patterns["prohibited_indicators"]
        ]
        self.compiled_ml_code = [
            re.compile(p, re.IGNORECASE) for p in self.patterns["ml_code_patterns"]
        ]

    def classify_from_code(
        self,
        code_content: str,
        file_names: list[str] | None = None,
        description: str = "",
    ) -> AISystemClassification:
        """Classify AI system risk level from code analysis."""
        detected_patterns = []
        high_risk_areas = []
        reasons = []
        
        # Check for ML libraries
        for lib in self.patterns["ml_libraries"]:
            if lib.lower() in code_content.lower():
                detected_patterns.append(f"ML library: {lib}")

        # Check ML code patterns
        for pattern in self.compiled_ml_code:
            if pattern.search(code_content):
                detected_patterns.append(f"ML code pattern: {pattern.pattern}")

        # Check file names for ML patterns
        if file_names:
            for file_name in file_names:
                for pattern in self.patterns["ml_file_patterns"]:
                    if re.search(pattern, file_name, re.IGNORECASE):
                        detected_patterns.append(f"ML file: {file_name}")
                        break

        # If no AI/ML detected, return minimal risk
        if not detected_patterns:
            return AISystemClassification(
                risk_level=AIRiskLevel.MINIMAL,
                confidence=0.9,
                reasons=["No AI/ML patterns detected in codebase"],
                detected_patterns=[],
                high_risk_areas=[],
                applicable_requirements=[],
                recommendations=["Continue monitoring for AI/ML additions"],
            )

        # Check for prohibited uses
        combined_text = code_content + " " + description
        for pattern in self.compiled_prohibited:
            match = pattern.search(combined_text)
            if match:
                return AISystemClassification(
                    risk_level=AIRiskLevel.UNACCEPTABLE,
                    confidence=0.85,
                    reasons=[f"Potentially prohibited AI use detected: {match.group()}"],
                    detected_patterns=detected_patterns,
                    high_risk_areas=["prohibited_practice"],
                    applicable_requirements=["Immediate review required - potentially prohibited under EU AI Act Article 5"],
                    recommendations=[
                        "Immediately review the AI system for compliance",
                        "Consult legal counsel on AI Act Article 5 (Prohibited Practices)",
                        "Consider alternative approaches that do not fall under prohibited categories",
                    ],
                )

        # Check for high-risk indicators
        for pattern in self.compiled_high_risk:
            match = pattern.search(combined_text)
            if match:
                high_risk_areas.append(match.group())
                reasons.append(f"High-risk indicator detected: {match.group()}")

        # Determine risk level
        if high_risk_areas:
            risk_level = AIRiskLevel.HIGH
            confidence = min(0.85, 0.5 + 0.1 * len(high_risk_areas))
            applicable_requirements = [
                "Article 9: Risk Management System",
                "Article 10: Data Governance",
                "Article 11: Technical Documentation",
                "Article 12: Record-keeping (Logging)",
                "Article 13: Transparency",
                "Article 14: Human Oversight",
                "Article 15: Accuracy, Robustness, Cybersecurity",
                "Article 16: Quality Management System",
                "Article 17: EU Declaration of Conformity",
                "Article 49: CE Marking",
            ]
            recommendations = [
                "Conduct a comprehensive AI impact assessment",
                "Establish a risk management system per Article 9",
                "Ensure data quality and governance per Article 10",
                "Prepare technical documentation per Article 11",
                "Implement logging capabilities per Article 12",
                "Design for human oversight per Article 14",
                "Consider engaging a notified body for conformity assessment",
            ]
        else:
            # Limited risk - transparency obligations
            risk_level = AIRiskLevel.LIMITED
            confidence = 0.7
            applicable_requirements = [
                "Article 50: Transparency obligations for certain AI systems",
            ]
            recommendations = [
                "Ensure users are informed they are interacting with AI",
                "Disclose AI-generated content where applicable",
                "Document AI system capabilities and limitations",
            ]

        return AISystemClassification(
            risk_level=risk_level,
            confidence=confidence,
            reasons=reasons if reasons else ["AI/ML system detected, classified based on use case indicators"],
            detected_patterns=detected_patterns,
            high_risk_areas=list(set(high_risk_areas)),
            applicable_requirements=applicable_requirements,
            recommendations=recommendations,
        )

    def classify_from_description(
        self,
        system_description: str,
        use_case: str,
        data_types: list[str] | None = None,
    ) -> AISystemClassification:
        """Classify AI system risk level from description."""
        return self.classify_from_code(
            code_content="",
            file_names=[],
            description=f"{system_description} {use_case} {' '.join(data_types or [])}",
        )


class AISafetyParser:
    """Parser for AI safety standards documents."""

    def __init__(self):
        self.article_pattern = re.compile(r"Article\s+(\d+)", re.IGNORECASE)
        self.function_pattern = re.compile(r"(GOVERN|MAP|MEASURE|MANAGE)", re.IGNORECASE)

    def parse_nist_ai_rmf(self, content: str) -> dict[str, Any]:
        """Parse NIST AI RMF documentation."""
        soup = BeautifulSoup(content, "lxml")

        result = {
            "title": "NIST AI Risk Management Framework",
            "functions": NIST_AI_RMF_FUNCTIONS,
            "profiles": [],
            "guidance": [],
        }

        # Extract guidance sections
        for section in soup.find_all(["section", "div", "article"]):
            heading = section.find(["h1", "h2", "h3"])
            if heading:
                result["guidance"].append({
                    "title": heading.get_text(strip=True),
                    "content": section.get_text(separator="\n", strip=True)[:500],
                })

        return result

    def parse_iso42001(self, content: str) -> dict[str, Any]:
        """Parse ISO 42001 standard overview."""
        soup = BeautifulSoup(content, "lxml")

        result = {
            "title": "ISO/IEC 42001 - AI Management System",
            "clauses": [],
            "controls": [],
        }

        return result

    def extract_requirements(self, content: str, framework: str) -> list[dict[str, Any]]:
        """Extract requirements from AI safety content."""
        requirements = []

        obligation_patterns = [
            (r"shall\s+(?:be\s+)?(\w+(?:\s+\w+){0,10})", "must"),
            (r"must\s+(\w+(?:\s+\w+){0,10})", "must"),
            (r"should\s+(\w+(?:\s+\w+){0,10})", "should"),
            (r"organizations?\s+(?:shall|must|should)\s+(\w+(?:\s+\w+){0,10})", "must"),
        ]

        for pattern, obligation_type in obligation_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                action = match.group(1).strip()
                context_start = max(0, match.start() - 100)
                context_end = min(len(content), match.end() + 100)
                context = content[context_start:context_end]

                requirements.append({
                    "framework": framework,
                    "obligation_type": obligation_type,
                    "action": action,
                    "source_text": context,
                    "category": "ai_risk_management",
                })

        return requirements


class AISafetySourceMonitor:
    """Monitors AI safety standards sources."""

    def __init__(self):
        self.crawler = RegulatoryCrawler()
        self.parser = AISafetyParser()
        self.classifier = AIRiskClassifier()

    async def check_source(self, source: RegulatorySource) -> dict[str, Any]:
        """Check an AI safety source for updates."""
        async with self.crawler:
            result = await self.crawler.crawl(source)

            if result.has_changed:
                if source.framework == RegulatoryFramework.NIST_AI_RMF:
                    parsed = self.parser.parse_nist_ai_rmf(result.content)
                elif source.framework == RegulatoryFramework.ISO42001:
                    parsed = self.parser.parse_iso42001(result.content)
                else:
                    parsed = {"content": result.content[:1000]}

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
        """Extract requirements from AI safety content."""
        framework = source.framework.value if source.framework else "ai_safety"
        return self.parser.extract_requirements(content, framework)

    def classify_ai_system(
        self,
        code_content: str = "",
        file_names: list[str] | None = None,
        description: str = "",
    ) -> AISystemClassification:
        """Classify an AI system's risk level."""
        return self.classifier.classify_from_code(
            code_content=code_content,
            file_names=file_names,
            description=description,
        )


def get_ai_safety_source_definitions() -> list[dict[str, Any]]:
    """Get predefined AI safety source definitions."""
    return AI_SAFETY_SOURCES


async def initialize_ai_safety_sources(db) -> list[RegulatorySource]:
    """Initialize AI safety sources in the database."""
    sources = []

    for source_def in AI_SAFETY_SOURCES:
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
