from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260427_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "source_documents",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("filename", sa.String(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("file_path", sa.String(), nullable=True),
        sa.Column("fingerprint", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("fingerprint", name="uq_source_documents_fingerprint"),
    )
    op.create_table(
        "evidence_records",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("source_document_id", sa.String(), sa.ForeignKey("source_documents.id"), nullable=False),
        sa.Column("evidence_type", sa.String(), nullable=False),
        sa.Column("merchant_raw", sa.String(), nullable=True),
        sa.Column("merchant_normalized", sa.String(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("amount_minor", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(), nullable=True),
        sa.Column("description_raw", sa.Text(), nullable=True),
        sa.Column("extraction_confidence", sa.Integer(), nullable=False),
        sa.Column("fingerprint", sa.String(), nullable=False),
        sa.Column("raw_payload_json", sa.Text(), nullable=True),
        sa.Column("warnings", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("fingerprint", name="uq_evidence_records_fingerprint"),
    )
    op.create_table(
        "spending_events",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("merchant_normalized", sa.String(), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("direction", sa.String(), nullable=False),
        sa.Column("category_id", sa.String(), nullable=True),
        sa.Column("confirmation_status", sa.String(), nullable=False),
        sa.Column("review_status", sa.String(), nullable=False),
        sa.Column("lifecycle_status", sa.String(), nullable=False),
        sa.Column("source_quality", sa.String(), nullable=False),
        sa.Column("canonical_source_evidence_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "evidence_links",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("spending_event_id", sa.String(), sa.ForeignKey("spending_events.id"), nullable=False),
        sa.Column("evidence_record_id", sa.String(), sa.ForeignKey("evidence_records.id"), nullable=False),
        sa.Column("link_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("match_score", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "match_candidates",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("spending_event_id", sa.String(), sa.ForeignKey("spending_events.id"), nullable=False),
        sa.Column(
            "statement_evidence_record_id",
            sa.String(),
            sa.ForeignKey("evidence_records.id"),
            nullable=False,
        ),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("decision", sa.String(), nullable=False),
        sa.Column("reasons", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("match_candidates")
    op.drop_table("evidence_links")
    op.drop_table("spending_events")
    op.drop_table("evidence_records")
    op.drop_table("source_documents")

