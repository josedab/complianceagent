"""Regulatory Change Impact Timeline Service."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.impact_timeline.models import (
    RemediationTask,
    TaskPriority,
    TaskStatus,
    TimelineEvent,
    TimelineEventType,
    TimelineView,
)

logger = structlog.get_logger()

# Built-in upcoming regulatory events
_UPCOMING_EVENTS: list[dict] = [
    {"title": "EU AI Act — Full Enforcement", "framework": "eu_ai_act", "jurisdiction": "EU",
     "type": TimelineEventType.ENFORCEMENT_START, "days_offset": 120,
     "impact": 8.5, "effort": 160, "repos": ["backend", "ml-pipeline"]},
    {"title": "DORA — ICT Risk Management", "framework": "dora", "jurisdiction": "EU",
     "type": TimelineEventType.COMPLIANCE_DEADLINE, "days_offset": 90,
     "impact": 7.0, "effort": 80, "repos": ["infrastructure", "backend"]},
    {"title": "NIS2 Directive — Deadline", "framework": "nis2", "jurisdiction": "EU",
     "type": TimelineEventType.COMPLIANCE_DEADLINE, "days_offset": 180,
     "impact": 6.5, "effort": 60, "repos": ["infrastructure"]},
    {"title": "US Federal Privacy Act (Predicted)", "framework": "us_privacy", "jurisdiction": "US",
     "type": TimelineEventType.PREDICTED, "days_offset": 365,
     "impact": 9.0, "effort": 200, "repos": ["backend", "frontend", "data-pipeline"],
     "confidence": 0.45},
    {"title": "GDPR — Cross-border Transfer Update", "framework": "gdpr", "jurisdiction": "EU",
     "type": TimelineEventType.AMENDMENT, "days_offset": 60,
     "impact": 5.0, "effort": 40, "repos": ["backend"]},
    {"title": "PCI DSS v4.0.1 — Migration Deadline", "framework": "pci_dss", "jurisdiction": "GLOBAL",
     "type": TimelineEventType.COMPLIANCE_DEADLINE, "days_offset": 45,
     "impact": 7.5, "effort": 120, "repos": ["payments-service", "backend"]},
    {"title": "HIPAA — Updated Breach Notification", "framework": "hipaa", "jurisdiction": "US",
     "type": TimelineEventType.AMENDMENT, "days_offset": 150,
     "impact": 6.0, "effort": 30, "repos": ["health-service"]},
    {"title": "Singapore PDPA Amendment", "framework": "pdpa", "jurisdiction": "SG",
     "type": TimelineEventType.REGULATION_EFFECTIVE, "days_offset": 210,
     "impact": 4.0, "effort": 20, "repos": ["backend"]},
]


class ImpactTimelineService:
    """Regulatory change impact timeline with task generation."""

    def __init__(self, db: AsyncSession, copilot_client: object | None = None):
        self.db = db
        self.copilot = copilot_client
        self._custom_events: list[TimelineEvent] = []
        self._tasks: dict[UUID, RemediationTask] = {}
        self._builtin_events: list[TimelineEvent] | None = None

    def _get_builtin_events(self) -> list[TimelineEvent]:
        """Get or create cached built-in events."""
        if self._builtin_events is None:
            now = datetime.now(UTC)
            self._builtin_events = []
            for evt_data in _UPCOMING_EVENTS:
                effective = now + timedelta(days=evt_data["days_offset"])
                event = TimelineEvent(
                    title=evt_data["title"],
                    description=f"{evt_data['framework'].upper()} regulatory change",
                    event_type=evt_data["type"],
                    framework=evt_data["framework"],
                    jurisdiction=evt_data["jurisdiction"],
                    effective_date=effective,
                    days_remaining=evt_data["days_offset"],
                    impact_score=evt_data["impact"],
                    affected_repos=evt_data["repos"],
                    estimated_effort_hours=evt_data["effort"],
                    is_predicted=evt_data["type"] == TimelineEventType.PREDICTED,
                    confidence=evt_data.get("confidence", 1.0),
                )
                self._builtin_events.append(event)
        return self._builtin_events

    async def get_timeline(
        self,
        framework: str | None = None,
        jurisdiction: str | None = None,
        days_ahead: int = 365,
    ) -> TimelineView:
        """Get the regulatory change timeline."""
        builtin = self._get_builtin_events()
        events = []

        for event in builtin:
            if framework and event.framework != framework:
                continue
            if jurisdiction and event.jurisdiction != jurisdiction:
                continue
            if event.days_remaining > days_ahead:
                continue
            events.append(event)

        events.extend([e for e in self._custom_events if (e.days_remaining or 0) <= days_ahead])
        events.sort(key=lambda e: e.days_remaining)

        tasks = list(self._tasks.values())
        overdue = sum(1 for t in tasks if t.status == TaskStatus.OVERDUE)

        return TimelineView(
            events=events,
            tasks=tasks,
            total_events=len(events),
            upcoming_deadlines=sum(1 for e in events if e.days_remaining <= 90),
            overdue_count=overdue,
            total_effort_hours=sum(e.estimated_effort_hours for e in events),
        )

    async def add_event(
        self,
        title: str,
        framework: str,
        jurisdiction: str,
        effective_date: datetime,
        event_type: TimelineEventType = TimelineEventType.REGULATION_EFFECTIVE,
        impact_score: float = 5.0,
        effort_hours: float = 0.0,
        affected_repos: list[str] | None = None,
    ) -> TimelineEvent:
        """Add a custom timeline event."""
        days_remaining = max(0, (effective_date - datetime.now(UTC)).days)
        event = TimelineEvent(
            title=title,
            event_type=event_type,
            framework=framework,
            jurisdiction=jurisdiction,
            effective_date=effective_date,
            days_remaining=days_remaining,
            impact_score=impact_score,
            affected_repos=affected_repos or [],
            estimated_effort_hours=effort_hours,
        )
        self._custom_events.append(event)
        logger.info("Timeline event added", title=title, days_remaining=days_remaining)
        return event

    async def generate_tasks(self, event_id: UUID) -> list[RemediationTask]:
        """Auto-generate remediation tasks from a timeline event."""
        # Build events from built-in data and custom events
        view = await self.get_timeline()
        all_events = list(view.events) + self._custom_events
        event = next((e for e in all_events if e.id == event_id), None)
        if not event:
            raise ValueError(f"Event {event_id} not found")

        tasks = []
        base_priority = TaskPriority.CRITICAL if event.days_remaining <= 30 else (
            TaskPriority.HIGH if event.days_remaining <= 90 else TaskPriority.MEDIUM
        )

        task_templates = [
            f"Review {event.framework.upper()} requirements for {event.title}",
            f"Map affected code in {', '.join(event.affected_repos[:3])}",
            f"Implement compliance changes for {event.framework.upper()}",
            f"Run compliance scan and verify",
        ]

        effort_per_task = event.estimated_effort_hours / len(task_templates) if task_templates else 0
        for desc in task_templates:
            task = RemediationTask(
                timeline_event_id=event.id,
                title=desc,
                description=f"Auto-generated task for: {event.title}",
                priority=base_priority,
                estimated_hours=round(effort_per_task, 1),
                due_date=event.effective_date - timedelta(days=14) if event.effective_date else None,
                created_at=datetime.now(UTC),
            )
            self._tasks[task.id] = task
            tasks.append(task)

        logger.info("Tasks generated", event_title=event.title, count=len(tasks))
        return tasks

    async def update_task_status(self, task_id: UUID, new_status: TaskStatus) -> RemediationTask | None:
        task = self._tasks.get(task_id)
        if task:
            task.status = new_status
        return task

    async def get_tasks(
        self,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
    ) -> list[RemediationTask]:
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        if priority:
            tasks = [t for t in tasks if t.priority == priority]
        return sorted(tasks, key=lambda t: t.created_at or datetime.min, reverse=True)
