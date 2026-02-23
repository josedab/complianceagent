"""Data models for Pipeline Builder Service."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class PipelineTarget(str, Enum):
    """CI/CD platform targets for pipeline generation."""

    GITHUB_ACTIONS = "github_actions"
    GITLAB_CI = "gitlab_ci"
    AZURE_PIPELINES = "azure_pipelines"
    GENERIC = "generic"


class StepType(str, Enum):
    """Types of pipeline steps."""

    SCAN = "scan"
    GATE = "gate"
    FIX = "fix"
    REVIEW = "review"
    NOTIFY = "notify"
    DEPLOY = "deploy"


class PipelineStatus(str, Enum):
    """Status of a pipeline definition."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


@dataclass
class PipelineStep:
    """A single step in a compliance pipeline."""

    id: str = ""
    name: str = ""
    step_type: StepType = StepType.SCAN
    config: dict[str, Any] = field(default_factory=dict)
    order: int = 0


@dataclass
class PipelineDefinition:
    """A complete pipeline definition."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    target: PipelineTarget = PipelineTarget.GITHUB_ACTIONS
    steps: list[PipelineStep] = field(default_factory=list)
    status: PipelineStatus = PipelineStatus.DRAFT
    repo: str = ""
    created_at: datetime | None = None
    last_deployed_at: datetime | None = None


@dataclass
class GeneratedConfig:
    """Generated CI/CD configuration from a pipeline definition."""

    pipeline_id: UUID = field(default_factory=uuid4)
    target: PipelineTarget = PipelineTarget.GITHUB_ACTIONS
    config_yaml: str = ""
    filename: str = ""
    generated_at: datetime | None = None


@dataclass
class PipelineTemplate:
    """A reusable pipeline template."""

    id: str = ""
    name: str = ""
    description: str = ""
    target: str = ""
    steps: list[dict[str, Any]] = field(default_factory=list)
    category: str = ""


@dataclass
class PipelineStats:
    """Statistics for pipeline operations."""

    total_pipelines: int = 0
    active: int = 0
    by_target: dict[str, int] = field(default_factory=dict)
    total_deployments: int = 0
    templates_used: int = 0
