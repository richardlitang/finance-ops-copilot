from datetime import datetime, timezone
import unittest

from app.domain import (
    ConfirmationStatus,
    Direction,
    EvidenceType,
    LifecycleStatus,
    ReviewStatus,
    SourceQuality,
)
from app.domain.models import EvidenceRecord, SpendingEvent
from app.domain.reconciliation import ReconciliationError, apply_statement_confirmation
from app.domain.reconciliation import build_match_candidate, score_statement_match


def dt(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


class StatementConfirmationTests(unittest.TestCase):
    def test_statement_confirmation_updates_canonical_event_and_preserves_receipt_evidence(self):
        receipt = EvidenceRecord(
            id="ev_receipt_1",
            source_document_id="src_receipt_1",
            evidence_type=EvidenceType.RECEIPT,
            merchant_raw="Aldi receipt",
            merchant_normalized="Aldi",
            occurred_at=dt("2026-04-17T10:00:00"),
            amount_minor=4297,
            currency="EUR",
            extraction_confidence=0.92,
            fingerprint="receipt-fingerprint",
            created_at=dt("2026-04-17T10:03:00"),
            raw_payload_json='{"total":"42,97"}',
        )
        event = SpendingEvent(
            id="evt_1",
            occurred_at=receipt.occurred_at,
            merchant_normalized=receipt.merchant_normalized,
            amount_minor=receipt.amount_minor,
            currency=receipt.currency,
            direction=Direction.EXPENSE,
            confirmation_status=ConfirmationStatus.PROVISIONAL,
            review_status=ReviewStatus.CLEAR,
            lifecycle_status=LifecycleStatus.ACTIVE,
            source_quality=SourceQuality.RECEIPT_ONLY,
            created_at=dt("2026-04-17T10:03:00"),
            updated_at=dt("2026-04-17T10:03:00"),
            canonical_source_evidence_id=receipt.id,
        )
        statement = EvidenceRecord(
            id="ev_statement_1",
            source_document_id="src_statement_1",
            evidence_type=EvidenceType.STATEMENT_ROW,
            merchant_raw="ALDI BE",
            merchant_normalized="Aldi",
            occurred_at=dt("2026-04-17T00:00:00"),
            posted_at=dt("2026-04-18T00:00:00"),
            amount_minor=4300,
            currency="EUR",
            extraction_confidence=1.0,
            fingerprint="statement-row-fingerprint",
            created_at=dt("2026-04-20T08:00:00"),
        )

        confirmed, link = apply_statement_confirmation(
            event,
            statement,
            link_id="link_1",
            matched_at=dt("2026-04-20T08:01:00"),
            match_score=86,
        )

        self.assertEqual(confirmed.amount_minor, 4300)
        self.assertEqual(confirmed.posted_at, statement.posted_at)
        self.assertEqual(confirmed.confirmation_status, ConfirmationStatus.CONFIRMED)
        self.assertEqual(confirmed.source_quality, SourceQuality.RECEIPT_AND_STATEMENT)
        self.assertEqual(confirmed.canonical_source_evidence_id, statement.id)
        self.assertEqual(link.evidence_record_id, statement.id)
        self.assertEqual(link.spending_event_id, event.id)
        self.assertEqual(link.match_score, 86)

        self.assertEqual(receipt.amount_minor, 4297)
        self.assertEqual(receipt.raw_payload_json, '{"total":"42,97"}')
        self.assertEqual(event.amount_minor, 4297)
        self.assertEqual(event.confirmation_status, ConfirmationStatus.PROVISIONAL)

    def test_statement_confirmation_rejects_receipt_evidence(self):
        event = SpendingEvent(
            id="evt_1",
            occurred_at=dt("2026-04-17T10:00:00"),
            merchant_normalized="Aldi",
            amount_minor=4297,
            currency="EUR",
            direction=Direction.EXPENSE,
            confirmation_status=ConfirmationStatus.PROVISIONAL,
            review_status=ReviewStatus.CLEAR,
            lifecycle_status=LifecycleStatus.ACTIVE,
            source_quality=SourceQuality.RECEIPT_ONLY,
            created_at=dt("2026-04-17T10:03:00"),
            updated_at=dt("2026-04-17T10:03:00"),
        )
        receipt = EvidenceRecord(
            id="ev_receipt_1",
            source_document_id="src_receipt_1",
            evidence_type=EvidenceType.RECEIPT,
            extraction_confidence=0.92,
            fingerprint="receipt-fingerprint",
            amount_minor=4297,
            currency="EUR",
            created_at=dt("2026-04-17T10:03:00"),
        )

        with self.assertRaises(ReconciliationError):
            apply_statement_confirmation(
                event,
                receipt,
                link_id="link_1",
                matched_at=dt("2026-04-20T08:01:00"),
                match_score=86,
            )

    def test_score_statement_match_auto_confirms_exact_amount_date_and_merchant(self):
        event = SpendingEvent(
            id="evt_1",
            occurred_at=dt("2026-04-17T10:00:00"),
            merchant_normalized="Aldi",
            amount_minor=4297,
            currency="EUR",
            direction=Direction.EXPENSE,
            confirmation_status=ConfirmationStatus.PROVISIONAL,
            review_status=ReviewStatus.CLEAR,
            lifecycle_status=LifecycleStatus.ACTIVE,
            source_quality=SourceQuality.RECEIPT_ONLY,
            created_at=dt("2026-04-17T10:03:00"),
            updated_at=dt("2026-04-17T10:03:00"),
        )
        statement = EvidenceRecord(
            id="ev_statement_1",
            source_document_id="src_statement_1",
            evidence_type=EvidenceType.STATEMENT_ROW,
            merchant_normalized="Aldi",
            occurred_at=dt("2026-04-17T00:00:00"),
            amount_minor=4297,
            currency="EUR",
            extraction_confidence=1.0,
            fingerprint="statement-row-fingerprint",
            created_at=dt("2026-04-20T08:00:00"),
        )

        score, reasons = score_statement_match(event, statement)
        candidate = build_match_candidate(
            candidate_id="match_1",
            event=event,
            statement=statement,
            created_at=dt("2026-04-20T08:01:00"),
        )

        self.assertGreaterEqual(score, 80)
        self.assertIn("exact_amount", reasons)
        self.assertEqual(candidate.decision, "auto_confirm")

    def test_score_statement_match_routes_medium_confidence_to_review(self):
        event = SpendingEvent(
            id="evt_1",
            occurred_at=dt("2026-04-17T10:00:00"),
            merchant_normalized="Aldi",
            amount_minor=4297,
            currency="EUR",
            direction=Direction.EXPENSE,
            confirmation_status=ConfirmationStatus.PROVISIONAL,
            review_status=ReviewStatus.CLEAR,
            lifecycle_status=LifecycleStatus.ACTIVE,
            source_quality=SourceQuality.RECEIPT_ONLY,
            created_at=dt("2026-04-17T10:03:00"),
            updated_at=dt("2026-04-17T10:03:00"),
        )
        statement = EvidenceRecord(
            id="ev_statement_1",
            source_document_id="src_statement_1",
            evidence_type=EvidenceType.STATEMENT_ROW,
            merchant_normalized="Different Shop",
            occurred_at=dt("2026-04-30T00:00:00"),
            amount_minor=4297,
            currency="EUR",
            extraction_confidence=1.0,
            fingerprint="statement-row-fingerprint",
            created_at=dt("2026-04-20T08:00:00"),
        )

        candidate = build_match_candidate(
            candidate_id="match_1",
            event=event,
            statement=statement,
            created_at=dt("2026-04-20T08:01:00"),
        )

        self.assertEqual(candidate.score, 60)
        self.assertEqual(candidate.decision, "needs_review")


if __name__ == "__main__":
    unittest.main()
