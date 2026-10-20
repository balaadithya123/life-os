"""Offline tests for schedule intake."""
import sys, unittest
from datetime import date
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import schedule_intake as intake

class ScheduleIntakeTests(unittest.TestCase):
    def test_parse_iso_and_text_dates(self):
        daily, events, warnings, rows = intake.parse_schedule_text(
            "2026-11-08 Physics: Electrostatics\n29 Nov 2026 AITS Full Test 1 — JEE Main\n2026-12-28 QPT 13 All Class 11\n")
        self.assertEqual(daily[0]["date"], "2026-11-08")
        self.assertEqual(events[0]["date"], "2026-11-29")
        self.assertEqual(events[0]["kind"], "aits-main")
        self.assertEqual(events[1]["kind"], "qpt")
        self.assertEqual(len(warnings), 0)
        self.assertEqual(len(rows), 3)
    def test_invalid_date_and_unclassified_warning(self):
        daily, events, warnings, rows = intake.parse_schedule_text("2026-13-40 Physics: Rotation\n2026-11-02 Important announcement\n")
        self.assertEqual(daily, [])
        self.assertEqual(events, [])
        self.assertEqual(len(warnings), 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["text"], "Important announcement")
    def test_no_qpt_on_aits_main_sunday(self):
        tests = {"tests": [{"name":"AITS Full Test","date":date(2026,11,29),"kind":"aits-main"}]}
        events = [{"name":"QPT 6","date":"2026-11-29","kind":"qpt","source_line":1}]
        _, changes, conflicts = intake.compare_with_authoritative([], events, {"daily":{},"cycles":[]}, tests)
        self.assertEqual(changes[0]["change"], "date-conflict-review")
        self.assertTrue(any(c["rule"] == "No QPT on an AITS Main Sunday" for c in conflicts))
    def test_cycle_7_only_one_qpt(self):
        tests = {"tests": [{"name":"QPT 13","date":date(2026,12,28),"kind":"qpt"}]}
        events = [{"name":"QPT 12","date":"2026-12-30","kind":"qpt","source_line":2}]
        _, _, conflicts = intake.compare_with_authoritative([], events, {"daily":{},"cycles":[]}, tests)
        self.assertTrue(any(c["rule"] == "Cycle 7 allows only one QPT" for c in conflicts))
    def test_existing_daily_is_compared_not_overwritten(self):
        plan = {"daily":{"2026-11-08":["Physics: Kinematics"]},"cycles":[]}
        daily = [{"date":"2026-11-08","chapters":["Physics: Electrostatics"],"source_line":1}]
        changes, _, _ = intake.compare_with_authoritative(daily, [], plan, {"tests":[]})
        self.assertEqual(changes[0]["existing"], ["Physics: Kinematics"])
        self.assertEqual(changes[0]["proposed"], ["Physics: Electrostatics"])

if __name__ == "__main__": unittest.main()
