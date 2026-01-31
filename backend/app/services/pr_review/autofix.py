"""Auto-Fix Generator - Phase 3: Generate and apply auto-fixes for compliance violations."""

import re
import time
from typing import Any
from uuid import uuid4

import structlog

from app.agents.copilot import CopilotClient, CopilotMessage
from app.services.github.client import GitHubClient
from app.services.pr_review.models import (
    AutoFix,
    AutoFixStatus,
    ComplianceViolation,
    PRReviewResult,
    ViolationSeverity,
)


logger = structlog.get_logger()


# Pre-built fix templates for common patterns
FIX_TEMPLATES = {
    "GDPR-CONSENT_MISSING": {
        "python": '''# GDPR Compliance: Verify consent before processing
if not user.has_consent("{data_type}_processing"):
    raise ConsentRequiredError("User consent required for {data_type} processing")
{original_code}''',
        "javascript": '''// GDPR Compliance: Verify consent before processing
if (!user.hasConsent("{data_type}_processing")) {{
    throw new ConsentRequiredError("User consent required for {data_type} processing");
}}
{original_code}''',
        "typescript": '''// GDPR Compliance: Verify consent before processing
if (!user.hasConsent("{data_type}_processing")) {{
    throw new ConsentRequiredError("User consent required for {data_type} processing");
}}
{original_code}''',
    },
    "SEC-HARDCODED_SECRETS": {
        "python": '''# Security: Use environment variable instead of hardcoded secret
import os
{var_name} = os.environ.get("{env_var_name}")
if not {var_name}:
    raise ValueError("{env_var_name} environment variable not set")''',
        "javascript": '''// Security: Use environment variable instead of hardcoded secret
const {var_name} = process.env.{env_var_name};
if (!{var_name}) {{
    throw new Error("{env_var_name} environment variable not set");
}}''',
        "typescript": '''// Security: Use environment variable instead of hardcoded secret
const {var_name} = process.env.{env_var_name};
if (!{var_name}) {{
    throw new Error("{env_var_name} environment variable not set");
}}''',
    },
    "SEC-SQL_INJECTION": {
        "python": '''# Security: Use parameterized query to prevent SQL injection
cursor.execute(
    "{query_template}",
    ({params})
)''',
        "javascript": '''// Security: Use parameterized query to prevent SQL injection
await db.query(
    "{query_template}",
    [{params}]
);''',
    },
    "PCI-DSS-PAYMENT_LOGGING": {
        "python": '''# PCI-DSS: Mask sensitive payment data in logs
from app.utils.masking import mask_card_data
logger.info(f"Processing payment: {{mask_card_data(card_data)}}")''',
        "javascript": '''// PCI-DSS: Mask sensitive payment data in logs
const {{ maskCardData }} = require("./utils/masking");
console.log(`Processing payment: ${{maskCardData(cardData)}}`);''',
    },
    "EUAI-AI_DECISION_MAKING": {
        "python": '''# EU AI Act: Add human oversight for automated decisions
from app.compliance.ai import require_human_review

@require_human_review(decision_type="{decision_type}")
def {function_name}({params}):
    {original_code}
    # Flag for human review if confidence below threshold
    if confidence < 0.95:
        return await request_human_review(result, context)
    return result''',
    },
}


