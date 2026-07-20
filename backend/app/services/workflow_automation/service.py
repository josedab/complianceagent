"""Compliance Workflow Automation Service."""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_state import WorkflowDefinitionRecord, WorkflowExecutionRecord
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
    WorkflowTemplate(
        id="score-drop-alert",
        name="Score Drop Alert",
        description="Notify team when compliance score drops below threshold",
        trigger_type="score_drop",
        actions=[
            {"type": "notify_slack", "config": {"channel": "#compliance"}},
            {"type": "create_ticket", "config": {"project": "COMP"}},
        ],
        category="alerting",
    ),
    WorkflowTemplate(
        id="violation-remediate",
        name="Violation Auto-Remediate",
        description="Automatically trigger scan and create PR when violation detected",
        trigger_type="violation_detected",
        actions=[
            {"type": "trigger_scan"},
            {"type": "create_pr"},
            {"type": "notify_email", "config": {"to": "compliance-team"}},
        ],
        category="automation",
    ),
    WorkflowTemplate(
        id="regulation-update",
        name="Regulation Change Response",
        description="Notify and escalate when new regulation change detected",
        trigger_type="regulation_change",
        actions=[{"type": "notify_slack"}, {"type": "notify_email"}, {"type": "escalate"}],
        category="alerting",
    ),
    WorkflowTemplate(
        id="weekly-report",
        name="Weekly Compliance Report",
        description="Generate and distribute weekly compliance report",
        trigger_type="schedule",
        actions=[
            {"type": "run_pipeline", "config": {"pipeline": "weekly_report"}},
            {"type": "notify_email", "config": {"to": "leadership"}},
        ],
        category="reporting",
    ),
    WorkflowTemplate(
        id="drift-response",
        name="Drift Auto-Response",
        description="Auto-detect and remediate compliance drift",
        trigger_type="drift_detected",
        actions=[{"type": "trigger_scan"}, {"type": "create_pr"}, {"type": "notify_slack"}],
        category="automation",
    ),
]


def _parse_datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _definition_record_to_domain(record: WorkflowDefinitionRecord) -> WorkflowDefinition:
    meta = record.workflow_metadata or {}
    return WorkflowDefinition(
        id=record.id,
        name=record.name,
        description=record.description,
        trigger=WorkflowTrigger(
            trigger_type=TriggerType(record.trigger_type),
            conditions=meta.get("trigger_conditions", {}),
        ),
        actions=[
            WorkflowAction(
                action_type=ActionType(action.get("type", "notify_slack")),
                config=action.get("config", {}),
                order=index,
            )
            for index, action in enumerate(record.steps or [])
        ],
        status=WorkflowStatus.ACTIVE if record.is_active else WorkflowStatus.PAUSED,
        execution_count=meta.get("execution_count", 0),
        last_executed_at=_parse_datetime(meta.get("last_executed_at")),
        created_at=record.created_at,
    )


def _execution_record_to_domain(record: WorkflowExecutionRecord) -> WorkflowExecution:
    log = record.execution_log or {}
    return WorkflowExecution(
        id=record.id,
        workflow_id=record.definition_id,
        status=ExecutionStatus(record.status),
        trigger_data=log.get("trigger_data", {}),
        actions_completed=log.get("actions_completed", []),
        error_message=log.get("error_message", ""),
        started_at=record.created_at,
        completed_at=record.completed_at,
    )


