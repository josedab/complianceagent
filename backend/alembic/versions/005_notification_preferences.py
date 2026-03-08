"""Add notification preferences table.

Revision ID: 005_notification_preferences
Revises: 004_production_features
Create Date: 2026-03-07
"""

from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005_notification_preferences"
down_revision: Union[str, None] = "004_production_features"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "notification_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("email_enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("email_digest", sa.String(20), server_default="daily", nullable=False),
        sa.Column("slack_enabled", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("slack_webhook_url", sa.String(500), nullable=True),
        sa.Column("webhook_enabled", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("webhook_url", sa.String(2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_notification_preferences_user_id", "notification_preferences", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_notification_preferences_user_id", table_name="notification_preferences")
    op.drop_table("notification_preferences")
