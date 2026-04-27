from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class SourceDocumentRow(Base):
    __tablename__ = "source_documents"
    __table_args__ = (UniqueConstraint("fingerprint", name="uq_source_documents_fingerprint"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    filename: Mapped[str | None] = mapped_column(String, nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str | None] = mapped_column(String, nullable=True)
    fingerprint: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class EvidenceRecordRow(Base):
    __tablename__ = "evidence_records"
    __table_args__ = (UniqueConstraint("fingerprint", name="uq_evidence_records_fingerprint"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    source_document_id: Mapped[str] = mapped_column(ForeignKey("source_documents.id"), nullable=False)
    evidence_type: Mapped[str] = mapped_column(String, nullable=False)
    merchant_raw: Mapped[str | None] = mapped_column(String, nullable=True)
    merchant_normalized: Mapped[str | None] = mapped_column(String, nullable=True)
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    amount_minor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str | None] = mapped_column(String, nullable=True)
    description_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    extraction_confidence: Mapped[int] = mapped_column(Integer, nullable=False)
    fingerprint: Mapped[str] = mapped_column(String, nullable=False)
    raw_payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    warnings: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SpendingEventRow(Base):
    __tablename__ = "spending_events"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    merchant_normalized: Mapped[str] = mapped_column(String, nullable=False)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False)
    direction: Mapped[str] = mapped_column(String, nullable=False)
    category_id: Mapped[str | None] = mapped_column(String, nullable=True)
    confirmation_status: Mapped[str] = mapped_column(String, nullable=False)
    review_status: Mapped[str] = mapped_column(String, nullable=False)
    lifecycle_status: Mapped[str] = mapped_column(String, nullable=False)
    source_quality: Mapped[str] = mapped_column(String, nullable=False)
    canonical_source_evidence_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class EvidenceLinkRow(Base):
    __tablename__ = "evidence_links"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    spending_event_id: Mapped[str] = mapped_column(ForeignKey("spending_events.id"), nullable=False)
    evidence_record_id: Mapped[str] = mapped_column(ForeignKey("evidence_records.id"), nullable=False)
    link_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    match_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MatchCandidateRow(Base):
    __tablename__ = "match_candidates"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    spending_event_id: Mapped[str] = mapped_column(ForeignKey("spending_events.id"), nullable=False)
    statement_evidence_record_id: Mapped[str] = mapped_column(
        ForeignKey("evidence_records.id"), nullable=False
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    decision: Mapped[str] = mapped_column(String, nullable=False)
    reasons: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CategoryRow(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MappingRuleRow(Base):
    __tablename__ = "mapping_rules"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    pattern: Mapped[str] = mapped_column(String, nullable=False)
    pattern_type: Mapped[str] = mapped_column(String, nullable=False)
    category_id: Mapped[str] = mapped_column(ForeignKey("categories.id"), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    created_from_review: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
