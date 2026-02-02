"""Label Service - Auto-labeling PRs based on compliance status."""

from dataclasses import dataclass
from enum import Enum
from typing import Any

import structlog

from app.services.github.client import GitHubClient

logger = structlog.get_logger()


class ComplianceLabel(str, Enum):
    """Standard compliance labels for PRs."""
    # Status labels
    COMPLIANT = "compliance:passed"
    NON_COMPLIANT = "compliance:failed"
    NEEDS_REVIEW = "compliance:needs-review"
    IN_PROGRESS = "compliance:in-progress"
    
    # Severity labels
    CRITICAL_ISSUES = "compliance:critical"
    HIGH_ISSUES = "compliance:high"
    MEDIUM_ISSUES = "compliance:medium"
    LOW_ISSUES = "compliance:low"
    
    # Regulation labels
    GDPR = "regulation:gdpr"
    HIPAA = "regulation:hipaa"
    PCI_DSS = "regulation:pci-dss"
    EU_AI_ACT = "regulation:eu-ai-act"
    SOX = "regulation:sox"
    CCPA = "regulation:ccpa"
    
    # Action labels
    AUTO_FIX_AVAILABLE = "compliance:auto-fix-available"
    MANUAL_REVIEW_REQUIRED = "compliance:manual-review-required"
    SECURITY_RISK = "compliance:security-risk"


@dataclass
class LabelDefinition:
    """Definition of a label with color and description."""
    name: str
    color: str
    description: str


# Predefined label configurations
LABEL_DEFINITIONS: dict[ComplianceLabel, LabelDefinition] = {
    ComplianceLabel.COMPLIANT: LabelDefinition(
        name="compliance:passed",
        color="0E8A16",  # Green
        description="All compliance checks passed",
    ),
    ComplianceLabel.NON_COMPLIANT: LabelDefinition(
        name="compliance:failed",
        color="D93F0B",  # Red
        description="Compliance issues detected that must be resolved",
    ),
    ComplianceLabel.NEEDS_REVIEW: LabelDefinition(
        name="compliance:needs-review",
        color="FBCA04",  # Yellow
        description="Compliance review pending or requires manual verification",
    ),
    ComplianceLabel.IN_PROGRESS: LabelDefinition(
        name="compliance:in-progress",
        color="1D76DB",  # Blue
        description="Compliance analysis is running",
    ),
    ComplianceLabel.CRITICAL_ISSUES: LabelDefinition(
        name="compliance:critical",
        color="B60205",  # Dark red
        description="Critical compliance violations detected",
    ),
    ComplianceLabel.HIGH_ISSUES: LabelDefinition(
        name="compliance:high",
        color="D93F0B",  # Orange-red
        description="High severity compliance issues",
    ),
    ComplianceLabel.MEDIUM_ISSUES: LabelDefinition(
        name="compliance:medium",
        color="FBCA04",  # Yellow
        description="Medium severity compliance issues",
    ),
    ComplianceLabel.LOW_ISSUES: LabelDefinition(
        name="compliance:low",
        color="0E8A16",  # Green
        description="Low severity compliance issues",
    ),
    ComplianceLabel.GDPR: LabelDefinition(
        name="regulation:gdpr",
        color="5319E7",  # Purple
        description="GDPR-related changes",
    ),
    ComplianceLabel.HIPAA: LabelDefinition(
        name="regulation:hipaa",
        color="5319E7",
        description="HIPAA-related changes",
    ),
    ComplianceLabel.PCI_DSS: LabelDefinition(
        name="regulation:pci-dss",
        color="5319E7",
        description="PCI-DSS-related changes",
    ),
    ComplianceLabel.EU_AI_ACT: LabelDefinition(
        name="regulation:eu-ai-act",
        color="5319E7",
        description="EU AI Act-related changes",
    ),
    ComplianceLabel.SOX: LabelDefinition(
        name="regulation:sox",
        color="5319E7",
        description="SOX-related changes",
    ),
    ComplianceLabel.CCPA: LabelDefinition(
        name="regulation:ccpa",
        color="5319E7",
        description="CCPA-related changes",
    ),
    ComplianceLabel.AUTO_FIX_AVAILABLE: LabelDefinition(
        name="compliance:auto-fix-available",
        color="84B6EB",  # Light blue
        description="Automated fix is available for this PR",
    ),
    ComplianceLabel.MANUAL_REVIEW_REQUIRED: LabelDefinition(
        name="compliance:manual-review-required",
        color="E99695",  # Light red
        description="Manual compliance review required",
    ),
    ComplianceLabel.SECURITY_RISK: LabelDefinition(
        name="compliance:security-risk",
        color="B60205",  # Dark red
        description="Security vulnerability detected",
    ),
}


