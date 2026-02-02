"""Regulatory diff service for detecting and analyzing changes."""

import difflib
import hashlib
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.copilot import CopilotClient, CopilotMessage
from app.models.regulation import Regulation
from app.services.diff_alerts.models import (
    AlertSeverity,
    AlertStatus,
    DiffChange,
    DiffChangeType,
    ImpactAnalysis,
    RegulatoryAlert,
    TextDiff,
)

logger = structlog.get_logger()


class RegulatoryDiffService:
    """Service for detecting and analyzing regulatory text changes."""

    def __init__(
        self,
        db: AsyncSession,
        copilot: CopilotClient | None = None,
    ):
        self.db = db
        self.copilot = copilot
        self._text_cache: dict[str, tuple[str, datetime]] = {}

    async def detect_changes(
        self,
        regulation_id: UUID,
        new_text: str,
        old_text: str | None = None,
    ) -> RegulatoryAlert | None:
        """
        Detect changes between old and new regulatory text.
        
        Args:
            regulation_id: ID of the regulation being checked
            new_text: New version of the regulatory text
            old_text: Previous version (if None, fetch from cache/DB)
            
        Returns:
            RegulatoryAlert if changes detected, None otherwise
        """
        # Get regulation details
        result = await self.db.execute(
            select(Regulation).where(Regulation.id == regulation_id)
        )
        regulation = result.scalar_one_or_none()
        
        if not regulation:
            raise ValueError(f"Regulation {regulation_id} not found")

        # Get old text from cache if not provided
        cache_key = str(regulation_id)
        if old_text is None:
            cached = self._text_cache.get(cache_key)
            if cached:
                old_text, _ = cached
            else:
                old_text = ""  # First time seeing this regulation

        # Generate diff
        diff = self._generate_diff(old_text, new_text)
        
        if not diff.has_changes:
            return None

        # Update cache
        self._text_cache[cache_key] = (new_text, datetime.now(UTC))

        # Create alert
        alert = RegulatoryAlert(
            regulation_id=regulation_id,
            regulation_name=regulation.name,
            jurisdiction=regulation.jurisdiction,
            framework=regulation.framework.value,
            diff=diff,
            old_version_id=self._hash_text(old_text) if old_text else None,
            new_version_id=self._hash_text(new_text),
            severity=self._calculate_severity(diff),
            status=AlertStatus.PENDING,
            created_at=datetime.now(UTC),
        )

        # Perform AI impact analysis if copilot available
        if self.copilot and diff.has_changes:
            try:
                alert.impact_analysis = await self._analyze_impact(
                    regulation_name=regulation.name,
                    old_text=old_text,
                    new_text=new_text,
                    diff=diff,
                )
                # Update severity based on analysis
                if alert.impact_analysis:
                    alert.severity = alert.impact_analysis.urgency_level
            except Exception as e:
                logger.warning("Impact analysis failed", error=str(e))

        return alert

    def _generate_diff(self, old_text: str, new_text: str) -> TextDiff:
        """Generate a structured diff between two text versions."""
        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)
        
        differ = difflib.unified_diff(
            old_lines,
            new_lines,
            lineterm="",
        )
        
        changes: list[DiffChange] = []
        additions = 0
        deletions = 0
        modifications = 0
        
        old_line_num = 0
        new_line_num = 0
        
        # Parse unified diff output
        for line in differ:
            if line.startswith("---") or line.startswith("+++"):
                continue
            elif line.startswith("@@"):
                # Parse hunk header
                continue
            elif line.startswith("-"):
                deletions += 1
                changes.append(DiffChange(
                    change_type=DiffChangeType.REMOVED,
                    line_number_old=old_line_num,
                    line_number_new=None,
                    old_text=line[1:].rstrip("\n"),
                    new_text=None,
                ))
                old_line_num += 1
            elif line.startswith("+"):
                additions += 1
                changes.append(DiffChange(
                    change_type=DiffChangeType.ADDED,
                    line_number_old=None,
                    line_number_new=new_line_num,
                    old_text=None,
                    new_text=line[1:].rstrip("\n"),
                ))
                new_line_num += 1
            else:
                old_line_num += 1
                new_line_num += 1

        # Calculate similarity ratio
        matcher = difflib.SequenceMatcher(None, old_text, new_text)
        similarity = matcher.ratio()

        return TextDiff(
            old_version=old_text[:1000] if old_text else "",  # Truncate for storage
            new_version=new_text[:1000],
            old_version_date=None,
            new_version_date=datetime.now(UTC),
            changes=changes,
            additions_count=additions,
            deletions_count=deletions,
            modifications_count=modifications,
            similarity_ratio=similarity,
        )

    def _calculate_severity(self, diff: TextDiff) -> AlertSeverity:
        """Calculate alert severity based on diff metrics."""
        total_changes = diff.additions_count + diff.deletions_count
        
        # Major structural changes
        if diff.similarity_ratio < 0.5:
            return AlertSeverity.CRITICAL
        
        # Significant changes
        if total_changes > 50 or diff.similarity_ratio < 0.7:
            return AlertSeverity.HIGH
        
        # Moderate changes
        if total_changes > 10 or diff.similarity_ratio < 0.9:
            return AlertSeverity.MEDIUM
        
        return AlertSeverity.LOW

    async def _analyze_impact(
        self,
        regulation_name: str,
        old_text: str,
        new_text: str,
        diff: TextDiff,
    ) -> ImpactAnalysis | None:
        """Use AI to analyze the impact of regulatory changes."""
        if not self.copilot:
            return None

        # Build change summary for AI
        changes_summary = []
        for change in diff.changes[:20]:  # Limit to first 20 changes
            if change.change_type == DiffChangeType.ADDED:
                changes_summary.append(f"+ {change.new_text}")
            elif change.change_type == DiffChangeType.REMOVED:
                changes_summary.append(f"- {change.old_text}")
        
        prompt = f"""Analyze the following changes to {regulation_name} and provide an impact assessment.

Changes detected:
{chr(10).join(changes_summary)}

Metrics:
- Lines added: {diff.additions_count}
- Lines removed: {diff.deletions_count}
- Similarity ratio: {diff.similarity_ratio:.2f}

Provide a JSON response with:
- summary: Brief description of changes (1-2 sentences)
- key_changes: List of 3-5 most important changes
- affected_areas: List of compliance areas affected (e.g., "data retention", "consent management")
- compliance_impact: Description of impact on existing compliance implementations
- recommended_actions: List of 3-5 recommended actions
- urgency_level: One of "critical", "high", "medium", "low"
- affected_frameworks: List of framework names affected
- confidence: Confidence score 0.0-1.0

Return only valid JSON."""

        try:
            async with self.copilot as client:
                response = await client.chat(
                    messages=[CopilotMessage(role="user", content=prompt)],
                    system_message="You are a regulatory compliance expert analyzing changes to regulations.",
                    temperature=0.3,
                    max_tokens=2048,
                )
            
            # Parse JSON response
            import json
            result = json.loads(response.content.strip().strip("```json").strip("```"))
            
            urgency_map = {
                "critical": AlertSeverity.CRITICAL,
                "high": AlertSeverity.HIGH,
                "medium": AlertSeverity.MEDIUM,
                "low": AlertSeverity.LOW,
            }
            
            return ImpactAnalysis(
                summary=result.get("summary", ""),
                key_changes=result.get("key_changes", []),
                affected_areas=result.get("affected_areas", []),
                compliance_impact=result.get("compliance_impact", ""),
                recommended_actions=result.get("recommended_actions", []),
                urgency_level=urgency_map.get(
                    result.get("urgency_level", "medium").lower(),
                    AlertSeverity.MEDIUM
                ),
                affected_frameworks=result.get("affected_frameworks", []),
                affected_requirements=result.get("affected_requirements", []),
                confidence=result.get("confidence", 0.0),
            )
            
        except Exception as e:
            logger.error("AI impact analysis failed", error=str(e))
            return None

    def _hash_text(self, text: str) -> str:
        """Generate a hash for text versioning."""
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    async def acknowledge_alert(
        self,
        alert_id: UUID,
        user_id: UUID,
        notes: str | None = None,
    ) -> bool:
        """Mark an alert as acknowledged."""
        # In a full implementation, this would update the database
        logger.info(
            "Alert acknowledged",
            alert_id=str(alert_id),
            user_id=str(user_id),
            notes=notes,
        )
        return True

    async def get_pending_alerts(
        self,
        organization_id: UUID,
        severity: AlertSeverity | None = None,
        limit: int = 50,
    ) -> list[RegulatoryAlert]:
        """Get pending alerts for an organization."""
        # This would query from database in production
        return []
