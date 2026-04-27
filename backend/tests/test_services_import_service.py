from datetime import datetime, timezone
import unittest

from app.domain import ConfirmationStatus, EvidenceType, ReviewStatus, SourceQuality
from app.services.import_service import import_receipt_text


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


if __name__ == "__main__":
    unittest.main()
