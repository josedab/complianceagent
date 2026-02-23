"""Compliance Workflow Automation Service."""

from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.workflow_automation.models import (
    ActionType,
    ExecutionStatus,
    TriggerType,
    WorkflowAction,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowStats,
    WorkflowStatus,
    WorkflowTemplate,
    WorkflowTrigger,
)


logger = structlog.get_logger()

_TEMPLATES: list[WorkflowTemplate] = [
    WorkflowTemplate(id="score-drop-alert", name="Score Drop Alert", description="Notify team when compliance score drops below threshold", trigger_type="score_drop", actions=[{"type": "notify_slack", "config": {"channel": "#compliance"}}, {"type": "create_ticket", "config": {"project": "COMP"}}], category="alerting"),
    WorkflowTemplate(id="violation-remediate", name="Violation Auto-Remediate", description="Automatically trigger scan and create PR when violation detected", trigger_type="violation_detected", actions=[{"type": "trigger_scan"}, {"type": "create_pr"}, {"type": "notify_email", "config": {"to": "compliance-team"}}], category="automation"),
    WorkflowTemplate(id="regulation-update", name="Regulation Change Response", description="Notify and escalate when new regulation change detected", trigger_type="regulation_change", actions=[{"type": "notify_slack"}, {"type": "notify_email"}, {"type": "escalate"}], category="alerting"),
    WorkflowTemplate(id="weekly-report", name="Weekly Compliance Report", description="Generate and distribute weekly compliance report", trigger_type="schedule", actions=[{"type": "run_pipeline", "config": {"pipeline": "weekly_report"}}, {"type": "notify_email", "config": {"to": "leadership"}}], category="reporting"),
    WorkflowTemplate(id="drift-response", name="Drift Auto-Response", description="Auto-detect and remediate compliance drift", trigger_type="drift_detected", actions=[{"type": "trigger_scan"}, {"type": "create_pr"}, {"type": "notify_slack"}], category="automation"),
]


class WorkflowAutomationService:
    """Trigger-condition-action workflow engine."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._workflows: dict[str, WorkflowDefinition] = {}
        self._executions: list[WorkflowExecution] = []

    async def create_workflow(
        self,
        name: str,
        description: str = "",
        trigger_type: str = "manual",
        trigger_conditions: dict | None = None,
        actions: list[dict] | None = None,
    ) -> WorkflowDefinition:
        trigger = WorkflowTrigger(
            trigger_type=TriggerType(trigger_type),
            conditions=trigger_conditions or {},
        )
        wf_actions = [
            WorkflowAction(
                action_type=ActionType(a.get("type", "notify_slack")),
                config=a.get("config", {}),
                order=i,
            )
            for i, a in enumerate(actions or [])
        ]
        workflow = WorkflowDefinition(
            name=name,
            description=description,
            trigger=trigger,
            actions=wf_actions,
            status=WorkflowStatus.ACTIVE,
            created_at=datetime.now(UTC),
        )
        self._workflows[str(workflow.id)] = workflow
        logger.info("Workflow created", name=name, trigger=trigger_type)
        return workflow

    async def create_from_template(self, template_id: str, name: str = "") -> WorkflowDefinition | None:
        tmpl = next((t for t in _TEMPLATES if t.id == template_id), None)
        if not tmpl:
            return None
        return await self.create_workflow(
            name=name or tmpl.name,
            description=tmpl.description,
            trigger_type=tmpl.trigger_type,
            actions=tmpl.actions,
        )

    async def execute_workflow(self, workflow_id: str, trigger_data: dict | None = None) -> WorkflowExecution:
        workflow = self._workflows.get(workflow_id)
        if not workflow or workflow.status != WorkflowStatus.ACTIVE:
            return WorkflowExecution(status=ExecutionStatus.FAILED, error_message="Workflow not found or inactive")

        execution = WorkflowExecution(
            workflow_id=workflow.id,
            status=ExecutionStatus.RUNNING,
            trigger_data=trigger_data or {},
            started_at=datetime.now(UTC),
        )

        for action in sorted(workflow.actions, key=lambda a: a.order):
            execution.actions_completed.append(action.action_type.value)

        execution.status = ExecutionStatus.COMPLETED
        execution.completed_at = datetime.now(UTC)
        workflow.execution_count += 1
        workflow.last_executed_at = datetime.now(UTC)
        self._executions.append(execution)
        logger.info("Workflow executed", name=workflow.name, actions=len(execution.actions_completed))
        return execution

    async def pause_workflow(self, workflow_id: str) -> WorkflowDefinition | None:
        wf = self._workflows.get(workflow_id)
        if not wf:
            return None
        wf.status = WorkflowStatus.PAUSED
        return wf

    async def resume_workflow(self, workflow_id: str) -> WorkflowDefinition | None:
        wf = self._workflows.get(workflow_id)
        if not wf:
            return None
        wf.status = WorkflowStatus.ACTIVE
        return wf

    def get_workflow(self, workflow_id: str) -> WorkflowDefinition | None:
        return self._workflows.get(workflow_id)

    def list_workflows(self, status: WorkflowStatus | None = None) -> list[WorkflowDefinition]:
        results = list(self._workflows.values())
        if status:
            results = [w for w in results if w.status == status]
        return results

    def list_templates(self, category: str | None = None) -> list[WorkflowTemplate]:
        templates = list(_TEMPLATES)
        if category:
            templates = [t for t in templates if t.category == category]
        return templates

    def list_executions(self, workflow_id: str | None = None, limit: int = 50) -> list[WorkflowExecution]:
        results = list(self._executions)
        if workflow_id:
            wf = self._workflows.get(workflow_id)
            if wf:
                results = [e for e in results if e.workflow_id == wf.id]
        return sorted(results, key=lambda e: e.started_at or datetime.min.replace(tzinfo=UTC), reverse=True)[:limit]

    def get_stats(self) -> WorkflowStats:
        by_trigger: dict[str, int] = {}
        by_action: dict[str, int] = {}
        active = 0
        for wf in self._workflows.values():
            by_trigger[wf.trigger.trigger_type.value] = by_trigger.get(wf.trigger.trigger_type.value, 0) + 1
            if wf.status == WorkflowStatus.ACTIVE:
                active += 1
            for a in wf.actions:
                by_action[a.action_type.value] = by_action.get(a.action_type.value, 0) + 1
        successful = sum(1 for e in self._executions if e.status == ExecutionStatus.COMPLETED)
        return WorkflowStats(
            total_workflows=len(self._workflows),
            active_workflows=active,
            total_executions=len(self._executions),
            successful_executions=successful,
            by_trigger_type=by_trigger,
            by_action_type=by_action,
        )
