from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.domain import (
    ConfirmationStatus,
    Direction,
    EvidenceLink,
    EvidenceLinkStatus,
    EvidenceLinkType,
    EvidenceRecord,
    EvidenceType,
    LifecycleStatus,
    ReviewStatus,
    SourceDocument,
    SourceDocumentStatus,
    SourceQuality,
    SourceType,
    SpendingEvent,
    build_evidence_fingerprint,
    build_source_document_fingerprint,
)

from .receipt_parser import parse_receipt_text


@dataclass(frozen=True, slots=True)
class ReceiptImportResult:
    source_document: SourceDocument
    evidence_record: EvidenceRecord
    spending_event: SpendingEvent
    evidence_link: EvidenceLink


def import_receipt_text(
    *,
    raw_text: str,
    now: datetime | None = None,
    source_document_id: str = "src_receipt_1",
    evidence_record_id: str = "ev_receipt_1",
    spending_event_id: str = "evt_receipt_1",
    evidence_link_id: str = "link_receipt_1",
    filename: str | None = None,
) -> ReceiptImportResult:
    created_at = now or datetime.now(timezone.utc)
    parsed = parse_receipt_text(raw_text)

    source_fingerprint = build_source_document_fingerprint(
        source_type=SourceType.RECEIPT_TEXT,
        raw_text=raw_text,
        filename=filename,
    )
    source_document = SourceDocument(
        id=source_document_id,
        source_type=SourceType.RECEIPT_TEXT,
        status=SourceDocumentStatus.PARSED,
        filename=filename,
        raw_text=raw_text,
        fingerprint=source_fingerprint,
        created_at=created_at,
    )
    evidence_fingerprint = build_evidence_fingerprint(
        source_document_id=source_document.id,
        evidence_type=EvidenceType.RECEIPT,
        fields={
            "merchant_raw": parsed.merchant_raw,
            "occurred_at": parsed.occurred_at.isoformat() if parsed.occurred_at else None,
            "amount_minor": parsed.amount_minor,
            "currency": parsed.currency,
        },
    )
    evidence_record = EvidenceRecord(
        id=evidence_record_id,
        source_document_id=source_document.id,
        evidence_type=EvidenceType.RECEIPT,
        merchant_raw=parsed.merchant_raw,
        merchant_normalized=parsed.merchant_normalized,
        occurred_at=parsed.occurred_at,
        amount_minor=parsed.amount_minor,
        currency=parsed.currency,
        extraction_confidence=parsed.confidence,
        fingerprint=evidence_fingerprint,
        raw_payload_json=None,
        warnings=parsed.warnings,
        created_at=created_at,
    )
    review_status = ReviewStatus.NEEDS_REVIEW if parsed.warnings else ReviewStatus.CLEAR
    spending_event = SpendingEvent(
        id=spending_event_id,
        occurred_at=parsed.occurred_at or created_at,
        merchant_normalized=parsed.merchant_normalized or "Unknown Merchant",
        amount_minor=parsed.amount_minor or 0,
        currency=parsed.currency,
        direction=Direction.EXPENSE,
        confirmation_status=ConfirmationStatus.PROVISIONAL,
        review_status=review_status,
        lifecycle_status=LifecycleStatus.ACTIVE,
        source_quality=SourceQuality.RECEIPT_ONLY,
        created_at=created_at,
        updated_at=created_at,
        canonical_source_evidence_id=evidence_record.id,
    )
    evidence_link = EvidenceLink(
        id=evidence_link_id,
        spending_event_id=spending_event.id,
        evidence_record_id=evidence_record.id,
        link_type=EvidenceLinkType.CREATED_FROM,
        status=EvidenceLinkStatus.CONFIRMED,
        created_at=created_at,
    )
    return ReceiptImportResult(source_document, evidence_record, spending_event, evidence_link)
