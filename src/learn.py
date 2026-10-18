"""The learning core. Everything personal lives here: chapter weakness, spacing, feedback, weekly profile."""
import difflib, datetime as dt
from common import *
import hub, snapshot

KINDS = {"concept": 1.0, "time": 0.6, "silly": 0.5}   # how strongly each mistake type raises weakness
SUBJ = {"p": "Physics", "c": "Chemistry", "m": "Maths"}


def _new(subject, w): return {"subject": subject, "w": w, "last": None, "interval": 3, "n_mistakes": 0}


def chapters():
    ch = load("chapters.json", None)
    if ch is None:
        ch = {}
        for subj, d in (cfg("chapters.yml", {}) or {}).items():
            for n in d.get("weak", []): ch[f"{subj}: {n}"] = _new(subj, 0.7)
            for n in d.get("other", []): ch[f"{subj}: {n}"] = _new(subj, 0.35)
        save("chapters.json", ch)
    return ch


def add_chapter(ch, subject, name, w=0.4):
    key = f"{subject}: {name}"
    ch.setdefault(key, _new(subject, w))
    return key


def find(query, ch):
    """Fuzzy-match a chapter. Accepts 'p:optics' style prefix to pick/create a subject."""
    q = query.lower().strip()
    subj = None
    if len(q) > 2 and q[1] == ":" and q[0] in SUBJ: subj, q = SUBJ[q[0]], q[2:].strip()
    names = {k.lower(): k for k, v in ch.items() if subj is None or v["subject"] == subj}
    hits = [k for n, k in names.items() if q in n]
    if len(hits) == 1: return hits[0], subj
    if hits: return min(hits, key=len), subj
    m = difflib.get_close_matches(q, [n.split(": ", 1)[1] for n in names], n=1, cutoff=0.55)
    if m:
        for n, k in names.items():
            if n.endswith(": " + m[0]): return k, subj
    return None, subj


def mistake(ch, key, kind, n=1):
    c = ch[key]
    a = min(0.6, 0.25 * KINDS[kind] * (1 + 0.15 * (n - 1)))
    c["w"] = round(c["w"] + a * (1 - c["w"]), 3)        # weakness moves toward 1
    c["interval"] = max(1, c["interval"] // 2)           # see it sooner
    c["n_mistakes"] += n
    append("mistakes.jsonl", {"d": today().isoformat(), "chapter": key, "kind": kind, "n": n})


def ok(ch, key):
    c = ch[key]
    c["w"] = round(c["w"] * 0.85, 3)                     # weakness shrinks
    c["interval"] = min(30, int(c["interval"] * 2) or 2) # spacing grows
    c["last"] = today().isoformat()


def studied(ch, key):
    c = ch[key]
    c["w"] = round(c["w"] * 0.95, 3)
    c["interval"] = min(30, c["interval"] + 1)
    c["last"] = today().isoformat()


def feedback(item_id, up):
    """Thumbs on a radar item: nudge keyword + source weights."""
    it = load("radar_items.json", {}).get(item_id)
    if not it: return False
    p, d = profile(), (0.3 if up else -0.3)
    for t in it["tokens"]: p["kw"][t] = max(-3, min(3, round(p["kw"].get(t, 0) + d, 2)))
    s = p["src"].get(it["src"], 1.0) * (1.1 if up else 0.9)
    p["src"][it["src"]] = max(0.3, min(2.0, round(s, 3)))
    save("profile.json", p)
    append("feedback.jsonl", {"d": today().isoformat(), "id": item_id, "up": up})
    return True


def weekly():
    ch, p = chapters(), profile()
    # slow drift back toward 0.35: untouched chapters are neither forgotten nor stuck
    for c in ch.values(): c["w"] = round(0.35 + (c["w"] - 0.35) * 0.97, 3)
    save("chapters.json", ch)

    cutoff = (today() - dt.timedelta(days=30)).isoformat()
    ms = [m for m in rows("mistakes.jsonl") if m["d"] >= cutoff]
    tot = sum(m["n"] for m in ms) or 1
    p["mistake_mix"] = {k: round(sum(m["n"] for m in ms if m["kind"] == k) / tot, 2) for k in KINDS}

    ev = [e for e in rows("events.jsonl") if e["type"] == "done"]
    hrs = {}
    for e in ev: hrs[str(e["hour"])] = hrs.get(str(e["hour"]), 0) + 1
    p["hours"] = hrs

    tests = rows("tests.jsonl")
    trend = {}
    for i, s in enumerate(["Physics", "Chemistry", "Maths"]):
        v = [t["scores"][i] for t in tests if len(t.get("scores", [])) == 3]
        if len(v) >= 2: trend[s] = round(v[-1] - sum(v[:-1][-3:]) / len(v[:-1][-3:]), 1)
    p["test_trend"] = trend
    p["updated"] = today().isoformat()
    save("profile.json", p)

    weakest = sorted(ch.items(), key=lambda kv: -kv[1]["w"])[:5]
    summary = (f"life-os weekly profile {today()}: weakest = " +
               ", ".join(f"{k} ({v['w']})" for k, v in weakest) +
               f"; mistake mix = {p['mistake_mix']}; completion = {round(p['completion'], 2)}; trend = {trend}")
    print(summary)
    hub.remember(summary, ["life-os", "profile"])

    # Hand heavy content work to a stronger chat agent (your subscription, not a free API)
    top_key, top = weakest[0]
    sent = load("handoffs.json", {})
    last = sent.get(top_key)
    if top["w"] >= 0.65 and (not last or (today() - dt.date.fromisoformat(last)).days >= 14):
        to = (cfg("agents.yml", {}) or {}).get("handoff_to", "claude")
        task = f"Create a JEE Advanced-level practice set + concise solutions for: {top_key}"
        ctx = f"Mistake mix: {p['mistake_mix']}. Focus on the dominant mistake type."
        data = {"chapter": top_key, "weakness": top["w"], "mistakes": top["n_mistakes"]}
        r, via = hub.hand_off(task, to, context=ctx, data=data), "via hub"
        if r is None:   # GitHub runners may not reach the hub: park it in the repo, AIs read it from the snapshot
            append("requests.jsonl", {"id": short_id(top_key + today().isoformat()), "d": today().isoformat(),
                                      "type": "open", "to": to, "task": task, "context": ctx, "data": data})
            r, via = True, "via the repo snapshot"
        sent[top_key] = today().isoformat(); save("handoffs.json", sent)
        tg(f"Handed to {to} {via}: practice set for {top_key}")
    snapshot.write()


if __name__ == "__main__":
    weekly()
