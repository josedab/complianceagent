"""Regulation-to-Architecture Advisor Service."""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.architecture_review import ArchitectureReview, ArchitectureRiskRecord
from app.services.architecture_advisor.models import (
    ArchitecturePattern,
    ArchitectureRecommendation,
    ArchitectureScore,
    ComplianceRisk,
    DesignReviewResult,
    PatternType,
    RiskSeverity,
)


logger = structlog.get_logger()

# Anti-patterns: architecture patterns that violate specific regulations
_ANTI_PATTERNS: list[dict] = [
    {
        "pattern": PatternType.DATA_LAKE,
        "regulation": "GDPR",
        "severity": RiskSeverity.CRITICAL,
        "title": "Centralized data lake violates data minimization",
        "description": "GDPR Article 5(1)(c) requires data minimization. A centralized data lake "
        "aggregating all user data violates this principle by collecting more data than necessary "
        "for each specific processing purpose.",
        "recommendation": "Adopt a data mesh architecture with domain-specific data products, each "
        "scoped to its processing purpose. Implement access controls per data domain.",
    },
    {
        "pattern": PatternType.MONOLITH,
        "regulation": "GDPR",
        "severity": RiskSeverity.HIGH,
        "title": "Monolith complicates data isolation and deletion",
        "description": "Monolithic architectures make it difficult to isolate personal data and "
        "implement granular deletion for DSAR requests (GDPR Article 17). Shared database schemas "
        "create cascading dependencies.",
        "recommendation": "Introduce bounded contexts with clear data ownership. Consider modular "
        "monolith or microservices for user data, consent, and analytics domains.",
    },
    {
        "pattern": PatternType.EVENT_DRIVEN,
        "regulation": "HIPAA",
        "severity": RiskSeverity.HIGH,
        "title": "Event streams may leak PHI without encryption",
        "description": "Event-driven architectures using message queues (Kafka, RabbitMQ) can "
        "expose PHI in transit if messages are not encrypted. HIPAA requires encryption of PHI "
        "in transit per the Security Rule.",
        "recommendation": "Enable TLS for all message broker connections. Encrypt PHI fields "
        "within event payloads at the application level. Implement schema validation for events.",
    },
    {
        "pattern": PatternType.SERVERLESS,
        "regulation": "HIPAA",
        "severity": RiskSeverity.MEDIUM,
        "title": "Serverless cold starts may miss audit logging",
        "description": "Serverless functions may fail to initialize audit logging during cold starts, "
        "creating gaps in HIPAA-required access logs for PHI.",
        "recommendation": "Implement centralized logging with guaranteed delivery (e.g., async "
        "log shipping). Use provisioned concurrency for PHI-handling functions.",
    },
    {
        "pattern": PatternType.MICROSERVICES,
        "regulation": "PCI-DSS",
        "severity": RiskSeverity.MEDIUM,
        "title": "Service-to-service communication may expose card data",
        "description": "Microservices communicating over internal networks may transmit card data "
        "in plaintext, violating PCI-DSS Requirement 4 (encrypt transmission of cardholder data).",
        "recommendation": "Implement mTLS for all inter-service communication. Isolate card data "
        "into a dedicated payment microservice with its own network segment.",
    },
    {
        "pattern": PatternType.API_GATEWAY,
        "regulation": "EU_AI_ACT",
        "severity": RiskSeverity.MEDIUM,
        "title": "API Gateway may obscure AI decision transparency",
        "description": "API gateways aggregating multiple AI model endpoints can obscure which "
        "model made a specific decision, violating EU AI Act Article 13 transparency requirements.",
        "recommendation": "Add model provenance headers to all AI responses. Log model version, "
        "input hash, and confidence score at the gateway level.",
    },
    {
        "pattern": PatternType.DATA_MESH,
        "regulation": "GDPR",
        "severity": RiskSeverity.LOW,
        "title": "Data mesh domains may have inconsistent retention policies",
        "description": "Decentralized data mesh domains may apply different retention policies, "
        "creating inconsistencies in GDPR Article 5(1)(e) storage limitation compliance.",
        "recommendation": "Implement a federated governance layer with centralized retention policy "
        "definitions that each domain must implement.",
    },
    {
        "pattern": PatternType.CQRS,
        "regulation": "GDPR",
        "severity": RiskSeverity.MEDIUM,
        "title": "CQRS read models may retain deleted data",
        "description": "In CQRS architectures, read-side projections may retain personal data "
        "after deletion from the write side, violating GDPR right to erasure (Article 17).",
        "recommendation": "Implement event-driven deletion propagation to all read models. "
        "Add deletion verification checks across all projections.",
    },
]

