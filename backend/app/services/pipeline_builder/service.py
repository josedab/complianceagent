"""Pipeline Builder Service."""

from datetime import UTC, datetime
from uuid import UUID

import structlog
import yaml
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.pipeline_builder.models import (
    GeneratedConfig,
    PipelineDefinition,
    PipelineStats,
    PipelineStatus,
    PipelineStep,
    PipelineTarget,
    PipelineTemplate,
    StepType,
)


logger = structlog.get_logger()

_TEMPLATES: list[PipelineTemplate] = [
    PipelineTemplate(
        id="basic-scan",
        name="Basic Compliance Scan",
        description="Simple scan-and-report pipeline",
        target="any",
        steps=[
            {"id": "scan-1", "name": "Compliance Scan", "step_type": "scan", "order": 0},
            {"id": "notify-1", "name": "Send Report", "step_type": "notify", "order": 1},
        ],
        category="starter",
    ),
    PipelineTemplate(
        id="full-compliance",
        name="Full Compliance Pipeline",
        description="Complete scan, gate, fix, review, and deploy pipeline",
        target="any",
        steps=[
            {"id": "scan-1", "name": "Compliance Scan", "step_type": "scan", "order": 0},
            {"id": "gate-1", "name": "Compliance Gate", "step_type": "gate", "order": 1},
            {"id": "fix-1", "name": "Auto Fix", "step_type": "fix", "order": 2},
            {"id": "review-1", "name": "Review Changes", "step_type": "review", "order": 3},
            {"id": "deploy-1", "name": "Deploy", "step_type": "deploy", "order": 4},
        ],
        category="advanced",
    ),
    PipelineTemplate(
        id="security-gate",
        name="Security Gate",
        description="Block deployments that fail compliance checks",
        target="any",
        steps=[
            {"id": "scan-1", "name": "Security Scan", "step_type": "scan", "order": 0},
            {"id": "gate-1", "name": "Security Gate", "step_type": "gate", "order": 1},
            {"id": "notify-1", "name": "Notify Team", "step_type": "notify", "order": 2},
        ],
        category="security",
    ),
    PipelineTemplate(
        id="auto-fix",
        name="Auto-Fix Pipeline",
        description="Automatically fix compliance violations and submit for review",
        target="any",
        steps=[
            {"id": "scan-1", "name": "Compliance Scan", "step_type": "scan", "order": 0},
            {"id": "fix-1", "name": "Auto Fix", "step_type": "fix", "order": 1},
            {"id": "review-1", "name": "Review Fixes", "step_type": "review", "order": 2},
            {"id": "notify-1", "name": "Notify", "step_type": "notify", "order": 3},
        ],
        category="remediation",
    ),
]


