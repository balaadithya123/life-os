"""Daily radar: fetch feeds + watch official pages, rank by what you've liked before, send a compact digest."""
import sys, re, time, hashlib, pathlib
import feedparser, requests
from common import *
import llm

TOK = re.compile(r"[a-z][a-z0-9+#.]{3,}")
STOP = {"with", "from", "that", "this", "have", "will", "your", "about", "into", "more", "what", "after", "their", "says"}
TOP_N = 5
FETCH_TIMEOUT = 5


def tokens(t): return {w for w in TOK.findall(t.lower()) if w not in STOP}


def fetch(src, fixture=None):
    if src["kind"] == "rss":
        if fixture:
            feed = feedparser.parse(pathlib.Path(fixture).read_bytes())
        else:
            response = requests.get(src["url"], timeout=FETCH_TIMEOUT,
                                    headers={"User-Agent": "life-os/1.0"})
            response.raise_for_status()
            feed = feedparser.parse(response.content)
        out = []
        for e in feed.entries[:30]:
            ts = e.get("published_parsed")
            if ts and not fixture and time.time() - time.mktime(ts) > 3 * 86400: continue
            out.append({"title": e.get("title", "(untitled)"),
                        "link": e.get("link", src.get("url", "")),
                        "src": src["name"], "page": False})
        return out
    if src["kind"] == "page":   # official pages: alert when visible text changes
        # Fixture mode is deliberately offline; page checks are skipped rather than making live requests.
        if fixture: return []
        response = requests.get(src["url"], timeout=FETCH_TIMEOUT,
                                headers={"User-Agent": "life-os/1.0"})
        response.raise_for_status()
        html = response.text
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
        h, seen = hashlib.md5(text.encode()).hexdigest(), load("pages.json", {})
        changed = src["name"] in seen and seen[src["name"]] != h
        seen[src["name"]] = h; save("pages.json", seen)
        if changed:
            return [{"title": f"Page changed: {src['name']}", "link": src["url"], "src": src["name"], "page": True}]
    return []


def score(it, src, p, base_kw):
    s = src.get("weight", 1.0) * p["src"].get(src["name"], 1.0) * (4 if it["page"] else 1)
    return s + sum(base_kw.get(t, 0) + p["kw"].get(t, 0) for t in tokens(it["title"]))


def main(fixture=None):
    conf, p = cfg("sources.yml", {}), profile()
    seen, meta, pool = set(load("seen.json", [])), load("radar_items.json", {}), []
    for src in conf["sources"]:
        try:
            for it in fetch(src, fixture):
                it["id"] = short_id(it["link"] + it["title"])
                if it["id"] in seen or any(x["id"] == it["id"] for x in pool): continue
                it["score"] = score(it, src, p, conf.get("keywords", {})); pool.append(it)
        except Exception as e:
            print(f"[radar] {src['name']} failed: {type(e).__name__}: {str(e)[:160]}")
    top = [i for i in sorted(pool, key=lambda i: -i["score"]) if i["score"] > 0.5][:TOP_N]
    if not top:
        tg("Radar: nothing new worth your time today.")
        return
    why = {}
    ans = llm.ask("radar", "For each numbered headline, write ONE line (max 15 words) on why it matters to a JEE Advanced "
                  "aspirant who builds web apps and a bus-fleet startup. Format '1. text'.\n" +
                  "\n".join(f"{n}. {i['title'][:160]}" for n, i in enumerate(top, 1)))
    for line in (ans or "").splitlines():
        m = re.match(r"\s*(\d+)[.)]\s*(.+)", line)
        if m: why[int(m.group(1))] = m.group(2).strip()[:120]

    blocks, buttons = [], []
    for n, it in enumerate(top, 1):
        title = str(it["title"]).strip()[:160]
        link = str(it["link"]).strip()[:250]
        explanation = why.get(n, "")
        block = f"{n}. {title}"
        if explanation: block += f"\n{explanation}"
        if link: block += f"\n{link}"
        blocks.append(block)
        buttons.append([("👍", f"r|u|{it['id']}"), ("👎", f"r|d|{it['id']}")])
        meta[it["id"]] = {"title": it["title"], "src": it["src"], "tokens": sorted(tokens(it["title"]))}
        seen.add(it["id"])

    # One digest reduces Telegram API calls and keeps related headlines together.
    tg("LIFEOS RADAR · TOP PICKS\n\n" + "\n\n".join(blocks), buttons)
    save("seen.json", list(seen)[-2000:]); save("radar_items.json", dict(list(meta.items())[-300:]))


if __name__ == "__main__":
    main(sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--fixture" else None)
