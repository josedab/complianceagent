"""Add health_scores table.

Revision ID: 007_health_scores
Revises: 006_remaining_models
Create Date: 2026-03-08

Persists compliance health scores computed by the ScoreCalculator service.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007_health_scores"
down_revision: str | None = "006_remaining_models"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "health_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "repository_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            index=True,
        ),
        sa.Column("overall_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("grade", sa.String(5), nullable=False, server_default="F"),
        sa.Column(
            "calculated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("trend", sa.String(20), server_default="stable"),
        sa.Column("trend_delta", sa.Float(), server_default="0"),
        sa.Column(
            "regulations_checked",
            postgresql.ARRAY(sa.String()),
            server_default="{}",
        ),
        sa.Column(
            "category_scores",
            postgresql.JSONB(),
            server_default="{}",
        ),
        sa.Column("total_controls", sa.Integer(), server_default="0"),
        sa.Column("passing_controls", sa.Integer(), server_default="0"),
        sa.Column("failing_controls", sa.Integer(), server_default="0"),
        sa.Column("not_applicable_controls", sa.Integer(), server_default="0"),
        sa.Column(
            "recommendations",
            postgresql.ARRAY(sa.String()),
            server_default="{}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Index for fast lookups: latest score per repository
    op.create_index(
        "ix_health_scores_repo_calculated",
        "health_scores",
        ["repository_id", "calculated_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_health_scores_repo_calculated", table_name="health_scores")
    op.drop_table("health_scores")