class PipelineBuilderService:
    """Service for building and generating CI/CD compliance pipelines."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._pipelines: dict[UUID, PipelineDefinition] = {}
        self._templates_used: int = 0
        self._total_deployments: int = 0

    async def create_pipeline(
        self,
        name: str,
        target: str,
        repo: str,
        steps: list[dict],
    ) -> PipelineDefinition:
        """Create a new pipeline definition."""
        pipeline_steps = [
            PipelineStep(
                id=s.get("id", f"step-{i}"),
                name=s.get("name", ""),
                step_type=StepType(s.get("step_type", "scan")),
                config=s.get("config", {}),
                order=s.get("order", i),
            )
            for i, s in enumerate(steps)
        ]

        pipeline = PipelineDefinition(
            name=name,
            description=f"Compliance pipeline for {repo}",
            target=PipelineTarget(target),
            steps=pipeline_steps,
            status=PipelineStatus.DRAFT,
            repo=repo,
            created_at=datetime.now(UTC),
        )
        self._pipelines[pipeline.id] = pipeline
        logger.info("Pipeline created", name=name, target=target, steps=len(pipeline_steps))
        return pipeline

    async def create_from_template(
        self,
        template_id: str,
        repo: str,
    ) -> PipelineDefinition:
        """Create a pipeline from a predefined template."""
        template = next((t for t in _TEMPLATES if t.id == template_id), None)
        if not template:
            raise ValueError(f"Template '{template_id}' not found")

        self._templates_used += 1
        return await self.create_pipeline(
            name=template.name,
            target=PipelineTarget.GITHUB_ACTIONS.value,
            repo=repo,
            steps=template.steps,
        )

    def _generate_github_actions(self, pipeline: PipelineDefinition) -> str:
        """Generate GitHub Actions YAML configuration."""
        jobs: dict = {}
        for step in sorted(pipeline.steps, key=lambda s: s.order):
            job_id = step.id.replace("-", "_")
            jobs[job_id] = {
                "name": step.name,
                "runs-on": "ubuntu-latest",
                "steps": [
                    {"uses": "actions/checkout@v4"},
                    {
                        "name": step.name,
                        "run": f"echo 'Running {step.step_type.value}: {step.name}'",
                    },
                ],
            }

        config = {
            "name": pipeline.name,
            "on": {"push": {"branches": ["main"]}, "pull_request": {"branches": ["main"]}},
            "jobs": jobs,
        }
        return yaml.dump(config, default_flow_style=False, sort_keys=False)

    def _generate_gitlab_ci(self, pipeline: PipelineDefinition) -> str:
        """Generate GitLab CI YAML configuration."""
        stages = [step.id for step in sorted(pipeline.steps, key=lambda s: s.order)]
        config: dict = {"stages": stages}

        for step in sorted(pipeline.steps, key=lambda s: s.order):
            config[step.id] = {
                "stage": step.id,
                "image": "python:3.12",
                "script": [f"echo 'Running {step.step_type.value}: {step.name}'"],
            }
        return yaml.dump(config, default_flow_style=False, sort_keys=False)

    def _generate_azure_pipelines(self, pipeline: PipelineDefinition) -> str:
        """Generate Azure Pipelines YAML configuration."""
        steps_list = []
        for step in sorted(pipeline.steps, key=lambda s: s.order):
            steps_list.append({
                "script": f"echo 'Running {step.step_type.value}: {step.name}'",
                "displayName": step.name,
            })

        config = {
            "trigger": ["main"],
            "pool": {"vmImage": "ubuntu-latest"},
            "steps": steps_list,
        }
        return yaml.dump(config, default_flow_style=False, sort_keys=False)

    async def generate_config(self, pipeline_id: UUID) -> GeneratedConfig:
        """Generate CI/CD configuration for a pipeline."""
        pipeline = self._pipelines.get(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_id} not found")

        generators = {
            PipelineTarget.GITHUB_ACTIONS: (self._generate_github_actions, ".github/workflows/compliance.yml"),
            PipelineTarget.GITLAB_CI: (self._generate_gitlab_ci, ".gitlab-ci.yml"),
            PipelineTarget.AZURE_PIPELINES: (self._generate_azure_pipelines, "azure-pipelines.yml"),
        }

        generator, filename = generators.get(
            pipeline.target,
            (self._generate_github_actions, "compliance-pipeline.yml"),
        )

        config_yaml = generator(pipeline)
        generated = GeneratedConfig(
            pipeline_id=pipeline.id,
            target=pipeline.target,
            config_yaml=config_yaml,
            filename=filename,
            generated_at=datetime.now(UTC),
        )
        logger.info(
            "Config generated",
            pipeline_id=str(pipeline_id),
            target=pipeline.target.value,
            filename=filename,
        )
        return generated

    async def deploy_pipeline(self, pipeline_id: UUID) -> GeneratedConfig:
        """Deploy a pipeline by generating config and marking as active."""
        pipeline = self._pipelines.get(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_id} not found")

        config = await self.generate_config(pipeline_id)
        pipeline.status = PipelineStatus.ACTIVE
        pipeline.last_deployed_at = datetime.now(UTC)
        self._total_deployments += 1
        logger.info("Pipeline deployed", pipeline_id=str(pipeline_id))
        return config

    async def list_pipelines(self) -> list[PipelineDefinition]:
        """List all pipeline definitions."""
        return list(self._pipelines.values())

    async def list_templates(self) -> list[PipelineTemplate]:
        """List available pipeline templates."""
        return list(_TEMPLATES)

    async def get_stats(self) -> PipelineStats:
        """Get pipeline builder statistics."""
        pipelines = list(self._pipelines.values())
        by_target: dict[str, int] = {}
        active_count = 0
        for p in pipelines:
            by_target[p.target.value] = by_target.get(p.target.value, 0) + 1
            if p.status == PipelineStatus.ACTIVE:
                active_count += 1

        return PipelineStats(
            total_pipelines=len(pipelines),
            active=active_count,
            by_target=by_target,
            total_deployments=self._total_deployments,
            templates_used=self._templates_used,
        )
