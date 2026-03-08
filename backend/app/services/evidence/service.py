"""Evidence service facade — unified entry point for evidence collection and reporting."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import structlog

from app.services.evidence import (
    ControlFramework,
    Evidence,
    EvidenceCollector,
    EvidenceStatus,
    EvidenceType,
    get_evidence_collector,
)
from app.services.evidence.collector import (
    EvidenceCollector as ExtendedEvidenceCollector,
)
from app.services.evidence.collector import (
    get_evidence_collector as get_extended_collector,
)
from app.services.evidence.mapping import ControlMapper, get_control_mapper
from app.services.evidence.models import EvidenceReport, Framework
from app.services.evidence.report import ReportGenerator, get_report_generator


if TYPE_CHECKING:
    from uuid import UUID


logger = structlog.get_logger(__name__)

__all__ = [
    "ControlFramework",
    "Evidence",
    "EvidenceReport",
    "EvidenceService",
    "EvidenceStatus",
    "EvidenceType",
    "Framework",
    "get_evidence_service",
]


@dataclass
class EvidenceService:
    """Facade over evidence sub-modules: collector, mapping, and reporting."""

    collector: EvidenceCollector = field(default_factory=get_evidence_collector)
    extended_collector: ExtendedEvidenceCollector = field(default_factory=get_extended_collector)
    mapper: ControlMapper = field(default_factory=get_control_mapper)
    report_generator: ReportGenerator = field(default_factory=get_report_generator)

    # ------------------------------------------------------------------
    # Collection
    # ------------------------------------------------------------------

    async def collect_evidence(
        self,
        control_id: str,
        evidence_type: EvidenceType,
        content: str | bytes,
        title: str,
        source: str,
        collected_by: str,
        content_type: str = "text/plain",
        metadata: dict[str, Any] | None = None,
    ) -> Evidence:
        """Collect a single piece of compliance evidence."""
        evidence = await self.collector.collect_evidence(
            control_id,
            evidence_type,
            content,
            title,
            source,
            collected_by,
            content_type=content_type,
            metadata=metadata,
        )
        logger.info("evidence_collected", evidence_id=str(evidence.id), control=control_id)
        return evidence

    async def collect_for_frameworks(
        self,
        organization_id: UUID,
        frameworks: list[Framework],
        sources: dict[str, Any] | None = None,
    ) -> list:
        """Bulk-collect evidence for the given compliance frameworks."""
        return await self.extended_collector.collect_evidence(
            organization_id,
            frameworks,
            sources=sources,
        )

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get_evidence(
        self,
        control_id: str,
        status: EvidenceStatus | None = None,
    ) -> list[Evidence]:
        """Return all evidence items for a control, optionally filtered by status."""
        return self.collector.get_evidence_for_control(control_id, status=status)

    def list_controls(
        self,
        framework: ControlFramework,
    ) -> list:
        """List all control mappings for a given framework."""
        return self.collector.get_controls_for_framework(framework)

    def get_compliance_coverage(
        self,
        framework: ControlFramework,
    ) -> dict[str, Any]:
        """Compute evidence coverage for a framework."""
        return self.collector.get_compliance_coverage(framework)

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    async def export_report(
        self,
        organization_id: UUID,
        frameworks: list[Framework],
        title: str | None = None,
        include_evidence_details: bool = True,
    ) -> EvidenceReport:
        """Generate a compliance evidence report."""
        report = await self.report_generator.generate_report(
            organization_id,
            frameworks,
            title=title,
            include_evidence_details=include_evidence_details,
        )
        logger.info("evidence_report_generated", report_id=str(report.id))
        return report

    async def export_gap_analysis(
        self,
        organization_id: UUID,
        frameworks: list[Framework],
    ) -> dict[str, Any]:
        """Generate a gap analysis across frameworks."""
        return await self.report_generator.generate_gap_analysis(organization_id, frameworks)


_service: EvidenceService | None = None


def get_evidence_service() -> EvidenceService:
    """Return the global EvidenceService singleton."""
    global _service
    if _service is None:
        _service = EvidenceService()
        logger.info("evidence_service_initialized")
    return _service
