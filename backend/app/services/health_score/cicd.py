"""CI/CD integration for compliance health checks."""

from datetime import datetime
from hashlib import sha256
from secrets import token_urlsafe
from uuid import UUID, uuid4

from app.services.health_score.models import (
    CICDIntegration,
    CICDResult,
    HealthScore,
    score_to_grade,
)


class CICDIntegrationService:
    """Manages CI/CD integrations for compliance checks."""
    
    SUPPORTED_PLATFORMS = [
        "github_actions",
        "gitlab_ci",
        "jenkins",
        "circleci",
        "azure_devops",
        "bitbucket_pipelines",
    ]
    
    def __init__(self):
        self._integrations: dict[UUID, CICDIntegration] = {}
        self._results: dict[UUID, list[CICDResult]] = {}
        self._tokens: dict[str, UUID] = {}  # token_hash -> integration_id
    
    async def create_integration(
        self,
        repository_id: UUID,
        platform: str,
        fail_threshold: float = 70.0,
        warn_threshold: float = 85.0,
        block_on_failure: bool = False,
        regulations_required: list[str] | None = None,
    ) -> tuple[CICDIntegration, str]:
        """Create a CI/CD integration with API token.
        
        Returns the integration and the raw API token (only returned once).
        """
        if platform not in self.SUPPORTED_PLATFORMS:
            raise ValueError(f"Unsupported platform: {platform}. Use one of: {self.SUPPORTED_PLATFORMS}")
        
        # Generate API token
        raw_token = token_urlsafe(32)
        token_hash = sha256(raw_token.encode()).hexdigest()
        
        integration = CICDIntegration(
            id=uuid4(),
            repository_id=repository_id,
            platform=platform,
            fail_threshold=fail_threshold,
            warn_threshold=warn_threshold,
            block_on_failure=block_on_failure,
            regulations_required=regulations_required or [],
            api_token_hash=token_hash,
        )
        
        self._integrations[integration.id] = integration
        self._tokens[token_hash] = integration.id
        
        return integration, raw_token
    
    async def get_integration(
        self,
        integration_id: UUID,
    ) -> CICDIntegration | None:
        """Get integration by ID."""
        return self._integrations.get(integration_id)
    
    async def get_integrations_for_repo(
        self,
        repository_id: UUID,
    ) -> list[CICDIntegration]:
        """Get all integrations for a repository."""
        return [
            i for i in self._integrations.values()
            if i.repository_id == repository_id
        ]
    
    async def validate_token(
        self,
        token: str,
    ) -> CICDIntegration | None:
        """Validate API token and return associated integration."""
        token_hash = sha256(token.encode()).hexdigest()
        integration_id = self._tokens.get(token_hash)
        
        if integration_id:
            return self._integrations.get(integration_id)
        return None
    
    async def run_check(
        self,
        integration_id: UUID,
        score: HealthScore,
        commit_sha: str,
        branch: str,
        pr_number: int | None = None,
    ) -> CICDResult:
        """Run compliance check for CI/CD pipeline."""
        integration = self._integrations.get(integration_id)
        if not integration:
            raise ValueError(f"Integration not found: {integration_id}")
        
        # Determine pass/fail/warn status
        passed = score.overall_score >= integration.fail_threshold
        warning = integration.fail_threshold <= score.overall_score < integration.warn_threshold
        
        # Check required regulations
        regulation_issues = []
        for reg in integration.regulations_required:
            if reg not in score.regulations_checked:
                regulation_issues.append(f"Missing required regulation check: {reg}")
                passed = False
        
        # Generate summary
        summary = self._generate_summary(score, passed, warning, regulation_issues)
        
        result = CICDResult(
            id=uuid4(),
            integration_id=integration_id,
            repository_id=integration.repository_id,
            score=score.overall_score,
            grade=score.grade,
            passed=passed,
            commit_sha=commit_sha,
            branch=branch,
            pr_number=pr_number,
            summary=summary,
            details={
                "threshold_pass": integration.fail_threshold,
                "threshold_warn": integration.warn_threshold,
                "warning": warning,
                "regulation_issues": regulation_issues,
                "block_merge": integration.block_on_failure and not passed,
                "category_scores": {
                    k: v.score for k, v in score.category_scores.items()
                },
            },
        )
        
        # Store result
        if integration_id not in self._results:
            self._results[integration_id] = []
        self._results[integration_id].append(result)
        
        # Keep only last 1000 results per integration
        if len(self._results[integration_id]) > 1000:
            self._results[integration_id] = self._results[integration_id][-1000:]
        
        return result
    
    def _generate_summary(
        self,
        score: HealthScore,
        passed: bool,
        warning: bool,
        regulation_issues: list[str],
    ) -> str:
        """Generate human-readable summary."""
        status = "✅ PASSED" if passed else "❌ FAILED"
        if warning:
            status = "⚠️ PASSED (with warnings)"
        
        lines = [
            f"Compliance Check {status}",
            f"Score: {score.overall_score:.1f}% ({score.grade.value})",
        ]
        
        if regulation_issues:
            lines.append(f"Regulation Issues: {len(regulation_issues)}")
        
        if score.recommendations:
            lines.append(f"Recommendations: {len(score.recommendations)}")
        
        return " | ".join(lines)
    
    async def get_results(
        self,
        integration_id: UUID,
        limit: int = 50,
    ) -> list[CICDResult]:
        """Get recent results for an integration."""
        results = self._results.get(integration_id, [])
        return results[-limit:]
    
    async def update_integration(
        self,
        integration_id: UUID,
        fail_threshold: float | None = None,
        warn_threshold: float | None = None,
        block_on_failure: bool | None = None,
        regulations_required: list[str] | None = None,
    ) -> CICDIntegration | None:
        """Update integration settings."""
        integration = self._integrations.get(integration_id)
        if not integration:
            return None
        
        if fail_threshold is not None:
            integration.fail_threshold = fail_threshold
        if warn_threshold is not None:
            integration.warn_threshold = warn_threshold
        if block_on_failure is not None:
            integration.block_on_failure = block_on_failure
        if regulations_required is not None:
            integration.regulations_required = regulations_required
        
        integration.updated_at = datetime.utcnow()
        return integration
    
    async def delete_integration(
        self,
        integration_id: UUID,
    ) -> bool:
        """Delete an integration."""
        integration = self._integrations.get(integration_id)
        if not integration:
            return False
        
        # Remove token mapping
        if integration.api_token_hash:
            self._tokens.pop(integration.api_token_hash, None)
        
        # Remove integration and results
        del self._integrations[integration_id]
        self._results.pop(integration_id, None)
        
        return True
    
    def generate_workflow_snippet(
        self,
        integration: CICDIntegration,
        api_base_url: str = "https://api.complianceagent.io",
    ) -> str:
        """Generate platform-specific CI/CD workflow snippet."""
        if integration.platform == "github_actions":
            return self._github_actions_snippet(integration, api_base_url)
        elif integration.platform == "gitlab_ci":
            return self._gitlab_ci_snippet(integration, api_base_url)
        elif integration.platform == "jenkins":
            return self._jenkins_snippet(integration, api_base_url)
        elif integration.platform == "circleci":
            return self._circleci_snippet(integration, api_base_url)
        elif integration.platform == "azure_devops":
            return self._azure_devops_snippet(integration, api_base_url)
        elif integration.platform == "bitbucket_pipelines":
            return self._bitbucket_snippet(integration, api_base_url)
        
        return f"# No snippet available for platform: {integration.platform}"
    
    def _github_actions_snippet(
        self,
        integration: CICDIntegration,
        api_base_url: str,
    ) -> str:
        return f'''# Add to your workflow file (.github/workflows/compliance.yml)
name: Compliance Check

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  compliance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Compliance Check
        env:
          COMPLIANCE_API_TOKEN: ${{{{ secrets.COMPLIANCE_API_TOKEN }}}}
        run: |
          curl -X POST "{api_base_url}/v1/health-score/check" \\
            -H "Authorization: Bearer $COMPLIANCE_API_TOKEN" \\
            -H "Content-Type: application/json" \\
            -d '{{"commit_sha": "${{{{ github.sha }}}}", "branch": "${{{{ github.ref_name }}}}", "pr_number": ${{{{ github.event.pull_request.number || 'null' }}}}}}'
'''
    
    def _gitlab_ci_snippet(
        self,
        integration: CICDIntegration,
        api_base_url: str,
    ) -> str:
        return f'''# Add to your .gitlab-ci.yml
compliance_check:
  stage: test
  script:
    - |
      curl -X POST "{api_base_url}/v1/health-score/check" \\
        -H "Authorization: Bearer $COMPLIANCE_API_TOKEN" \\
        -H "Content-Type: application/json" \\
        -d '{{"commit_sha": "$CI_COMMIT_SHA", "branch": "$CI_COMMIT_REF_NAME", "pr_number": null}}'
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
'''
    
    def _jenkins_snippet(
        self,
        integration: CICDIntegration,
        api_base_url: str,
    ) -> str:
        return f"""// Add to your Jenkinsfile
pipeline {{
    agent any
    stages {{
        stage('Compliance Check') {{
            steps {{
                withCredentials([string(credentialsId: 'compliance-api-token', variable: 'COMPLIANCE_API_TOKEN')]) {{
                    sh \"\"\"
                        curl -X POST "{api_base_url}/v1/health-score/check" \\
                            -H "Authorization: Bearer $COMPLIANCE_API_TOKEN" \\
                            -H "Content-Type: application/json" \\
                            -d '{{"commit_sha": "'$GIT_COMMIT'", "branch": "'$GIT_BRANCH'", "pr_number": null}}'
                    \"\"\"
                }}
            }}
        }}
    }}
}}
"""
    
    def _circleci_snippet(
        self,
        integration: CICDIntegration,
        api_base_url: str,
    ) -> str:
        return f'''# Add to your .circleci/config.yml
version: 2.1

jobs:
  compliance:
    docker:
      - image: cimg/base:stable
    steps:
      - checkout
      - run:
          name: Run Compliance Check
          command: |
            curl -X POST "{api_base_url}/v1/health-score/check" \\
              -H "Authorization: Bearer $COMPLIANCE_API_TOKEN" \\
              -H "Content-Type: application/json" \\
              -d '{{"commit_sha": "$CIRCLE_SHA1", "branch": "$CIRCLE_BRANCH", "pr_number": null}}'

workflows:
  compliance:
    jobs:
      - compliance
'''
    
    def _azure_devops_snippet(
        self,
        integration: CICDIntegration,
        api_base_url: str,
    ) -> str:
        return f'''# Add to your azure-pipelines.yml
trigger:
  - main

pool:
  vmImage: 'ubuntu-latest'

steps:
  - task: Bash@3
    displayName: 'Run Compliance Check'
    inputs:
      targetType: 'inline'
      script: |
        curl -X POST "{api_base_url}/v1/health-score/check" \\
          -H "Authorization: Bearer $(COMPLIANCE_API_TOKEN)" \\
          -H "Content-Type: application/json" \\
          -d '{{"commit_sha": "$(Build.SourceVersion)", "branch": "$(Build.SourceBranchName)", "pr_number": null}}'
'''
    
    def _bitbucket_snippet(
        self,
        integration: CICDIntegration,
        api_base_url: str,
    ) -> str:
        return f'''# Add to your bitbucket-pipelines.yml
pipelines:
  default:
    - step:
        name: Compliance Check
        script:
          - |
            curl -X POST "{api_base_url}/v1/health-score/check" \\
              -H "Authorization: Bearer $COMPLIANCE_API_TOKEN" \\
              -H "Content-Type: application/json" \\
              -d '{{"commit_sha": "$BITBUCKET_COMMIT", "branch": "$BITBUCKET_BRANCH", "pr_number": null}}'
'''


# Singleton instance
_cicd_service: CICDIntegrationService | None = None


def get_cicd_service() -> CICDIntegrationService:
    """Get singleton CI/CD service."""
    global _cicd_service
    if _cicd_service is None:
        _cicd_service = CICDIntegrationService()
    return _cicd_service
