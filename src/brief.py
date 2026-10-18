"""Morning brief: today's picks, test countdown, learned nudge, hub handoffs."""
import datetime as dt
from common import *
import learn, study, hub, llm, snapshot
from bot import fmt_today


def nudge(p, ch):
    top = sorted(ch.items(), key=lambda kv: -kv[1]["w"])[:3]
    mix = p["mistake_mix"]
    if not mix or not any(mix.values()): return None
    prompt = (f"My weakest chapters: {[k for k, _ in top]}. Mistake mix last 30 days: {mix}. Test trend: {p['test_trend']}. "
              "Give a 2-sentence plan tweak for today. Specific, no motivation talk.")
    fallback = {"silly": "Silly mistakes dominate: keep the last 15 min of each session for re-checking signs, units, limits.",
                "time": "Time pressure dominates: do one timed set today and skip any question that passes 2.5 min.",
                "concept": "Concept gaps dominate: re-derive the core formulas of today's chapters before any problems."}
    return llm.ask("nudge", prompt) or fallback[max(mix, key=mix.get)]


def main():
    miss = study.close_yesterday()
    t, p, ch = study.pick(), profile(), learn.chapters()
    parts = [f"Good morning. {today().strftime('%a %d %b')}"]

    if t.get("cycle"):
        parts.append(f"Active: {t['cycle']}")
    else:
        parts.append("Using weakness + spaced repetition")

    # Flag test days from daily map
    day_items = (cfg("plan.yml", {}) or {}).get("daily", {}).get(today().isoformat()) or []
    for item in day_items:
        if "test day" in item.lower() or "unit tests" in item.lower():
            parts.append(f"⚠️ {item}")

    nxt = sorted((x for x in (cfg("tests.yml", {}) or {}).get("tests", []) if x["date"] >= today()), key=lambda x: x["date"])
    if nxt:
        note = nxt[0].get("note", "")
        parts.append(f"Next QPT: {nxt[0]['name']} in {(nxt[0]['date'] - today()).days} days" + (f" ({note})" if note else ""))

    if miss is not None and miss < 1:
        parts.append(f"Yesterday: {round(miss * 100)}% done")

    parts.append(fmt_today(t))

    if p["hours"]:
        best = max(p["hours"], key=p["hours"].get)
        parts.append(f"You finish most tasks around {best}:00.")

    n = nudge(p, ch)
    if n:
        parts.append(n)

    hand = hub.my_handoffs()
    if isinstance(hand, list) and hand:
        parts.append(f"Hub: {len(hand)} task(s) waiting")

    parts.append("Reply /done 1 2 or /mistake chapter kind")
    tg("\n\n".join(parts))
    snapshot.write()


if __name__ == "__main__":
    main()
