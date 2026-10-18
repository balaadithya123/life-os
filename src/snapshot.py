"""Writes state/hub_snapshot.md: a plain-text view of your learned profile that Claude, ChatGPT and Grok can
read through the hub's GitHub tools (the repo must be on the hub allowlist). No secrets, no login to life-os."""
from common import *


def open_requests():
    done, opened = set(), {}
    for r in rows("requests.jsonl"):
        if r.get("type") == "done": done.add(r["id"])
        elif r.get("type") == "open": opened[r["id"]] = r
    return [r for i, r in opened.items() if i not in done]


def build():
    ch, p, t = load("chapters.json", {}), profile(), load("today.json", {})
    weak = sorted(ch.items(), key=lambda kv: -kv[1]["w"])[:6]
    L = ["# life-os snapshot (auto-generated, do not edit)", f"Updated: {now().strftime('%Y-%m-%d %H:%M')} IST", ""]
    if t.get("picks"):
        L.append(f"Today ({t.get('cycle') or 'no cycle set'}):")
        L += [f"{i}. {'[done]' if k in t.get('done', []) else '[ ]'} {k}" for i, k in enumerate(t["picks"], 1)]
    else:
        L.append("Today: no picks yet")
    L += ["", "Weakest chapters (0 = strong, 1 = weak):"]
    L += [f"- {k}: {v['w']} (review every ~{v['interval']}d, {v['n_mistakes']} mistakes logged)" for k, v in weak] or ["- none yet"]
    L += ["", f"Completion rate (learned): {round(p['completion'] * 100)}%",
          f"Mistake mix, last 30 days: {p['mistake_mix'] or 'not enough data'}",
          f"Test trend: {p['test_trend'] or 'not enough data'}",
          f"Hours when tasks get finished: {p['hours'] or 'not enough data'}", "", "Open requests for AI agents:"]
    reqs = open_requests()
    L += [f"- id {r['id']} -> {r['to']}: {r['task']} | {r.get('context', '')} | {r.get('data', {})}" for r in reqs] or ["- none"]
    L += ["", "How to talk to life-os from an AI chat (hub GitHub tools, repo allowlisted):",
          "- Log something: commit inbox/<any-name>.json containing {\"text\": \"/mistake p:optics concept 2\"}",
          "  (same commands as Telegram: /done /test /mistake /ok /addchapter)",
          "- Finish a request: commit inbox/<any-name>.json containing {\"complete\": \"<id>\", \"result\": \"short summary\"}",
          "- Never edit files in state/ directly. life-os picks inbox files up within an hour and replies on Telegram."]
    return "\n".join(L) + "\n"


def write():
    STATE.mkdir(exist_ok=True)
    (STATE / "hub_snapshot.md").write_text(build(), encoding="utf-8")
