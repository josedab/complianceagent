"""Add APAC, ESG, and AI Safety regulatory frameworks

Revision ID: 002_add_apac_esg_ai_frameworks
Revises: 001_initial
Create Date: 2026-01-30

This migration adds support for:
- Asia-Pacific jurisdictions (Japan, Brazil, Australia, Canada)
- Asia-Pacific regulatory frameworks (DPDP, APPI, PIPA)
- ESG/Sustainability frameworks (CSRD, SEC_CLIMATE, TCFD)
- AI Safety frameworks (NIST_AI_RMF, ISO42001)
- New requirement categories for ESG and AI
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "002_add_apac_esg_ai_frameworks"
down_revision: str | None = "001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# New jurisdiction values to add
NEW_JURISDICTIONS = ["jp", "br", "au", "ca"]

# New framework values to add
NEW_FRAMEWORKS = [
    "dpdp",  # India Digital Personal Data Protection
    "appi",  # Japan Act on Protection of Personal Information
    "pipa",  # South Korea Personal Information Protection Act
    "csrd",  # EU Corporate Sustainability Reporting Directive
    "sec_climate",  # SEC Climate Disclosure Rules
    "tcfd",  # Task Force on Climate-related Financial Disclosures
    "nist_ai_rmf",  # NIST AI Risk Management Framework
    "iso42001",  # ISO AI Management System
    "lgpd",  # Brazil General Data Protection Law
    "ferpa",  # US Family Educational Rights and Privacy Act
    "wcag",  # Web Content Accessibility Guidelines
]

# New requirement category values to add
NEW_REQUIREMENT_CATEGORIES = [
    "breach_notification",
    "ai_risk_classification",
    "sustainability_reporting",
    "ghg_emissions",
    "climate_risk",
    "environmental_impact",
    "social_impact",
    "governance_disclosure",
    "accessibility",
]


def upgrade() -> None:
    """Add new enum values for APAC, ESG, and AI Safety support.

    Note: PostgreSQL enums require ALTER TYPE to add new values.
    SQLite and other databases use VARCHAR and don't need modification.
    """
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect != "postgresql":
        return

    # Migration 001 stores these values in VARCHAR columns, so fresh databases
    # have no enum types to alter. Older deployments may still have enum-backed
    # columns; update those types only when they actually exist.
    enum_names = {
        row[0]
        for row in bind.execute(
            sa.text(
                "SELECT typname FROM pg_type "
                "WHERE typname IN ('jurisdiction', 'regulatoryframework', "
                "'requirementcategory')"
            )
        )
    }
    additions = {
        "jurisdiction": NEW_JURISDICTIONS,
        "regulatoryframework": NEW_FRAMEWORKS,
        "requirementcategory": NEW_REQUIREMENT_CATEGORIES,
    }
    for enum_name, values in additions.items():
        if enum_name not in enum_names:
            continue
        for value in values:
            op.execute(f"ALTER TYPE {enum_name} ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    """Remove new enum values.

    Note: PostgreSQL does not support removing enum values easily.
    The values are harmless when retained, so downgrade intentionally does
    nothing for both VARCHAR-backed and legacy enum-backed schemas.
    """
