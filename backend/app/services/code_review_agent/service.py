"""Compliance-Aware Code Review Agent Service."""

import hashlib
from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.code_review_agent.models import (
    ComplianceSuggestion,
    DiffHunk,
    PRComplianceReview,
    ReviewConfig,
    ReviewDecision,
    ReviewRiskLevel,
    ReviewStats,
    SuggestionStatus,
)


logger = structlog.get_logger()

_COMPLIANCE_PATTERNS: dict[str, list[dict]] = {
    "GDPR": [
        {"pattern": "personal_data|user_email|user_name|ip_address", "rule": "gdpr-personal-data", "article": "Art. 5", "message": "Processing personal data requires documented lawful basis"},
        {"pattern": "cookie|tracking|analytics", "rule": "gdpr-consent", "article": "Art. 6", "message": "Tracking/analytics requires user consent"},
        {"pattern": "store.*forever|no.*expir|permanent.*stor", "rule": "gdpr-retention", "article": "Art. 5(1)(e)", "message": "Data must have defined retention periods"},
    ],
    "HIPAA": [
        {"pattern": "patient|medical|diagnosis|health_record", "rule": "hipaa-phi", "article": "§164.312", "message": "PHI must be encrypted at rest and in transit"},
        {"pattern": "log.*health|print.*patient", "rule": "hipaa-logging", "article": "§164.312(b)", "message": "PHI must not appear in logs"},
    ],
    "PCI-DSS": [
        {"pattern": "card_number|credit_card|cvv|pan", "rule": "pci-card-data", "article": "Req 3", "message": "Card data must be tokenized; never store CVV"},
        {"pattern": "password.*plain|md5|sha1", "rule": "pci-crypto", "article": "Req 4", "message": "Use strong cryptography (AES-256, SHA-256+)"},
    ],
    "SOC2": [
        {"pattern": "admin.*password|root.*access|sudo", "rule": "soc2-access", "article": "CC6.1", "message": "Administrative access requires MFA and audit logging"},
    ],
}


