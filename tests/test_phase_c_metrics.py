import pathlib
import sys
import unittest
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import phase_c_metrics as metrics


class PhaseCMetricsTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 21, 12, tzinfo=timezone.utc)

    def test_sampled_health_rate_is_calculated_from_timestamped_samples(self):
        observations = [
            {"project": "demo", "status": "ok", "observed_at": "2026-10-20T10:00:00Z"},
            {"project": "demo", "status": "incident", "category": "http-5xx", "observed_at": "2026-10-20T11:00:00Z"},
        ]
        report = metrics.build_report(observations, [], [], now=self.now)
        self.assertIn("1/2 checks (50.0%)", report)
        self.assertIn("not an SLA uptime measurement", report)

    def test_repeated_incident_is_prioritised(self):
        observations = [
            {"project": "demo", "status": "incident", "category": "http-5xx", "observed_at": "2026-10-20T10:00:00Z"},
            {"project": "demo", "status": "incident", "category": "http-5xx", "observed_at": "2026-10-20T11:00:00Z"},
        ]
        report = metrics.build_report(observations, [], [], now=self.now)
        self.assertIn("observed 2 times", report)
        self.assertIn("recurring demo signal", report.lower())

    def test_recovery_interval_is_labelled_as_sample_interval(self):
        observations = [
            {"project": "demo", "status": "incident", "observed_at": "2026-10-20T10:00:00Z"},
            {"project": "demo", "status": "ok", "observed_at": "2026-10-20T13:00:00Z"},
        ]
        report = metrics.build_report(observations, [], [], now=self.now)
        self.assertIn("mean 3.0 hours", report)
        self.assertIn("not the exact incident duration", report)

    def test_missing_data_is_not_reported_as_zero_failure(self):
        report = metrics.build_report([], [], [], now=self.now)
        self.assertIn("unavailable", report)
        self.assertNotIn("0.0%", report)
        self.assertIn("data coverage gap", report)

    def test_deployment_rate_only_uses_timestamped_records(self):
        deployments = [
            {"status": "success", "deployed_at": "2026-10-20T10:00:00Z"},
            {"status": "failure", "deployed_at": "2026-10-20T11:00:00Z"},
            {"status": "failure"},
        ]
        report = metrics.build_report([], [], deployments, now=self.now)
        self.assertIn("1/2 (50.0%)", report)
        self.assertIn("no timestamped deployment records", report.lower() if "no timestamped deployment records" in report.lower() else "timestamped deployment records")

    def test_old_and_future_samples_are_excluded(self):
        observations = [
            {"project": "demo", "status": "ok", "observed_at": "2026-09-01T10:00:00Z"},
            {"project": "demo", "status": "incident", "observed_at": "2026-10-22T10:00:00Z"},
        ]
        report = metrics.build_report(observations, [], [], now=self.now)
        self.assertIn("unavailable", report)


if __name__ == "__main__":
    unittest.main()
