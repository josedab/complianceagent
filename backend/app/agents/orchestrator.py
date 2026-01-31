"""Compliance processing orchestrator - coordinates AI agents."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.codebase_analyzer import CodebaseAnalyzer
from app.agents.copilot import CopilotClient, get_copilot_client
from app.agents.relevance_filter import RelevanceFilter
from app.agents.requirement_extractor import RequirementExtractor
from app.core.exceptions import (
    CopilotError,
    RequirementExtractionError,
)
from app.models.audit import AuditEventType
from app.models.codebase import CodebaseMapping, Repository
from app.models.customer_profile import CustomerProfile
from app.models.regulation import Regulation
from app.models.requirement import Requirement
from app.services.audit.service import AuditService


logger = structlog.get_logger()
tracer = trace.get_tracer("complianceagent.orchestrator")


class ComplianceOrchestrator:
    """Orchestrates the compliance analysis pipeline with OpenTelemetry tracing.
    
    This class coordinates the pipeline components:
    - RequirementExtractor: Extracts requirements from regulatory text
    - RelevanceFilter: Filters requirements by customer profile
    - CodebaseAnalyzer: Analyzes codebases for compliance gaps
    """

    def __init__(
        self,
        db: AsyncSession,
        organization_id: UUID,
        copilot: CopilotClient | None = None,
        relevance_filter: RelevanceFilter | None = None,
    ):
        self.db = db
        self.organization_id = organization_id
        self.audit_service = AuditService(db)
        self._copilot = copilot
        self._relevance_filter = relevance_filter or RelevanceFilter()

    async def get_copilot(self) -> CopilotClient:
        """Get or create Copilot client."""
        if self._copilot is None:
            self._copilot = await get_copilot_client()
        return self._copilot

    async def process_regulatory_change(
        self,
        regulation: Regulation,
        content: str,
        customer_profile: CustomerProfile,
    ) -> dict[str, Any]:
        """Process a detected regulatory change through the full pipeline."""
        with tracer.start_as_current_span(
            "process_regulatory_change",
            attributes={
                "regulation.id": str(regulation.id),
                "regulation.name": regulation.name,
                "regulation.framework": regulation.framework.value,
                "organization.id": str(self.organization_id),
            },
        ) as span:
            try:
                logger.info(
                    "Processing regulatory change",
                    regulation_id=str(regulation.id),
                    regulation_name=regulation.name,
                )

                # Log detection
                await self.audit_service.log_event(
                    organization_id=self.organization_id,
                    event_type=AuditEventType.REGULATION_DETECTED,
                    event_description=f"Regulatory change detected: {regulation.name}",
                    regulation_id=regulation.id,
                    actor_type="system",
                )

                copilot = await self.get_copilot()

                # Step 1: Extract requirements
                with tracer.start_as_current_span("extract_requirements") as extract_span:
                    extractor = RequirementExtractor(copilot)
                    requirements = await extractor.extract(regulation, content)
                    extract_span.set_attribute("requirements.count", len(requirements))

                # Step 2: Filter for relevance
                with tracer.start_as_current_span("filter_requirements") as filter_span:
                    relevant_requirements = self._relevance_filter.filter(
                        requirements, customer_profile
                    )
                    filter_span.set_attribute("requirements.relevant_count", len(relevant_requirements))

                span.set_attribute("requirements.total", len(requirements))
                span.set_attribute("requirements.relevant", len(relevant_requirements))

                if not relevant_requirements:
                    logger.info("No relevant requirements found")
                    span.set_status(Status(StatusCode.OK))
                    return {
                        "status": "not_applicable",
                        "requirements_found": len(requirements),
                        "relevant_requirements": 0,
                    }

                # Log extraction
                await self.audit_service.log_event(
                    organization_id=self.organization_id,
                    event_type=AuditEventType.REQUIREMENTS_EXTRACTED,
                    event_description=f"Extracted {len(relevant_requirements)} relevant requirements",
                    regulation_id=regulation.id,
                    event_data={
                        "total_found": len(requirements),
                        "relevant": len(relevant_requirements),
                    },
                    actor_type="ai",
                    ai_model="copilot",
                )

                # Step 3: Save requirements to database
                with tracer.start_as_current_span("save_requirements") as save_span:
                    saved_requirements = await self._save_requirements(
                        regulation, relevant_requirements
                    )
                    save_span.set_attribute("requirements.saved_count", len(saved_requirements))

                span.set_status(Status(StatusCode.OK))
                return {
                    "status": "processed",
                    "requirements_found": len(requirements),
                    "relevant_requirements": len(relevant_requirements),
                    "saved_requirements": [str(r.id) for r in saved_requirements],
                }

            except CopilotError as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                logger.exception("Copilot error during regulatory processing", error=str(e))
                raise RequirementExtractionError(
                    f"Failed to process regulation {regulation.name}: {e}"
                ) from e
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    async def _save_requirements(
        self,
        regulation: Regulation,
        relevant_requirements: list[dict[str, Any]],
    ) -> list[Requirement]:
        """Save extracted requirements to database."""
        saved_requirements = []
        for req_data in relevant_requirements:
            requirement = Requirement(
                regulation_id=regulation.id,
                reference_id=req_data.get("reference_id", f"REQ-{regulation.framework.value}-{datetime.now(UTC).timestamp()}"),
                title=req_data.get("title", "Untitled"),
                description=req_data.get("description", ""),
                obligation_type=req_data.get("obligation_type", "must").lower(),
                category=req_data.get("category", "other").lower(),
                subject=req_data.get("subject", ""),
                action=req_data.get("action", ""),
                object=req_data.get("object"),
                data_types=req_data.get("data_types", []),
                processes=req_data.get("processes", []),
                timeframe=req_data.get("timeframe"),
                source_text=req_data.get("source_text", ""),
                citations=req_data.get("citations", []),
                extraction_confidence=req_data.get("confidence", 0.0),
                extracted_at=datetime.now(UTC),
            )
            self.db.add(requirement)
            saved_requirements.append(requirement)

        await self.db.flush()
        return saved_requirements

    async def analyze_repository(
        self,
        repository: Repository,
        requirements: list[Requirement],
    ) -> list[CodebaseMapping]:
        """Analyze a repository against requirements."""
        copilot = await self.get_copilot()
        analyzer = CodebaseAnalyzer(
            db=self.db,
            organization_id=self.organization_id,
            copilot=copilot,
            audit_service=self.audit_service,
        )
        return await analyzer.analyze(repository, requirements)

    async def generate_compliance_fix(
        self,
        mapping: CodebaseMapping,
        requirement: Requirement,
        repository: Repository,
    ) -> dict[str, Any]:
        """Generate compliant code for a mapping."""
        with tracer.start_as_current_span(
            "generate_compliance_fix",
            attributes={
                "mapping.id": str(mapping.id),
                "requirement.reference_id": requirement.reference_id,
                "repository.full_name": repository.full_name,
                "gaps.count": len(mapping.gaps) if mapping.gaps else 0,
            },
        ) as span:
            logger.info(
                "Generating compliance fix",
                mapping_id=str(mapping.id),
                requirement=requirement.reference_id,
            )

            if not mapping.gaps:
                span.set_status(Status(StatusCode.OK))
                return {
                    "status": "no_gaps",
                    "message": "No gaps to address",
                }

            copilot = await self.get_copilot()

            async with copilot:
                result = await copilot.generate_compliant_code(
                    requirement={
                        "reference_id": requirement.reference_id,
                        "title": requirement.title,
                        "description": requirement.description,
                        "regulation_name": requirement.regulation.name if requirement.regulation else "Unknown",
                    },
                    gaps=mapping.gaps,
                    existing_code={},  # Would fetch from GitHub
                    language=repository.primary_language or "python",
                )

            span.set_attribute("files.generated", len(result.get("files", [])))
            span.set_attribute("tests.generated", len(result.get("tests", [])))
            span.set_attribute("confidence", result.get("confidence", 0.0))

            # Log generation
            await self.audit_service.log_event(
                organization_id=self.organization_id,
                event_type=AuditEventType.CODE_GENERATED,
                event_description=f"Generated compliance code for {requirement.reference_id}",
                requirement_id=requirement.id,
                repository_id=repository.id,
                mapping_id=mapping.id,
                event_data={
                    "files_generated": len(result.get("files", [])),
                    "tests_generated": len(result.get("tests", [])),
                    "confidence": result.get("confidence", 0.0),
                },
                actor_type="ai",
                ai_model="copilot",
                ai_confidence=result.get("confidence"),
            )

            span.set_status(Status(StatusCode.OK))
            return result
