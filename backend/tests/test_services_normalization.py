import unittest

from app.services.normalization import parse_amount_minor, parse_datetime, normalize_merchant


class NormalizationTests(unittest.TestCase):
    def test_parse_amount_minor_handles_eu_decimal_comma(self):
        self.assertEqual(parse_amount_minor("€ 1.234,56"), 123456)

    def test_parse_amount_minor_handles_us_decimal_point(self):
        self.assertEqual(parse_amount_minor("$1,234.56"), 123456)

    def test_parse_amount_minor_handles_negative_values(self):
        self.assertEqual(parse_amount_minor("-42.97"), -4297)

    def test_parse_datetime_accepts_supported_date_formats(self):
        self.assertEqual(parse_datetime("2026-04-17").date().isoformat(), "2026-04-17")
        self.assertEqual(parse_datetime("17/04/2026").date().isoformat(), "2026-04-17")

    def test_normalize_merchant_collapses_whitespace_and_title_cases(self):
        self.assertEqual(normalize_merchant("  aldi   be "), "Aldi Be")


if __name__ == "__main__":
    unittest.main()
