"""Playbook Generator - Creates customized compliance implementation guides."""

from typing import Any
from uuid import UUID

import structlog

from app.services.playbook.models import (
    CloudProvider,
    Framework,
    Playbook,
    PlaybookCategory,
    PlaybookExecution,
    PlaybookStep,
    PLAYBOOK_TEMPLATES,
    StackProfile,
    StepDifficulty,
    TechStack,
)


logger = structlog.get_logger()


# Step templates by category and tech stack
STEP_TEMPLATES: dict[str, dict[str, list[dict[str, Any]]]] = {
    "encryption_at_rest": {
        "python": [
            {
                "title": "Install encryption libraries",
                "description": "Install cryptography library for encryption operations",
                "commands": ["pip install cryptography"],
                "difficulty": StepDifficulty.EASY,
                "estimated_minutes": 5,
            },
            {
                "title": "Configure encryption key management",
                "description": "Set up secure key storage using environment variables or a secrets manager",
                "code_snippet": '''import os
from cryptography.fernet import Fernet

# Load encryption key from environment
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY environment variable not set")

cipher = Fernet(ENCRYPTION_KEY.encode())''',
                "difficulty": StepDifficulty.MEDIUM,
                "estimated_minutes": 20,
            },
            {
                "title": "Implement data encryption wrapper",
                "description": "Create utility functions for encrypting/decrypting sensitive data",
                "code_snippet": '''def encrypt_data(data: str) -> bytes:
    """Encrypt sensitive data before storage."""
    return cipher.encrypt(data.encode())

def decrypt_data(encrypted: bytes) -> str:
    """Decrypt data when retrieving."""
    return cipher.decrypt(encrypted).decode()''',
                "verification_steps": ["Write unit tests for encryption functions"],
                "difficulty": StepDifficulty.MEDIUM,
                "estimated_minutes": 30,
            },
            {
                "title": "Update database models",
                "description": "Apply encryption to sensitive fields in your data models",
                "difficulty": StepDifficulty.HARD,
                "estimated_minutes": 60,
            },
            {
                "title": "Document and verify",
                "description": "Document encryption approach and verify implementation",
                "verification_steps": [
                    "Verify encrypted data in database",
                    "Test decryption works correctly",
                    "Document key rotation procedure",
                ],
                "difficulty": StepDifficulty.EASY,
                "estimated_minutes": 20,
            },
        ],
        "javascript": [
            {
                "title": "Install encryption packages",
                "commands": ["npm install crypto-js @types/crypto-js"],
                "difficulty": StepDifficulty.EASY,
                "estimated_minutes": 5,
            },
            {
                "title": "Set up encryption configuration",
                "code_snippet": '''import CryptoJS from 'crypto-js';

const ENCRYPTION_KEY = process.env.ENCRYPTION_KEY;
if (!ENCRYPTION_KEY) {
  throw new Error('ENCRYPTION_KEY not configured');
}

export function encrypt(data: string): string {
  return CryptoJS.AES.encrypt(data, ENCRYPTION_KEY).toString();
}

export function decrypt(encrypted: string): string {
  const bytes = CryptoJS.AES.decrypt(encrypted, ENCRYPTION_KEY);
  return bytes.toString(CryptoJS.enc.Utf8);
}''',
                "difficulty": StepDifficulty.MEDIUM,
                "estimated_minutes": 25,
            },
        ],
    },
    "mfa_implementation": {
        "python": [
            {
                "title": "Install TOTP library",
                "commands": ["pip install pyotp qrcode[pil]"],
                "difficulty": StepDifficulty.EASY,
                "estimated_minutes": 5,
            },
            {
                "title": "Implement TOTP generation",
                "code_snippet": '''import pyotp
import qrcode
from io import BytesIO

def generate_mfa_secret() -> str:
    """Generate a new MFA secret for a user."""
    return pyotp.random_base32()

def get_totp_uri(secret: str, user_email: str, issuer: str) -> str:
    """Get URI for QR code generation."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=user_email, issuer_name=issuer)

def verify_totp(secret: str, code: str) -> bool:
    """Verify a TOTP code."""
    totp = pyotp.TOTP(secret)
    return totp.verify(code)''',
                "difficulty": StepDifficulty.MEDIUM,
                "estimated_minutes": 30,
            },
            {
                "title": "Add MFA to user model",
                "description": "Update user model to store MFA secret and status",
                "difficulty": StepDifficulty.MEDIUM,
                "estimated_minutes": 30,
            },
            {
                "title": "Create MFA setup flow",
                "description": "Implement API endpoints for MFA enrollment",
                "difficulty": StepDifficulty.HARD,
                "estimated_minutes": 60,
            },
            {
                "title": "Enforce MFA at login",
                "description": "Add MFA verification step to authentication flow",
                "difficulty": StepDifficulty.HARD,
                "estimated_minutes": 45,
            },
        ],
    },
    "audit_logging": {
        "python": [
            {
                "title": "Set up structured logging",
                "commands": ["pip install structlog python-json-logger"],
                "difficulty": StepDifficulty.EASY,
                "estimated_minutes": 5,
            },
            {
                "title": "Configure audit logger",
                "code_snippet": '''import structlog
from datetime import datetime

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
)

audit_logger = structlog.get_logger("audit")

def log_audit_event(
    event_type: str,
    user_id: str,
    resource: str,
    action: str,
    outcome: str,
    **kwargs
):
    """Log an audit event."""
    audit_logger.info(
        event_type,
        user_id=user_id,
        resource=resource,
        action=action,
        outcome=outcome,
        timestamp=datetime.utcnow().isoformat(),
        **kwargs
    )''',
                "difficulty": StepDifficulty.MEDIUM,
                "estimated_minutes": 30,
            },
            {
                "title": "Add middleware for request logging",
                "description": "Log all API requests with relevant context",
                "difficulty": StepDifficulty.MEDIUM,
                "estimated_minutes": 45,
            },
            {
                "title": "Configure log retention",
                "description": "Set up log aggregation and retention policy",
                "difficulty": StepDifficulty.MEDIUM,
                "estimated_minutes": 30,
            },
        ],
    },
}

