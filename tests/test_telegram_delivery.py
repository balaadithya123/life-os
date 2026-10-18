"""Focused, network-free tests for Telegram message delivery helpers."""
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import common


class FakeResponse:
    def __init__(self, payload=None, error=None):
        self.payload = payload or {"ok": True, "result": {"message_id": 1}}
        self.error = error

    def raise_for_status(self):
        if self.error:
            raise self.error

    def json(self):
        return self.payload


class TelegramDeliveryTests(unittest.TestCase):
    def test_long_message_chunks_below_telegram_limit(self):
        chunks = common._telegram_chunks(("line\n" * 1500))
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= common.TELEGRAM_SAFE_LIMIT for chunk in chunks))
        self.assertEqual("".join(chunks).replace("\n", ""), ("line" * 1500))

    @patch.dict(os.environ, {"TELEGRAM_TOKEN": "test-token", "TELEGRAM_CHAT_ID": "123"})
    @patch("common.requests.post")
    def test_api_error_is_not_silently_ignored(self, post):
        post.return_value = FakeResponse({"ok": False, "description": "chat not found"})
        with patch.object(common, "DRY", False):
            with self.assertRaisesRegex(RuntimeError, "chat not found"):
                common.tg("hello")
        post.assert_called_once()

    @patch.dict(os.environ, {"TELEGRAM_TOKEN": "test-token", "TELEGRAM_CHAT_ID": "123"})
    @patch("common.requests.post")
    def test_http_error_propagates(self, post):
        import requests
        post.return_value = FakeResponse(error=requests.HTTPError("429 Too Many Requests"))
        with patch.object(common, "DRY", False):
            with self.assertRaises(requests.HTTPError):
                common.tg("hello")

    @patch.dict(os.environ, {"TELEGRAM_TOKEN": "test-token", "TELEGRAM_CHAT_ID": "123"})
    @patch("common.requests.post")
    def test_feedback_keyboard_attaches_to_final_chunk(self, post):
        post.return_value = FakeResponse()
        with patch.object(common, "DRY", False):
            common.tg("x" * (common.TELEGRAM_SAFE_LIMIT + 10), buttons=[[("👍", "r|u|abc")]])
        self.assertEqual(post.call_count, 2)
        self.assertNotIn("reply_markup", post.call_args_list[0].kwargs["json"])
        self.assertIn("reply_markup", post.call_args_list[1].kwargs["json"])


if __name__ == "__main__":
    unittest.main()
