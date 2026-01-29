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
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_apac_esg_ai_frameworks'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# New jurisdiction values to add
NEW_JURISDICTIONS = ['jp', 'br', 'au', 'ca']

# New framework values to add
NEW_FRAMEWORKS = [
    'dpdp',        # India Digital Personal Data Protection
    'appi',        # Japan Act on Protection of Personal Information
    'pipa',        # South Korea Personal Information Protection Act
    'csrd',        # EU Corporate Sustainability Reporting Directive
    'sec_climate', # SEC Climate Disclosure Rules
    'tcfd',        # Task Force on Climate-related Financial Disclosures
    'nist_ai_rmf', # NIST AI Risk Management Framework
    'iso42001',    # ISO AI Management System
    'lgpd',        # Brazil General Data Protection Law
    'ferpa',       # US Family Educational Rights and Privacy Act
    'wcag',        # Web Content Accessibility Guidelines
]

# New requirement category values to add
NEW_REQUIREMENT_CATEGORIES = [
    'breach_notification',
    'ai_risk_classification',
    'sustainability_reporting',
    'ghg_emissions',
    'climate_risk',
    'environmental_impact',
    'social_impact',
    'governance_disclosure',
    'accessibility',
]


def upgrade() -> None:
    """Add new enum values for APAC, ESG, and AI Safety support.
    
    Note: PostgreSQL enums require ALTER TYPE to add new values.
    SQLite and other databases use VARCHAR and don't need modification.
    """
    # Get database dialect
    bind = op.get_bind()
    dialect = bind.dialect.name
    
    if dialect == 'postgresql':
        # PostgreSQL: Add new enum values using ALTER TYPE
        # Jurisdictions
        for jurisdiction in NEW_JURISDICTIONS:
            op.execute(f"ALTER TYPE jurisdiction ADD VALUE IF NOT EXISTS '{jurisdiction}'")
        
        # Frameworks
        for framework in NEW_FRAMEWORKS:
            op.execute(f"ALTER TYPE regulatoryframework ADD VALUE IF NOT EXISTS '{framework}'")
        
        # Requirement categories
        for category in NEW_REQUIREMENT_CATEGORIES:
            op.execute(f"ALTER TYPE requirementcategory ADD VALUE IF NOT EXISTS '{category}'")
    
    # For SQLite/others: VARCHAR columns accept any value, no migration needed
    
    # Log the migration
    print(f"Added {len(NEW_JURISDICTIONS)} new jurisdictions")
    print(f"Added {len(NEW_FRAMEWORKS)} new regulatory frameworks")
    print(f"Added {len(NEW_REQUIREMENT_CATEGORIES)} new requirement categories")


def downgrade() -> None:
    """Remove new enum values.
    
    Note: PostgreSQL does not support removing enum values easily.
    This downgrade will only work if no data uses the new values.
    """
    bind = op.get_bind()
    dialect = bind.dialect.name
    
    if dialect == 'postgresql':
        # PostgreSQL: Cannot easily remove enum values
        # Would need to:
        # 1. Create new enum type without the values
        # 2. Update all columns to use new type
        # 3. Drop old type
        # This is complex and data-destructive, so we skip it
        print("WARNING: PostgreSQL enum values cannot be easily removed.")
        print("Manual intervention required if downgrade is needed.")
        print("Ensure no data uses the new enum values before downgrading.")
    
    # For SQLite/others: VARCHAR columns don't need modification
