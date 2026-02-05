"""Compliance Co-Pilot IDE Agent - Agentic AI for proactive code compliance."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.copilot import CopilotClient, get_copilot_client
from app.services.ide_agent.models import (
    AgentAction,
    AgentActionType,
    AgentConfig,
    AgentSession,
    AgentStatus,
    AgentTriggerType,
    CodeLocation,
    ComplianceViolation,
    FixConfidence,
    ProposedFix,
    RefactorPlan,
)


logger = structlog.get_logger()


class IDEAgentService:
    """Service for the Compliance Co-Pilot IDE Agent.

    This agent proactively analyzes code for compliance violations and
    generates fixes with multi-step reasoning.
    """

    def __init__(
        self,
        db: AsyncSession,
        organization_id: UUID,
        copilot: CopilotClient | None = None,
    ):
        self.db = db
        self.organization_id = organization_id
        self._copilot = copilot
        self._sessions: dict[UUID, AgentSession] = {}
        self._configs: dict[UUID, AgentConfig] = {}

    async def get_copilot(self) -> CopilotClient:
        """Get or create Copilot client."""
        if self._copilot is None:
            self._copilot = await get_copilot_client()
        return self._copilot

    def get_config(self, organization_id: UUID) -> AgentConfig:
        """Get agent configuration for organization."""
        if organization_id not in self._configs:
            self._configs[organization_id] = AgentConfig(organization_id=organization_id)
        return self._configs[organization_id]

    def update_config(self, organization_id: UUID, updates: dict[str, Any]) -> AgentConfig:
        """Update agent configuration."""
        config = self.get_config(organization_id)

        for key, value in updates.items():
            if hasattr(config, key):
                if key == "enabled_triggers":
                    value = [AgentTriggerType(t) for t in value]
                setattr(config, key, value)

        return config

    async def start_session(
        self,
        trigger_type: AgentTriggerType,
        trigger_context: dict[str, Any],
        user_id: UUID | None = None,
        repository_id: UUID | None = None,
    ) -> AgentSession:
        """Start a new agent session."""
        session = AgentSession(
            organization_id=self.organization_id,
            user_id=user_id,
            repository_id=repository_id,
            trigger_type=trigger_type,
            trigger_context=trigger_context,
            status=AgentStatus.ANALYZING,
        )

        self._sessions[session.id] = session

        logger.info(
            "IDE Agent session started",
            session_id=str(session.id),
            organization_id=str(self.organization_id),
            trigger_type=trigger_type.value,
        )

        return session

    def get_session(self, session_id: UUID) -> AgentSession | None:
        """Get an agent session by ID."""
        return self._sessions.get(session_id)

    def list_sessions(
        self,
        status: AgentStatus | None = None,
        limit: int = 50,
    ) -> list[AgentSession]:
        """List agent sessions."""
        sessions = list(self._sessions.values())

        if status:
            sessions = [s for s in sessions if s.status == status]

        # Sort by started_at descending
        sessions.sort(key=lambda s: s.started_at, reverse=True)

        return sessions[:limit]

    async def analyze_code(
        self,
        session: AgentSession,
        code: str,
        file_path: str,
        language: str = "python",
        regulations: list[str] | None = None,
    ) -> list[ComplianceViolation]:
        """Analyze code for compliance violations."""
        session.status = AgentStatus.ANALYZING
        session.current_step = "Analyzing code for compliance violations"

        config = self.get_config(self.organization_id)
        active_regulations = regulations or config.enabled_regulations

        copilot = await self.get_copilot()

        violations = []

        try:
            async with copilot:
                # Use Copilot to analyze code
                analysis_prompt = f"""Analyze the following {language} code for compliance violations.

Regulations to check: {', '.join(active_regulations)}

Code:
```{language}
{code}
```

For each violation found, provide:
1. Rule ID (e.g., GDPR-PII-001)
2. Rule name
3. Regulation name
4. Article reference (if applicable)
5. Severity (error, warning, info)
6. Message explaining the violation
7. Line numbers affected
8. Confidence score (0.0-1.0)