# Compliance-friendly patterns per regulation
_RECOMMENDED_PATTERNS: list[dict] = [
    {
        "regulation": "GDPR",
        "title": "Domain-Driven Data Isolation",
        "description": "Separate personal data into bounded contexts with clear ownership, "
        "making DSAR, deletion, and consent management manageable.",
        "pattern": "data_mesh_or_modular_monolith",
        "effort_days": 30,
        "impact": RiskSeverity.HIGH,
        "trade_offs": ["Increased operational complexity", "Cross-domain query overhead"],
    },
    {
        "regulation": "GDPR",
        "title": "Consent-as-a-Service Pattern",
        "description": "Extract consent management into a dedicated service that all data "
        "processing components check before operations.",
        "pattern": "consent_microservice",
        "effort_days": 15,
        "impact": RiskSeverity.HIGH,
        "trade_offs": ["Additional latency per request", "Service dependency"],
    },
    {
        "regulation": "HIPAA",
        "title": "PHI Encryption Gateway",
        "description": "Route all PHI through a dedicated encryption/decryption gateway that "
        "ensures data is never stored or transmitted in plaintext.",
        "pattern": "encryption_gateway",
        "effort_days": 20,
        "impact": RiskSeverity.CRITICAL,
        "trade_offs": ["Single point of failure risk", "Key management complexity"],
    },
    {
        "regulation": "HIPAA",
        "title": "Zero-Trust PHI Access Architecture",
        "description": "Implement zero-trust access for all PHI with per-request authorization, "
        "continuous verification, and comprehensive audit logging.",
        "pattern": "zero_trust",
        "effort_days": 40,
        "impact": RiskSeverity.HIGH,
        "trade_offs": ["Performance overhead", "Implementation complexity", "User friction"],
    },
    {
        "regulation": "PCI-DSS",
        "title": "Card Data Isolation Segment",
        "description": "Isolate all card data processing into a separate network segment (CDE) "
        "with strict ingress/egress controls, reducing PCI scope.",
        "pattern": "network_segmentation",
        "effort_days": 25,
        "impact": RiskSeverity.CRITICAL,
        "trade_offs": ["Network complexity", "Deployment overhead"],
    },
    {
        "regulation": "EU_AI_ACT",
        "title": "AI Model Registry with Provenance Tracking",
        "description": "Central registry for all AI models with version tracking, risk "
        "classification, performance metrics, and decision audit trails.",
        "pattern": "model_registry",
        "effort_days": 20,
        "impact": RiskSeverity.HIGH,
        "trade_offs": ["Operational overhead", "Model deployment friction"],
    },
]


