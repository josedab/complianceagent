"""Codebase analysis for compliance mapping."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.copilot import CopilotClient
from app.models.audit import AuditEventType
from app.models.codebase import CodebaseMapping, ComplianceStatus, Repository
from app.models.requirement import Requirement
from app.services.audit.service import AuditService


logger = structlog.get_logger()
tracer = trace.get_tracer("complianceagent.codebase_analyzer")


class CodebaseAnalyzer:
    """Analyzes codebases for compliance against requirements."""

    def __init__(
        self,
        db: AsyncSession,
        organization_id: UUID,
        copilot: CopilotClient,
        audit_service: AuditService | None = None,
    ):
        self.db = db
        self.organization_id = organization_id
        self._copilot = copilot
        self._audit = audit_service or AuditService(db)

    async def analyze(
        self,
        repository: Repository,
        requirements: list[Requirement],
    ) -> list[CodebaseMapping]:
        """Analyze a repository against requirements."""
        with tracer.start_as_current_span(
            "analyze_repository",
            attributes={
                "repository.full_name": repository.full_name,
                "requirements.count": len(requirements),
                "organization.id": str(self.organization_id),
            },
        ) as span:
            logger.info(
                "Analyzing repository",
                repository=repository.full_name,
                requirements_count=len(requirements),
            )

            mappings = []

            # Get codebase structure (would come from GitHub API in real implementation)
            codebase_structure = repository.structure_cache or {}
            structure_text = self._format_structure(codebase_structure)

            async with self._copilot:
                for requirement in requirements:
                    mapping = await self._map_requirement(
                        repository, requirement, structure_text
                    )
                    mappings.append(mapping)

            await self.db.flush()
            span.set_attribute("mappings.created", len(mappings))
            span.set_status(Status(StatusCode.OK))
            return mappings

    async def _map_requirement(
        self,
        repository: Repository,
        requirement: Requirement,
        structure_text: str,
    ) -> CodebaseMapping:
        """Map a single requirement to codebase."""
        with tracer.start_as_current_span(
            "map_requirement",
            attributes={
                "requirement.reference_id": requirement.reference_id,
                "requirement.category": requirement.category.value,
            },
        ) as span:
            mapping_result = await self._copilot.map_requirement_to_code(
                requirement={
                    "reference_id": requirement.reference_id,
                    "title": requirement.title,
                    "description": requirement.description,
                    "category": requirement.category.value,
                    "data_types": requirement.data_types,
                    "processes": requirement.processes,
                },
                codebase_structure=structure_text,
                sample_files={},  # Would fetch from GitHub
                languages=repository.languages,
            )

            mapping = self._create_mapping(repository, requirement, mapping_result)
            self.db.add(mapping)

            # Set span attributes
            gaps = mapping_result.get("gaps", [])
            span.set_attribute("gaps.total", len(gaps))
            span.set_attribute("gaps.critical", mapping.critical_gaps)
            span.set_attribute("confidence", mapping_result.get("confidence", 0.0))

            # Log mapping
            await self._audit.log_event(
                organization_id=self.organization_id,
                event_type=AuditEventType.CODEBASE_MAPPED,
                event_description=f"Mapped requirement {requirement.reference_id} to {repository.full_name}",
                requirement_id=requirement.id,
                repository_id=repository.id,
                event_data={
                    "gaps_found": len(gaps),
                    "confidence": mapping_result.get("confidence", 0.0),
                },
                actor_type="ai",
                ai_model="copilot",
                ai_confidence=mapping_result.get("confidence"),
            )

            return mapping

    def _create_mapping(
        self,
        repository: Repository,
        requirement: Requirement,
        mapping_result: dict[str, Any],
    ) -> CodebaseMapping:
        """Create CodebaseMapping from AI result."""
        gaps = mapping_result.get("gaps", [])
        critical = sum(1 for g in gaps if g.get("severity") == "critical")
        major = sum(1 for g in gaps if g.get("severity") == "major")
        minor = sum(1 for g in gaps if g.get("severity") == "minor")

        # Determine status
        if not gaps:
            if mapping_result.get("existing_implementations"):
                status = ComplianceStatus.COMPLIANT
            else:
                status = ComplianceStatus.PENDING_REVIEW
        elif critical > 0:
            status = ComplianceStatus.NON_COMPLIANT
        else:
            status = ComplianceStatus.PARTIAL

        return CodebaseMapping(
            repository_id=repository.id,
            requirement_id=requirement.id,
            compliance_status=status,
            affected_files=mapping_result.get("affected_files", []),
            affected_functions=[],
            affected_classes=[],
            data_flows=mapping_result.get("data_flows", []),
            existing_implementations=mapping_result.get("existing_implementations", []),
            gaps=gaps,
            gap_count=len(gaps),
            critical_gaps=critical,
            major_gaps=major,
            minor_gaps=minor,
            estimated_effort_hours=mapping_result.get("estimated_effort_hours"),
            estimated_effort_description=mapping_result.get("estimated_effort_description"),
            risk_level=mapping_result.get("risk_level"),
            mapping_confidence=mapping_result.get("confidence", 0.0),
            analyzed_at=datetime.now(UTC),
        )

    @staticmethod
    def _format_structure(structure: dict[str, Any]) -> str:
        """Format codebase structure for AI prompt."""
        lines = []
        for path, info in structure.items():
            if isinstance(info, dict):
                lines.append(f"- {path}/ ({info.get('type', 'dir')})")
            else:
                lines.append(f"- {path}")
        return "\n".join(lines[:200])
