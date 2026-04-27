import unittest

from app.domain import build_evidence_fingerprint, build_source_document_fingerprint


class FingerprintTests(unittest.TestCase):
    def test_source_document_fingerprint_is_stable_for_equivalent_receipt_text(self):
        a = build_source_document_fingerprint(
            source_type="receipt_text",
            raw_text="ALDI\nTotal: 42,97 EUR",
            filename="aldi.txt",
        )
        b = build_source_document_fingerprint(
            source_type=" receipt_text ",
            raw_text="  aldi  total:   42,97 eur ",
            filename="ALDI.TXT",
        )

        self.assertEqual(a, b)

    def test_evidence_fingerprint_is_order_independent(self):
        a = build_evidence_fingerprint(
            source_document_id="src_1",
            evidence_type="statement_row",
            fields={
                "raw_date": "2026-04-18",
                "raw_description": "ALDI BE",
                "raw_amount": "43.00",
            },
        )
        b = build_evidence_fingerprint(
            source_document_id="src_1",
            evidence_type="statement_row",
            fields={
                "raw_amount": "43.00",
                "raw_description": " aldi   be ",
                "raw_date": "2026-04-18",
            },
        )

        self.assertEqual(a, b)

    def test_evidence_fingerprint_changes_when_source_row_changes(self):
        a = build_evidence_fingerprint(
            source_document_id="src_1",
            evidence_type="statement_row",
            fields={"raw_date": "2026-04-18", "raw_description": "ALDI BE", "raw_amount": "43.00"},
        )
        b = build_evidence_fingerprint(
            source_document_id="src_1",
            evidence_type="statement_row",
            fields={"raw_date": "2026-04-18", "raw_description": "NETFLIX", "raw_amount": "43.00"},
        )

        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
