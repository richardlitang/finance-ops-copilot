from datetime import datetime, timezone
import unittest

from app.domain import ConfirmationStatus, EvidenceType, ReviewStatus, SourceQuality
from app.services.import_service import import_receipt_text, import_statement_csv


class ImportServiceTests(unittest.TestCase):
    def test_import_receipt_text_creates_provisional_event_with_evidence_link(self):
        result = import_receipt_text(
            raw_text="ALDI BE\nDate: 17/04/2026\nTotal: €42,97 EUR",
            now=datetime(2026, 4, 17, 12, 0, tzinfo=timezone.utc),
            filename="aldi.txt",
        )

        self.assertEqual(result.source_document.fingerprint, result.source_document.fingerprint)
        self.assertEqual(result.evidence_record.evidence_type, EvidenceType.RECEIPT)
        self.assertEqual(result.evidence_record.amount_minor, 4297)
        self.assertEqual(result.spending_event.confirmation_status, ConfirmationStatus.PROVISIONAL)
        self.assertEqual(result.spending_event.review_status, ReviewStatus.CLEAR)
        self.assertEqual(result.spending_event.source_quality, SourceQuality.RECEIPT_ONLY)
        self.assertEqual(result.spending_event.canonical_source_evidence_id, result.evidence_record.id)
        self.assertEqual(result.evidence_link.spending_event_id, result.spending_event.id)
        self.assertEqual(result.evidence_link.evidence_record_id, result.evidence_record.id)

    def test_import_receipt_text_routes_parse_warnings_to_review(self):
        result = import_receipt_text(
            raw_text="ALDI BE\nDate: 17/04/2026",
            now=datetime(2026, 4, 17, 12, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(result.spending_event.review_status, ReviewStatus.NEEDS_REVIEW)
        self.assertIn("missing_total", result.evidence_record.warnings)

    def test_import_receipt_text_uses_stable_evidence_fingerprint_across_generated_ids(self):
        first = import_receipt_text(
            raw_text="ALDI BE\nDate: 17/04/2026\nTotal: €42,97 EUR",
            source_document_id="src_1",
            evidence_record_id="ev_1",
        )
        second = import_receipt_text(
            raw_text="ALDI BE\nDate: 17/04/2026\nTotal: €42,97 EUR",
            source_document_id="src_2",
            evidence_record_id="ev_2",
        )

        self.assertEqual(first.evidence_record.fingerprint, second.evidence_record.fingerprint)

    def test_import_statement_csv_auto_confirms_existing_receipt_event(self):
        receipt = import_receipt_text(
            raw_text="ALDI\nDate: 17/04/2026\nTotal: €42,97 EUR",
            now=datetime(2026, 4, 17, 12, 0, tzinfo=timezone.utc),
        )

        result = import_statement_csv(
            raw_csv="date,posted_date,description,merchant,amount,currency\n2026-04-17,2026-04-18,ALDI,ALDI,42.97,EUR",
            existing_events=[receipt.spending_event],
            now=datetime(2026, 4, 20, 12, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(len(result.evidence_records), 1)
        self.assertEqual(len(result.spending_events), 1)
        self.assertEqual(result.spending_events[0].confirmation_status, ConfirmationStatus.CONFIRMED)
        self.assertEqual(result.spending_events[0].source_quality, SourceQuality.RECEIPT_AND_STATEMENT)
        self.assertEqual(result.evidence_links[0].evidence_record_id, result.evidence_records[0].id)
        self.assertEqual(result.match_candidates[0].decision, "auto_confirm")

    def test_import_statement_csv_creates_statement_only_event_when_unmatched(self):
        result = import_statement_csv(
            raw_csv="date,description,merchant,amount,currency\n2026-04-19,Netflix,Netflix,15.99,EUR",
            existing_events=[],
            now=datetime(2026, 4, 20, 12, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(len(result.spending_events), 1)
        self.assertEqual(result.spending_events[0].confirmation_status, ConfirmationStatus.CONFIRMED)
        self.assertEqual(result.spending_events[0].source_quality, SourceQuality.STATEMENT_ONLY)


if __name__ == "__main__":
    unittest.main()
