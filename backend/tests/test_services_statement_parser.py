import unittest

from app.services.statement_parser import parse_statement_csv


class StatementParserTests(unittest.TestCase):
    def test_parse_statement_csv_extracts_rows(self):
        rows = parse_statement_csv(
            """
date,posted_date,description,merchant,amount,currency
2026-04-17,2026-04-18,ALDI BE,ALDI BE,43.00,EUR
2026-04-19,2026-04-20,Netflix,,15.99,EUR
            """
        )

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].occurred_at.date().isoformat(), "2026-04-17")
        self.assertEqual(rows[0].posted_at.date().isoformat(), "2026-04-18")
        self.assertEqual(rows[0].amount_minor, 4300)
        self.assertEqual(rows[0].merchant_normalized, "Aldi Be")
        self.assertEqual(rows[1].merchant_normalized, "Netflix")

    def test_parse_statement_csv_requires_v1_columns(self):
        with self.assertRaises(ValueError):
            parse_statement_csv("date,description\n2026-04-17,ALDI BE")

    def test_parse_statement_csv_reports_row_context_for_invalid_values(self):
        with self.assertRaisesRegex(ValueError, r"row 2 column amount"):
            parse_statement_csv(
                """
date,posted_date,description,merchant,amount,currency
2026-04-17,2026-04-18,ALDI BE,ALDI BE,43.00,EUR
2026-04-19,2026-04-20,Netflix,Netflix,invalid,EUR
                """
            )


if __name__ == "__main__":
    unittest.main()
