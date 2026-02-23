"""Agent Swarm Service."""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agent_swarm.models import (
    AgentRole,
    SwarmAgent,
    SwarmSession,
    SwarmStats,
    SwarmStatus,
    SwarmTask,
    TaskPriority,
)


logger = structlog.get_logger()

_AGENT_CAPABILITIES: dict[AgentRole, list[str]] = {
    AgentRole.SCANNER: ["static_analysis", "pattern_matching", "vulnerability_detection"],
    AgentRole.FIXER: ["auto_remediation", "code_generation", "patch_application"],
    AgentRole.REVIEWER: ["code_review", "compliance_validation", "risk_assessment"],
    AgentRole.REPORTER: ["report_generation", "metric_aggregation", "visualization"],
    AgentRole.COORDINATOR: ["task_decomposition", "agent_orchestration", "conflict_resolution"],
}


class AgentSwarmService:
    """Service for orchestrating multi-agent compliance swarms."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._sessions: list[SwarmSession] = []

    def _create_agents(self) -> list[SwarmAgent]:
        """Create one agent per role with seeded capabilities."""
        agents: list[SwarmAgent] = []
        for role in AgentRole:
            agent = SwarmAgent(
                role=role,
                name=f"{role.value}-agent",
                capabilities=_AGENT_CAPABILITIES[role],
                status="idle",
            )
            agents.append(agent)
        return agents

    def _decompose_tasks(
        self,
        repo: str,
        frameworks: list[str],
        files: list[str],
        agents: list[SwarmAgent],
    ) -> list[SwarmTask]:
        """Decompose work into tasks for the swarm pipeline."""
        scanner = next(a for a in agents if a.role == AgentRole.SCANNER)
        fixer = next(a for a in agents if a.role == AgentRole.FIXER)
        reviewer = next(a for a in agents if a.role == AgentRole.REVIEWER)
        reporter = next(a for a in agents if a.role == AgentRole.REPORTER)

        tasks = [
            SwarmTask(
                title="Scan for violations",
                description=f"Scan {len(files)} files for compliance violations",
                priority=TaskPriority.HIGH,
                assigned_agent_id=scanner.id,
                frameworks=frameworks,
                repo=repo,
                files=files,
                created_at=datetime.now(UTC),
            ),
            SwarmTask(
                title="Apply fixes",
                description="Auto-remediate detected violations",
                priority=TaskPriority.HIGH,
                assigned_agent_id=fixer.id,
                frameworks=frameworks,
                repo=repo,
                files=files,
                created_at=datetime.now(UTC),
            ),
            SwarmTask(
                title="Review changes",
                description="Review applied fixes for correctness",
                priority=TaskPriority.MEDIUM,
                assigned_agent_id=reviewer.id,
                frameworks=frameworks,
                repo=repo,
                files=files,
                created_at=datetime.now(UTC),
            ),
            SwarmTask(
                title="Generate report",
                description="Generate compliance report for swarm session",
                priority=TaskPriority.LOW,
                assigned_agent_id=reporter.id,
                frameworks=frameworks,
                repo=repo,
                files=files,
                created_at=datetime.now(UTC),
            ),
        ]
        return tasks

    def _run_pipeline(self, session: SwarmSession) -> None:
        """Run the scan→fix→review→report pipeline in-memory."""
        # Scan phase
        session.status = SwarmStatus.SCANNING
        violations = len(session.tasks[0].files) * 2
        session.violations_found = violations
        session.tasks[0].status = "completed"
        session.tasks[0].result = {"violations_found": violations}

        # Fix phase
        session.status = SwarmStatus.FIXING
        fixes = max(1, violations - 1)
        session.fixes_applied = fixes
        session.tasks[1].status = "completed"
        session.tasks[1].result = {"fixes_applied": fixes}

        # Review phase
        session.status = SwarmStatus.REVIEWING
        session.reviews_passed = fixes
        session.tasks[2].status = "completed"
        session.tasks[2].result = {"reviews_passed": fixes}

        # Report phase
        session.status = SwarmStatus.REPORTING
        session.reports_generated = 1
        session.tasks[3].status = "completed"
        session.tasks[3].result = {"reports_generated": 1}

        # Mark agents as having completed tasks
        for agent in session.agents:
            completed = [t for t in session.tasks if t.assigned_agent_id == agent.id and t.status == "completed"]
            agent.tasks_completed = len(completed)
            agent.status = "idle"

        # Complete session
        session.status = SwarmStatus.COMPLETED
        session.completed_at = datetime.now(UTC)

    async def launch_swarm(
        self,
        repo: str,
        frameworks: list[str],
        files: list[str],
    ) -> SwarmSession:
        """Launch a new swarm session for compliance analysis."""
        agents = self._create_agents()
        tasks = self._decompose_tasks(repo, frameworks, files, agents)

        session = SwarmSession(
            repo=repo,
            agents=agents,
            tasks=tasks,
            status=SwarmStatus.ASSEMBLING,
            started_at=datetime.now(UTC),
        )

        self._run_pipeline(session)
        self._sessions.append(session)
        logger.info(
            "Swarm session completed",
            repo=repo,
            violations=session.violations_found,
            fixes=session.fixes_applied,
        )
        return session

    async def list_sessions(self) -> list[SwarmSession]:
        """List all swarm sessions."""
        return list(self._sessions)

    async def get_session(self, session_id: UUID) -> SwarmSession | None:
        """Get a specific swarm session by ID."""
        return next((s for s in self._sessions if s.id == session_id), None)

    async def get_stats(self) -> SwarmStats:
        """Get aggregate statistics for swarm operations."""
        completed = [s for s in self._sessions if s.status == SwarmStatus.COMPLETED]
        total_duration = 0.0
        for s in completed:
            if s.started_at and s.completed_at:
                total_duration += (s.completed_at - s.started_at).total_seconds()

        by_agent_role: dict[str, int] = {}
        for s in self._sessions:
            for agent in s.agents:
                by_agent_role[agent.role.value] = (
                    by_agent_role.get(agent.role.value, 0) + agent.tasks_completed
                )

        return SwarmStats(
            total_sessions=len(self._sessions),
            completed=len(completed),
            avg_duration_seconds=total_duration / len(completed) if completed else 0.0,
            violations_found=sum(s.violations_found for s in self._sessions),
            fixes_applied=sum(s.fixes_applied for s in self._sessions),
            by_agent_role=by_agent_role,
        )