Format as JSON array."""

                result = await copilot.complete(
                    prompt=analysis_prompt,
                    system_prompt="You are a compliance analysis expert. Identify potential compliance violations in code.",
                    max_tokens=2000,
                )

                # Parse violations from response
                violations = self._parse_violations(result.get("text", ""), code, file_path)

        except Exception as e:
            logger.exception("Error analyzing code", error=str(e))
            session.status = AgentStatus.FAILED
            session.error_message = str(e)
            return []

        session.violations_found = len(violations)
        session.progress = 30.0

        # Create analysis action
        action = AgentAction(
            action_type=AgentActionType.ANALYZE,
            description=f"Analyzed {file_path} for compliance violations",
            target_files=[file_path],
            violations=violations,
            requires_approval=False,
            executed=True,
        )
        session.actions.append(action)

        return violations

    def _parse_violations(
        self,
        response: str,
        code: str,
        file_path: str,
    ) -> list[ComplianceViolation]:
        """Parse violations from Copilot response."""
        violations = []

        # Try to parse JSON from response
        import json
        import re

        # Find JSON array in response
        json_match = re.search(r'\[[\s\S]*\]', response)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                for v in parsed:
                    location = None
                    if "start_line" in v:
                        location = CodeLocation(
                            file_path=file_path,
                            start_line=v.get("start_line", 1),
                            end_line=v.get("end_line", v.get("start_line", 1)),
                        )

                    violations.append(ComplianceViolation(
                        rule_id=v.get("rule_id", "UNKNOWN"),
                        rule_name=v.get("rule_name", "Unknown Rule"),
                        regulation=v.get("regulation", "Unknown"),
                        article_reference=v.get("article_reference"),
                        severity=v.get("severity", "warning"),
                        message=v.get("message", "Compliance violation detected"),
                        location=location,
                        original_code=self._extract_code_segment(code, location),
                        confidence=v.get("confidence", 0.5),
                    ))
            except json.JSONDecodeError:
                logger.warning("Failed to parse violations JSON")

        return violations

    def _extract_code_segment(
        self,
        code: str,
        location: CodeLocation | None,
    ) -> str:
        """Extract code segment from location."""
        if not location:
            return ""

        lines = code.split("\n")
        start = max(0, location.start_line - 1)
        end = min(len(lines), location.end_line)
        return "\n".join(lines[start:end])

    async def generate_fixes(
        self,
        session: AgentSession,
        violations: list[ComplianceViolation],
        code: str,
        language: str = "python",
    ) -> list[ProposedFix]:
        """Generate fixes for violations."""
        session.status = AgentStatus.PLANNING
        session.current_step = "Generating compliance fixes"

        if not violations:
            return []

        copilot = await self.get_copilot()
        fixes = []

        try:
            async with copilot:
                for violation in violations:
                    fix_prompt = f"""Generate a fix for this compliance violation.

Violation:
- Rule: {violation.rule_id} ({violation.rule_name})
- Regulation: {violation.regulation}
- Message: {violation.message}
- Severity: {violation.severity}

Original code:
```{language}
{violation.original_code or code}
```

Provide:
1. Fixed code
2. Explanation of the fix
3. Any imports needed
4. Whether this is a breaking change
5. Suggested tests

