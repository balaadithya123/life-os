"""Runs by itself whenever code or config is pushed. Tells you on Telegram what is set up and what is missing,
and validates your config files, so you never have to open the Actions tab."""
import os, sys
from common import *

REQUIRED = ["TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID"]
LLMS = {"GEMINI_API_KEY": "Gemini", "GROQ_API_KEY": "Groq", "OPENAI_API_KEY": "OpenAI", "XAI_API_KEY": "xAI"}


def main():
    miss = [k for k in REQUIRED if not os.getenv(k)]
    bad = []
    for f in ["plan.yml", "sources.yml", "tests.yml", "chapters.yml", "agents.yml"]:
        try: cfg(f, {})
        except Exception as e: bad.append(f"{f}: {str(e)[:80]}")
    cyc = (cfg("plan.yml", {}) or {}).get("cycles", [])
    dated = sum(1 for c in cyc if c.get("start") and c.get("end"))
    on = [n for k, n in LLMS.items() if os.getenv(k)]
    L = ["life-os is live ✅" if not (miss or bad) else "life-os needs attention ⚠️"]
    if miss: L.append("Missing required secrets: " + ", ".join(miss))
    if bad: L.append("Broken config: " + "; ".join(bad))
    L.append("AI keys: " + (", ".join(on) if on else "none yet (radar and nudges use plain fallbacks; add GEMINI_API_KEY, it is free)"))
    L.append(f"Cycles with dates: {dated} of {len(cyc)}" + ("" if dated else " (fill start/end in config/plan.yml to make picks follow your cycle)"))
    L.append("Hub link from GitHub: " + ("on" if os.getenv("HUB_URL") and os.getenv("HUB_TOKEN") else "off (fine: AIs read state/hub_snapshot.md instead)"))
    L.append("Automatic schedule: brief 07:00 IST, command check hourly 06-23, weekly pass Sun 07:30. Nothing to run by hand.")
    tg("\n".join(L))
    if miss or bad: sys.exit(1)   # red run in GitHub = you get an email


if __name__ == "__main__":
    main()