class AutoFixGenerator:
    """Generates and manages auto-fixes for compliance violations."""

    def __init__(
        self,
        copilot_client: CopilotClient | None = None,
        github_client: GitHubClient | None = None,
    ):
        self.copilot_client = copilot_client
        self.github_client = github_client

    async def generate_fixes(
        self,
        review: PRReviewResult,
        file_contents: dict[str, str] | None = None,
    ) -> list[AutoFix]:
        """Generate auto-fixes for all fixable violations in a review.
        
        Args:
            review: The PR review result with violations
            file_contents: Optional dict of file_path -> content for context
            
        Returns:
            List of generated AutoFix objects
        """
        if not review.analysis:
            return []
        
        fixes: list[AutoFix] = []
        
        for violation in review.analysis.violations:
            # Skip info-level violations
            if violation.severity == ViolationSeverity.INFO:
                continue
            
            fix = await self.generate_fix(
                violation=violation,
                file_content=file_contents.get(violation.file_path) if file_contents else None,
            )
            
            if fix:
                fixes.append(fix)
        
        return fixes

    async def generate_fix(
        self,
        violation: ComplianceViolation,
        file_content: str | None = None,
    ) -> AutoFix | None:
        """Generate an auto-fix for a single violation.
        
        Args:
            violation: The compliance violation to fix
            file_content: Optional file content for context
            
        Returns:
            AutoFix if generation successful, None otherwise
        """
        start_time = time.perf_counter()
        
        # Try template-based fix first
        template_fix = self._try_template_fix(violation)
        if template_fix:
            return template_fix
        
        # Fall back to AI-generated fix
        if self.copilot_client:
            ai_fix = await self._generate_ai_fix(violation, file_content)
            if ai_fix:
                ai_fix.metadata = {"generation_method": "ai", "time_ms": (time.perf_counter() - start_time) * 1000}
                return ai_fix
        
        return None

    def _try_template_fix(self, violation: ComplianceViolation) -> AutoFix | None:
        """Try to generate a fix using pre-built templates."""
        language = violation.metadata.get("language", "python")
        
        # Find matching template
        template_key = violation.code.replace("-", "_").upper()
        template = FIX_TEMPLATES.get(template_key, {}).get(language)
        
        if not template:
            # Try partial match
            for key, lang_templates in FIX_TEMPLATES.items():
                if key.split("-")[0] in violation.code:
                    template = lang_templates.get(language)
                    if template:
                        break
        
        if not template:
            return None
        
        # Extract variables for template
        original_code = violation.metadata.get("line_content", "# TODO: Add compliant code")
        evidence = violation.evidence or ""
        
        # Parse variable names from evidence
        var_name = self._extract_variable_name(evidence)
        
        try:
            fixed_code = template.format(
                original_code=original_code,
                var_name=var_name,
                env_var_name=var_name.upper() if var_name else "SECRET_KEY",
                data_type=violation.category or "data",
                decision_type=violation.category or "automated_decision",
                function_name="process_data",
                params="*args, **kwargs",
                query_template="SELECT * FROM users WHERE id = ?",
            )
        except KeyError:
            # Template has variables we couldn't fill
            return None
        
        return AutoFix(
            violation_id=violation.id,
            file_path=violation.file_path,
            original_code=original_code,
            fixed_code=fixed_code,
            diff=self._generate_diff(original_code, fixed_code),
            description=f"Template-based fix for {violation.code}: {violation.message[:100]}",
            confidence=0.75,
            status=AutoFixStatus.GENERATED,
        )

    async def _generate_ai_fix(
        self,
        violation: ComplianceViolation,
        file_content: str | None = None,
    ) -> AutoFix | None:
        """Generate a fix using AI."""
        if not self.copilot_client:
            return None
        
        language = violation.metadata.get("language", "python")
        original_code = violation.metadata.get("line_content", "")
        
        system_prompt = f"""You are an expert {language} developer fixing compliance issues.
Generate a minimal, production-ready fix that:
1. Addresses the compliance violation
2. Follows existing code patterns
3. Includes necessary imports
4. Adds compliance comments with regulation references

Return JSON only:
{{
    "fixed_code": "the corrected code",
    "imports": ["any new imports needed"],
    "explanation": "brief explanation of the fix",
    "tests": ["suggested test cases"]
}}"""

        context = f"\n\nFile context:\n```{language}\n{file_content[:2000]}\n```" if file_content else ""

        user_prompt = f"""Fix this compliance violation:

**Code:** `{original_code}`
**Violation:** {violation.code} - {violation.message}
**Regulation:** {violation.regulation or 'Security best practice'}
**Article:** {violation.article_reference or 'N/A'}

{context}

Return JSON only."""

        try:
            async with self.copilot_client:
                response = await self.copilot_client.chat(
                    messages=[CopilotMessage(role="user", content=user_prompt)],
                    system_message=system_prompt,
                    temperature=0.3,
                    max_tokens=1024,
                )
                
                result = self.copilot_client._parse_json_response(response.content, "fix generation")
                
                if isinstance(result, dict) and result.get("fixed_code"):
                    fixed_code = result["fixed_code"]
                    
                    # Add imports if needed
                    imports = result.get("imports", [])
                    if imports:
                        import_block = "\n".join(imports)
                        fixed_code = f"{import_block}\n\n{fixed_code}"
                    
                    return AutoFix(
                        violation_id=violation.id,
                        file_path=violation.file_path,
                        original_code=original_code,
                        fixed_code=fixed_code,
                        diff=self._generate_diff(original_code, fixed_code),
                        description=result.get("explanation", f"AI-generated fix for {violation.code}"),
                        confidence=0.85,
                        status=AutoFixStatus.GENERATED,
                        tests_generated=result.get("tests", []),
                    )
        except Exception as e:
            logger.warning(f"AI fix generation failed: {e}")
        
        return None

    def _extract_variable_name(self, text: str) -> str:
        """Extract a variable name from code text."""
        # Match common variable assignment patterns
        patterns = [
            r"(\w+)\s*=",  # var =
            r"const\s+(\w+)",  # const var
            r"let\s+(\w+)",  # let var
            r"var\s+(\w+)",  # var var
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return "value"

    def _generate_diff(self, original: str, fixed: str) -> str:
        """Generate a unified diff between original and fixed code."""
        original_lines = original.split("\n")
        fixed_lines = fixed.split("\n")
        
        diff_lines = ["--- original", "+++ fixed"]
        
        # Simple diff - show all original as removed, all fixed as added
        for line in original_lines:
            if line.strip():
                diff_lines.append(f"-{line}")
        
        for line in fixed_lines:
            if line.strip():
                diff_lines.append(f"+{line}")
        
        return "\n".join(diff_lines)

    async def apply_fix(
        self,
        fix: AutoFix,
        owner: str,
        repo: str,
        branch: str,
        access_token: str,
    ) -> bool:
        """Apply a fix to a repository by committing the change.
        
        Args:
            fix: The AutoFix to apply
            owner: Repository owner
            repo: Repository name
            branch: Branch to commit to
            access_token: GitHub access token
            
        Returns:
            True if fix was applied successfully
        """
        async with GitHubClient(access_token=access_token) as client:
            try:
                # Get current file content
                file_data = await client.get_file_content(owner, repo, fix.file_path, branch)
                current_content = file_data.content
                
                # Replace the original code with fixed code
                if fix.original_code in current_content:
                    new_content = current_content.replace(fix.original_code, fix.fixed_code, 1)
                else:
                    logger.warning(f"Original code not found in file, cannot apply fix")
                    return False
                
                # Commit the change
                commit_message = f"fix(compliance): {fix.description[:72]}\n\nAuto-generated compliance fix\nViolation ID: {fix.violation_id}"
                
                result = await client.create_or_update_file(
                    owner=owner,
                    repo=repo,
                    path=fix.file_path,
                    content=new_content,
                    message=commit_message,
                    branch=branch,
                    sha=file_data.sha,
                )
                
                fix.status = AutoFixStatus.APPLIED
                fix.commit_sha = result.get("commit", {}).get("sha")
                fix.applied_at = time.time()
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to apply fix: {e}")
                return False

    async def create_fix_pr(
        self,
        fixes: list[AutoFix],
        owner: str,
        repo: str,
        base_branch: str,
        access_token: str,
        pr_title: str | None = None,
    ) -> dict[str, Any] | None:
        """Create a PR with multiple fixes applied.
        
        Args:
            fixes: List of fixes to apply
            owner: Repository owner
            repo: Repository name
            base_branch: Base branch for the PR
            access_token: GitHub access token
            pr_title: Optional custom PR title
            
        Returns:
            Dict with PR info if successful
        """
        if not fixes:
            return None
        
        async with GitHubClient(access_token=access_token) as client:
            try:
                # Create a new branch for fixes
                branch_name = f"compliance-fixes-{uuid4().hex[:8]}"
                base_sha = await client.get_default_branch_sha(owner, repo)
                await client.create_branch(owner, repo, branch_name, base_sha)
                
                # Apply each fix
                applied_fixes = []
                for fix in fixes:
                    success = await self.apply_fix(fix, owner, repo, branch_name, access_token)
                    if success:
                        applied_fixes.append(fix)
                
                if not applied_fixes:
                    return None
                
                # Create PR
                title = pr_title or f"🔒 Compliance Fixes ({len(applied_fixes)} issues)"
                
                body = "## Auto-Generated Compliance Fixes\n\n"
                body += f"This PR addresses **{len(applied_fixes)}** compliance issues.\n\n"
                body += "### Fixed Issues\n\n"
                
                for fix in applied_fixes:
                    body += f"- **{fix.file_path}**: {fix.description}\n"
                
                body += "\n### Review Checklist\n"
                body += "- [ ] Review each fix for correctness\n"
                body += "- [ ] Ensure tests pass\n"
                body += "- [ ] Verify compliance requirements are met\n"
                body += "\n<sub>Generated by ComplianceAgent</sub>"
                
                pr = await client.create_pull_request(
                    owner=owner,
                    repo=repo,
                    title=title,
                    body=body,
                    head=branch_name,
                    base=base_branch,
                    draft=True,  # Create as draft for review
                )
                
                # Add labels
                await client.add_labels_to_pr(owner, repo, pr.number, ["compliance", "auto-fix"])
                
                return {
                    "pr_number": pr.number,
                    "pr_url": pr.html_url,
                    "branch": branch_name,
                    "fixes_applied": len(applied_fixes),
                }
                
            except Exception as e:
                logger.error(f"Failed to create fix PR: {e}")
                return None

    def format_fix_suggestion(self, fix: AutoFix) -> str:
        """Format a fix as a suggestion block for GitHub comments."""
        return f"""<details>
<summary>💡 Suggested Fix (confidence: {fix.confidence:.0%})</summary>

**Description:** {fix.description}

```suggestion
{fix.fixed_code}
```

</details>"""

    def get_batch_fixes_summary(self, fixes: list[AutoFix]) -> dict[str, Any]:
        """Get a summary of batch fixes for reporting."""
        by_file: dict[str, list[AutoFix]] = {}
        for fix in fixes:
            by_file.setdefault(fix.file_path, []).append(fix)
        
        return {
            "total_fixes": len(fixes),
            "by_file": {path: len(file_fixes) for path, file_fixes in by_file.items()},
            "avg_confidence": sum(f.confidence for f in fixes) / len(fixes) if fixes else 0,
            "high_confidence_count": sum(1 for f in fixes if f.confidence >= 0.8),
            "statuses": {
                status.value: sum(1 for f in fixes if f.status == status)
                for status in AutoFixStatus
            },
        }