class WorkflowAutomationService:
    """Trigger-condition-action workflow engine."""

    def __init__(self, db: AsyncSession, organization_id: UUID | None = None):
        self.db = db
        self.organization_id = organization_id

    async def create_workflow(
        self,
        name: str,
        description: str = "",
        trigger_type: str = "manual",
        trigger_conditions: dict | None = None,
        actions: list[dict] | None = None,
    ) -> WorkflowDefinition:
        workflow = WorkflowDefinition(
            name=name,
            description=description,
            trigger=WorkflowTrigger(
                trigger_type=TriggerType(trigger_type),
                conditions=trigger_conditions or {},
            ),
            actions=[
                WorkflowAction(
                    action_type=ActionType(action.get("type", "notify_slack")),
                    config=action.get("config", {}),
                    order=index,
                )
                for index, action in enumerate(actions or [])
            ],
            status=WorkflowStatus.ACTIVE,
            created_at=datetime.now(UTC),
        )
        record = WorkflowDefinitionRecord(
            id=workflow.id,
            organization_id=self.organization_id,
            name=workflow.name,
            description=workflow.description,
            trigger_type=workflow.trigger.trigger_type.value,
            steps=[
                {"type": action.action_type.value, "config": action.config}
                for action in workflow.actions
            ],
            workflow_metadata={
                "trigger_conditions": workflow.trigger.conditions,
                "execution_count": 0,
            },
            is_active=True,
        )
        self.db.add(record)
        await self.db.flush()
        logger.info("Workflow created", name=name, trigger=trigger_type)
        return _definition_record_to_domain(record)

    async def create_from_template(
        self, template_id: str, name: str = ""
    ) -> WorkflowDefinition | None:
        template = next((item for item in _TEMPLATES if item.id == template_id), None)
        if not template:
            return None
        return await self.create_workflow(
            name=name or template.name,
            description=template.description,
            trigger_type=template.trigger_type,
            actions=template.actions,
        )

    async def execute_workflow(
        self, workflow_id: str, trigger_data: dict | None = None
    ) -> WorkflowExecution:
        record = await self._get_workflow_record(workflow_id)
        if not record or not record.is_active:
            return WorkflowExecution(
                status=ExecutionStatus.FAILED, error_message="Workflow not found or inactive"
            )

        workflow = _definition_record_to_domain(record)
        execution = WorkflowExecution(
            workflow_id=workflow.id,
            status=ExecutionStatus.RUNNING,
            trigger_data=trigger_data or {},
            started_at=datetime.now(UTC),
        )
        for action in sorted(workflow.actions, key=lambda item: item.order):
            execution.actions_completed.append(action.action_type.value)

        execution.status = ExecutionStatus.COMPLETED
        execution.completed_at = datetime.now(UTC)
        exec_record = WorkflowExecutionRecord(
            id=execution.id,
            organization_id=self.organization_id,
            definition_id=workflow.id,
            status=execution.status.value,
            triggered_by=(trigger_data or {}).get("triggered_by", "system"),
            execution_log={
                "trigger_data": execution.trigger_data,
                "actions_completed": execution.actions_completed,
                "error_message": execution.error_message,
            },
            completed_at=execution.completed_at,
        )
        self.db.add(exec_record)

        meta = dict(record.workflow_metadata or {})
        meta["execution_count"] = meta.get("execution_count", 0) + 1
        meta["last_executed_at"] = (
            execution.completed_at.isoformat() if execution.completed_at else None
        )
        record.workflow_metadata = meta
        await self.db.flush()
        logger.info(
            "Workflow executed", name=workflow.name, actions=len(execution.actions_completed)
        )
        return _execution_record_to_domain(exec_record)

    async def pause_workflow(self, workflow_id: str) -> WorkflowDefinition | None:
        record = await self._get_workflow_record(workflow_id)
        if not record:
            return None
        record.is_active = False
        await self.db.flush()
        return _definition_record_to_domain(record)

    async def resume_workflow(self, workflow_id: str) -> WorkflowDefinition | None:
        record = await self._get_workflow_record(workflow_id)
        if not record:
            return None
        record.is_active = True
        await self.db.flush()
        return _definition_record_to_domain(record)

    async def get_workflow(self, workflow_id: str) -> WorkflowDefinition | None:
        record = await self._get_workflow_record(workflow_id)
        return _definition_record_to_domain(record) if record else None

    async def list_workflows(
        self, status: WorkflowStatus | None = None
    ) -> list[WorkflowDefinition]:
        stmt = select(WorkflowDefinitionRecord).where(
            WorkflowDefinitionRecord.organization_id == self.organization_id
        )
        if status == WorkflowStatus.ACTIVE:
            stmt = stmt.where(WorkflowDefinitionRecord.is_active.is_(True))
        elif status == WorkflowStatus.PAUSED:
            stmt = stmt.where(WorkflowDefinitionRecord.is_active.is_(False))
        result = await self.db.execute(stmt.order_by(WorkflowDefinitionRecord.created_at.desc()))
        return [_definition_record_to_domain(record) for record in result.scalars().all()]

    def list_templates(self, category: str | None = None) -> list[WorkflowTemplate]:
        templates = list(_TEMPLATES)
        if category:
            templates = [template for template in templates if template.category == category]
        return templates

    async def list_executions(
        self, workflow_id: str | None = None, limit: int = 50
    ) -> list[WorkflowExecution]:
        stmt = select(WorkflowExecutionRecord).where(
            WorkflowExecutionRecord.organization_id == self.organization_id
        )
        if workflow_id:
            stmt = stmt.where(WorkflowExecutionRecord.definition_id == UUID(workflow_id))
        result = await self.db.execute(
            stmt.order_by(WorkflowExecutionRecord.created_at.desc()).limit(limit)
        )
        return [_execution_record_to_domain(record) for record in result.scalars().all()]

    async def get_stats(self) -> WorkflowStats:
        workflows = await self.list_workflows()
        executions = await self.list_executions(limit=500)
        by_trigger: dict[str, int] = {}
        by_action: dict[str, int] = {}
        active = 0
        for workflow in workflows:
            by_trigger[workflow.trigger.trigger_type.value] = (
                by_trigger.get(workflow.trigger.trigger_type.value, 0) + 1
            )
            if workflow.status == WorkflowStatus.ACTIVE:
                active += 1
            for action in workflow.actions:
                by_action[action.action_type.value] = by_action.get(action.action_type.value, 0) + 1
        successful = sum(
            1 for execution in executions if execution.status == ExecutionStatus.COMPLETED
        )
        return WorkflowStats(
            total_workflows=len(workflows),
            active_workflows=active,
            total_executions=len(executions),
            successful_executions=successful,
            by_trigger_type=by_trigger,
            by_action_type=by_action,
        )

    async def _get_workflow_record(self, workflow_id: str) -> WorkflowDefinitionRecord | None:
        stmt = select(WorkflowDefinitionRecord).where(
            WorkflowDefinitionRecord.id == UUID(workflow_id),
            WorkflowDefinitionRecord.organization_id == self.organization_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
