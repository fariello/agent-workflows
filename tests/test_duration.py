"""Unit tests for age duration parsing."""

from __future__ import annotations

import unittest
from agent_workflows.duration import parse_age_duration


class DurationParserTests(unittest.TestCase):
    def test_default_none_and_empty(self):
        self.assertEqual(parse_age_duration(None), 14.0)
        self.assertEqual(parse_age_duration(None, default_days=30.0), 30.0)
        self.assertEqual(parse_age_duration(""), 14.0)
        self.assertEqual(parse_age_duration("   "), 14.0)

    def test_raw_numbers(self):
        self.assertEqual(parse_age_duration(14), 14.0)
        self.assertEqual(parse_age_duration(7.5), 7.5)
        self.assertEqual(parse_age_duration(0), 0.0)
        with self.assertRaises(ValueError):
            parse_age_duration(-1)

    def test_units(self):
        # hours
        self.assertAlmostEqual(parse_age_duration("1h"), 1.0 / 24.0)
        self.assertAlmostEqual(parse_age_duration("24h"), 1.0)
        self.assertAlmostEqual(parse_age_duration("12H"), 0.5)

        # days
        self.assertEqual(parse_age_duration("5d"), 5.0)
        self.assertEqual(parse_age_duration("14D"), 14.0)
        self.assertEqual(parse_age_duration("14"), 14.0)
        self.assertEqual(parse_age_duration("0.5d"), 0.5)

        # weeks
        self.assertEqual(parse_age_duration("1w"), 7.0)
        self.assertEqual(parse_age_duration("10w"), 70.0)
        self.assertEqual(parse_age_duration("2W"), 14.0)

        # months (30 days)
        self.assertEqual(parse_age_duration("1m"), 30.0)
        self.assertEqual(parse_age_duration("4m"), 120.0)
        self.assertEqual(parse_age_duration("0.5m"), 15.0)

        # years (365 days)
        self.assertEqual(parse_age_duration("1y"), 365.0)
        self.assertEqual(parse_age_duration("2Y"), 730.0)

    def test_invalid_strings(self):
        invalid_inputs = ["abc", "10x", "h", "-5d", "10 days", "10w5d", "1.2.3"]
        for inp in invalid_inputs:
            with self.assertRaises(ValueError) as ctx:
                parse_age_duration(inp)
            self.assertIn("invalid age duration", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
