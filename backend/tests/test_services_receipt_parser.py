import unittest

from app.services.receipt_parser import parse_receipt_text


class ReceiptParserTests(unittest.TestCase):
    def test_parse_receipt_text_extracts_core_fields(self):
        parsed = parse_receipt_text(
            """
            ALDI BE
            Date: 17/04/2026
            Bananas 2,50
            Total: €42,97 EUR
            """
        )

        self.assertEqual(parsed.merchant_raw, "ALDI BE")
        self.assertEqual(parsed.merchant_normalized, "Aldi Be")
        self.assertEqual(parsed.occurred_at.date().isoformat(), "2026-04-17")
        self.assertEqual(parsed.amount_minor, 4297)
        self.assertEqual(parsed.currency, "EUR")
        self.assertEqual(parsed.warnings, ())
        self.assertEqual(parsed.confidence, 1.0)

    def test_parse_receipt_text_warns_on_missing_total(self):
        parsed = parse_receipt_text(
            """
            ALDI BE
            Date: 2026-04-17
            """
        )

        self.assertIsNone(parsed.amount_minor)
        self.assertIn("missing_total", parsed.warnings)
        self.assertLess(parsed.confidence, 1.0)


if __name__ == "__main__":
    unittest.main()