class CodeReviewAgentService:
    """Compliance-aware code review agent for PR analysis."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._reviews: list[PRComplianceReview] = []
        self._config = ReviewConfig()

    async def analyze_pr(
        self,
        repo: str,
        pr_number: int,
        commit_sha: str = "",
        diff_content: str = "",
        changed_files: list[dict] | None = None,
    ) -> PRComplianceReview:
        start = datetime.now(UTC)
        hunks = self._parse_diff(diff_content, changed_files or [])
        suggestions: list[ComplianceSuggestion] = []

        for hunk in hunks:
            hunk_suggestions = self._analyze_hunk(hunk)
            suggestions.extend(hunk_suggestions)
            if hunk_suggestions:
                max_risk = max(s.risk_level for s in hunk_suggestions)
                hunk.risk_level = max_risk

        suggestions = suggestions[: self._config.max_suggestions_per_pr]
        overall_risk = self._compute_overall_risk(suggestions)
        decision = self._make_decision(overall_risk)
        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        # Compute score impact based on suggestion count
        score_delta = len(suggestions) * 2.5
        review = PRComplianceReview(
            repo=repo,
            pr_number=pr_number,
            commit_sha=commit_sha or hashlib.sha1(f"{repo}-{pr_number}".encode()).hexdigest()[:8],
            overall_risk=overall_risk,
            decision=decision,
            suggestions=suggestions,
            files_analyzed=len({h.file_path for h in hunks}),
            hunks_analyzed=len(hunks),
            compliance_score_before=95.0,
            compliance_score_after=max(0, 95.0 - score_delta),
            auto_approve_eligible=decision == ReviewDecision.AUTO_APPROVED,
            review_time_ms=round(duration, 2),
            created_at=datetime.now(UTC),
        )
        self._reviews.append(review)
        logger.info("PR reviewed", repo=repo, pr=pr_number, risk=overall_risk.value, suggestions=len(suggestions))
        return review

    def _parse_diff(self, diff_content: str, changed_files: list[dict]) -> list[DiffHunk]:
        hunks = []
        if changed_files:
            for f in changed_files:
                hunks.append(DiffHunk(
                    file_path=f.get("path", ""),
                    start_line=f.get("start_line", 1),
                    end_line=f.get("end_line", 100),
                    added_lines=f.get("added_lines", []),
                ))
        elif diff_content:
            hunks.append(DiffHunk(file_path="diff", added_lines=diff_content.split("\n")))
        return hunks

    def _analyze_hunk(self, hunk: DiffHunk) -> list[ComplianceSuggestion]:
        suggestions = []
        content = " ".join(hunk.added_lines).lower()
        for fw in self._config.frameworks:
            patterns = _COMPLIANCE_PATTERNS.get(fw, [])
            for pat in patterns:
                import re
                if re.search(pat["pattern"], content):
                    suggestions.append(ComplianceSuggestion(
                        file_path=hunk.file_path,
                        line_number=hunk.start_line,
                        rule_id=pat["rule"],
                        framework=fw,
                        article_ref=pat["article"],
                        message=pat["message"],
                        suggested_code=f"# TODO: {pat['message']}",
                        risk_level=ReviewRiskLevel.HIGH if fw in ("HIPAA", "PCI-DSS") else ReviewRiskLevel.MEDIUM,
                        created_at=datetime.now(UTC),
                    ))
                    hunk.frameworks_affected.append(fw)
        return suggestions

    def _compute_overall_risk(self, suggestions: list[ComplianceSuggestion]) -> ReviewRiskLevel:
        if not suggestions:
            return ReviewRiskLevel.NONE
        risk_order = {ReviewRiskLevel.NONE: 0, ReviewRiskLevel.LOW: 1, ReviewRiskLevel.MEDIUM: 2, ReviewRiskLevel.HIGH: 3, ReviewRiskLevel.CRITICAL: 4}
        max_risk = max(suggestions, key=lambda s: risk_order.get(s.risk_level, 0))
        return max_risk.risk_level

    def _make_decision(self, overall_risk: ReviewRiskLevel) -> ReviewDecision:
        if overall_risk == ReviewRiskLevel.NONE:
            return ReviewDecision.AUTO_APPROVED if self._config.auto_approve_low_risk else ReviewDecision.APPROVE
        if overall_risk == ReviewRiskLevel.LOW and self._config.auto_approve_low_risk:
            return ReviewDecision.AUTO_APPROVED
        risk_order = {ReviewRiskLevel.NONE: 0, ReviewRiskLevel.LOW: 1, ReviewRiskLevel.MEDIUM: 2, ReviewRiskLevel.HIGH: 3, ReviewRiskLevel.CRITICAL: 4}
        min_block = risk_order.get(self._config.min_risk_for_block, 3)
        if risk_order.get(overall_risk, 0) >= min_block:
            return ReviewDecision.REQUEST_CHANGES
        return ReviewDecision.COMMENT

    async def accept_suggestion(self, suggestion_id: UUID) -> bool:
        for review in self._reviews:
            for s in review.suggestions:
                if s.id == suggestion_id:
                    s.status = SuggestionStatus.ACCEPTED
                    return True
        return False

    async def reject_suggestion(self, suggestion_id: UUID) -> bool:
        for review in self._reviews:
            for s in review.suggestions:
                if s.id == suggestion_id:
                    s.status = SuggestionStatus.REJECTED
                    return True
        return False

    async def update_config(self, config: ReviewConfig) -> ReviewConfig:
        self._config = config
        return config

    def get_config(self) -> ReviewConfig:
        return self._config

    def get_review(self, review_id: str) -> PRComplianceReview | None:
        return next((r for r in self._reviews if str(r.id) == review_id), None)

    def list_reviews(self, repo: str | None = None, limit: int = 50) -> list[PRComplianceReview]:
        results = list(self._reviews)
        if repo:
            results = [r for r in results if r.repo == repo]
        return sorted(results, key=lambda r: r.created_at or datetime.min.replace(tzinfo=UTC), reverse=True)[:limit]

    def get_stats(self) -> ReviewStats:
        total = len(self._reviews)
        auto = sum(1 for r in self._reviews if r.decision == ReviewDecision.AUTO_APPROVED)
        all_suggestions = [s for r in self._reviews for s in r.suggestions]
        accepted = sum(1 for s in all_suggestions if s.status == SuggestionStatus.ACCEPTED)
        by_risk: dict[str, int] = {}
        for r in self._reviews:
            by_risk[r.overall_risk.value] = by_risk.get(r.overall_risk.value, 0) + 1
        times = [r.review_time_ms for r in self._reviews if r.review_time_ms > 0]
        return ReviewStats(
            total_reviews=total,
            auto_approved=auto,
            suggestions_made=len(all_suggestions),
            suggestions_accepted=accepted,
            acceptance_rate=round(accepted / len(all_suggestions), 2) if all_suggestions else 0.0,
            avg_review_time_ms=round(sum(times) / len(times), 2) if times else 0.0,
            by_risk_level=by_risk,
        )
