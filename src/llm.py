"""Provider router. Free providers first; paid ones only as fallback, and only if you add their key.
Learns which provider works best per task (success rate, latency) and orders them accordingly."""
import os, time, requests
from common import DRY, load, save

# Model names change often: override with env vars instead of editing code.
P = {
    "gemini": dict(key="GEMINI_API_KEY", free=True, model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash")),
    "groq":   dict(key="GROQ_API_KEY", free=True, model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                   url="https://api.groq.com/openai/v1/chat/completions"),
    "openai": dict(key="OPENAI_API_KEY", free=False, model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                   url="https://api.openai.com/v1/chat/completions"),
    "xai":    dict(key="XAI_API_KEY", free=False, model=os.getenv("XAI_MODEL", "grok-3-mini"),
                   url="https://api.x.ai/v1/chat/completions"),
}
SYSTEM = "You are a concise assistant for a JEE Advanced aspirant who also builds web apps. Be direct. No fluff."


def _call(name, prompt, system):
    p, key = P[name], os.getenv(P[name]["key"])
    if name == "gemini":
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{p['model']}:generateContent",
            headers={"x-goog-api-key": key}, timeout=60,
            json={"systemInstruction": {"parts": [{"text": system}]},
                  "contents": [{"parts": [{"text": prompt}]}]})
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    r = requests.post(p["url"], headers={"Authorization": f"Bearer {key}"}, timeout=60,
                      json={"model": p["model"],
                            "messages": [{"role": "system", "content": system},
                                         {"role": "user", "content": prompt}]})
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def order(task, stats):
    def score(n):
        s = stats.get(n, {}).get(task, {"ok": 0, "fail": 0, "ms": 0})
        ok, tot = s["ok"], s["ok"] + s["fail"]
        return (ok + 1) / (tot + 2) - 0.00002 * (s["ms"] / max(ok, 1))
    on = [n for n in P if os.getenv(P[n]["key"])]
    return (sorted([n for n in on if P[n]["free"]], key=score, reverse=True) +
            sorted([n for n in on if not P[n]["free"]], key=score, reverse=True))


def ask(task, prompt, system=SYSTEM):
    if DRY: return None
    stats = load("llm_stats.json", {})
    for name in order(task, stats):
        t0 = time.time()
        s = stats.setdefault(name, {}).setdefault(task, {"ok": 0, "fail": 0, "ms": 0})
        try:
            out = _call(name, prompt, system)
            s["ok"] += 1; s["ms"] += int((time.time() - t0) * 1000)
            save("llm_stats.json", stats)
            return out.strip()
        except Exception as e:
            s["fail"] += 1
            print(f"[llm] {name} failed: {e}")
    save("llm_stats.json", stats)
    return None
