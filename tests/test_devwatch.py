"""Offline regression tests for DevWatch; all external calls use fixtures."""
import json
import os
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import devwatch


class DevWatchTests(unittest.TestCase):
    def fixture_file(self, data):
        f = tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False)
        json.dump(data, f)
        f.close()
        self.addCleanup(lambda: os.path.exists(f.name) and os.unlink(f.name))
        return f.name

    def test_detects_failed_run_bad_status_and_stale_pr(self):
        now = datetime(2026, 10, 20, 0, 0, tzinfo=timezone.utc)
        fixture = self.fixture_file({
            "/repos/acme/app/actions/runs": {"workflow_runs": [
                {"name": "CI", "conclusion": "failure", "html_url": "https://example.test/run/1"}
            ]},
            "/repos/acme/app": {"default_branch": "main"},
            "/repos/acme/app/branches/main": {"commit": {"sha": "abc"}},
            "/repos/acme/app/commits/abc/status": {"state": "failure"},
            "/repos/acme/app/commits/abc/check-runs": {"check_runs": [{"name": "required-check", "conclusion": "failure", "html_url": "https://example.test/check/1"}]},
            "/repos/acme/app/pulls": [
                {"number": 7, "title": "old PR", "html_url": "https://example.test/pr/7",
                 "created_at": "2026-10-01T00:00:00Z"}
            ]
        })
        problems = devwatch.check_repo("acme/app", fixture=fixture, clock=now)
        joined = "\n".join(problems)
        self.assertIn("workflow CI failure", joined)
        self.assertIn("combined status is failure", joined)
        self.assertIn("check run required-check failure", joined)
        self.assertIn("PR #7 open", joined)

    def test_fixture_site_health(self):
        fixture = self.fixture_file({"site:https://site.test/": {"status": 503}})
        result = devwatch.check_site({"name": "site", "url": "https://site.test/"}, fixture=fixture)
        self.assertIn("HTTP 503", result[0])

    def test_rejects_invalid_url_scheme(self):
        self.assertTrue(devwatch.check_site({"name": "bad", "url": "javascript:alert(1)"}))

    def test_green_run_is_silent_and_persists_state(self):
        from unittest.mock import patch
        with patch.object(devwatch, "load_config", return_value={"repos": [], "sites": []}), \
             patch.object(devwatch, "load", return_value={"problems": []}), \
             patch.object(devwatch, "save") as save, \
             patch.object(devwatch, "tg") as tg:
            result = devwatch.main()
        self.assertEqual(result["summary"], "green")
        tg.assert_not_called()
        save.assert_called_once()

    def test_pagination_collects_more_than_one_page(self):
        from unittest.mock import patch
        first = {"workflow_runs": [{"id": i} for i in range(100)]}
        second = {"workflow_runs": [{"id": 100}]}
        with patch.object(devwatch, "gh_get", side_effect=[first, second]) as get:
            rows = devwatch.gh_get_all("/repos/acme/app/actions/runs", {"per_page": 100}, collection="workflow_runs")
        self.assertEqual(len(rows), 101)
        self.assertEqual(get.call_count, 2)

    def test_site_soft_404_expected_content(self):
        fixture = self.fixture_file({"site:https://site.test/": {"status": 200, "body": "generic error page"}})
        result = devwatch.check_site({"name": "site", "url": "https://site.test/", "expected_text": "App dashboard"}, fixture=fixture)
        self.assertIn("soft-404", result[0])

    def test_pagination_collects_more_than_one_page(self):
        from unittest.mock import patch
        first = {"workflow_runs": [{"id": i} for i in range(100)]}
        second = {"workflow_runs": [{"id": 100}]}
        with patch.object(devwatch, "gh_get", side_effect=[first, second]) as get:
            rows = devwatch.gh_get_all("/repos/acme/app/actions/runs", {"per_page": 100}, collection="workflow_runs")
        self.assertEqual(len(rows), 101)
        self.assertEqual(get.call_count, 2)

    def test_site_soft_404_expected_content(self):
        fixture = self.fixture_file({"site:https://site.test/": {"status": 200, "body": "generic error page"}})
        result = devwatch.check_site({"name": "site", "url": "https://site.test/", "expected_text": "App dashboard"}, fixture=fixture)
        self.assertIn("soft-404", result[0])

    def test_changed_run_url_does_not_repeat_same_incident(self):
        from contextlib import ExitStack
        from unittest.mock import patch
        old_problem = "acme/app: workflow CI failure (https://github.com/acme/app/actions/runs/1)"
        new_problem = "acme/app: workflow CI failure (https://github.com/acme/app/actions/runs/2)"
        with ExitStack() as stack:
            stack.enter_context(patch.object(devwatch, "load_config", return_value={"repos": [], "sites": [{"name": "site", "url": "https://site.test/"}]}))
            stack.enter_context(patch.object(devwatch, "load", return_value={"problems": [old_problem]}))
            stack.enter_context(patch.object(devwatch, "check_site", return_value=[new_problem]))
            save = stack.enter_context(patch.object(devwatch, "save"))
            tg = stack.enter_context(patch.object(devwatch, "tg"))
            devwatch.main()
        tg.assert_not_called()
        self.assertEqual(save.call_count, 1)
        self.assertEqual(save.call_args.args[1]["problems"], [new_problem])

    def test_state_is_not_saved_if_telegram_alert_fails(self):
        from contextlib import ExitStack
        from unittest.mock import patch
        problem = "site: HTTP 503 at https://site.test/"
        with ExitStack() as stack:
            stack.enter_context(patch.object(devwatch, "load_config", return_value={"repos": [], "sites": [{"name": "site", "url": "https://site.test/"}]}))
            stack.enter_context(patch.object(devwatch, "load", return_value={"problems": []}))
            stack.enter_context(patch.object(devwatch, "check_site", return_value=[problem]))
            save = stack.enter_context(patch.object(devwatch, "save"))
            stack.enter_context(patch.object(devwatch, "tg", side_effect=RuntimeError("Telegram down")))
            with self.assertRaises(RuntimeError):
                devwatch.main()
        save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
