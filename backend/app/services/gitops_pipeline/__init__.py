"""GitOps Compliance Pipeline — pre-commit hooks and auto-remediation."""

from app.services.gitops_pipeline.service import GitOpsPipelineService

__all__ = ["GitOpsPipelineService"]
