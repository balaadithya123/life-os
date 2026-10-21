"""Stdlib-only model router: local Ollama first for routine tasks, hosted APIs as fallback."""
from __future__ import annotations
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class ProviderError(RuntimeError):
    pass


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> dict[str, Any]:
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **(headers or {})}, method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read(2_000_000).decode())
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        raise ProviderError(f"provider request failed ({type(exc).__name__})") from exc


@dataclass(frozen=True)
class ProviderResult:
    provider: str
    model: str
    text: str


class ModelRouter:
    def __init__(self, env: dict[str, str] | None = None):
        self.env = env if env is not None else os.environ

    def _ollama(self, messages: list[dict[str, str]]) -> ProviderResult:
        base = self.env.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        model = self.env.get("OLLAMA_MODEL", "qwen2.5:3b")
        data = _post_json(f"{base}/api/chat", {
            "model": model, "messages": messages, "stream": False,
            "options": {"temperature": 0.2},
        })
        text = (data.get("message") or {}).get("content")
        if not isinstance(text, str) or not text:
            raise ProviderError("Ollama returned no message content")
        return ProviderResult("ollama", model, text)

    def _cloudflare(self, messages: list[dict[str, str]]) -> ProviderResult:
        account, token = self.env.get("CF_ACCOUNT_ID"), self.env.get("CF_API_TOKEN")
        if not account or not token:
            raise ProviderError("Cloudflare provider not configured")
        model = self.env.get("CF_MODEL", "@cf/meta/llama-3.1-8b-instruct")
        url = f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{model}"
        data = _post_json(url, {"messages": messages}, {"Authorization": f"Bearer {token}"})
        text = (data.get("result") or {}).get("response")
        if not isinstance(text, str) or not text:
            raise ProviderError("Cloudflare returned no text")
        return ProviderResult("cloudflare", model, text)

    def _gemini(self, messages: list[dict[str, str]]) -> ProviderResult:
        key = self.env.get("GEMINI_API_KEY")
        if not key:
            raise ProviderError("Gemini provider not configured")
        model = self.env.get("GEMINI_MODEL", "gemini-2.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        contents = [{"role": "model" if m.get("role") == "assistant" else "user",
                     "parts": [{"text": str(m.get("content", ""))}]} for m in messages]
        data = _post_json(url, {"contents": contents}, {"x-goog-api-key": key})
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("Gemini returned no text") from exc
        if not isinstance(text, str) or not text:
            raise ProviderError("Gemini returned no text")
        return ProviderResult("gemini", model, text)

    def complete(self, messages: list[dict[str, str]], task_class: str = "routine") -> ProviderResult:
        if task_class not in {"routine", "complex"}:
            raise ValueError("task_class must be routine or complex")
        order = [self._ollama, self._cloudflare, self._gemini] if task_class == "routine" else [
            self._cloudflare, self._gemini, self._ollama
        ]
        errors = []
        for provider in order:
            try:
                return provider(messages)
            except ProviderError as exc:
                errors.append(str(exc))
        raise ProviderError("no provider succeeded: " + "; ".join(errors))
