"""Agentic Compliance Autopilot Engine for autonomous remediation."""

import re
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import structlog

from app.services.autopilot.models import (
    RemediationStatus,
    RemediationPriority,
    RemediationType,
    ApprovalStatus,
    ComplianceViolation,
    RemediationAction,
    RemediationPlan,
    AutopilotConfig,
    RemediationResult,
    AutopilotSession,
    REMEDIATION_TEMPLATES,
    CODE_FIX_PATTERNS,
)

logger = structlog.get_logger()


class AutopilotEngine:
    """Engine for autonomous compliance remediation."""
    
    def __init__(self) -> None:
        self._sessions: dict[UUID, AutopilotSession] = {}
        self._plans: dict[UUID, RemediationPlan] = {}
        self._actions: dict[UUID, RemediationAction] = {}
    
    async def create_session(
        self,
        organization_id: UUID,
        name: str | None = None,
        config: AutopilotConfig | None = None,
    ) -> AutopilotSession:
        """Create a new autopilot session."""
        session = AutopilotSession(
            organization_id=organization_id,
            name=name or "Compliance Remediation Session",
            config=config or AutopilotConfig(),
        )
        
        self._sessions[session.id] = session
        return session
    
    async def get_session(self, session_id: UUID) -> AutopilotSession | None:
        """Get a session by ID."""
        return self._sessions.get(session_id)
    
    async def analyze_violations(
        self,
        session_id: UUID,
        violations: list[dict[str, Any]],
    ) -> RemediationPlan:
        """Analyze violations and generate a remediation plan."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        # Convert violations to model
        violation_models = [
            ComplianceViolation(
                rule_id=v.get("rule_id", str(uuid4())),
                rule_name=v.get("rule_name", "Unknown Rule"),
                regulation=v.get("regulation", "Unknown"),
                requirement=v.get("requirement"),
                article=v.get("article"),
                file_path=v.get("file_path"),
                line_number=v.get("line_number"),
                code_snippet=v.get("code_snippet"),
                severity=v.get("severity", "medium"),
                priority=self._determine_priority(v.get("severity", "medium")),
                description=v.get("description", "Compliance violation detected"),
                impact=v.get("impact"),
                repository_id=UUID(v["repository_id"]) if v.get("repository_id") else None,
            )
            for v in violations
        ]
        
        # Generate remediation actions
        actions = []
        for violation in violation_models:
            action = await self._generate_action(violation, session.config)
            if action:
                actions.append(action)
                self._actions[action.id] = action
        
        # Create plan
        plan = RemediationPlan(
            organization_id=session.organization_id,
            name=f"Remediation Plan - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            description=f"Auto-generated plan for {len(violation_models)} violations",
            violations=violation_models,
            actions=actions,
            total_violations=len(violation_models),
            pending_count=len(actions),
            auto_execute=session.config.auto_remediate_low_risk,
            require_all_approvals=session.config.require_approval_for_critical,
        )
        
        self._plans[plan.id] = plan
        session.plans.append(plan)
        session.total_violations += len(violation_models)
        session.total_actions += len(actions)
        session.pending_approvals = len([a for a in actions if a.requires_approval])
        
        return plan
    
    def _determine_priority(self, severity: str) -> RemediationPriority:
        """Determine remediation priority from severity."""
        severity_map = {
            "critical": RemediationPriority.CRITICAL,
            "high": RemediationPriority.HIGH,
            "medium": RemediationPriority.MEDIUM,
            "low": RemediationPriority.LOW,
        }
        return severity_map.get(severity.lower(), RemediationPriority.MEDIUM)
    
    async def _generate_action(
        self,
        violation: ComplianceViolation,
        config: AutopilotConfig,
    ) -> RemediationAction | None:
        """Generate a remediation action for a violation."""
        # Determine action type based on violation
        action_type = self._determine_action_type(violation)
        
        # Get template
        template_key = self._get_template_key(violation)
        template = REMEDIATION_TEMPLATES.get(template_key, {})
        
        # Generate code fix if applicable
        fixed_code = None
        diff = None
        if action_type == RemediationType.CODE_FIX and violation.code_snippet:
            fixed_code, diff = await self._generate_code_fix(violation)
        
        # Determine if approval is required
        requires_approval = self._requires_approval(violation, config)
        
        action = RemediationAction(
            violation_id=violation.id,
            action_type=template.get("action_type", action_type),
            title=template.get("title", f"Fix: {violation.rule_name}"),
            description=template.get("description", f"Remediate {violation.description}"),
            automated=template.get("automated", True),
            requires_approval=requires_approval,
            file_path=violation.file_path,
            original_code=violation.code_snippet,
            fixed_code=fixed_code,
            diff=diff,
            validation_steps=template.get("validation_steps", [
                "Run compliance scan to verify fix",
                "Run existing tests to ensure no regression",
            ]),
            rollback_steps=template.get("rollback_steps", [
                "Revert the code change",
                "Restore original configuration",
            ]),
            approval_status=(
                ApprovalStatus.PENDING if requires_approval
                else ApprovalStatus.NOT_REQUIRED
            ),
            branch_name=self._generate_branch_name(violation, config),
        )
        
        return action
    
    def _determine_action_type(self, violation: ComplianceViolation) -> RemediationType:
        """Determine the type of remediation action needed."""
        rule_lower = violation.rule_name.lower()
        desc_lower = violation.description.lower()
        
        if any(kw in rule_lower or kw in desc_lower for kw in ["encrypt", "cipher", "aes"]):
            return RemediationType.ENCRYPTION
        if any(kw in rule_lower or kw in desc_lower for kw in ["log", "audit", "trace"]):
            return RemediationType.LOGGING
        if any(kw in rule_lower or kw in desc_lower for kw in ["access", "permission", "role", "auth"]):
            return RemediationType.ACCESS_CONTROL
        if any(kw in rule_lower or kw in desc_lower for kw in ["pii", "personal", "data", "gdpr"]):
            return RemediationType.DATA_HANDLING
        if any(kw in rule_lower or kw in desc_lower for kw in ["vulnerability", "cve", "dependency"]):
            return RemediationType.DEPENDENCY_UPDATE
        if any(kw in rule_lower or kw in desc_lower for kw in ["config", "setting"]):
            return RemediationType.CONFIG_CHANGE
        if any(kw in rule_lower or kw in desc_lower for kw in ["document", "policy", "readme"]):
            return RemediationType.DOCUMENTATION
        
        return RemediationType.CODE_FIX
    
    def _get_template_key(self, violation: ComplianceViolation) -> str:
        """Get the template key for a violation."""
        rule_lower = violation.rule_name.lower()
        desc_lower = violation.description.lower()
        
        if "missing" in desc_lower and "encrypt" in desc_lower:
            return "missing_encryption"
        if "weak" in desc_lower and "encrypt" in desc_lower:
            return "weak_encryption"
        if "missing" in desc_lower and ("log" in desc_lower or "audit" in desc_lower):
            return "missing_audit_logging"
        if "permission" in desc_lower or "access" in desc_lower:
            return "overly_permissive_access"
        if "pii" in desc_lower or "exposure" in desc_lower:
            return "pii_exposure"
        if "consent" in desc_lower:
            return "missing_consent_check"
        if "vulnerab" in desc_lower or "cve" in desc_lower:
            return "vulnerable_dependency"
        if "privacy policy" in desc_lower:
            return "missing_privacy_policy"
        if "config" in desc_lower and ("insecure" in desc_lower or "unsafe" in desc_lower):
            return "insecure_configuration"
        
        return "generic_fix"
    
    async def _generate_code_fix(
        self,
        violation: ComplianceViolation,
    ) -> tuple[str | None, str | None]:
        """Generate a code fix for a violation."""
        if not violation.code_snippet:
            return None, None
        
        original = violation.code_snippet
        fixed = original
        
        # Try to apply known fix patterns
        for pattern_name, pattern_config in CODE_FIX_PATTERNS.items():
            if re.search(pattern_config["pattern"], original, re.IGNORECASE):
                # Apply the fix template
                fixed = self._apply_fix_pattern(original, pattern_config)
                break
        
        # Generate diff if changes were made
        if fixed != original:
            diff = self._generate_diff(original, fixed, violation.file_path)
            return fixed, diff
        
        # Return suggested fix based on violation type
        suggested_fix = self._suggest_fix(violation)
        if suggested_fix:
            diff = self._generate_diff(original, suggested_fix, violation.file_path)
            return suggested_fix, diff
        
        return None, None
    
    def _apply_fix_pattern(
        self,
        original: str,
        pattern_config: dict[str, str],
    ) -> str:
        """Apply a fix pattern to code."""
        # Simple replacement for now
        return pattern_config.get("fix_template", original)
    
    def _suggest_fix(self, violation: ComplianceViolation) -> str | None:
        """Suggest a code fix based on violation type."""
        desc_lower = violation.description.lower()
        
        if "hardcoded" in desc_lower and "secret" in desc_lower:
            return "# TODO: Move secret to environment variable or secrets manager\n" + \
                   "# import os\n# secret = os.environ.get('SECRET_NAME')"
        
        if "sql injection" in desc_lower:
            return "# Use parameterized queries to prevent SQL injection\n" + \
                   "# cursor.execute('SELECT * FROM table WHERE id = ?', (user_id,))"
        
        if "logging" in desc_lower and "pii" in desc_lower:
            return "# Redact PII before logging\n" + \
                   "# logger.info('User action performed', extra={'user_id': user_id})"
        
        return None
    
    def _generate_diff(
        self,
        original: str,
        fixed: str,
        file_path: str | None,
    ) -> str:
        """Generate a simple diff between original and fixed code."""
        lines = [
            f"--- a/{file_path or 'file'}" if file_path else "--- a/original",
            f"+++ b/{file_path or 'file'}" if file_path else "+++ b/fixed",
            "@@ -1,{} +1,{} @@".format(
                len(original.split('\n')),
                len(fixed.split('\n'))
            ),
        ]
        
        for line in original.split('\n'):
            lines.append(f"-{line}")
        for line in fixed.split('\n'):
            lines.append(f"+{line}")
        
        return '\n'.join(lines)
    
    def _requires_approval(
        self,
        violation: ComplianceViolation,
        config: AutopilotConfig,
    ) -> bool:
        """Determine if an action requires approval."""
        # Critical always requires approval
        if violation.severity == "critical" and config.require_approval_for_critical:
            return True
        
        # Low severity might not need approval
        if violation.severity == "low" and config.auto_remediate_low_risk:
            return False
        
        # Code changes usually require approval
        if config.require_approval_for_code_changes:
            return True
        
        return True  # Default to requiring approval
    
    def _generate_branch_name(
        self,
        violation: ComplianceViolation,
        config: AutopilotConfig,
    ) -> str:
        """Generate a branch name for the fix."""
        prefix = config.pr_branch_prefix
        rule_slug = re.sub(r'[^a-z0-9]+', '-', violation.rule_name.lower())[:30]
        timestamp = datetime.utcnow().strftime('%Y%m%d-%H%M')
        return f"{prefix}{rule_slug}-{timestamp}"
    
    async def approve_action(
        self,
        action_id: UUID,
        approver: str,
    ) -> RemediationAction | None:
        """Approve a remediation action."""
        action = self._actions.get(action_id)
        if not action:
            return None
        
        action.approval_status = ApprovalStatus.APPROVED
        action.approved_by = approver
        action.approved_at = datetime.utcnow()
        action.status = RemediationStatus.APPROVED
        
        return action
    
    async def reject_action(
        self,
        action_id: UUID,
        rejector: str,
        reason: str,
    ) -> RemediationAction | None:
        """Reject a remediation action."""
        action = self._actions.get(action_id)
        if not action:
            return None
        
        action.approval_status = ApprovalStatus.REJECTED
        action.rejection_reason = reason
        action.status = RemediationStatus.SKIPPED
        
        return action
    
    async def execute_action(
        self,
        action_id: UUID,
    ) -> RemediationResult:
        """Execute a remediation action."""
        action = self._actions.get(action_id)
        if not action:
            raise ValueError(f"Action not found: {action_id}")
        
        if action.requires_approval and action.approval_status != ApprovalStatus.APPROVED:
            return RemediationResult(
                action_id=action_id,
                success=False,
                error="Action requires approval before execution",
            )
        
        start_time = datetime.utcnow()
        action.status = RemediationStatus.IN_PROGRESS
        action.started_at = start_time
        
        try:
            # Simulate execution based on action type
            result = await self._execute_action_impl(action)
            
            action.status = RemediationStatus.COMPLETED
            action.completed_at = datetime.utcnow()
            
            return result
            
        except Exception as e:
            action.status = RemediationStatus.FAILED
            action.error_message = str(e)
            action.completed_at = datetime.utcnow()
            
            return RemediationResult(
                action_id=action_id,
                success=False,
                error=str(e),
                execution_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
            )
    
    async def _execute_action_impl(
        self,
        action: RemediationAction,
    ) -> RemediationResult:
        """Implementation of action execution (simulated)."""
        start_time = datetime.utcnow()
        
        files_modified = []
        pr_created = False
        pr_url = None
        
        if action.action_type == RemediationType.CODE_FIX:
            if action.file_path and action.fixed_code:
                files_modified.append(action.file_path)
                pr_created = True
                pr_url = f"https://github.com/org/repo/pull/{action.pr_number or 999}"
        
        elif action.action_type == RemediationType.CONFIG_CHANGE:
            if action.config_path:
                files_modified.append(action.config_path)
        
        elif action.action_type == RemediationType.DEPENDENCY_UPDATE:
            files_modified.append("package.json")  # or requirements.txt, etc.
            pr_created = True
            pr_url = f"https://github.com/org/repo/pull/{action.pr_number or 999}"
        
        action.pr_url = pr_url
        
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return RemediationResult(
            action_id=action.id,
            success=True,
            execution_time_ms=execution_time,
            files_modified=files_modified,
            pr_created=pr_created,
            pr_url=pr_url,
            validation_passed=True,
            validation_output="Compliance scan passed after fix",
        )
    
    async def execute_plan(
        self,
        plan_id: UUID,
        execute_approved_only: bool = True,
    ) -> list[RemediationResult]:
        """Execute all actions in a plan."""
        plan = self._plans.get(plan_id)
        if not plan:
            raise ValueError(f"Plan not found: {plan_id}")
        
        results = []
        plan.status = RemediationStatus.IN_PROGRESS
        
        for action in plan.actions:
            if execute_approved_only:
                if action.approval_status != ApprovalStatus.APPROVED:
                    if action.requires_approval:
                        continue
            
            result = await self.execute_action(action.id)
            results.append(result)
            
            if result.success:
                plan.remediated_count += 1
            else:
                plan.failed_count += 1
        
        plan.pending_count = len([
            a for a in plan.actions
            if a.status == RemediationStatus.PENDING
        ])
        
        if plan.pending_count == 0:
            plan.status = RemediationStatus.COMPLETED
        
        plan.updated_at = datetime.utcnow()
        
        return results
    
    async def rollback_action(
        self,
        action_id: UUID,
    ) -> RemediationResult:
        """Rollback a completed action."""
        action = self._actions.get(action_id)
        if not action:
            raise ValueError(f"Action not found: {action_id}")
        
        if action.status != RemediationStatus.COMPLETED:
            return RemediationResult(
                action_id=action_id,
                success=False,
                error="Can only rollback completed actions",
            )
        
        # Execute rollback steps (simulated)
        action.status = RemediationStatus.ROLLED_BACK
        
        return RemediationResult(
            action_id=action_id,
            success=True,
            rollback_performed=True,
        )
    
    async def get_plan(self, plan_id: UUID) -> RemediationPlan | None:
        """Get a remediation plan by ID."""
        return self._plans.get(plan_id)
    
    async def get_action(self, action_id: UUID) -> RemediationAction | None:
        """Get a remediation action by ID."""
        return self._actions.get(action_id)
    
    async def get_pending_approvals(
        self,
        organization_id: UUID,
    ) -> list[RemediationAction]:
        """Get all pending approval actions for an organization."""
        pending = []
        
        for session in self._sessions.values():
            if session.organization_id != organization_id:
                continue
            
            for plan in session.plans:
                for action in plan.actions:
                    if action.approval_status == ApprovalStatus.PENDING:
                        pending.append(action)
        
        return pending


# Singleton instance
_engine_instance: AutopilotEngine | None = None


def get_autopilot_engine() -> AutopilotEngine:
    """Get or create the autopilot engine singleton."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = AutopilotEngine()
    return _engine_instance
