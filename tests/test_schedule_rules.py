"""Regression tests for the correlated JEE calendar."""
import datetime as dt
import pathlib
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
with (ROOT / "config" / "tests.yml").open(encoding="utf-8") as handle:
    CALENDAR = yaml.safe_load(handle)["tests"]


class JEECalendarTests(unittest.TestCase):
    def test_calendar_is_chronological(self):
        dates = [item["date"] for item in CALENDAR]
        self.assertEqual(dates, sorted(dates))

    def test_seven_qpts_and_only_one_in_cycle_seven(self):
        qpts = [item for item in CALENDAR if item.get("kind") == "qpt"]
        self.assertEqual(len(qpts), 7)
        cycle_seven = [item for item in qpts if item.get("cycle") == 7]
        self.assertEqual(len(cycle_seven), 1)
        self.assertEqual(cycle_seven[0]["name"], "QPT 13 — Cycle 7 QPT")

    def test_no_qpt_on_aits_main_sundays_or_removed_conflict_dates(self):
        qpts = [item for item in CALENDAR if item.get("kind") == "qpt"]
        qpt_dates = {item["date"] for item in qpts}
        aits_main_dates = {
            dt.date(2026, 11, 29),
            dt.date(2026, 12, 13),
            dt.date(2026, 12, 27),
        }
        self.assertTrue(qpt_dates.isdisjoint(aits_main_dates))
        for removed_date in (
            dt.date(2026, 12, 12),
            dt.date(2026, 12, 26),
        ):
            self.assertNotIn(removed_date, qpt_dates)

    def test_diwali_pair_and_full_mock_phase_are_present(self):
        qpts = {item["name"]: item for item in CALENDAR if item.get("kind") == "qpt"}
        self.assertEqual(qpts["QPT 4"]["date"], dt.date(2026, 11, 7))
        self.assertEqual(qpts["QPT 1"]["date"], dt.date(2026, 11, 8))
        mocks = [item for item in CALENDAR if item.get("kind") == "full-mock"]
        self.assertEqual(len(mocks), 15)
        self.assertEqual(mocks[0]["date"], dt.date(2027, 1, 4))
        self.assertEqual(mocks[-1]["date"], dt.date(2027, 1, 20))


if __name__ == "__main__":
    unittest.main()
