"""Migration Planner - Generate compliance migration plans from simulations."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

import structlog

from app.services.digital_twin.models import ComplianceIssue, SimulationResult


logger = structlog.get_logger()


class MigrationPhase(str, Enum):
    """Phases of a migration plan."""
    PREPARATION = "preparation"
    IMPLEMENTATION = "implementation"
    VALIDATION = "validation"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"


class TaskPriority(str, Enum):
    """Priority levels for migration tasks."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(str, Enum):
    """Status of a migration task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


@dataclass
class MigrationTask:
    """A single task in the migration plan."""
    id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    phase: MigrationPhase = MigrationPhase.IMPLEMENTATION
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    estimated_hours: float = 0.0
    assigned_to: str | None = None
    dependencies: list[UUID] = field(default_factory=list)
    related_issues: list[str] = field(default_factory=list)
    related_files: list[str] = field(default_factory=list)
    related_regulations: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MigrationMilestone:
    """A milestone in the migration plan."""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    phase: MigrationPhase = MigrationPhase.IMPLEMENTATION
    target_date: datetime | None = None
    tasks: list[UUID] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)
    compliance_target_score: float = 0.0
    is_complete: bool = False


@dataclass
class MigrationPlan:
    """A complete migration plan for achieving compliance."""
    id: UUID = field(default_factory=uuid4)
    simulation_result_id: UUID | None = None
    organization_id: UUID | None = None
    name: str = ""
    description: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Plan components
    tasks: list[MigrationTask] = field(default_factory=list)
    milestones: list[MigrationMilestone] = field(default_factory=list)
    
    # Metrics
    total_estimated_hours: float = 0.0
    total_tasks: int = 0
    completed_tasks: int = 0
    blocked_tasks: int = 0
    
    # Compliance targets
    current_score: float = 0.0
    target_score: float = 1.0
    regulations_addressed: list[str] = field(default_factory=list)
    
    # Risk assessment
    risk_level: str = "medium"
    risk_factors: list[str] = field(default_factory=list)
    
    # PR generation
    suggested_prs: list[dict[str, Any]] = field(default_factory=list)
    
    @property
    def progress_percentage(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100

    @property
    def tasks_by_phase(self) -> dict[MigrationPhase, list[MigrationTask]]:
        result: dict[MigrationPhase, list[MigrationTask]] = {}
        for task in self.tasks:
            if task.phase not in result:
                result[task.phase] = []
            result[task.phase].append(task)
        return result


class MigrationPlanner:
    """Generates migration plans from simulation results."""

    def __init__(self):
        self._plans: dict[UUID, MigrationPlan] = {}

    async def generate_plan(
        self,
        simulation_result: SimulationResult,
        organization_id: UUID | None = None,
        target_score: float = 0.95,
        timeline_days: int = 90,
    ) -> MigrationPlan:
        """Generate a migration plan from simulation results."""
        plan = MigrationPlan(
            simulation_result_id=simulation_result.id,
            organization_id=organization_id,
            name=f"Compliance Migration Plan - {datetime.utcnow().strftime('%Y-%m-%d')}",
            current_score=simulation_result.baseline_score,
            target_score=target_score,
        )
        
        # Generate tasks from simulation issues
        await self._generate_tasks_from_issues(plan, simulation_result)
        
        # Create milestones
        await self._create_milestones(plan, timeline_days)
        
        # Generate suggested PRs
        await self._generate_pr_suggestions(plan, simulation_result)
        
        # Calculate metrics
        self._calculate_metrics(plan)
        
        # Assess risks
        self._assess_risks(plan, simulation_result)
        
        # Store plan
        self._plans[plan.id] = plan
        
        logger.info(
            "migration_plan_generated",
            plan_id=str(plan.id),
            tasks=plan.total_tasks,
            estimated_hours=plan.total_estimated_hours,
        )
        
        return plan

    async def _generate_tasks_from_issues(
        self,
        plan: MigrationPlan,
        simulation_result: SimulationResult,
    ) -> None:
        """Generate migration tasks from compliance issues."""
        # Sort issues by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_issues = sorted(
            simulation_result.new_issues,
            key=lambda i: severity_order.get(i.severity, 4)
        )
        
        for issue in sorted_issues:
            task = self._create_task_from_issue(issue)
            plan.tasks.append(task)
            
            if issue.regulation and issue.regulation not in plan.regulations_addressed:
                plan.regulations_addressed.append(issue.regulation)
        
        # Add preparation tasks
        plan.tasks.insert(0, MigrationTask(
            title="Compliance Gap Assessment Review",
            description="Review all identified compliance gaps and validate priorities",
            phase=MigrationPhase.PREPARATION,
            priority=TaskPriority.HIGH,
            estimated_hours=4.0,
            acceptance_criteria=[
                "All gaps reviewed and confirmed",
                "Priorities validated with stakeholders",
                "Resource requirements identified",
            ],
        ))
        
        # Add validation tasks
        plan.tasks.append(MigrationTask(
            title="Compliance Validation Testing",
            description="Run comprehensive compliance tests to verify all issues are resolved",
            phase=MigrationPhase.VALIDATION,
            priority=TaskPriority.HIGH,
            estimated_hours=8.0,
            acceptance_criteria=[
                "All compliance tests pass",
                "No new critical issues introduced",
                "Compliance score meets target",
            ],
        ))
        
        # Add monitoring tasks
        plan.tasks.append(MigrationTask(
            title="Post-Migration Monitoring Setup",
            description="Configure compliance monitoring for ongoing assessment",
            phase=MigrationPhase.MONITORING,
            priority=TaskPriority.MEDIUM,
            estimated_hours=4.0,
            acceptance_criteria=[
                "Monitoring dashboards configured",
                "Alerts set up for compliance drift",
                "Regular assessment schedule established",
            ],
        ))

    def _create_task_from_issue(self, issue: ComplianceIssue) -> MigrationTask:
        """Create a migration task from a compliance issue."""
        # Map severity to priority
        priority_map = {
            "critical": TaskPriority.CRITICAL,
            "high": TaskPriority.HIGH,
            "medium": TaskPriority.MEDIUM,
            "low": TaskPriority.LOW,
        }
        
        # Estimate hours based on category and severity
        base_hours = {
            "critical": 16.0,
            "high": 8.0,
            "medium": 4.0,
            "low": 2.0,
        }
        
        estimated = base_hours.get(issue.severity, 4.0)
        
        # Adjust based on category
        category_multipliers = {
            "architecture": 2.0,
            "data_flow": 1.5,
            "security": 1.3,
            "vendor": 1.0,
            "documentation": 0.5,
        }
        multiplier = category_multipliers.get(issue.category or "", 1.0)
        estimated *= multiplier
        
        task = MigrationTask(
            title=f"Fix: {issue.message[:80]}",
            description=self._generate_task_description(issue),
            phase=MigrationPhase.IMPLEMENTATION,
            priority=priority_map.get(issue.severity, TaskPriority.MEDIUM),
            estimated_hours=estimated,
            related_issues=[issue.code],
            related_files=[issue.file_path] if issue.file_path else [],
            related_regulations=[issue.regulation] if issue.regulation else [],
            acceptance_criteria=self._generate_acceptance_criteria(issue),
        )
        
        return task

    def _generate_task_description(self, issue: ComplianceIssue) -> str:
        """Generate detailed task description from issue."""
        parts = [
            f"**Issue Code**: {issue.code}",
            f"**Severity**: {issue.severity.upper()}",
            f"**Message**: {issue.message}",
        ]
        
        if issue.regulation:
            parts.append(f"**Regulation**: {issue.regulation}")
        
        if issue.file_path:
            parts.append(f"**File**: {issue.file_path}")
            if issue.line_number:
                parts.append(f"**Line**: {issue.line_number}")
        
        if issue.remediation:
            parts.append(f"\n**Recommended Fix**:\n{issue.remediation}")
        
        return "\n".join(parts)

    def _generate_acceptance_criteria(self, issue: ComplianceIssue) -> list[str]:
        """Generate acceptance criteria for a task."""
        criteria = [
            f"Issue {issue.code} is resolved",
            "No regression in existing compliance checks",
            "Changes are documented",
        ]
        
        if issue.regulation:
            criteria.append(f"{issue.regulation} compliance requirements met")
        
        if issue.severity == "critical":
            criteria.append("Security review completed")
        
        return criteria

    async def _create_milestones(
        self,
        plan: MigrationPlan,
        timeline_days: int,
    ) -> None:
        """Create milestones for the migration plan."""
        now = datetime.utcnow()
        
        # Phase 1: Preparation (10% of timeline)
        prep_milestone = MigrationMilestone(
            name="Preparation Complete",
            description="All preparation tasks completed, team ready to implement",
            phase=MigrationPhase.PREPARATION,
            target_date=now + timedelta(days=int(timeline_days * 0.1)),
            compliance_target_score=plan.current_score,
            success_criteria=[
                "Gap assessment reviewed",
                "Resources allocated",
                "Implementation plan approved",
            ],
        )
        
        # Phase 2: Implementation (60% of timeline)
        impl_milestone = MigrationMilestone(
            name="Implementation Complete",
            description="All compliance fixes implemented",
            phase=MigrationPhase.IMPLEMENTATION,
            target_date=now + timedelta(days=int(timeline_days * 0.7)),
            compliance_target_score=plan.target_score * 0.9,
            success_criteria=[
                "All tasks completed",
                "Code reviewed and merged",
                "Initial testing passed",
            ],
        )
        
        # Phase 3: Validation (20% of timeline)
        val_milestone = MigrationMilestone(
            name="Validation Complete",
            description="All compliance validations passed",
            phase=MigrationPhase.VALIDATION,
            target_date=now + timedelta(days=int(timeline_days * 0.9)),
            compliance_target_score=plan.target_score,
            success_criteria=[
                "Compliance tests pass",
                "Audit trail complete",
                "Documentation updated",
            ],
        )
        
        # Phase 4: Monitoring (10% of timeline)
        mon_milestone = MigrationMilestone(
            name="Migration Complete",
            description="Monitoring in place, migration fully complete",
            phase=MigrationPhase.MONITORING,
            target_date=now + timedelta(days=timeline_days),
            compliance_target_score=plan.target_score,
            success_criteria=[
                "Monitoring dashboards live",
                "Alerts configured",
                "Handoff complete",
            ],
        )
        
        plan.milestones = [prep_milestone, impl_milestone, val_milestone, mon_milestone]
        
        # Assign tasks to milestones
        for task in plan.tasks:
            for milestone in plan.milestones:
                if task.phase == milestone.phase:
                    milestone.tasks.append(task.id)
                    break

    async def _generate_pr_suggestions(
        self,
        plan: MigrationPlan,
        simulation_result: SimulationResult,
    ) -> None:
        """Generate suggested PRs for the migration."""
        # Group issues by file or regulation
        by_regulation: dict[str, list[MigrationTask]] = {}
        by_file: dict[str, list[MigrationTask]] = {}
        
        for task in plan.tasks:
            if task.phase != MigrationPhase.IMPLEMENTATION:
                continue
                
            for reg in task.related_regulations:
                if reg not in by_regulation:
                    by_regulation[reg] = []
                by_regulation[reg].append(task)
            
            for file in task.related_files:
                if file not in by_file:
                    by_file[file] = []
                by_file[file].append(task)
        
        # Create PR suggestions by regulation
        for reg, tasks in by_regulation.items():
            pr = {
                "title": f"Compliance: {reg} requirements",
                "description": f"Addresses {len(tasks)} compliance issues for {reg}",
                "labels": ["compliance", reg.lower().replace(" ", "-")],
                "tasks": [str(t.id) for t in tasks],
                "files_affected": list(set(f for t in tasks for f in t.related_files)),
                "estimated_hours": sum(t.estimated_hours for t in tasks),
            }
            plan.suggested_prs.append(pr)

    def _calculate_metrics(self, plan: MigrationPlan) -> None:
        """Calculate plan metrics."""
        plan.total_tasks = len(plan.tasks)
        plan.completed_tasks = sum(1 for t in plan.tasks if t.status == TaskStatus.COMPLETED)
        plan.blocked_tasks = sum(1 for t in plan.tasks if t.status == TaskStatus.BLOCKED)
        plan.total_estimated_hours = sum(t.estimated_hours for t in plan.tasks)

    def _assess_risks(
        self,
        plan: MigrationPlan,
        simulation_result: SimulationResult,
    ) -> None:
        """Assess migration risks."""
        risk_factors = []
        
        # High number of critical issues
        critical_count = sum(
            1 for t in plan.tasks 
            if t.priority == TaskPriority.CRITICAL
        )
        if critical_count > 5:
            risk_factors.append(f"{critical_count} critical issues require immediate attention")
        
        # Large effort estimate
        if plan.total_estimated_hours > 200:
            risk_factors.append(f"Large effort estimate ({plan.total_estimated_hours}h) may require phased approach")
        
        # Multiple regulations
        if len(plan.regulations_addressed) > 3:
            risk_factors.append(f"Multiple regulations ({len(plan.regulations_addressed)}) increase complexity")
        
        # Score gap
        score_gap = plan.target_score - plan.current_score
        if score_gap > 0.3:
            risk_factors.append(f"Large compliance gap ({score_gap:.0%}) requires significant changes")
        
        plan.risk_factors = risk_factors
        
        # Determine overall risk level
        if critical_count > 5 or score_gap > 0.4:
            plan.risk_level = "high"
        elif critical_count > 2 or score_gap > 0.2:
            plan.risk_level = "medium"
        else:
            plan.risk_level = "low"

    async def get_plan(self, plan_id: UUID) -> MigrationPlan | None:
        """Get a migration plan by ID."""
        return self._plans.get(plan_id)

    async def update_task_status(
        self,
        plan_id: UUID,
        task_id: UUID,
        status: TaskStatus,
    ) -> MigrationTask | None:
        """Update the status of a task."""
        plan = self._plans.get(plan_id)
        if not plan:
            return None
        
        for task in plan.tasks:
            if task.id == task_id:
                task.status = status
                if status == TaskStatus.COMPLETED:
                    task.completed_at = datetime.utcnow()
                plan.updated_at = datetime.utcnow()
                self._calculate_metrics(plan)
                return task
        
        return None

    async def export_plan(
        self,
        plan_id: UUID,
        format: str = "json",
    ) -> dict[str, Any]:
        """Export migration plan in various formats."""
        plan = self._plans.get(plan_id)
        if not plan:
            raise ValueError(f"Plan not found: {plan_id}")
        
        if format == "json":
            return self._export_json(plan)
        elif format == "markdown":
            return {"content": self._export_markdown(plan), "format": "markdown"}
        elif format == "jira":
            return self._export_jira(plan)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_json(self, plan: MigrationPlan) -> dict[str, Any]:
        """Export plan as JSON."""
        return {
            "id": str(plan.id),
            "name": plan.name,
            "description": plan.description,
            "created_at": plan.created_at.isoformat(),
            "metrics": {
                "total_tasks": plan.total_tasks,
                "completed_tasks": plan.completed_tasks,
                "progress_percentage": plan.progress_percentage,
                "total_estimated_hours": plan.total_estimated_hours,
                "current_score": plan.current_score,
                "target_score": plan.target_score,
            },
            "risk": {
                "level": plan.risk_level,
                "factors": plan.risk_factors,
            },
            "tasks": [
                {
                    "id": str(t.id),
                    "title": t.title,
                    "phase": t.phase.value,
                    "priority": t.priority.value,
                    "status": t.status.value,
                    "estimated_hours": t.estimated_hours,
                    "regulations": t.related_regulations,
                }
                for t in plan.tasks
            ],
            "milestones": [
                {
                    "id": str(m.id),
                    "name": m.name,
                    "phase": m.phase.value,
                    "target_date": m.target_date.isoformat() if m.target_date else None,
                    "task_count": len(m.tasks),
                }
                for m in plan.milestones
            ],
            "suggested_prs": plan.suggested_prs,
        }

    def _export_markdown(self, plan: MigrationPlan) -> str:
        """Export plan as Markdown."""
        lines = [
            f"# {plan.name}",
            "",
            f"**Created**: {plan.created_at.strftime('%Y-%m-%d')}",
            f"**Current Score**: {plan.current_score:.0%}",
            f"**Target Score**: {plan.target_score:.0%}",
            f"**Risk Level**: {plan.risk_level.upper()}",
            "",
            "## Summary",
            "",
            f"- Total Tasks: {plan.total_tasks}",
            f"- Estimated Hours: {plan.total_estimated_hours:.1f}",
            f"- Regulations: {', '.join(plan.regulations_addressed)}",
            "",
        ]
        
        # Tasks by phase
        for phase in MigrationPhase:
            phase_tasks = [t for t in plan.tasks if t.phase == phase]
            if phase_tasks:
                lines.append(f"## {phase.value.title()} Phase")
                lines.append("")
                for task in phase_tasks:
                    status_emoji = {
                        TaskStatus.PENDING: "⬜",
                        TaskStatus.IN_PROGRESS: "🟨",
                        TaskStatus.COMPLETED: "✅",
                        TaskStatus.BLOCKED: "🔴",
                        TaskStatus.SKIPPED: "⏭️",
                    }
                    emoji = status_emoji.get(task.status, "⬜")
                    lines.append(f"- {emoji} **{task.title}** ({task.estimated_hours:.1f}h)")
                lines.append("")
        
        # Risk factors
        if plan.risk_factors:
            lines.append("## Risk Factors")
            lines.append("")
            for factor in plan.risk_factors:
                lines.append(f"- ⚠️ {factor}")
            lines.append("")
        
        return "\n".join(lines)

    def _export_jira(self, plan: MigrationPlan) -> dict[str, Any]:
        """Export plan as Jira-compatible issues."""
        issues = []
        
        # Create epic
        epic = {
            "type": "Epic",
            "summary": plan.name,
            "description": plan.description,
            "labels": ["compliance", "migration"],
            "custom_fields": {
                "target_score": plan.target_score,
                "current_score": plan.current_score,
            },
        }
        issues.append(epic)
        
        # Create stories for each task
        for task in plan.tasks:
            priority_map = {
                TaskPriority.CRITICAL: "Highest",
                TaskPriority.HIGH: "High",
                TaskPriority.MEDIUM: "Medium",
                TaskPriority.LOW: "Low",
            }
            
            story = {
                "type": "Story",
                "summary": task.title,
                "description": task.description,
                "priority": priority_map.get(task.priority, "Medium"),
                "labels": ["compliance"] + task.related_regulations,
                "story_points": int(task.estimated_hours / 4),  # Assuming 4h per point
                "acceptance_criteria": task.acceptance_criteria,
            }
            issues.append(story)
        
        return {"issues": issues, "count": len(issues)}


# Global instance
_migration_planner: MigrationPlanner | None = None


def get_migration_planner() -> MigrationPlanner:
    """Get or create the migration planner."""
    global _migration_planner
    if _migration_planner is None:
        _migration_planner = MigrationPlanner()
    return _migration_planner
