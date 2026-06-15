from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

from reminder_bot.time_parser import parse_local_datetime


class TimeParserTest(unittest.TestCase):
    def setUp(self) -> None:
        self.timezone = timezone(timedelta(hours=9), "JST")

    def test_parse_local_absolute_datetime(self) -> None:
        parsed = parse_local_datetime("2026-06-20 18:00", self.timezone)

        self.assertEqual(datetime(2026, 6, 20, 18, 0, tzinfo=self.timezone), parsed)

    def test_parse_relative_minutes(self) -> None:
        now = datetime(2026, 6, 20, 18, 0, tzinfo=self.timezone)

        parsed = parse_local_datetime("10m", self.timezone, now=now)

        self.assertEqual(datetime(2026, 6, 20, 18, 10, tzinfo=self.timezone), parsed)

    def test_parse_quoted_relative_minutes(self) -> None:
        now = datetime(2026, 6, 20, 18, 0, tzinfo=self.timezone)

        parsed = parse_local_datetime('"10m"', self.timezone, now=now)

        self.assertEqual(datetime(2026, 6, 20, 18, 10, tzinfo=self.timezone), parsed)

    def test_parse_quoted_absolute_datetime(self) -> None:
        parsed = parse_local_datetime('"2026-06-20 18:00"', self.timezone)

        self.assertEqual(datetime(2026, 6, 20, 18, 0, tzinfo=self.timezone), parsed)

    def test_parse_relative_hours(self) -> None:
        now = datetime(2026, 6, 20, 18, 0, tzinfo=self.timezone)

        parsed = parse_local_datetime("2h", self.timezone, now=now)

        self.assertEqual(datetime(2026, 6, 20, 20, 0, tzinfo=self.timezone), parsed)

    def test_parse_relative_days(self) -> None:
        now = datetime(2026, 6, 20, 18, 0, tzinfo=self.timezone)

        parsed = parse_local_datetime("3d", self.timezone, now=now)

        self.assertEqual(datetime(2026, 6, 23, 18, 0, tzinfo=self.timezone), parsed)

    def test_rejects_empty_datetime(self) -> None:
        with self.assertRaises(ValueError):
            parse_local_datetime(" ", self.timezone)

    def test_rejects_invalid_datetime(self) -> None:
        with self.assertRaises(ValueError):
            parse_local_datetime("not-a-date", self.timezone)

    def test_parse_timezone_aware_iso_datetime(self) -> None:
        parsed = parse_local_datetime("2026-06-20T09:00:00+00:00", self.timezone)

        self.assertEqual(datetime(2026, 6, 20, 18, 0, tzinfo=self.timezone), parsed)


if __name__ == "__main__":
    unittest.main()
