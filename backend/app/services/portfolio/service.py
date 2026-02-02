"""Portfolio service for multi-repo compliance management."""

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.codebase import CodebaseMapping, ComplianceStatus, Repository
from app.models.customer_profile import CustomerProfile
from app.models.requirement import Requirement
from app.services.portfolio.models import (
    CrossRepoAnalysis,
    FrameworkAggregation,
    Portfolio,
    PortfolioSummary,
    PortfolioTrend,
    RepositoryRiskProfile,
    RiskLevel,
    TrendDirection,
)
from app.services.scoring import ComplianceGrade

logger = structlog.get_logger()


class PortfolioService:
    """Service for managing compliance portfolios across multiple repositories."""

    def __init__(self, db: AsyncSession):
        self.db = db
        # In-memory storage for portfolios (use DB in production)
        self._portfolios: dict[UUID, Portfolio] = {}

    async def create_portfolio(
        self,
        organization_id: UUID,
        name: str,
        repository_ids: list[UUID],
        description: str | None = None,
        created_by: UUID | None = None,
        tags: list[str] | None = None,
    ) -> Portfolio:
        """Create a new compliance portfolio."""
        portfolio = Portfolio(
            id=uuid4(),
            organization_id=organization_id,
            name=name,
            description=description,
            repository_ids=repository_ids,
            created_by=created_by,
            tags=tags or [],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        
        # Store portfolio
        self._portfolios[portfolio.id] = portfolio
        
        # Calculate initial summary
        portfolio.summary = await self._calculate_summary(portfolio)
        portfolio.repository_profiles = await self._get_repository_profiles(repository_ids)
        
        logger.info(
            "Portfolio created",
            portfolio_id=str(portfolio.id),
            repository_count=len(repository_ids),
        )
        
        return portfolio

    async def get_portfolio(
        self,
        portfolio_id: UUID,
        include_profiles: bool = True,
        include_trends: bool = False,
    ) -> Portfolio | None:
        """Get a portfolio by ID with optional detailed data."""
        portfolio = self._portfolios.get(portfolio_id)
        
        if not portfolio:
            return None
        
        # Refresh summary
        portfolio.summary = await self._calculate_summary(portfolio)
        
        if include_profiles:
            portfolio.repository_profiles = await self._get_repository_profiles(
                portfolio.repository_ids
            )
        
        if include_trends:
            portfolio.trend_history = await self._get_trend_history(portfolio_id)
        
        return portfolio

    async def list_portfolios(
        self,
        organization_id: UUID,
        include_summaries: bool = True,
    ) -> list[Portfolio]:
        """List all portfolios for an organization."""
        portfolios = [
            p for p in self._portfolios.values()
            if p.organization_id == organization_id
        ]
        
        if include_summaries:
            for portfolio in portfolios:
                portfolio.summary = await self._calculate_summary(portfolio)
        
        return portfolios

    async def update_portfolio(
        self,
        portfolio_id: UUID,
        name: str | None = None,
        description: str | None = None,
        repository_ids: list[UUID] | None = None,
        tags: list[str] | None = None,
    ) -> Portfolio | None:
        """Update portfolio metadata or repository list."""
        portfolio = self._portfolios.get(portfolio_id)
        
        if not portfolio:
            return None
        
        if name is not None:
            portfolio.name = name
        if description is not None:
            portfolio.description = description
        if repository_ids is not None:
            portfolio.repository_ids = repository_ids
        if tags is not None:
            portfolio.tags = tags
        
        portfolio.updated_at = datetime.now(UTC)
        
        # Recalculate summary
        portfolio.summary = await self._calculate_summary(portfolio)
        
        return portfolio

    async def delete_portfolio(self, portfolio_id: UUID) -> bool:
        """Delete a portfolio."""
        if portfolio_id in self._portfolios:
            del self._portfolios[portfolio_id]
            return True
        return False

    async def add_repositories(
        self,
        portfolio_id: UUID,
        repository_ids: list[UUID],
    ) -> Portfolio | None:
        """Add repositories to a portfolio."""
        portfolio = self._portfolios.get(portfolio_id)
        
        if not portfolio:
            return None
        
        # Add unique repositories
        existing = set(portfolio.repository_ids)
        for repo_id in repository_ids:
            if repo_id not in existing:
                portfolio.repository_ids.append(repo_id)
        
        portfolio.updated_at = datetime.now(UTC)
        portfolio.summary = await self._calculate_summary(portfolio)
        
        return portfolio

    async def remove_repositories(
        self,
        portfolio_id: UUID,
        repository_ids: list[UUID],
    ) -> Portfolio | None:
        """Remove repositories from a portfolio."""
        portfolio = self._portfolios.get(portfolio_id)
        
        if not portfolio:
            return None
        
        remove_set = set(repository_ids)
        portfolio.repository_ids = [
            r for r in portfolio.repository_ids if r not in remove_set
        ]
        
        portfolio.updated_at = datetime.now(UTC)
        portfolio.summary = await self._calculate_summary(portfolio)
        
        return portfolio

    async def get_cross_repo_analysis(
        self,
        portfolio_id: UUID,
    ) -> CrossRepoAnalysis | None:
        """Analyze patterns and common issues across repositories."""
        portfolio = self._portfolios.get(portfolio_id)
        
        if not portfolio:
            return None

        profiles = await self._get_repository_profiles(portfolio.repository_ids)
        
        # Find common gaps
        gap_counts: dict[str, int] = defaultdict(int)
        for profile in profiles:
            for fw, score in profile.framework_scores.items():
                if score < 80:  # Below B grade
                    gap_counts[fw] += 1
        
        common_gaps = [
            {"framework": fw, "affected_repos": count}
            for fw, count in gap_counts.items()
            if count > 1  # Appears in multiple repos
        ]
        common_gaps.sort(key=lambda x: x["affected_repos"], reverse=True)
        
        # Analyze framework coverage
        framework_coverage = {}
        for profile in profiles:
            for fw, score in profile.framework_scores.items():
                if fw not in framework_coverage:
                    framework_coverage[fw] = {
                        "total_repos": 0,
                        "compliant_repos": 0,
                        "average_score": 0,
                        "scores": [],
                    }
                framework_coverage[fw]["total_repos"] += 1
                framework_coverage[fw]["scores"].append(score)
                if score >= 90:
                    framework_coverage[fw]["compliant_repos"] += 1
        
        # Calculate averages
        for fw, data in framework_coverage.items():
            if data["scores"]:
                data["average_score"] = sum(data["scores"]) / len(data["scores"])
            del data["scores"]  # Remove raw scores
        
        # Generate recommendations
        recommendations = []
        if common_gaps:
            top_gap = common_gaps[0]
            recommendations.append(
                f"Address {top_gap['framework']} compliance gaps affecting "
                f"{top_gap['affected_repos']} repositories"
            )
        
        critical_repos = [p for p in profiles if p.risk_level == RiskLevel.CRITICAL]
        if critical_repos:
            recommendations.append(
                f"Prioritize {len(critical_repos)} repositories with critical risk levels"
            )
        
        return CrossRepoAnalysis(
            portfolio_id=portfolio_id,
            common_gaps=common_gaps,
            shared_risky_dependencies=[],  # Would require dependency analysis
            framework_coverage=framework_coverage,
            portfolio_recommendations=recommendations,
            analyzed_at=datetime.now(UTC),
        )

    async def _calculate_summary(self, portfolio: Portfolio) -> PortfolioSummary:
        """Calculate summary statistics for a portfolio."""
        profiles = await self._get_repository_profiles(portfolio.repository_ids)
        
        if not profiles:
            return PortfolioSummary(
                portfolio_id=portfolio.id,
                portfolio_name=portfolio.name,
            )
        
        # Calculate aggregates
        total_repos = len(profiles)
        scores = [p.compliance_score for p in profiles]
        avg_score = sum(scores) / total_repos if total_repos > 0 else 0
        
        # Grade distribution
        grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        for p in profiles:
            grade = p.compliance_grade
            if grade in grade_counts:
                grade_counts[grade] += 1
        
        # Risk distribution
        risk_counts = {level: 0 for level in RiskLevel}
        for p in profiles:
            risk_counts[p.risk_level] += 1
        
        # Gap totals
        total_critical = sum(p.critical_gaps for p in profiles)
        total_major = sum(p.major_gaps for p in profiles)
        total_minor = sum(p.minor_gaps for p in profiles)
        
        # Framework aggregations
        framework_data: dict[str, list[float]] = defaultdict(list)
        for p in profiles:
            for fw, score in p.framework_scores.items():
                framework_data[fw].append(score)
        
        framework_aggregations = []
        for fw, fw_scores in framework_data.items():
            compliant = sum(1 for s in fw_scores if s >= 90)
            at_risk = sum(1 for s in fw_scores if s < 70)
            framework_aggregations.append(FrameworkAggregation(
                framework=fw,
                average_score=sum(fw_scores) / len(fw_scores),
                min_score=min(fw_scores),
                max_score=max(fw_scores),
                repositories_count=len(fw_scores),
                compliant_repos=compliant,
                at_risk_repos=at_risk,
                total_gaps=0,  # Would need gap-level data
            ))
        
        # Determine overall risk
        if risk_counts[RiskLevel.CRITICAL] > 0:
            overall_risk = RiskLevel.CRITICAL
        elif risk_counts[RiskLevel.HIGH] > total_repos * 0.3:
            overall_risk = RiskLevel.HIGH
        elif avg_score >= 80:
            overall_risk = RiskLevel.LOW
        else:
            overall_risk = RiskLevel.MEDIUM
        
        # Repos needing attention (critical or high risk)
        attention_repos = [
            p.repository_id for p in profiles
            if p.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]
        ]
        
        return PortfolioSummary(
            portfolio_id=portfolio.id,
            portfolio_name=portfolio.name,
            total_repositories=total_repos,
            average_compliance_score=round(avg_score, 2),
            weighted_compliance_score=round(avg_score, 2),  # Could weight by repo importance
            overall_risk_level=overall_risk,
            repos_grade_a=grade_counts["A"],
            repos_grade_b=grade_counts["B"],
            repos_grade_c=grade_counts["C"],
            repos_grade_d=grade_counts["D"],
            repos_grade_f=grade_counts["F"],
            repos_critical_risk=risk_counts[RiskLevel.CRITICAL],
            repos_high_risk=risk_counts[RiskLevel.HIGH],
            repos_medium_risk=risk_counts[RiskLevel.MEDIUM],
            repos_low_risk=risk_counts[RiskLevel.LOW] + risk_counts[RiskLevel.MINIMAL],
            total_critical_gaps=total_critical,
            total_major_gaps=total_major,
            total_minor_gaps=total_minor,
            framework_aggregations=framework_aggregations,
            score_trend=TrendDirection.STABLE,
            repositories_needing_attention=attention_repos,
        )

    async def _get_repository_profiles(
        self,
        repository_ids: list[UUID],
    ) -> list[RepositoryRiskProfile]:
        """Get compliance profiles for repositories."""
        if not repository_ids:
            return []
        
        profiles = []
        
        for repo_id in repository_ids:
            # Get repository
            repo_result = await self.db.execute(
                select(Repository).where(Repository.id == repo_id)
            )
            repo = repo_result.scalar_one_or_none()
            
            if not repo:
                continue
            
            # Get mappings for scoring
            mappings_result = await self.db.execute(
                select(CodebaseMapping)
                .options(
                    selectinload(CodebaseMapping.requirement)
                    .selectinload(Requirement.regulation)
                )
                .where(CodebaseMapping.repository_id == repo_id)
            )
            mappings = list(mappings_result.scalars().all())
            
            # Calculate metrics
            total_reqs = len(mappings)
            compliant = sum(1 for m in mappings if m.compliance_status == ComplianceStatus.COMPLIANT)
            critical = sum(m.critical_gaps or 0 for m in mappings)
            major = sum(m.major_gaps or 0 for m in mappings)
            minor = sum(m.minor_gaps or 0 for m in mappings)
            
            score = (compliant / total_reqs * 100) if total_reqs > 0 else 0
            grade = ComplianceGrade.from_score(score)
            
            # Calculate framework scores
            fw_stats: dict[str, dict] = defaultdict(lambda: {"compliant": 0, "total": 0})
            for m in mappings:
                if m.requirement and m.requirement.regulation:
                    fw = m.requirement.regulation.framework.value
                    fw_stats[fw]["total"] += 1
                    if m.compliance_status == ComplianceStatus.COMPLIANT:
                        fw_stats[fw]["compliant"] += 1
            
            framework_scores = {
                fw: (data["compliant"] / data["total"] * 100) if data["total"] > 0 else 0
                for fw, data in fw_stats.items()
            }
            
            # Determine risk level
            if critical > 0 or score < 50:
                risk_level = RiskLevel.CRITICAL
            elif major > 3 or score < 60:
                risk_level = RiskLevel.HIGH
            elif score < 80:
                risk_level = RiskLevel.MEDIUM
            elif score < 90:
                risk_level = RiskLevel.LOW
            else:
                risk_level = RiskLevel.MINIMAL
            
            profiles.append(RepositoryRiskProfile(
                repository_id=repo_id,
                repository_name=repo.name,
                repository_url=repo.url,
                compliance_score=round(score, 2),
                compliance_grade=grade.value,
                risk_level=risk_level,
                total_requirements=total_reqs,
                compliant_requirements=compliant,
                critical_gaps=critical,
                major_gaps=major,
                minor_gaps=minor,
                framework_scores=framework_scores,
                trend=TrendDirection.STABLE,
                last_scanned=repo.last_analyzed_at,
            ))
        
        return profiles

    async def _get_trend_history(
        self,
        portfolio_id: UUID,
        days: int = 30,
    ) -> list[PortfolioTrend]:
        """Get historical trend data for a portfolio."""
        # In production, this would query from a time-series table
        # For now, return empty list
        return []
