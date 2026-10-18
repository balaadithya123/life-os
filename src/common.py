"""Shared helpers: state files, config, Telegram, profile defaults."""
import json, os, pathlib, hashlib, datetime as dt, textwrap
import requests, yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
STATE, CONFIG = ROOT / "state", ROOT / "config"
DRY = os.getenv("DRY_RUN") == "1"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
TELEGRAM_SAFE_LIMIT = 3900


def now(): return dt.datetime.now(IST)
def today(): return now().date()
def short_id(s): return hashlib.md5(s.encode()).hexdigest()[:8]


def load(name, default):
    try: return json.loads((STATE / name).read_text())
    except Exception: return default


def save(name, obj):
    STATE.mkdir(exist_ok=True)
    (STATE / name).write_text(json.dumps(obj, indent=1, ensure_ascii=False))


def append(name, row):
    STATE.mkdir(exist_ok=True)
    with open(STATE / name, "a") as f: f.write(json.dumps(row, ensure_ascii=False) + "\n")


def rows(name):
    p = STATE / name
    if not p.exists(): return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def cfg(name, default=None):
    p = CONFIG / name
    return yaml.safe_load(p.read_text()) if p.exists() else default


DEFAULT_PROFILE = {
    "kw": {},            # learned keyword deltas from thumbs up/down
    "src": {},           # learned source multipliers
    "completion": 0.8,   # EWMA of daily task completion
    "hours": {},         # hour-of-day -> completed sessions
    "mistake_mix": {},   # last 30 days: concept/silly/time share
    "test_trend": {},    # subject -> recent score change
    "updated": None,
}


def profile():
    return {**DEFAULT_PROFILE, **load("profile.json", {})}


def _telegram_chunks(text, limit=TELEGRAM_SAFE_LIMIT):
    """Split long Telegram messages without cutting ordinary words."""
    text = str(text)
    if len(text) <= limit:
        return [text]
    chunks = []
    while len(text) > limit:
        cut = text.rfind("\n", 0, limit + 1)
        if cut < limit // 2:
            cut = text.rfind(" ", 0, limit + 1)
        if cut < limit // 2:
            cut = limit
        chunks.append(text[:cut].rstrip())
        text = text[cut:].lstrip()
    if text:
        chunks.append(text)
    return chunks


def tg(text, buttons=None):
    """Send checked Telegram messages; fail loudly so Actions logs show delivery errors."""
    token, chat = os.getenv("TELEGRAM_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    chunks = _telegram_chunks(text)
    if DRY or not (token and chat):
        for chunk in chunks:
            print("[TG]", chunk, buttons or "")
        return
    for index, chunk in enumerate(chunks):
        body = {"chat_id": chat, "text": chunk, "disable_web_page_preview": True}
        # Attach feedback buttons to the final chunk, so they remain beside the end of the item.
        if buttons and index == len(chunks) - 1:
            body["reply_markup"] = {"inline_keyboard": buttons}
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json=body,
            timeout=15,
        )
        response.raise_for_status()
        try:
            payload = response.json()
        except ValueError as exc:
            raise RuntimeError("Telegram returned a non-JSON response") from exc
        if not isinstance(payload, dict) or not payload.get("ok"):
            description = payload.get("description", "unknown Telegram API error") if isinstance(payload, dict) else "invalid Telegram API response"
            raise RuntimeError(f"Telegram send failed: {description}")
