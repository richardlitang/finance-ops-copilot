from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260427_0002"
down_revision = "20260427_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "mapping_rules",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("pattern", sa.String(), nullable=False),
        sa.Column("pattern_type", sa.String(), nullable=False),
        sa.Column("category_id", sa.String(), sa.ForeignKey("categories.id"), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("created_from_review", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("mapping_rules")
    op.drop_table("categories")
