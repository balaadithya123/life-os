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

    # Clear cycle indicator (especially for v5 / Cycle 5)
    if t.get("cycle"):
        parts.append(f"Active schedule: {t['cycle']}")
    else:
        parts.append("No active cycle dates set – using weakness + spaced repetition")

    nxt = sorted((x for x in (cfg("tests.yml", {}) or {}).get("tests", []) if x["date"] >= today()), key=lambda x: x["date"])
    if nxt: parts.append(f"Next: {nxt[0]['name']} in {(nxt[0]['date'] - today()).days} days")
    if miss is not None and miss < 1: parts.append(f"Yesterday: {round(miss * 100)}% of tasks done")

    parts.append(fmt_today(t))

    if p["hours"]:
        best = max(p["hours"], key=p["hours"].get)
        parts.append(f"You finish most tasks around {best}:00. Put the hardest one there.")

    n = nudge(p, ch)
    if n: parts.append(n)

    hand = hub.my_handoffs()
    if isinstance(hand, list) and hand: parts.append(f"Hub: {len(hand)} task(s) waiting for life-os")

    parts.append("Reply /done 1 2 or /mistake chapter kind to log progress.")
    tg("\n\n".join(parts))
    snapshot.write()


if __name__ == "__main__":
    main()
