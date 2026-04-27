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
from app.domain.models import MatchCandidate
from app.domain.reconciliation import apply_statement_confirmation, build_match_candidate

from .receipt_parser import parse_receipt_text
from .statement_parser import parse_statement_csv


@dataclass(frozen=True, slots=True)
class ReceiptImportResult:
    source_document: SourceDocument
    evidence_record: EvidenceRecord
    spending_event: SpendingEvent
    evidence_link: EvidenceLink


@dataclass(frozen=True, slots=True)
class StatementImportResult:
    source_document: SourceDocument
    evidence_records: tuple[EvidenceRecord, ...]
    spending_events: tuple[SpendingEvent, ...]
    evidence_links: tuple[EvidenceLink, ...]
    match_candidates: tuple[MatchCandidate, ...]


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
        source_document_id=source_fingerprint,
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


def import_statement_csv(
    *,
    raw_csv: str,
    existing_events: list[SpendingEvent],
    now: datetime | None = None,
    source_document_id: str = "src_statement_1",
    filename: str | None = None,
) -> StatementImportResult:
    created_at = now or datetime.now(timezone.utc)
    source_document = SourceDocument(
        id=source_document_id,
        source_type=SourceType.CARD_CSV,
        status=SourceDocumentStatus.PARSED,
        filename=filename,
        raw_text=raw_csv,
        fingerprint=build_source_document_fingerprint(
            source_type=SourceType.CARD_CSV,
            raw_text=raw_csv,
            filename=filename,
        ),
        created_at=created_at,
    )
    source_fingerprint = source_document.fingerprint or source_document.id

    evidence_records: list[EvidenceRecord] = []
    spending_events: list[SpendingEvent] = list(existing_events)
    links: list[EvidenceLink] = []
    candidates: list[MatchCandidate] = []

    for row in parse_statement_csv(raw_csv):
        evidence_id = f"ev_statement_{row.row_index}"
        evidence = EvidenceRecord(
            id=evidence_id,
            source_document_id=source_document.id,
            evidence_type=EvidenceType.STATEMENT_ROW,
            merchant_raw=row.merchant_raw,
            merchant_normalized=row.merchant_normalized,
            occurred_at=row.occurred_at,
            posted_at=row.posted_at,
            amount_minor=row.amount_minor,
            currency=row.currency,
            description_raw=row.description_raw,
            extraction_confidence=1.0,
            fingerprint=build_evidence_fingerprint(
                source_document_id=source_fingerprint,
                evidence_type=EvidenceType.STATEMENT_ROW,
                fields={
                    "row_index": row.row_index,
                    "occurred_at": row.occurred_at.isoformat(),
                    "description_raw": row.description_raw,
                    "amount_minor": row.amount_minor,
                    "currency": row.currency,
                },
            ),
            warnings=row.warnings,
            created_at=created_at,
        )
        evidence_records.append(evidence)

        best_candidate: MatchCandidate | None = None
        for event in spending_events:
            if event.confirmation_status is not ConfirmationStatus.PROVISIONAL:
                continue
            candidate = build_match_candidate(
                candidate_id=f"match_{row.row_index}_{event.id}",
                event=event,
                statement=evidence,
                created_at=created_at,
            )
            if candidate.decision != "no_match":
                candidates.append(candidate)
            if best_candidate is None or candidate.score > best_candidate.score:
                best_candidate = candidate

        if best_candidate and best_candidate.decision == "auto_confirm":
            event = next(item for item in spending_events if item.id == best_candidate.spending_event_id)
            confirmed, link = apply_statement_confirmation(
                event,
                evidence,
                link_id=f"link_statement_{row.row_index}",
                matched_at=created_at,
                match_score=best_candidate.score,
            )
            spending_events = [confirmed if item.id == confirmed.id else item for item in spending_events]
            links.append(link)
            continue

        event = SpendingEvent(
            id=f"evt_statement_{row.row_index}",
            occurred_at=row.occurred_at,
            posted_at=row.posted_at,
            merchant_normalized=row.merchant_normalized,
            amount_minor=row.amount_minor,
            currency=row.currency,
            direction=Direction.EXPENSE if row.amount_minor >= 0 else Direction.INCOME,
            confirmation_status=ConfirmationStatus.CONFIRMED,
            review_status=ReviewStatus.CLEAR,
            lifecycle_status=LifecycleStatus.ACTIVE,
            source_quality=SourceQuality.STATEMENT_ONLY,
            created_at=created_at,
            updated_at=created_at,
            canonical_source_evidence_id=evidence.id,
        )
        spending_events.append(event)
        links.append(
            EvidenceLink(
                id=f"link_statement_{row.row_index}",
                spending_event_id=event.id,
                evidence_record_id=evidence.id,
                link_type=EvidenceLinkType.CREATED_FROM,
                status=EvidenceLinkStatus.CONFIRMED,
                created_at=created_at,
            )
        )

    return StatementImportResult(
        source_document=source_document,
        evidence_records=tuple(evidence_records),
        spending_events=tuple(spending_events),
        evidence_links=tuple(links),
        match_candidates=tuple(candidates),
    )
