"""Optional Handoff Hub link (MCP over HTTP). Fail-soft: without HUB_URL/HUB_TOKEN, or if a call fails,
everything else keeps working. Lets life-os hand work to claude / chatgpt / grok and see what they handed it."""
import os, json, requests

URL, TOKEN = os.getenv("HUB_URL"), os.getenv("HUB_TOKEN")
AGENT = "life-os"


def enabled(): return bool(URL and TOKEN)


class _Client:
    def __init__(self): self.sid = None; self.n = 0

    def post(self, payload):
        h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
             "Authorization": f"Bearer {TOKEN}"}
        if self.sid: h["Mcp-Session-Id"] = self.sid
        r = requests.post(URL, json=payload, headers=h, timeout=30); r.raise_for_status()
        self.sid = r.headers.get("Mcp-Session-Id", self.sid)
        if "text/event-stream" in r.headers.get("Content-Type", ""):
            for line in r.text.splitlines():
                if line.startswith("data:"): return json.loads(line[5:])
            return {}
        return r.json() if r.text.strip() else {}

    def start(self):
        self.post({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {
            "protocolVersion": "2025-03-26", "capabilities": {},
            "clientInfo": {"name": "life-os", "version": "1"}}})
        try: self.post({"jsonrpc": "2.0", "method": "notifications/initialized"})
        except Exception: pass

    def call(self, tool, args):
        self.n += 1
        res = self.post({"jsonrpc": "2.0", "id": self.n, "method": "tools/call",
                         "params": {"name": tool, "arguments": args}}).get("result", {})
        txt = (res.get("content") or [{}])[0].get("text", "")
        try: return json.loads(txt)
        except Exception: return txt


_c = None


def call(tool, **args):
    global _c
    if not enabled(): return None
    try:
        if _c is None: _c = _Client(); _c.start()
        return _c.call(tool, args)
    except Exception as e:
        print(f"[hub] {tool} failed: {e}"); return None


def remember(text, tags): return call("remember", memory=text, tags=tags, source=AGENT)
def my_handoffs(): return call("get_my_handoffs", agent=AGENT)
def hand_off(task, to_agent, context="", data=None):
    return call("hand_off_task", agent=AGENT, to_agent=to_agent, task=task, context=context, data=data or {})