# Cloud-specific configurations
CLOUD_CONFIGS: dict[str, dict[str, Any]] = {
    "aws": {
        "encryption_at_rest": {
            "service": "AWS KMS",
            "steps": [
                "Create KMS key in AWS Console",
                "Configure IAM permissions for key access",
                "Use aws-encryption-sdk for application encryption",
            ],
        },
        "logging": {
            "service": "CloudWatch Logs",
            "steps": [
                "Create CloudWatch log group",
                "Configure retention period",
                "Set up log insights queries",
            ],
        },
    },
    "gcp": {
        "encryption_at_rest": {
            "service": "Cloud KMS",
            "steps": [
                "Create keyring and cryptokey",
                "Grant IAM permissions",
                "Use google-cloud-kms library",
            ],
        },
    },
    "azure": {
        "encryption_at_rest": {
            "service": "Azure Key Vault",
            "steps": [
                "Create Key Vault",
                "Configure access policies",
                "Use azure-keyvault-keys SDK",
            ],
        },
    },
}


class PlaybookGenerator:
    """Generates customized compliance playbooks."""

    def __init__(self):
        self._playbooks: dict[UUID, Playbook] = {}
        self._executions: dict[UUID, PlaybookExecution] = {}

    async def generate_playbook(
        self,
        template_slug: str,
        stack_profile: StackProfile,
        organization_id: UUID | None = None,
    ) -> Playbook:
        """Generate a customized playbook from a template.
        
        Args:
            template_slug: Template to use
            stack_profile: Technology stack profile
            organization_id: Organization context
            
        Returns:
            Customized Playbook
        """
        template = PLAYBOOK_TEMPLATES.get(template_slug)
        if not template:
            raise ValueError(f"Unknown template: {template_slug}")
        
        playbook = Playbook(
            name=template["name"],
            slug=template_slug,
            category=template["category"],
            regulations=template.get("regulations", []),
            controls=template.get("controls", []),
            difficulty=template.get("difficulty", StepDifficulty.MEDIUM),
            estimated_hours=template.get("estimated_hours", 4),
            tech_stacks=[stack_profile.tech_stack],
        )
        
        if stack_profile.framework:
            playbook.frameworks = [stack_profile.framework]
        if stack_profile.cloud_provider:
            playbook.cloud_providers = [stack_profile.cloud_provider]
        
        # Generate steps
        playbook.steps = await self._generate_steps(
            template_slug, stack_profile
        )
        playbook.total_steps = len(playbook.steps)
        
        # Add cloud-specific context
        if stack_profile.cloud_provider:
            await self._add_cloud_context(playbook, stack_profile.cloud_provider)
        
        # Generate overview
        playbook.overview = self._generate_overview(playbook)
        
        # Generate prerequisites
        playbook.prerequisites = self._generate_prerequisites(playbook, stack_profile)
        
        # Store
        self._playbooks[playbook.id] = playbook
        
        logger.info(
            "Generated playbook",
            playbook_id=str(playbook.id),
            template=template_slug,
            tech_stack=stack_profile.tech_stack.value,
            steps=playbook.total_steps,
        )
        
        return playbook

    async def _generate_steps(
        self,
        template_slug: str,
        profile: StackProfile,
    ) -> list[PlaybookStep]:
        """Generate implementation steps."""
        steps = []
        step_templates = STEP_TEMPLATES.get(template_slug, {})
        
        # Get tech-specific steps
        tech_steps = step_templates.get(profile.tech_stack.value, [])
        
        for i, step_data in enumerate(tech_steps, 1):
            step = PlaybookStep(
                step_number=i,
                title=step_data.get("title", ""),
                description=step_data.get("description", ""),
                code_snippet=step_data.get("code_snippet", ""),
                commands=step_data.get("commands", []),
                prerequisites=step_data.get("prerequisites", []),
                required_tools=step_data.get("required_tools", []),
                difficulty=step_data.get("difficulty", StepDifficulty.MEDIUM),
                estimated_minutes=step_data.get("estimated_minutes", 15),
                verification_steps=step_data.get("verification_steps", []),
            )
            steps.append(step)
        
        # If no tech-specific steps, add generic ones
        if not steps:
            steps = self._generate_generic_steps(template_slug)
        
        return steps

    def _generate_generic_steps(self, template_slug: str) -> list[PlaybookStep]:
        """Generate generic steps when no tech-specific ones exist."""
        return [
            PlaybookStep(
                step_number=1,
                title="Assess current state",
                description="Review existing implementation and identify gaps",
                difficulty=StepDifficulty.EASY,
                estimated_minutes=30,
            ),
            PlaybookStep(
                step_number=2,
                title="Plan implementation",
                description="Create detailed implementation plan with timeline",
                difficulty=StepDifficulty.MEDIUM,
                estimated_minutes=60,
            ),
            PlaybookStep(
                step_number=3,
                title="Implement changes",
                description="Execute the implementation according to plan",
                difficulty=StepDifficulty.HARD,
                estimated_minutes=120,
            ),
            PlaybookStep(
                step_number=4,
                title="Test and verify",
                description="Verify implementation meets requirements",
                difficulty=StepDifficulty.MEDIUM,
                estimated_minutes=60,
            ),
            PlaybookStep(
                step_number=5,
                title="Document and evidence",
                description="Create documentation and collect evidence",
                difficulty=StepDifficulty.EASY,
                estimated_minutes=30,
            ),
        ]

    async def _add_cloud_context(
        self,
        playbook: Playbook,
        cloud_provider: CloudProvider,
    ) -> None:
        """Add cloud-specific context to playbook."""
        cloud_config = CLOUD_CONFIGS.get(cloud_provider.value, {})
        category_config = cloud_config.get(playbook.slug, {})
        
        if category_config:
            # Add cloud-specific step at the beginning
            cloud_step = PlaybookStep(
                step_number=0,
                title=f"Configure {category_config.get('service', 'cloud service')}",
                description=f"Set up {cloud_provider.value.upper()} services",
                commands=category_config.get("steps", []),
                difficulty=StepDifficulty.MEDIUM,
                estimated_minutes=30,
            )
            
            # Insert at beginning and renumber
            playbook.steps.insert(0, cloud_step)
            for i, step in enumerate(playbook.steps, 1):
                step.step_number = i

    def _generate_overview(self, playbook: Playbook) -> str:
        """Generate playbook overview."""
        return (
            f"This playbook guides you through implementing {playbook.name.lower()} "
            f"for compliance with {', '.join(playbook.regulations)}. "
            f"Estimated completion time: {playbook.estimated_hours} hours."
        )

    def _generate_prerequisites(
        self,
        playbook: Playbook,
        profile: StackProfile,
    ) -> list[str]:
        """Generate prerequisites list."""
        prereqs = [
            f"Development environment with {profile.tech_stack.value} configured",
            "Access to version control system",
            "Ability to deploy changes to target environment",
        ]
        
        if profile.cloud_provider:
            prereqs.append(f"Admin access to {profile.cloud_provider.value.upper()} account")
        
        if playbook.category == PlaybookCategory.ENCRYPTION:
            prereqs.append("Understanding of cryptographic concepts")
        
        return prereqs

    async def get_playbook(self, playbook_id: UUID) -> Playbook | None:
        """Get a playbook by ID."""
        return self._playbooks.get(playbook_id)

    async def list_templates(
        self,
        category: PlaybookCategory | None = None,
        regulation: str | None = None,
    ) -> list[dict[str, Any]]:
        """List available playbook templates."""
        templates = []
        
        for slug, template in PLAYBOOK_TEMPLATES.items():
            if category and template.get("category") != category:
                continue
            if regulation and regulation not in template.get("regulations", []):
                continue
            
            templates.append({
                "slug": slug,
                "name": template["name"],
                "category": template["category"].value,
                "regulations": template.get("regulations", []),
                "difficulty": template.get("difficulty", StepDifficulty.MEDIUM).value,
                "estimated_hours": template.get("estimated_hours", 4),
            })
        
        return templates

    async def start_execution(
        self,
        playbook_id: UUID,
        organization_id: UUID,
    ) -> PlaybookExecution:
        """Start executing a playbook."""
        from datetime import datetime
        
        execution = PlaybookExecution(
            playbook_id=playbook_id,
            organization_id=organization_id,
            status="in_progress",
            started_at=datetime.utcnow(),
            current_step=1,
        )
        
        self._executions[execution.id] = execution
        return execution

    async def update_execution(
        self,
        execution_id: UUID,
        completed_step: int | None = None,
        skipped_step: int | None = None,
        note: str | None = None,
    ) -> PlaybookExecution | None:
        """Update execution progress."""
        execution = self._executions.get(execution_id)
        if not execution:
            return None
        
        if completed_step:
            if completed_step not in execution.completed_steps:
                execution.completed_steps.append(completed_step)
            execution.current_step = completed_step + 1
        
        if skipped_step:
            if skipped_step not in execution.skipped_steps:
                execution.skipped_steps.append(skipped_step)
            execution.current_step = skipped_step + 1
        
        if note:
            execution.step_notes[execution.current_step] = note
        
        # Check if complete
        playbook = self._playbooks.get(execution.playbook_id)
        if playbook:
            total_handled = len(execution.completed_steps) + len(execution.skipped_steps)
            if total_handled >= playbook.total_steps:
                execution.status = "completed"
                execution.completed_at = datetime.utcnow()
        
        return execution


# Global instance
_generator: PlaybookGenerator | None = None


def get_playbook_generator() -> PlaybookGenerator:
    """Get or create playbook generator."""
    global _generator
    if _generator is None:
        _generator = PlaybookGenerator()
    return _generator