Format as JSON."""

                    result = await copilot.complete(
                        prompt=fix_prompt,
                        system_prompt="You are a compliance remediation expert. Generate secure, compliant code fixes.",
                        max_tokens=1500,
                    )

                    fix = self._parse_fix(result.get("text", ""), violation)
                    if fix:
                        fixes.append(fix)

        except Exception as e:
            logger.exception("Error generating fixes", error=str(e))
            session.error_message = str(e)

        session.progress = 60.0

        return fixes

    def _parse_fix(
        self,
        response: str,
        violation: ComplianceViolation,
    ) -> ProposedFix | None:
        """Parse fix from Copilot response."""
        import json
        import re

        # Find JSON in response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                confidence_score = parsed.get("confidence", violation.confidence)

                # Determine confidence level
                if confidence_score >= 0.9:
                    confidence = FixConfidence.HIGH
                elif confidence_score >= 0.7:
                    confidence = FixConfidence.MEDIUM
                else:
                    confidence = FixConfidence.LOW

                return ProposedFix(
                    violation_id=violation.id,
                    fixed_code=parsed.get("fixed_code", ""),
                    explanation=parsed.get("explanation", ""),
                    confidence=confidence,
                    confidence_score=confidence_score,
                    imports_to_add=parsed.get("imports", []),
                    breaking_changes=parsed.get("breaking_change", False),
                    test_suggestions=parsed.get("tests", []),
                )
            except json.JSONDecodeError:
                logger.warning("Failed to parse fix JSON")

        return None

    async def create_refactor_plan(
        self,
        session: AgentSession,
        violations: list[ComplianceViolation],
        fixes: list[ProposedFix],
    ) -> RefactorPlan:
        """Create a refactoring plan from violations and fixes."""
        session.current_step = "Creating refactor plan"

        plan = RefactorPlan(session_id=session.id)

        # Group by file
        file_violations: dict[str, list[ComplianceViolation]] = {}
        for v in violations:
            if v.location:
                path = v.location.file_path
                if path not in file_violations:
                    file_violations[path] = []
                file_violations[path].append(v)

        # Map fixes to files
        fix_by_violation: dict[UUID, ProposedFix] = {f.violation_id: f for f in fixes if f.violation_id}

        for path, path_violations in file_violations.items():
            plan.changes_by_file[path] = []
            for v in path_violations:
                if v.id in fix_by_violation:
                    plan.changes_by_file[path].append(fix_by_violation[v.id])

        # Group by regulation
        for v in violations:
            if v.regulation not in plan.changes_by_regulation:
                plan.changes_by_regulation[v.regulation] = []
            if v.id in fix_by_violation:
                plan.changes_by_regulation[v.regulation].append(fix_by_violation[v.id])

        # Set counts
        plan.total_violations = len(violations)
        plan.fixable_violations = len(fixes)
        plan.manual_review_required = len(violations) - len(fixes)

        # Determine execution order (files with most violations first)
        plan.execution_order = sorted(
            plan.changes_by_file.keys(),
            key=lambda p: len(plan.changes_by_file[p]),
            reverse=True,
        )

        # Check for breaking changes
        plan.breaking_change_risk = any(f.breaking_changes for f in fixes)

        # Estimate impact
        if len(fixes) > 10 or plan.breaking_change_risk:
            plan.estimated_impact = "high"
        elif len(fixes) > 3:
            plan.estimated_impact = "medium"
        else:
            plan.estimated_impact = "low"

        # Generate diff preview
        plan.diff_preview = self._generate_diff_preview(fixes)

        session.progress = 80.0

        return plan

    def _generate_diff_preview(self, fixes: list[ProposedFix]) -> str:
        """Generate a unified diff preview of all fixes."""
        diff_lines = []
        for fix in fixes[:5]:  # Limit to first 5 for preview
            diff_lines.append(f"--- Fix for violation {fix.violation_id}")
            diff_lines.append(f"+++ {fix.explanation[:50]}...")
            if fix.fixed_code:
                for line in fix.fixed_code.split("\n")[:10]:
                    diff_lines.append(f"+ {line}")
            diff_lines.append("")

        if len(fixes) > 5:
            diff_lines.append(f"... and {len(fixes) - 5} more fixes")

        return "\n".join(diff_lines)

    async def apply_fixes(
        self,
        session: AgentSession,
        fixes: list[ProposedFix],
        dry_run: bool = True,
    ) -> dict[str, Any]:
        """Apply fixes to code (or simulate in dry run)."""
        session.status = AgentStatus.EXECUTING
        session.current_step = "Applying fixes"

        config = self.get_config(self.organization_id)
        results = {
            "dry_run": dry_run,
            "fixes_applied": 0,
            "fixes_skipped": 0,
            "errors": [],
            "applied_fixes": [],
        }

        for fix in fixes:
            # Check confidence threshold for auto-apply
            if not dry_run and config.auto_fix_enabled:
                if fix.confidence_score < config.auto_fix_confidence_threshold:
                    results["fixes_skipped"] += 1
                    continue

            if dry_run:
                # In dry run, just report what would happen
                results["applied_fixes"].append({
                    "fix_id": str(fix.id),
                    "violation_id": str(fix.violation_id),
                    "confidence": fix.confidence.value,
                    "would_apply": True,
                })
            else:
                # Actually apply the fix
                # In a real implementation, this would write to files
                results["applied_fixes"].append({
                    "fix_id": str(fix.id),
                    "violation_id": str(fix.violation_id),
                    "applied": True,
                })

            results["fixes_applied"] += 1

        session.fixes_applied = results["fixes_applied"]
        session.progress = 100.0
        session.status = AgentStatus.COMPLETED
        session.completed_at = datetime.now(UTC)

        # Create action for fixes
        action = AgentAction(
            action_type=AgentActionType.REFACTOR if not dry_run else AgentActionType.SUGGEST_FIX,
            description=f"{'Applied' if not dry_run else 'Proposed'} {results['fixes_applied']} fixes",
            proposed_fixes=fixes,
            requires_approval=config.require_approval_for_refactor and not dry_run,
            executed=not dry_run,
            result=results,
        )
        session.actions.append(action)

        logger.info(
            "Fixes applied",
            session_id=str(session.id),
            dry_run=dry_run,
            fixes_applied=results["fixes_applied"],
        )

        return results

    async def run_full_analysis(
        self,
        code: str,
        file_path: str,
        language: str = "python",
        trigger_type: AgentTriggerType = AgentTriggerType.MANUAL,
        user_id: UUID | None = None,
        repository_id: UUID | None = None,
        auto_fix: bool = False,
    ) -> AgentSession:
        """Run a full analysis and fix generation pipeline."""
        # Start session
        session = await self.start_session(
            trigger_type=trigger_type,
            trigger_context={
                "file_path": file_path,
                "language": language,
                "code_length": len(code),
            },
            user_id=user_id,
            repository_id=repository_id,
        )

        try:
            # Analyze code
            violations = await self.analyze_code(
                session=session,
                code=code,
                file_path=file_path,
                language=language,
            )

            if not violations:
                session.status = AgentStatus.COMPLETED
                session.completed_at = datetime.now(UTC)
                session.current_step = "No violations found"
                session.progress = 100.0
                return session

            # Generate fixes
            fixes = await self.generate_fixes(
                session=session,
                violations=violations,
                code=code,
                language=language,
            )

            # Create refactor plan
            plan = await self.create_refactor_plan(
                session=session,
                violations=violations,
                fixes=fixes,
            )

            # Apply fixes if requested
            config = self.get_config(self.organization_id)
            if auto_fix and config.auto_fix_enabled:
                await self.apply_fixes(
                    session=session,
                    fixes=fixes,
                    dry_run=False,
                )
            else:
                # Do a dry run to show what would be fixed
                await self.apply_fixes(
                    session=session,
                    fixes=fixes,
                    dry_run=True,
                )

                # Wait for approval if fixes are pending
                if fixes and config.require_approval_for_refactor:
                    session.status = AgentStatus.WAITING_APPROVAL
                    session.pending_approval_count = len(fixes)

        except Exception as e:
            session.status = AgentStatus.FAILED
            session.error_message = str(e)
            logger.exception("Agent session failed", session_id=str(session.id), error=str(e))

        return session

    async def approve_action(
        self,
        session_id: UUID,
        action_id: UUID,
    ) -> AgentAction | None:
        """Approve a pending action."""
        session = self.get_session(session_id)
        if not session:
            return None

        for action in session.actions:
            if action.id == action_id and action.requires_approval and not action.approved:
                action.approved = True
                session.pending_approval_count = max(0, session.pending_approval_count - 1)

                # Execute the action if it was waiting
                if action.action_type == AgentActionType.REFACTOR:
                    action.executed = True
                    action.executed_at = datetime.now(UTC)
                    session.fixes_applied += len(action.proposed_fixes)

                logger.info(
                    "Action approved",
                    session_id=str(session_id),
                    action_id=str(action_id),
                )
                return action

        return None

    async def reject_action(
        self,
        session_id: UUID,
        action_id: UUID,
        reason: str = "",
    ) -> AgentAction | None:
        """Reject a pending action."""
        session = self.get_session(session_id)
        if not session:
            return None

        for action in session.actions:
            if action.id == action_id and action.requires_approval:
                action.result["rejected"] = True
                action.result["rejection_reason"] = reason
                session.pending_approval_count = max(0, session.pending_approval_count - 1)

                logger.info(
                    "Action rejected",
                    session_id=str(session_id),
                    action_id=str(action_id),
                    reason=reason,
                )
                return action

        return None

    def cancel_session(self, session_id: UUID) -> AgentSession | None:
        """Cancel an active session."""
        session = self.get_session(session_id)
        if session and session.status not in [AgentStatus.COMPLETED, AgentStatus.FAILED]:
            session.status = AgentStatus.CANCELLED
            session.completed_at = datetime.now(UTC)
            logger.info("Session cancelled", session_id=str(session_id))
            return session
        return None


def get_ide_agent_service(
    db: AsyncSession,
    organization_id: UUID,
) -> IDEAgentService:
    """Factory function to create IDE Agent service."""
    return IDEAgentService(db=db, organization_id=organization_id)
