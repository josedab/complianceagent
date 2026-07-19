"""013 user mfa avatar apikey ownership invitations

Add MFA fields, avatar_url, deactivation dates to users.
Add created_by to api_keys.
Add organization_invitations table.
Add verification_token_expires to users.

Revision ID: 013
Revises: 012_secondary_persistence
Create Date: 2026-07-27
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers
revision = "013"
down_revision = "012_secondary_persistence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Users ---
    op.add_column("users", sa.Column("avatar_url", sa.String(2000), nullable=True))
    op.add_column("users", sa.Column("mfa_secret_encrypted", sa.Text(), nullable=True))
    op.add_column(
        "users", sa.Column("mfa_enabled", sa.Boolean(), server_default="false", nullable=False)
    )
    op.add_column(
        "users",
        sa.Column(
            "mfa_recovery_codes",
            postgresql.ARRAY(sa.String()),
            nullable=True,
        ),
    )
    op.add_column(
        "users", sa.Column("mfa_last_used_counter", sa.Integer(), server_default="0", nullable=False)
    )
    op.add_column(
        "users", sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "users", sa.Column("deletion_scheduled_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "users",
        sa.Column("verification_token_expires", sa.DateTime(timezone=True), nullable=True),
    )

    # --- API Keys ---
    op.add_column(
        "api_keys",
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # --- Organization Invitations ---
    op.create_table(
        "organization_invitations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), server_default="member"),
        sa.Column("invited_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_organization_invitations_org_id",
        "organization_invitations",
        ["organization_id"],
    )


def downgrade() -> None:
    op.drop_table("organization_invitations")
    op.drop_column("api_keys", "created_by")
    op.drop_column("users", "verification_token_expires")
    op.drop_column("users", "deletion_scheduled_at")
    op.drop_column("users", "deactivated_at")
    op.drop_column("users", "mfa_last_used_counter")
    op.drop_column("users", "mfa_recovery_codes")
    op.drop_column("users", "mfa_enabled")
    op.drop_column("users", "mfa_secret_encrypted")
    op.drop_column("users", "avatar_url")
