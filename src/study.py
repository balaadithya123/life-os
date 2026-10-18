"""Daily picks. Uses exact day map first (full schedule), then cycle, then weakness."""
import datetime as dt
from common import *
import learn

MAX_TOPICS = 3


def _daily_chapters(ch):
    """Exact day entry from plan.yml daily: map. Highest priority."""
    day = today().isoformat()
    items = (cfg("plan.yml", {}) or {}).get("daily", {}).get(day) or []
    if not items:
        return [], None
    keys = []
    for name in items:
        if name.lower().startswith("test day"):
            continue  # test days handled in brief
        subj, _, n = name.partition(": ")
        if subj and n:
            keys.append(learn.add_chapter(ch, subj, n))
        else:
            keys.append(learn.add_chapter(ch, "General", name))
    return keys, f"Daily {day}"


def _plan_chapters(ch):
    for cyc in (cfg("plan.yml", {}) or {}).get("cycles", []):
        s, e = cyc.get("start"), cyc.get("end")
        if s and e and s <= today() <= e:
            keys = []
            for name in cyc.get("chapters") or []:
                subj, _, n = name.partition(": ")
                keys.append(learn.add_chapter(ch, subj, n))
            return keys, cyc["name"]
    return [], None


def n_tasks():
    load_f = max(0.6, min(1.2, profile()["completion"] / 0.8))
    return max(2, min(MAX_TOPICS, round(MAX_TOPICS * load_f)))


def pick():
    t = load("today.json", {})
    if t.get("date") == today().isoformat():
        return t
    ch = learn.chapters()

    # 1. Exact daily map (October + any future day-level entries)
    day_keys, day_name = _daily_chapters(ch)
    if day_keys:
        picks = day_keys[:MAX_TOPICS]
        t = {"date": today().isoformat(), "cycle": day_name, "picks": picks, "done": []}
        save("today.json", t)
        save("chapters.json", ch)
        return t

    # 2. Active cycle
    cyc_keys, cyc_name = _plan_chapters(ch)
    pool = set(cyc_keys) | {k for k, v in ch.items() if v["w"] >= 0.6}
    if not pool:
        pool = set(ch)

    def prio(k):
        c = ch[k]
        since = (today() - dt.date.fromisoformat(c["last"])).days if c["last"] else c["interval"] * 2
        return 0.6 * c["w"] + 0.4 * min(1.0, since / c["interval"])

    ranked, picks, seen = sorted(pool, key=prio, reverse=True), [], set()
    for k in ranked:
        if len(picks) < n_tasks() and ch[k]["subject"] not in seen:
            picks.append(k)
            seen.add(ch[k]["subject"])
    for k in ranked:
        if len(picks) < n_tasks() and k not in picks:
            picks.append(k)

    t = {"date": today().isoformat(), "cycle": cyc_name, "picks": picks, "done": []}
    save("today.json", t)
    save("chapters.json", ch)
    return t


def mark_done(indices=None):
    t = pick()
    ch = learn.chapters()
    idx = indices or list(range(1, len(t["picks"]) + 1))
    for i in idx:
        if 1 <= i <= len(t["picks"]) and t["picks"][i - 1] not in t["done"]:
            k = t["picks"][i - 1]
            t["done"].append(k)
            learn.studied(ch, k)
            append("events.jsonl", {"type": "done", "d": today().isoformat(), "hour": now().hour, "chapter": k})
    save("today.json", t)
    save("chapters.json", ch)
    return t


def close_yesterday():
    t = load("today.json", {})
    if t.get("date") and t["date"] != today().isoformat() and not t.get("closed"):
        rate = len(t["done"]) / max(len(t["picks"]), 1)
        p = profile()
        p["completion"] = round(0.8 * p["completion"] + 0.2 * rate, 3)
        save("profile.json", p)
        t["closed"] = True
        save("today.json", t)
        return rate
    return None