class ArchitectureAdvisorService:
    """Service for analyzing architecture compliance risks and recommendations."""

    def __init__(
        self,
        db: AsyncSession,
        copilot_client: object | None = None,
    ):
        self.db = db
        self.copilot = copilot_client

    async def analyze_architecture(
        self,
        repo: str,
        files: list[str] | None = None,
        regulations: list[str] | None = None,
    ) -> DesignReviewResult:
        """Analyze repository architecture for compliance risks."""
        result = DesignReviewResult(
            repo=repo,
            regulations_analyzed=regulations or ["GDPR", "HIPAA", "PCI-DSS"],
        )

        # Detect architectural patterns from file structure
        detected = self._detect_patterns(files or [])
        result.detected_patterns = detected

        # Find risks based on detected patterns and regulations
        target_regulations = {r.upper().replace("-", "_") for r in (regulations or ["GDPR", "HIPAA", "PCI-DSS"])}
        detected_types = {p.pattern_type for p in detected}

        for anti in _ANTI_PATTERNS:
            reg = anti["regulation"].upper().replace("-", "_")
            if anti["pattern"] in detected_types and reg in target_regulations:
                risk = ComplianceRisk(
                    pattern=anti["pattern"],
                    regulation=anti["regulation"],
                    severity=anti["severity"],
                    title=anti["title"],
                    description=anti["description"],
                    recommendation=anti["recommendation"],
                    affected_components=[p.evidence[0] for p in detected if p.pattern_type == anti["pattern"] and p.evidence],
                )
                result.risks.append(risk)

        # Generate recommendations
        for rec_data in _RECOMMENDED_PATTERNS:
            rec_reg = rec_data["regulation"].upper().replace("-", "_")
            if rec_reg in target_regulations:
                rec = ArchitectureRecommendation(
                    title=rec_data["title"],
                    description=rec_data["description"],
                    regulation=rec_data["regulation"],
                    recommended_pattern=rec_data["pattern"],
                    effort_estimate_days=rec_data["effort_days"],
                    impact=rec_data["impact"],
                    trade_offs=rec_data["trade_offs"],
                )
                if detected:
                    rec.current_pattern = detected[0].pattern_type
                result.recommendations.append(rec)

        # Enhance with Copilot AI analysis if available
        if self.copilot:
            await self._enhance_with_copilot(result)

        # Compute score
        result.score = self._compute_score(result)
        result.reviewed_at = datetime.now(UTC)

        # Persist to database
        await self._persist_review(result)

        logger.info(
            "Architecture review complete",
            repo=repo,
            patterns=len(detected),
            risks=len(result.risks),
            score=result.score.overall_score,
        )
        return result

    async def _persist_review(self, result: DesignReviewResult) -> None:
        """Persist an architecture review and its risks to the database."""
        try:
            review = ArchitectureReview(
                id=result.id,
                repository=result.repo,
                overall_score=result.score.overall_score,
                grade=result.score.grade,
                total_patterns_detected=len(result.detected_patterns),
                anti_patterns_count=len(result.risks),
                recommended_patterns_count=len(result.recommendations),
                total_risks=len(result.risks),
                detected_patterns={
                    "patterns": [
                        {"type": p.pattern_type.value, "confidence": p.confidence}
                        for p in result.detected_patterns
                    ]
                },
                risks={
                    "risks": [
                        {"title": r.title, "severity": r.severity.value, "regulation": r.regulation}
                        for r in result.risks
                    ]
                },
                recommendations=[r.title for r in result.recommendations],
                regulations_analyzed=result.regulations_analyzed,
            )
            self.db.add(review)

            for risk in result.risks:
                record = ArchitectureRiskRecord(
                    review_id=result.id,
                    repository=result.repo,
                    risk_type=risk.pattern.value if risk.pattern else "unknown",
                    severity=risk.severity.value,
                    title=risk.title,
                    description=risk.description,
                    affected_files=risk.affected_components,
                    remediation=risk.recommendation,
                    regulations=[risk.regulation],
                )
                self.db.add(record)

            await self.db.commit()
        except Exception:
            await self.db.rollback()
            logger.warning("Failed to persist architecture review, continuing with in-memory result")

    async def _enhance_with_copilot(self, result: DesignReviewResult) -> None:
        """Use Copilot to provide deeper AI-powered risk analysis."""
        try:
            from app.agents.copilot import CopilotMessage

            patterns_summary = ", ".join(
                p.pattern_type.value for p in result.detected_patterns
            )
            risks_summary = "; ".join(
                f"{r.title} ({r.severity.value})" for r in result.risks[:5]
            )

            prompt = (
                f"Analyze these architecture compliance risks for repository '{result.repo}':\n"
                f"Detected patterns: {patterns_summary}\n"
                f"Regulations: {', '.join(result.regulations_analyzed)}\n"
                f"Known risks: {risks_summary}\n\n"
                f"Provide a brief (2-3 sentence) executive summary of the most critical "
                f"compliance concern and the single highest-priority remediation action."
            )

            response = await self.copilot.chat(
                messages=[CopilotMessage(role="user", content=prompt)],
                system_message=(
                    "You are a compliance architecture expert. Analyze the architecture "
                    "risks and provide concise, actionable advice. Be specific about "
                    "which regulation is most at risk and why."
                ),
                temperature=0.3,
                max_tokens=512,
            )

            # Store AI summary as a recommendation
            if response.content:
                result.recommendations.append(
                    ArchitectureRecommendation(
                        title="AI Analysis Summary",
                        description=response.content.strip(),
                        regulation=result.regulations_analyzed[0] if result.regulations_analyzed else "General",
                        recommended_pattern="ai_insight",
                        effort_estimate_days=0,
                        impact=RiskSeverity.INFO,
                        trade_offs=[],
                    )
                )
        except Exception:
            logger.debug("Copilot enhancement unavailable, using rule-based analysis only")

    async def get_review(self, review_id: UUID) -> DesignReviewResult | None:
        """Get an architecture review result from the database."""
        stmt = select(ArchitectureReview).where(ArchitectureReview.id == review_id)
        result = await self.db.execute(stmt)
        review = result.scalar_one_or_none()
        if not review:
            return None

        return DesignReviewResult(
            id=review.id,
            repo=review.repository,
            regulations_analyzed=review.regulations_analyzed or [],
            score=ArchitectureScore(
                overall_score=review.overall_score,
                grade=review.grade,
                risks_found=review.total_risks,
                recommendations_count=review.recommended_patterns_count,
            ),
            reviewed_at=review.created_at,
        )

    async def list_patterns(self) -> list[dict]:
        """List all known architectural patterns with compliance notes."""
        return [
            {
                "type": pt.value,
                "name": pt.value.replace("_", " ").title(),
                "compliance_notes": self._get_pattern_notes(pt),
            }
            for pt in PatternType
        ]

    async def get_score(self, repo: str) -> ArchitectureScore | None:
        """Get the latest architecture score for a repo from the database."""
        stmt = (
            select(ArchitectureReview)
            .where(ArchitectureReview.repository == repo)
            .order_by(ArchitectureReview.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        review = result.scalar_one_or_none()
        if not review:
            return None
        return ArchitectureScore(
            overall_score=review.overall_score,
            grade=review.grade,
            risks_found=review.total_risks,
            recommendations_count=review.recommended_patterns_count,
        )

    def _detect_patterns(self, files: list[str]) -> list[ArchitecturePattern]:
        """Detect architectural patterns from file structure."""
        patterns = []
        file_set = {f.lower() for f in files}

        # Detect Docker/Kubernetes → likely microservices
        if any("docker-compose" in f or "kubernetes" in f or "k8s" in f for f in file_set):
            patterns.append(ArchitecturePattern(
                pattern_type=PatternType.MICROSERVICES,
                confidence=0.75,
                evidence=[f for f in files if "docker" in f.lower() or "k8s" in f.lower()][:3],
                description="Docker Compose / Kubernetes configuration detected",
            ))

        # Detect Terraform/CloudFormation → infrastructure patterns
        if any("terraform" in f or "cloudformation" in f for f in file_set):
            if any("lambda" in f or "function" in f for f in file_set):
                patterns.append(ArchitecturePattern(
                    pattern_type=PatternType.SERVERLESS,
                    confidence=0.70,
                    evidence=[f for f in files if "lambda" in f.lower() or "function" in f.lower()][:3],
                    description="Serverless function definitions detected",
                ))

        # Detect event-driven patterns
        if any(kw in f for f in file_set for kw in ["kafka", "rabbitmq", "celery", "event", "queue"]):
            patterns.append(ArchitecturePattern(
                pattern_type=PatternType.EVENT_DRIVEN,
                confidence=0.70,
                evidence=[f for f in files if any(kw in f.lower() for kw in ["kafka", "celery", "event", "queue"])][:3],
                description="Event-driven / message queue components detected",
            ))

        # Detect API gateway
        if any(kw in f for f in file_set for kw in ["gateway", "nginx", "kong", "traefik"]):
            patterns.append(ArchitecturePattern(
                pattern_type=PatternType.API_GATEWAY,
                confidence=0.65,
                evidence=[f for f in files if any(kw in f.lower() for kw in ["gateway", "nginx"])][:3],
                description="API Gateway configuration detected",
            ))

        # Detect data lake patterns
        if any(kw in f for f in file_set for kw in ["datalake", "data_lake", "warehouse", "spark", "airflow"]):
            patterns.append(ArchitecturePattern(
                pattern_type=PatternType.DATA_LAKE,
                confidence=0.70,
                evidence=[f for f in files if any(kw in f.lower() for kw in ["lake", "warehouse", "spark"])][:3],
                description="Data lake / warehouse infrastructure detected",
            ))

        # Default: assume monolith if single app directory
        if not patterns:
            patterns.append(ArchitecturePattern(
                pattern_type=PatternType.MONOLITH,
                confidence=0.50,
                evidence=files[:3] if files else [],
                description="Single application structure (assumed monolith)",
            ))

        return patterns

    def _compute_score(self, review: DesignReviewResult) -> ArchitectureScore:
        """Compute architecture compliance score."""
        score = ArchitectureScore(
            data_isolation_score=80,
            encryption_score=80,
            audit_trail_score=80,
            access_control_score=80,
            data_flow_score=80,
            max_score=100,
        )

        severity_penalties = {
            RiskSeverity.CRITICAL: 25,
            RiskSeverity.HIGH: 15,
            RiskSeverity.MEDIUM: 8,
            RiskSeverity.LOW: 3,
            RiskSeverity.INFO: 0,
        }

        for risk in review.risks:
            penalty = severity_penalties.get(risk.severity, 5)
            # Distribute penalty across relevant score dimensions
            if "data" in risk.title.lower() or "isolation" in risk.title.lower():
                score.data_isolation_score = max(0, score.data_isolation_score - penalty)
            elif "encrypt" in risk.title.lower() or "plaintext" in risk.title.lower():
                score.encryption_score = max(0, score.encryption_score - penalty)
            elif "audit" in risk.title.lower() or "log" in risk.title.lower():
                score.audit_trail_score = max(0, score.audit_trail_score - penalty)
            elif "access" in risk.title.lower() or "transparenc" in risk.title.lower():
                score.access_control_score = max(0, score.access_control_score - penalty)
            else:
                score.data_flow_score = max(0, score.data_flow_score - penalty)

        score.overall_score = int(
            (score.data_isolation_score + score.encryption_score +
             score.audit_trail_score + score.access_control_score +
             score.data_flow_score) / 5
        )

        score.risks_found = len(review.risks)
        score.recommendations_count = len(review.recommendations)

        if score.overall_score >= 90:
            score.grade = "A"
        elif score.overall_score >= 80:
            score.grade = "B"
        elif score.overall_score >= 70:
            score.grade = "C"
        elif score.overall_score >= 60:
            score.grade = "D"
        else:
            score.grade = "F"

        return score

    def _get_pattern_notes(self, pattern: PatternType) -> str:
        """Get compliance notes for a pattern type."""
        notes = {
            PatternType.MICROSERVICES: "Good data isolation; watch inter-service data exposure",
            PatternType.MONOLITH: "Simpler compliance scope; harder data isolation and deletion",
            PatternType.EVENT_DRIVEN: "Excellent audit trails; ensure message encryption",
            PatternType.SERVERLESS: "Reduced attack surface; watch cold-start logging gaps",
            PatternType.DATA_LAKE: "Risk of data minimization violations; needs strict access controls",
            PatternType.API_GATEWAY: "Centralized policy enforcement; may obscure AI provenance",
            PatternType.CQRS: "Good read/write separation; ensure deletion propagation",
            PatternType.DATA_MESH: "Domain-aligned ownership; needs federated governance",
        }
        return notes.get(pattern, "No specific compliance notes")
