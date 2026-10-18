"""Fast-path regression tests: bounded timeouts, offline fixtures, and one radar digest."""
import os
import pathlib
import sys
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import llm
import radar


class FastMessageTests(unittest.TestCase):
    def test_llm_timeout_is_bounded(self):
        with patch.dict(os.environ, {"LLM_TIMEOUT_SECONDS": "999"}):
            self.assertEqual(llm._timeout(), 30)
        with patch.dict(os.environ, {"LLM_TIMEOUT_SECONDS": "1"}):
            self.assertEqual(llm._timeout(), 3)
        with patch.dict(os.environ, {"LLM_TIMEOUT_SECONDS": "invalid"}):
            self.assertEqual(llm._timeout(), 10)

    @patch("radar.requests.get")
    def test_page_source_is_offline_in_fixture_mode(self, get):
        result = radar.fetch(
            {"kind": "page", "name": "official", "url": "https://example.com"},
            fixture=str(ROOT / "tests" / "feed.xml"),
        )
        self.assertEqual(result, [])
        get.assert_not_called()

    def test_radar_bundles_headlines_into_one_message(self):
        fixture = str(ROOT / "tests" / "feed.xml")
        config = {
            "sources": [
                {"name": "fixture", "kind": "rss", "url": "https://example.com/rss", "weight": 1.0},
                {"name": "official", "kind": "page", "url": "https://example.com", "weight": 1.0},
            ],
            "keywords": {},
        }
        with patch.object(radar, "cfg", return_value=config), \
             patch.object(radar, "profile", return_value={"src": {}, "kw": {}}), \
             patch.object(radar, "load", side_effect=[[], {}]), \
             patch.object(radar, "save") as save, \
             patch.object(radar.llm, "ask", return_value="1. Relevant.\n2. Relevant.\n3. Relevant."), \
             patch.object(radar, "tg") as tg:
            radar.main(fixture)
        tg.assert_called_once()
        message, buttons = tg.call_args.args
        self.assertTrue(message.startswith("LIFEOS RADAR · TOP PICKS"))
        self.assertIn("JEE Advanced 2027 syllabus notice", message)
        self.assertIn("Vercel changes build output", message)
        self.assertEqual(len(buttons), 3)
        self.assertEqual(save.call_count, 2)


if __name__ == "__main__":
    unittest.main()
