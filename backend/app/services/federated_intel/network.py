"""Federated Compliance Intelligence Network implementation."""

import hashlib
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import structlog

from app.services.federated_intel.models import (
    ThreatCategory,
    IntelligenceType,
    SharingLevel,
    Severity,
    ComplianceThreat,
    CompliancePattern,
    IntelligenceReport,
    NetworkMember,
    FederatedNetwork,
    INITIAL_THREATS,
    INITIAL_PATTERNS,
)

logger = structlog.get_logger()


class FederatedIntelligenceNetwork:
    """Manages the federated compliance intelligence network."""
    
    def __init__(self) -> None:
        self._network = FederatedNetwork()
        self._members: dict[UUID, NetworkMember] = {}
        self._threats: dict[UUID, ComplianceThreat] = {}
        self._patterns: dict[UUID, CompliancePattern] = {}
        self._reports: dict[UUID, IntelligenceReport] = {}
        
        # Initialize with seed data
        self._initialize_seed_data()
    
    def _initialize_seed_data(self) -> None:
        """Initialize network with seed intelligence data."""
        # Add initial threats
        for threat_data in INITIAL_THREATS:
            threat = ComplianceThreat(
                title=threat_data["title"],
                description=threat_data["description"],
                category=threat_data["category"],
                severity=threat_data["severity"],
                regulations=threat_data["regulations"],
                industries=threat_data["industries"],
                regions=threat_data.get("regions", []),
                recommended_actions=threat_data.get("recommended_actions", []),
                sharing_level=SharingLevel.PUBLIC,
                verified=True,
                verified_by_count=10,
            )
            self._threats[threat.id] = threat
            self._network.total_threats += 1
            self._network.active_threats += 1
        
        # Add initial patterns
        for pattern_data in INITIAL_PATTERNS:
            pattern = CompliancePattern(
                name=pattern_data["name"],
                description=pattern_data["description"],
                pattern_type=pattern_data["pattern_type"],
                regulations=pattern_data["regulations"],
                code_patterns=pattern_data.get("code_patterns", []),
                detection_rules=pattern_data.get("detection_rules", []),
                compliance_risk=pattern_data.get("compliance_risk"),
                recommended_fix=pattern_data.get("recommended_fix"),
                seen_count=pattern_data.get("seen_count", 0),
                fixed_count=pattern_data.get("fixed_count", 0),
                sharing_level=SharingLevel.PUBLIC,
            )
            self._patterns[pattern.id] = pattern
            self._network.total_patterns += 1
        
        # Update network coverage
        self._update_network_stats()
    
    def _update_network_stats(self) -> None:
        """Update network statistics."""
        industries = set()
        regulations = set()
        regions = set()
        
        for threat in self._threats.values():
            industries.update(threat.industries)
            regulations.update(threat.regulations)
            regions.update(threat.regions)
        
        for pattern in self._patterns.values():
            industries.update(pattern.industries)
            regulations.update(pattern.regulations)
        
        self._network.industries_covered = list(industries)
        self._network.regulations_covered = list(regulations)
        self._network.regions_covered = list(regions)
        self._network.updated_at = datetime.utcnow()
    
    async def join_network(
        self,
        organization_id: UUID,
        industry: str,
        region: str,
        size_category: str = "medium",
        sharing_level: SharingLevel = SharingLevel.INDUSTRY,
    ) -> NetworkMember:
        """Join the federated intelligence network."""
        # Generate anonymous ID
        anonymous_id = hashlib.sha256(
            f"{organization_id}{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        member = NetworkMember(
            organization_id=organization_id,
            anonymous_id=anonymous_id,
            industry=industry,
            region=region,
            size_category=size_category,
            sharing_level=sharing_level,
            subscribed_categories=list(ThreatCategory),  # Subscribe to all by default
        )
        
        self._members[member.id] = member
        self._network.total_members += 1
        self._network.active_members += 1
        
        return member
    
    async def get_member(self, organization_id: UUID) -> NetworkMember | None:
        """Get member by organization ID."""
        for member in self._members.values():
            if member.organization_id == organization_id:
                return member
        return None
    
    async def get_network_stats(self) -> FederatedNetwork:
        """Get current network statistics."""
        return self._network
    
    async def contribute_threat(
        self,
        member_id: UUID,
        threat_data: dict[str, Any],
    ) -> ComplianceThreat:
        """Contribute a new threat to the network."""
        member = self._members.get(member_id)
        if not member:
            raise ValueError("Member not found")
        
        threat = ComplianceThreat(
            title=threat_data["title"],
            description=threat_data["description"],
            category=ThreatCategory(threat_data["category"]),
            severity=Severity(threat_data["severity"]),
            regulations=threat_data.get("regulations", []),
            industries=threat_data.get("industries", [member.industry]),
            regions=threat_data.get("regions", [member.region]),
            indicators=threat_data.get("indicators", []),
            potential_impact=threat_data.get("potential_impact"),
            recommended_actions=threat_data.get("recommended_actions", []),
            sharing_level=member.sharing_level,
            contributor_id=member.id,
            contributor_industry=member.industry,
        )
        
        self._threats[threat.id] = threat
        self._network.total_threats += 1
        self._network.active_threats += 1
        self._network.total_contributions += 1
        self._network.contributions_this_month += 1
        
        member.contributions_count += 1
        member.reputation_score = min(100, member.reputation_score + 2)
        member.last_active = datetime.utcnow()
        
        self._update_network_stats()
        
        return threat
    
    async def contribute_pattern(
        self,
        member_id: UUID,
        pattern_data: dict[str, Any],
    ) -> CompliancePattern:
        """Contribute a new pattern to the network."""
        member = self._members.get(member_id)
        if not member:
            raise ValueError("Member not found")
        
        pattern = CompliancePattern(
            name=pattern_data["name"],
            description=pattern_data["description"],
            pattern_type=pattern_data["pattern_type"],
            regulations=pattern_data.get("regulations", []),
            industries=pattern_data.get("industries", [member.industry]),
            detection_rules=pattern_data.get("detection_rules", []),
            code_patterns=pattern_data.get("code_patterns", []),
            compliance_risk=pattern_data.get("compliance_risk"),
            recommended_fix=pattern_data.get("recommended_fix"),
            example_fix=pattern_data.get("example_fix"),
            sharing_level=member.sharing_level,
        )
        
        self._patterns[pattern.id] = pattern
        self._network.total_patterns += 1
        self._network.total_contributions += 1
        self._network.contributions_this_month += 1
        
        member.contributions_count += 1
        member.reputation_score = min(100, member.reputation_score + 1)
        member.last_active = datetime.utcnow()
        
        self._update_network_stats()
        
        return pattern
    
    async def verify_threat(
        self,
        member_id: UUID,
        threat_id: UUID,
        verified: bool = True,
    ) -> ComplianceThreat | None:
        """Verify (or dispute) a threat."""
        member = self._members.get(member_id)
        threat = self._threats.get(threat_id)
        
        if not member or not threat:
            return None
        
        if verified:
            threat.verified_by_count += 1
            if threat.verified_by_count >= 3:
                threat.verified = True
            member.reputation_score = min(100, member.reputation_score + 0.5)
        
        member.verifications_count += 1
        member.last_active = datetime.utcnow()
        
        return threat
    
    async def get_threats(
        self,
        member_id: UUID,
        category: ThreatCategory | None = None,
        regulation: str | None = None,
        industry: str | None = None,
        severity: Severity | None = None,
        limit: int = 50,
    ) -> list[ComplianceThreat]:
        """Get threats visible to a member."""
        member = self._members.get(member_id)
        if not member:
            return []
        
        threats = []
        for threat in self._threats.values():
            # Check sharing level
            if threat.sharing_level == SharingLevel.PRIVATE:
                if threat.contributor_id != member.id:
                    continue
            elif threat.sharing_level == SharingLevel.INDUSTRY:
                if threat.contributor_industry != member.industry:
                    if member.industry not in threat.industries:
                        continue
            
            # Apply filters
            if category and threat.category != category:
                continue
            if regulation and regulation not in threat.regulations:
                continue
            if industry and industry not in threat.industries:
                continue
            if severity and threat.severity != severity:
                continue
            
            threats.append(threat)
        
        # Sort by severity and recency
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4,
        }
        threats.sort(key=lambda t: (severity_order.get(t.severity, 5), -t.first_seen.timestamp()))
        
        return threats[:limit]
    
    async def get_patterns(
        self,
        member_id: UUID,
        pattern_type: str | None = None,
        regulation: str | None = None,
        industry: str | None = None,
        limit: int = 50,
    ) -> list[CompliancePattern]:
        """Get patterns visible to a member."""
        member = self._members.get(member_id)
        if not member:
            return []
        
        patterns = []
        for pattern in self._patterns.values():
            # Check sharing level
            if pattern.sharing_level == SharingLevel.PRIVATE:
                continue  # Skip private patterns from others
            elif pattern.sharing_level == SharingLevel.INDUSTRY:
                if member.industry not in pattern.industries:
                    continue
            
            # Apply filters
            if pattern_type and pattern.pattern_type != pattern_type:
                continue
            if regulation and regulation not in pattern.regulations:
                continue
            if industry and industry not in pattern.industries:
                continue
            
            patterns.append(pattern)
        
        # Sort by frequency
        patterns.sort(key=lambda p: -p.seen_count)
        
        return patterns[:limit]
    
    async def get_threat_feed(
        self,
        member_id: UUID,
        since: datetime | None = None,
    ) -> list[ComplianceThreat]:
        """Get personalized threat feed for a member."""
        member = self._members.get(member_id)
        if not member:
            return []
        
        if since is None:
            since = datetime.utcnow() - timedelta(days=7)
        
        threats = []
        for threat in self._threats.values():
            # Filter by subscription preferences
            if threat.category not in member.subscribed_categories:
                continue
            
            # Filter by recency
            if threat.last_updated < since:
                continue
            
            # Filter by relevance
            if member.subscribed_regulations:
                if not any(r in threat.regulations for r in member.subscribed_regulations):
                    continue
            
            if member.subscribed_industries:
                if not any(i in threat.industries for i in member.subscribed_industries):
                    continue
            
            threats.append(threat)
        
        # Sort by urgency
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4,
        }
        threats.sort(key=lambda t: (severity_order.get(t.severity, 5), -t.last_updated.timestamp()))
        
        member.last_active = datetime.utcnow()
        
        return threats
    
    async def generate_intelligence_report(
        self,
        member_id: UUID,
        report_type: IntelligenceType = IntelligenceType.THREAT,
    ) -> IntelligenceReport:
        """Generate an intelligence report for a member."""
        member = self._members.get(member_id)
        if not member:
            raise ValueError("Member not found")
        
        now = datetime.utcnow()
        period = f"{now.year}-W{now.isocalendar()[1]}"
        
        # Get relevant threats
        relevant_threats = [
            t for t in self._threats.values()
            if member.industry in t.industries or not t.industries
        ]
        
        # Calculate statistics
        active = [t for t in relevant_threats if not t.expiry_date or t.expiry_date > now]
        new_threats = [t for t in active if t.first_seen > now - timedelta(days=7)]
        
        critical_threats = [t for t in active if t.severity == Severity.CRITICAL]
        high_threats = [t for t in active if t.severity == Severity.HIGH]
        
        # Get relevant patterns
        relevant_patterns = [
            p for p in self._patterns.values()
            if member.industry in p.industries or not p.industries
        ]
        
        anti_patterns = [p for p in relevant_patterns if p.pattern_type == "anti-pattern"]
        best_practices = [p for p in relevant_patterns if p.pattern_type == "best-practice"]
        
        report = IntelligenceReport(
            title=f"Compliance Intelligence Report - {period}",
            report_type=report_type,
            period=period,
            summary=f"Analysis of compliance threats and patterns for {member.industry} industry",
            key_findings=[
                f"{len(critical_threats)} critical threats require immediate attention",
                f"{len(new_threats)} new threats identified this week",
                f"{len(anti_patterns)} common anti-patterns detected across the network",
                f"{len(best_practices)} recommended best practices available",
            ],
            active_threats=len(active),
            new_threats=len(new_threats),
            top_threats=[
                {
                    "id": str(t.id),
                    "title": t.title,
                    "severity": t.severity.value,
                    "category": t.category.value,
                }
                for t in (critical_threats + high_threats)[:5]
            ],
            emerging_patterns=[
                p.name for p in sorted(anti_patterns, key=lambda x: -x.seen_count)[:5]
            ],
            industry_benchmarks={
                "average_compliance_score": 72,
                "average_remediation_time_days": 14,
                "top_violation_category": "data_protection",
            },
            recommendations=[
                f"Address {len(critical_threats)} critical threats immediately",
                f"Review {len(anti_patterns)} common anti-patterns in your codebase",
                f"Implement {len(best_practices)} recommended best practices",
            ],
            priority_actions=[
                t.recommended_actions[0] if t.recommended_actions else "Review threat details"
                for t in critical_threats[:3]
            ],
        )
        
        self._reports[report.id] = report
        
        return report
    
    async def get_industry_benchmarks(
        self,
        industry: str,
    ) -> dict[str, Any]:
        """Get compliance benchmarks for an industry."""
        # Simulated benchmark data
        benchmarks = {
            "Technology": {
                "average_compliance_score": 75,
                "top_regulations": ["GDPR", "CCPA", "SOC 2"],
                "common_violations": ["Data retention", "Consent tracking", "Encryption"],
                "average_time_to_compliance": 45,
            },
            "Finance": {
                "average_compliance_score": 82,
                "top_regulations": ["PCI-DSS", "SOX", "GDPR"],
                "common_violations": ["Access control", "Audit logging", "Data encryption"],
                "average_time_to_compliance": 60,
            },
            "Healthcare": {
                "average_compliance_score": 78,
                "top_regulations": ["HIPAA", "GDPR", "FDA 21 CFR Part 11"],
                "common_violations": ["PHI access", "Audit trails", "Data minimization"],
                "average_time_to_compliance": 90,
            },
        }
        
        return benchmarks.get(industry, {
            "average_compliance_score": 70,
            "top_regulations": ["GDPR", "SOC 2"],
            "common_violations": ["Data protection", "Access control"],
            "average_time_to_compliance": 45,
        })
    
    async def update_member_preferences(
        self,
        member_id: UUID,
        subscribed_categories: list[ThreatCategory] | None = None,
        subscribed_regulations: list[str] | None = None,
        subscribed_industries: list[str] | None = None,
        sharing_level: SharingLevel | None = None,
    ) -> NetworkMember | None:
        """Update member preferences."""
        member = self._members.get(member_id)
        if not member:
            return None
        
        if subscribed_categories is not None:
            member.subscribed_categories = subscribed_categories
        if subscribed_regulations is not None:
            member.subscribed_regulations = subscribed_regulations
        if subscribed_industries is not None:
            member.subscribed_industries = subscribed_industries
        if sharing_level is not None:
            member.sharing_level = sharing_level
        
        member.last_active = datetime.utcnow()
        
        return member


# Singleton instance
_network_instance: FederatedIntelligenceNetwork | None = None


def get_federated_network() -> FederatedIntelligenceNetwork:
    """Get or create the federated network singleton."""
    global _network_instance
    if _network_instance is None:
        _network_instance = FederatedIntelligenceNetwork()
    return _network_instance
