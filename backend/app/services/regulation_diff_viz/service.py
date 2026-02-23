"""Regulation Diff Visualizer Service."""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.regulation_diff_viz.models import (
    DiffAnnotation,
    DiffChangeType,
    DiffSection,
    ImpactLevel,
    RegulationDiffResult,
    RegulationVersion,
)


logger = structlog.get_logger()

# Sample regulation version data
_REGULATION_VERSIONS: dict[str, list[dict]] = {
    "GDPR": [
        {"version": "2016/679", "effective_date": "2018-05-25", "sections": [
            {"id": "art-5", "title": "Principles relating to processing", "text": "Personal data shall be processed lawfully, fairly and in a transparent manner."},
            {"id": "art-6", "title": "Lawfulness of processing", "text": "Processing shall be lawful only if and to the extent that at least one of the conditions applies."},
            {"id": "art-17", "title": "Right to erasure", "text": "The data subject shall have the right to obtain from the controller the erasure of personal data."},
        ]},
        {"version": "2024/amendment", "effective_date": "2025-01-01", "sections": [
            {"id": "art-5", "title": "Principles relating to processing", "text": "Personal data shall be processed lawfully, fairly, transparently, and with accountability measures."},
            {"id": "art-6", "title": "Lawfulness of processing", "text": "Processing shall be lawful only if and to the extent that at least one of the conditions applies. AI-based processing requires additional safeguards."},
            {"id": "art-17", "title": "Right to erasure", "text": "The data subject shall have the right to obtain from the controller the erasure of personal data."},
            {"id": "art-22a", "title": "AI-specific data processing", "text": "Automated decision-making using AI requires human oversight and explainability."},
        ]},
    ],
    "HIPAA": [
        {"version": "1996/original", "effective_date": "1996-08-21", "sections": [
            {"id": "164-312", "title": "Technical safeguards", "text": "Implement technical policies and procedures for electronic information systems."},
        ]},
        {"version": "2024/update", "effective_date": "2025-06-01", "sections": [
            {"id": "164-312", "title": "Technical safeguards", "text": "Implement technical policies and procedures for electronic information systems including AI-assisted diagnostics."},
            {"id": "164-312a", "title": "AI in healthcare", "text": "AI systems processing PHI must maintain audit logs and explainability."},
        ]},
    ],
}


class RegulationDiffVizService:
    """Service for visualizing regulation diffs with impact analysis."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._diffs: dict[str, RegulationDiffResult] = {}
        self._annotations: list[DiffAnnotation] = []

    def list_regulation_versions(self, regulation: str) -> list[RegulationVersion]:
        """List available versions for a regulation."""
        versions_data = _REGULATION_VERSIONS.get(regulation, [])
        return [
            RegulationVersion(
                regulation=regulation,
                version=v["version"],
                effective_date=v["effective_date"],
                sections=v["sections"],
                published_at=datetime.now(UTC),
            )
            for v in versions_data
        ]

    async def compute_diff(
        self,
        regulation: str,
        old_version: str = "",
        new_version: str = "",
    ) -> RegulationDiffResult:
        """Compute diff between two regulation versions."""
        versions = _REGULATION_VERSIONS.get(regulation, [])
        if len(versions) < 2:
            return RegulationDiffResult(regulation=regulation, generated_at=datetime.now(UTC))

        old_v = versions[0]
        new_v = versions[-1]
        old_version = old_version or old_v["version"]
        new_version = new_version or new_v["version"]

        old_sections = {s["id"]: s for s in old_v["sections"]}
        new_sections = {s["id"]: s for s in new_v["sections"]}

        diff_sections: list[DiffSection] = []
        all_ids = set(list(old_sections.keys()) + list(new_sections.keys()))

        for sid in sorted(all_ids):
            old_s = old_sections.get(sid)
            new_s = new_sections.get(sid)

            if old_s and not new_s:
                diff_sections.append(DiffSection(
                    section_id=sid, title=old_s["title"], change_type=DiffChangeType.REMOVED,
                    old_text=old_s["text"], impact_level=ImpactLevel.BREAKING,
                    recommendations=["Review dependent code for removed requirements"],
                ))
            elif new_s and not old_s:
                diff_sections.append(DiffSection(
                    section_id=sid, title=new_s["title"], change_type=DiffChangeType.ADDED,
                    new_text=new_s["text"], impact_level=ImpactLevel.SIGNIFICANT,
                    recommendations=["Implement new requirement", "Update compliance documentation"],
                ))
            elif old_s and new_s:
                if old_s["text"] != new_s["text"]:
                    diff_sections.append(DiffSection(
                        section_id=sid, title=new_s["title"], change_type=DiffChangeType.MODIFIED,
                        old_text=old_s["text"], new_text=new_s["text"],
                        impact_level=ImpactLevel.SIGNIFICANT,
                        recommendations=["Review code for compliance with updated text"],
                    ))
                else:
                    diff_sections.append(DiffSection(
                        section_id=sid, title=new_s["title"], change_type=DiffChangeType.UNCHANGED,
                        old_text=old_s["text"], new_text=new_s["text"],
                        impact_level=ImpactLevel.COSMETIC,
                    ))

        changed = [s for s in diff_sections if s.change_type != DiffChangeType.UNCHANGED]
        impact_summary = {}
        for s in diff_sections:
            impact_summary[s.change_type.value] = impact_summary.get(s.change_type.value, 0) + 1

        result = RegulationDiffResult(
            regulation=regulation,
            old_version=old_version,
            new_version=new_version,
            total_sections=len(diff_sections),
            changed_sections=len(changed),
            sections=diff_sections,
            impact_summary=impact_summary,
            generated_at=datetime.now(UTC),
        )
        self._diffs[str(result.id)] = result
        logger.info("Diff computed", regulation=regulation, changes=len(changed))
        return result

    async def add_annotation(
        self,
        diff_id: UUID,
        section_id: str,
        author: str,
        comment: str,
        action_required: bool = False,
    ) -> DiffAnnotation:
        annotation = DiffAnnotation(
            diff_id=diff_id,
            section_id=section_id,
            author=author,
            comment=comment,
            action_required=action_required,
            created_at=datetime.now(UTC),
        )
        self._annotations.append(annotation)
        return annotation

    def get_annotations(self, diff_id: UUID) -> list[DiffAnnotation]:
        return [a for a in self._annotations if a.diff_id == diff_id]

    def get_diff(self, diff_id: str) -> RegulationDiffResult | None:
        return self._diffs.get(diff_id)

    def list_available_regulations(self) -> list[str]:
        return list(_REGULATION_VERSIONS.keys())
