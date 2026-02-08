"""Seed the database with demo data for local development.

Usage:
    cd backend
    source .venv/bin/activate
    python -m scripts.seed

Requires: running PostgreSQL (via `make dev`) and applied migrations (`make migrate`).
"""

import asyncio
import sys
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.core.database import Base
from app.core.security import get_password_hash
from app.models.organization import MemberRole, Organization, OrganizationMember, PlanType
from app.models.regulation import (
    ChangeType,
    Jurisdiction,
    Regulation,
    RegulatoryFramework,
    RegulationStatus,
    RegulatorySource,
)
from app.models.user import User


DEMO_PASSWORD = "demo1234"  # noqa: S105


async def seed() -> None:
    """Insert demo data into the database."""
    engine = create_async_engine(settings.database_url, echo=False)

    async with engine.begin() as conn:
        # Check if data already exists
        result = await conn.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()
        if count and count > 0:
            print("⚠️  Database already has data. Skipping seed.")
            print("   Run `make db-reset && make migrate` first to start fresh.")
            await engine.dispose()
            return

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # --- Organizations ---
        org = Organization(
            id=uuid4(),
            name="Acme Corp",
            slug="acme-corp",
            description="Demo organization for local development",
            plan=PlanType.PROFESSIONAL,
            settings={"industry": "technology", "size": "medium"},
            max_repositories=10,
            max_frameworks=10,
            max_users=25,
        )
        session.add(org)

        # --- Users ---
        admin_user = User(
            id=uuid4(),
            email="admin@demo.local",
            hashed_password=get_password_hash(DEMO_PASSWORD),
            full_name="Demo Admin",
            is_active=True,
            is_verified=True,
            verified_at=datetime.now(UTC),
        )
        dev_user = User(
            id=uuid4(),
            email="dev@demo.local",
            hashed_password=get_password_hash(DEMO_PASSWORD),
            full_name="Demo Developer",
            is_active=True,
            is_verified=True,
            verified_at=datetime.now(UTC),
        )
        session.add_all([admin_user, dev_user])
        await session.flush()

        # --- Memberships ---
        session.add_all([
            OrganizationMember(
                id=uuid4(),
                organization_id=org.id,
                user_id=admin_user.id,
                role=MemberRole.ADMIN,
                accepted_at=datetime.now(UTC),
            ),
            OrganizationMember(
                id=uuid4(),
                organization_id=org.id,
                user_id=dev_user.id,
                role=MemberRole.MEMBER,
                accepted_at=datetime.now(UTC),
            ),
        ])

        # --- Regulatory Sources ---
        eur_lex = RegulatorySource(
            id=uuid4(),
            name="EUR-Lex",
            description="Official EU law database",
            url="https://eur-lex.europa.eu/",
            jurisdiction=Jurisdiction.EU,
            framework=RegulatoryFramework.GDPR,
            is_active=True,
            check_interval_hours=24,
        )
        hhs_gov = RegulatorySource(
            id=uuid4(),
            name="HHS.gov",
            description="US Department of Health and Human Services",
            url="https://www.hhs.gov/hipaa/",
            jurisdiction=Jurisdiction.US_FEDERAL,
            framework=RegulatoryFramework.HIPAA,
            is_active=True,
            check_interval_hours=24,
        )
        session.add_all([eur_lex, hhs_gov])
        await session.flush()

        # --- Regulations ---
        now = datetime.now(UTC)
        regulations = [
            Regulation(
                id=uuid4(),
                source_id=eur_lex.id,
                name="General Data Protection Regulation",
                short_name="GDPR",
                official_reference="Regulation (EU) 2016/679",
                jurisdiction=Jurisdiction.EU,
                framework=RegulatoryFramework.GDPR,
                status=RegulationStatus.EFFECTIVE,
                published_date=date(2016, 4, 27),
                effective_date=date(2018, 5, 25),
                source_url="https://eur-lex.europa.eu/eli/reg/2016/679/oj",
                content_summary="EU regulation on data protection and privacy for individuals within the EU and EEA.",
                is_parsed=True,
                parsed_at=now,
                parsing_confidence=0.95,
                tags=["privacy", "data-protection", "eu"],
            ),
            Regulation(
                id=uuid4(),
                source_id=None,
                name="California Consumer Privacy Act",
                short_name="CCPA",
                official_reference="Cal. Civ. Code §§ 1798.100–1798.199.100",
                jurisdiction=Jurisdiction.US_CALIFORNIA,
                framework=RegulatoryFramework.CCPA,
                status=RegulationStatus.EFFECTIVE,
                published_date=date(2018, 6, 28),
                effective_date=date(2020, 1, 1),
                source_url="https://oag.ca.gov/privacy/ccpa",
                content_summary="California law giving consumers more control over personal information collected by businesses.",
                is_parsed=True,
                parsed_at=now,
                parsing_confidence=0.92,
                tags=["privacy", "california", "consumer-rights"],
            ),
            Regulation(
                id=uuid4(),
                source_id=hhs_gov.id,
                name="Health Insurance Portability and Accountability Act",
                short_name="HIPAA",
                official_reference="Pub.L. 104–191",
                jurisdiction=Jurisdiction.US_FEDERAL,
                framework=RegulatoryFramework.HIPAA,
                status=RegulationStatus.EFFECTIVE,
                published_date=date(1996, 8, 21),
                effective_date=date(2003, 4, 14),
                source_url="https://www.hhs.gov/hipaa/index.html",
                content_summary="US law providing data privacy and security provisions for safeguarding medical information.",
                is_parsed=True,
                parsed_at=now,
                parsing_confidence=0.90,
                tags=["healthcare", "privacy", "phi"],
            ),
            Regulation(
                id=uuid4(),
                source_id=None,
                name="EU Artificial Intelligence Act",
                short_name="EU AI Act",
                official_reference="Regulation (EU) 2024/1689",
                jurisdiction=Jurisdiction.EU,
                framework=RegulatoryFramework.EU_AI_ACT,
                status=RegulationStatus.ADOPTED,
                published_date=date(2024, 7, 12),
                effective_date=date(2026, 8, 1),
                source_url="https://eur-lex.europa.eu/eli/reg/2024/1689/oj",
                content_summary="EU regulation laying down harmonised rules on artificial intelligence.",
                is_parsed=True,
                parsed_at=now,
                parsing_confidence=0.88,
                tags=["ai", "eu", "risk-based"],
            ),
        ]
        session.add_all(regulations)

        await session.commit()

    await engine.dispose()

    print("✅ Demo data seeded successfully!")
    print()
    print("  Demo accounts:")
    print(f"    Admin: admin@demo.local / {DEMO_PASSWORD}")
    print(f"    Dev:   dev@demo.local / {DEMO_PASSWORD}")
    print()
    print("  Organization: Acme Corp (professional plan)")
    print("  Regulations:  GDPR, CCPA, HIPAA, EU AI Act")


if __name__ == "__main__":
    asyncio.run(seed())
