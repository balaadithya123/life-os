"""Polls Telegram (no server needed), runs your commands, applies button feedback. Only answers your chat."""
import os, sys, json, requests
from common import *
import learn, study, snapshot

HELP = """LifeOS daily revision (follows active cycle in plan.yml – currently Cycle 5)

/today - today's picks (max 3 topics)
/done [1 3] - mark tasks done (all if no numbers)
/test NAME phy chem math - log a test, e.g. /test QPT3 62 48 80
/mistake optics concept 2 - kinds: concept, silly, time
/ok optics - practiced it and felt solid
/addchapter p: Wave Optics - prefix p: c: m:
/status - your weakest chapters and learned profile

Morning brief arrives ~07:00 IST with today's topics."""


def fmt_today(t):
    lines = [f"Today ({t['cycle'] or 'no cycle set'}):"]
    for i, k in enumerate(t["picks"], 1): lines.append(f"{i}. {'✅' if k in t['done'] else '▫️'} {k}")
    return "\n".join(lines)


def handle(text):
    cmd, _, arg = text.strip().partition(" ")
    cmd = cmd.lower().split("@")[0]
    ch = learn.chapters()
    if cmd in ("/start", "/help"): return HELP
    if cmd == "/today": return fmt_today(study.pick())
    if cmd == "/done":
        idx = [int(x) for x in arg.split() if x.isdigit()]
        return "Logged.\n" + fmt_today(study.mark_done(idx or None))
    if cmd == "/test":
        a = arg.split()
        try: scores = [float(x) for x in a[-3:]]; name = " ".join(a[:-3]) or "test"
        except ValueError: return "Format: /test NAME phy chem math"
        append("tests.jsonl", {"d": today().isoformat(), "name": name, "scores": scores})
        return f"Logged {name}: P {scores[0]:g} C {scores[1]:g} M {scores[2]:g}. Now /mistake chapter kind n for what cost you marks."
    if cmd == "/mistake":
        t = arg.split()
        k = next((i for i, w in enumerate(t) if w.lower() in learn.KINDS), None)
        if k is None: return "Format: /mistake chapter concept|silly|time [n]"
        n = int(t[k + 1]) if len(t) > k + 1 and t[k + 1].isdigit() else 1
        key, subj = learn.find(" ".join(t[:k]), ch)
        if not key and subj: key = learn.add_chapter(ch, subj, " ".join(t[:k])[2:].strip().title())
        if not key: return "Unknown chapter. Use a prefix to create it, e.g. /mistake p:optics concept"
        learn.mistake(ch, key, t[k].lower(), n); save("chapters.json", ch)
        return f"{key}: weakness now {ch[key]['w']}, next review in ~{ch[key]['interval']}d."
    if cmd == "/ok":
        key, _ = learn.find(arg, ch)
        if not key: return "Unknown chapter."
        learn.ok(ch, key); save("chapters.json", ch)
        return f"{key}: weakness down to {ch[key]['w']}, spacing {ch[key]['interval']}d."
    if cmd == "/addchapter":
        pre, _, name = arg.partition(":")
        if pre.lower().strip() not in learn.SUBJ or not name.strip(): return "Format: /addchapter p: Wave Optics"
        key = learn.add_chapter(ch, learn.SUBJ[pre.lower().strip()], name.strip()); save("chapters.json", ch)
        return f"Added {key}."
    if cmd == "/status":
        p = profile(); top = sorted(ch.items(), key=lambda kv: -kv[1]["w"])[:6]
        return ("Weakest:\n" + "\n".join(f"- {k} ({v['w']})" for k, v in top) +
                f"\nCompletion rate: {round(p['completion'] * 100)}%\nMistake mix: {p['mistake_mix'] or 'not enough data yet'}")
    return "Unknown command. /help"


def process_inbox():
    """Commands dropped into inbox/*.json by an AI chat (via the hub's GitHub tools) are run like Telegram commands."""
    d = ROOT / "inbox"
    if not d.exists(): return
    (d / "done").mkdir(exist_ok=True)
    for f in sorted(d.glob("*.json")):
        try:
            j = json.loads(f.read_text())
            if j.get("complete"):
                res = str(j.get("result", ""))[:1500]
                append("requests.jsonl", {"id": str(j["complete"]), "d": today().isoformat(), "type": "done", "result": res})
                tg(f"Request {j['complete']} finished by an AI agent:\n{res}")
            elif str(j.get("text", "")).startswith("/"):
                tg("(from an AI chat) " + handle(j["text"]))
        except Exception as e:
            tg(f"Inbox file {f.name} failed: {e}")
        f.rename(d / "done" / f.name)


def callback(data):
    parts = data.split("|")
    if parts[0] == "r" and len(parts) == 3: return "Noted." if learn.feedback(parts[2], parts[1] == "u") else "Expired."
    return "?"


def main(fixture=None):
    token, chat = os.getenv("TELEGRAM_TOKEN"), str(os.getenv("TELEGRAM_CHAT_ID", ""))
    off = load("tg_offset.json", {"o": 0})
    if fixture: ups = json.load(open(fixture))
    else:
        if not token: print("No TELEGRAM_TOKEN"); return
        ups = requests.get(f"https://api.telegram.org/bot{token}/getUpdates",
                           params={"offset": off["o"] + 1, "timeout": 0}, timeout=30).json().get("result", [])
    for u in ups:
        off["o"] = max(off["o"], u.get("update_id", 0))
        m, cb = u.get("message"), u.get("callback_query")
        chat_obj = (m or (cb or {}).get("message") or {}).get("chat", {})
        cid = str(chat_obj.get("id", ""))
        if not fixture and cid != chat: continue            # ignore strangers
        try:
            if m and m.get("text", "").startswith("/"): tg(handle(m["text"]))
            elif cb:
                msg = callback(cb["data"])
                if token and not fixture:
                    requests.post(f"https://api.telegram.org/bot{token}/answerCallbackQuery",
                                  json={"callback_query_id": cb["id"], "text": msg}, timeout=30)
                else: print("[CB]", msg)
        except Exception as e:
            tg(f"Error: {e}")
    process_inbox()
    snapshot.write()
    save("tg_offset.json", off)


if __name__ == "__main__":
    main(sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--fixture" else None)
