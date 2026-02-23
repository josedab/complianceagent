"""Data models for Agent Swarm Service."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class AgentRole(str, Enum):
    """Role of an agent in the swarm."""

    SCANNER = "scanner"
    FIXER = "fixer"
    REVIEWER = "reviewer"
    REPORTER = "reporter"
    COORDINATOR = "coordinator"


class SwarmStatus(str, Enum):
    """Status of a swarm session."""

    ASSEMBLING = "assembling"
    SCANNING = "scanning"
    FIXING = "fixing"
    REVIEWING = "reviewing"
    REPORTING = "reporting"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskPriority(str, Enum):
    """Priority level for swarm tasks."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class SwarmAgent:
    """An individual agent in the swarm."""

    id: UUID = field(default_factory=uuid4)
    role: AgentRole = AgentRole.SCANNER
    name: str = ""
    capabilities: list[str] = field(default_factory=list)
    status: str = "idle"
    tasks_completed: int = 0


@dataclass
class SwarmTask:
    """A task assigned within the swarm."""

    id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    assigned_agent_id: UUID | None = None
    frameworks: list[str] = field(default_factory=list)
    repo: str = ""
    files: list[str] = field(default_factory=list)
    status: str = "pending"
    result: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None


@dataclass
class SwarmSession:
    """A complete swarm session orchestrating multiple agents."""

    id: UUID = field(default_factory=uuid4)
    repo: str = ""
    agents: list[SwarmAgent] = field(default_factory=list)
    tasks: list[SwarmTask] = field(default_factory=list)
    status: SwarmStatus = SwarmStatus.ASSEMBLING
    violations_found: int = 0
    fixes_applied: int = 0
    reviews_passed: int = 0
    reports_generated: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class SwarmStats:
    """Statistics for swarm operations."""

    total_sessions: int = 0
    completed: int = 0
    avg_duration_seconds: float = 0.0
    violations_found: int = 0
    fixes_applied: int = 0
    by_agent_role: dict[str, int] = field(default_factory=dict)