class LabelService:
    """Service for managing compliance labels on PRs."""

    def __init__(self, github_client: GitHubClient | None = None):
        self.github = github_client

    async def ensure_labels_exist(
        self,
        owner: str,
        repo: str,
        access_token: str | None = None,
    ) -> None:
        """Ensure all compliance labels exist in the repository."""
        client = self.github or GitHubClient(access_token=access_token)
        
        async with client:
            # Get existing labels
            response = await client._client.get(
                f"/repos/{owner}/{repo}/labels",
                params={"per_page": 100},
            )
            
            if response.status_code != 200:
                logger.warning("Failed to fetch labels", status_code=response.status_code)
                return
            
            existing = {label["name"] for label in response.json()}
            
            # Create missing labels
            for label_def in LABEL_DEFINITIONS.values():
                if label_def.name not in existing:
                    await self._create_label(
                        client, owner, repo,
                        label_def.name, label_def.color, label_def.description
                    )

    async def _create_label(
        self,
        client: GitHubClient,
        owner: str,
        repo: str,
        name: str,
        color: str,
        description: str,
    ) -> bool:
        """Create a single label."""
        response = await client._client.post(
            f"/repos/{owner}/{repo}/labels",
            json={
                "name": name,
                "color": color,
                "description": description[:100],  # GitHub limits description
            },
        )
        
        if response.status_code in (200, 201):
            logger.info(f"Created label: {name}")
            return True
        elif response.status_code == 422:
            # Already exists
            return True
        else:
            logger.warning(f"Failed to create label {name}: {response.status_code}")
            return False

    def determine_labels(
        self,
        violations: list[dict[str, Any]],
        has_auto_fixes: bool = False,
    ) -> list[str]:
        """Determine which labels to apply based on analysis results."""
        labels: list[str] = []
        
        if not violations:
            labels.append(ComplianceLabel.COMPLIANT.value)
            return labels
        
        # Add status label
        labels.append(ComplianceLabel.NON_COMPLIANT.value)
        
        # Count by severity
        critical_count = sum(1 for v in violations if v.get("severity") == "critical")
        high_count = sum(1 for v in violations if v.get("severity") == "high")
        medium_count = sum(1 for v in violations if v.get("severity") == "medium")
        
        # Add severity labels
        if critical_count > 0:
            labels.append(ComplianceLabel.CRITICAL_ISSUES.value)
            labels.append(ComplianceLabel.SECURITY_RISK.value)
        if high_count > 0:
            labels.append(ComplianceLabel.HIGH_ISSUES.value)
        if medium_count > 0 and critical_count == 0 and high_count == 0:
            labels.append(ComplianceLabel.MEDIUM_ISSUES.value)
        
        # Add regulation labels
        regulations_found: set[str] = set()
        for v in violations:
            reg = v.get("regulation")
            if reg:
                regulations_found.add(reg.upper())
        
        regulation_label_map = {
            "GDPR": ComplianceLabel.GDPR.value,
            "HIPAA": ComplianceLabel.HIPAA.value,
            "PCI-DSS": ComplianceLabel.PCI_DSS.value,
            "EU AI ACT": ComplianceLabel.EU_AI_ACT.value,
            "SOX": ComplianceLabel.SOX.value,
            "CCPA": ComplianceLabel.CCPA.value,
        }
        
        for reg in regulations_found:
            if reg in regulation_label_map:
                labels.append(regulation_label_map[reg])
        
        # Add action labels
        if has_auto_fixes:
            labels.append(ComplianceLabel.AUTO_FIX_AVAILABLE.value)
        
        if critical_count > 0 or high_count > 0:
            labels.append(ComplianceLabel.MANUAL_REVIEW_REQUIRED.value)
        
        return labels

    async def apply_labels(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        labels: list[str],
        access_token: str | None = None,
        remove_existing_compliance_labels: bool = True,
    ) -> bool:
        """Apply labels to a PR."""
        client = self.github or GitHubClient(access_token=access_token)
        
        async with client:
            if remove_existing_compliance_labels:
                # Get current labels
                response = await client._client.get(
                    f"/repos/{owner}/{repo}/issues/{pr_number}/labels",
                )
                
                if response.status_code == 200:
                    current_labels = response.json()
                    # Remove existing compliance labels
                    for label in current_labels:
                        label_name = label.get("name", "")
                        if label_name.startswith(("compliance:", "regulation:")):
                            await client._client.delete(
                                f"/repos/{owner}/{repo}/issues/{pr_number}/labels/{label_name}",
                            )
            
            # Apply new labels
            if labels:
                response = await client._client.post(
                    f"/repos/{owner}/{repo}/issues/{pr_number}/labels",
                    json={"labels": labels},
                )
                
                if response.status_code in (200, 201):
                    logger.info(
                        "Labels applied to PR",
                        pr_number=pr_number,
                        labels=labels,
                    )
                    return True
                
                logger.error(
                    "Failed to apply labels",
                    status_code=response.status_code,
                )
            
            return False

    async def add_in_progress_label(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        access_token: str | None = None,
    ) -> bool:
        """Add in-progress label when analysis starts."""
        return await self.apply_labels(
            owner=owner,
            repo=repo,
            pr_number=pr_number,
            labels=[ComplianceLabel.IN_PROGRESS.value],
            access_token=access_token,
            remove_existing_compliance_labels=True,
        )

    async def remove_in_progress_label(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        access_token: str | None = None,
    ) -> bool:
        """Remove in-progress label when analysis completes."""
        client = self.github or GitHubClient(access_token=access_token)
        
        async with client:
            response = await client._client.delete(
                f"/repos/{owner}/{repo}/issues/{pr_number}/labels/{ComplianceLabel.IN_PROGRESS.value}",
            )
            return response.status_code in (200, 204)
