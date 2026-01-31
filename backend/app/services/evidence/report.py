"""Evidence Report Generator - Generates audit-ready compliance reports."""

import json
import time
from datetime import datetime
from typing import Any
from uuid import UUID

import structlog

from app.services.evidence.collector import EvidenceCollector, get_evidence_collector
from app.services.evidence.mapping import ControlMapper, get_control_mapper
from app.services.evidence.models import (
    EvidenceCollection,
    EvidenceReport,
    EvidenceStatus,
    Framework,
)


logger = structlog.get_logger()


class ReportGenerator:
    """Generates compliance evidence reports."""

    def __init__(
        self,
        collector: EvidenceCollector | None = None,
        mapper: ControlMapper | None = None,
    ):
        self.collector = collector or get_evidence_collector()
        self.mapper = mapper or get_control_mapper()
        self._reports: dict[UUID, EvidenceReport] = {}

    async def generate_report(
        self,
        organization_id: UUID,
        frameworks: list[Framework],
        title: str | None = None,
        include_evidence_details: bool = True,
    ) -> EvidenceReport:
        """Generate a comprehensive evidence report.
        
        Args:
            organization_id: Organization ID
            frameworks: Frameworks to include in report
            title: Optional report title
            include_evidence_details: Include full evidence details
            
        Returns:
            EvidenceReport
        """
        start_time = time.perf_counter()
        
        report = EvidenceReport(
            organization_id=organization_id,
            title=title or f"Compliance Evidence Report - {datetime.utcnow().strftime('%Y-%m-%d')}",
            frameworks=frameworks,
        )
        
        # Collect evidence for all frameworks
        all_collections = await self.collector.collect_evidence(
            organization_id=organization_id,
            frameworks=frameworks,
        )
        
        # Analyze collections
        total_controls = 0
        controls_with_evidence = 0
        controls_missing = 0
        gaps = []
        
        for collection in all_collections:
            total_controls += 1
            
            if collection.status in [EvidenceStatus.COLLECTED, EvidenceStatus.VALIDATED]:
                if not collection.missing_evidence:
                    controls_with_evidence += 1
                else:
                    controls_with_evidence += 1  # Partial
                    gaps.append({
                        "framework": collection.framework.value,
                        "control_id": collection.control_id,
                        "control_title": collection.control_title,
                        "missing_evidence": collection.missing_evidence,
                        "severity": "medium",
                    })
            else:
                controls_missing += 1
                gaps.append({
                    "framework": collection.framework.value,
                    "control_id": collection.control_id,
                    "control_title": collection.control_title,
                    "missing_evidence": collection.missing_evidence or ["all evidence"],
                    "severity": "high",
                })
        
        # Update report
        report.total_controls = total_controls
        report.controls_with_evidence = controls_with_evidence
        report.controls_missing_evidence = controls_missing
        report.coverage_percentage = (
            (controls_with_evidence / total_controls * 100) if total_controls > 0 else 0
        )
        report.gaps = gaps
        
        if include_evidence_details:
            report.collections = all_collections
        
        # Store report
        self._reports[report.id] = report
        
        logger.info(
            "Generated evidence report",
            report_id=str(report.id),
            frameworks=[f.value for f in frameworks],
            total_controls=total_controls,
            coverage=f"{report.coverage_percentage:.1f}%",
            gaps=len(gaps),
            duration_ms=(time.perf_counter() - start_time) * 1000,
        )
        
        return report

    async def generate_gap_analysis(
        self,
        organization_id: UUID,
        frameworks: list[Framework],
    ) -> dict[str, Any]:
        """Generate a gap analysis report.
        
        Identifies missing evidence and provides remediation guidance.
        """
        report = await self.generate_report(
            organization_id=organization_id,
            frameworks=frameworks,
            include_evidence_details=False,
        )
        
        # Categorize gaps
        critical_gaps = [g for g in report.gaps if g.get("severity") == "high"]
        medium_gaps = [g for g in report.gaps if g.get("severity") == "medium"]
        
        # Generate remediation plan
        remediations = []
        for gap in critical_gaps[:10]:  # Top 10 critical
            remediations.append({
                "framework": gap["framework"],
                "control_id": gap["control_id"],
                "priority": "high",
                "action": f"Collect missing evidence for {gap['control_title']}",
                "missing_items": gap.get("missing_evidence", []),
                "estimated_effort": "1-2 hours per item",
            })
        
        return {
            "organization_id": str(organization_id),
            "generated_at": datetime.utcnow().isoformat(),
            "frameworks": [f.value for f in frameworks],
            "summary": {
                "total_controls": report.total_controls,
                "compliant_controls": report.controls_with_evidence - len(medium_gaps),
                "partial_controls": len(medium_gaps),
                "non_compliant_controls": report.controls_missing_evidence,
                "coverage_percentage": round(report.coverage_percentage, 2),
            },
            "critical_gaps": len(critical_gaps),
            "medium_gaps": len(medium_gaps),
            "gap_details": report.gaps,
            "remediation_plan": remediations,
            "recommendations": [
                "Prioritize collection of critical evidence gaps",
                "Establish automated evidence collection where possible",
                "Schedule regular evidence refresh cycles",
                "Consider cross-framework evidence reuse opportunities",
            ],
        }

    async def generate_cross_framework_report(
        self,
        organization_id: UUID,
        primary_framework: Framework,
        target_frameworks: list[Framework],
    ) -> dict[str, Any]:
        """Generate a report showing how primary framework evidence maps to others.
        
        Useful for organizations pursuing multiple certifications.
        """
        # Get evidence for primary framework
        collections = await self.collector.collect_evidence(
            organization_id=organization_id,
            frameworks=[primary_framework],
        )
        
        # Get completed controls
        completed_controls = [
            c.control_id for c in collections
            if c.status in [EvidenceStatus.COLLECTED, EvidenceStatus.VALIDATED]
        ]
        
        # Calculate coverage for each target framework
        coverage_analysis = []
        for target in target_frameworks:
            if target == primary_framework:
                continue
            
            coverage = self.mapper.calculate_coverage(
                source_framework=primary_framework,
                completed_controls=completed_controls,
                target_framework=target,
            )
            coverage_analysis.append(coverage)
        
        # Calculate potential effort savings
        reuse_report = self.mapper.generate_reuse_report(
            [primary_framework] + target_frameworks
        )
        
        return {
            "organization_id": str(organization_id),
            "generated_at": datetime.utcnow().isoformat(),
            "primary_framework": primary_framework.value,
            "primary_framework_status": {
                "controls_completed": len(completed_controls),
                "total_controls": len(collections),
                "completion_percentage": round(
                    len(completed_controls) / len(collections) * 100 if collections else 0,
                    2,
                ),
            },
            "target_framework_coverage": coverage_analysis,
            "evidence_reuse": reuse_report,
            "recommendations": [
                f"Evidence from {primary_framework.value} can accelerate compliance with target frameworks",
                "Focus on filling gaps in equivalent controls first",
                "Document control mapping decisions for auditor reference",
            ],
        }

    async def export_report(
        self,
        report_id: UUID,
        format: str = "json",
    ) -> dict[str, Any]:
        """Export a report in the specified format.
        
        Supported formats: json, summary
        """
        report = self._reports.get(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")
        
        if format == "json":
            return self._export_json(report)
        elif format == "summary":
            return self._export_summary(report)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_json(self, report: EvidenceReport) -> dict[str, Any]:
        """Export report as JSON."""
        return {
            "report_id": str(report.id),
            "title": report.title,
            "organization_id": str(report.organization_id) if report.organization_id else None,
            "frameworks": [f.value for f in report.frameworks],
            "generated_at": report.generated_at.isoformat(),
            "summary": {
                "total_controls": report.total_controls,
                "controls_with_evidence": report.controls_with_evidence,
                "controls_missing_evidence": report.controls_missing_evidence,
                "coverage_percentage": round(report.coverage_percentage, 2),
            },
            "gaps": report.gaps,
            "collections": [
                {
                    "id": str(c.id),
                    "framework": c.framework.value,
                    "control_id": c.control_id,
                    "control_title": c.control_title,
                    "status": c.status.value,
                    "evidence_count": len(c.evidence),
                    "missing_evidence": c.missing_evidence,
                }
                for c in report.collections
            ],
        }

    def _export_summary(self, report: EvidenceReport) -> dict[str, Any]:
        """Export report summary."""
        by_framework = {}
        for collection in report.collections:
            fw = collection.framework.value
            if fw not in by_framework:
                by_framework[fw] = {"total": 0, "compliant": 0, "partial": 0}
            by_framework[fw]["total"] += 1
            if not collection.missing_evidence:
                by_framework[fw]["compliant"] += 1
            elif collection.evidence:
                by_framework[fw]["partial"] += 1
        
        return {
            "report_id": str(report.id),
            "title": report.title,
            "generated_at": report.generated_at.isoformat(),
            "overall_coverage": f"{report.coverage_percentage:.1f}%",
            "by_framework": by_framework,
            "top_gaps": report.gaps[:5],
        }

    async def get_report(self, report_id: UUID) -> EvidenceReport | None:
        """Get a report by ID."""
        return self._reports.get(report_id)


# Global instance
_generator: ReportGenerator | None = None


def get_report_generator() -> ReportGenerator:
    """Get or create report generator."""
    global _generator
    if _generator is None:
        _generator = ReportGenerator()
    return _generator
