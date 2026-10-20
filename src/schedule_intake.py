"""Approval-first JEE schedule PDF intake. Never edits authoritative plan/tests."""
from __future__ import annotations
import argparse, hashlib, json, re
from datetime import date, datetime
from pathlib import Path
import yaml
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
INBOX, STATE = ROOT / "inbox" / "schedules", ROOT / "state"
PLAN, TESTS = ROOT / "config" / "plan.yml", ROOT / "config" / "tests.yml"
PROPOSAL_MD, PROPOSAL_JSON = STATE / "schedule_proposal.md", STATE / "schedule_proposal.json"
ISO_DATE = re.compile(r"\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b")
DMY_DATE = re.compile(r"\b(\d{1,2})[./-](\d{1,2})[./-](20\d{2})\b")
TEXT_DATE = re.compile(r"\b(\d{1,2})\s+([A-Za-z]{3,9})\.?,?\s+(20\d{2})\b")
MONTHS = {m.lower(): i for i, m in enumerate(["January","February","March","April","May","June","July","August","September","October","November","December"], 1)}
SUBJECTS = ("Physics", "Chemistry", "Maths", "Mathematics")
TEST_WORDS = re.compile(r"\b(QPT|AITS|full[\s-]*mock|mock test|cycle[\s-]*end|unit test|full test|part test)\b", re.I)
QPT_WORD = re.compile(r"\bQPT\s*[-#]?\s*(\d+)\b", re.I)
AITS_MAIN = re.compile(r"\bAITS\b.*\bMAIN\b|\bMAIN\b.*\bAITS\b", re.I)

def _date_from_match(line):
    for pattern, order in ((ISO_DATE, "ymd"), (DMY_DATE, "dmy"), (TEXT_DATE, "text")):
        m = pattern.search(line)
        if not m: continue
        try:
            if order == "ymd": return date(int(m[1]), int(m[2]), int(m[3])), m.span()
            if order == "dmy": return date(int(m[3]), int(m[2]), int(m[1])), m.span()
            month = MONTHS.get(m[2].lower(), MONTHS.get(m[2][:3].lower()))
            if month: return date(int(m[3]), month, int(m[1])), m.span()
        except ValueError: continue
    return None, None

def extract_pdf(path):
    if path.suffix.lower() != ".pdf": raise ValueError(f"Only PDF files are accepted: {path.name}")
    reader = PdfReader(str(path))
    if reader.is_encrypted:
        try: reader.decrypt("")
        except Exception as exc: raise ValueError(f"Encrypted PDF cannot be read: {path.name}") from exc
    text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    if not text: raise ValueError(f"No selectable text found in {path.name}; scanned PDFs need manual conversion first.")
    return text

def parse_schedule_text(text):
    daily, events, warnings, raw_rows = [], [], [], []
    for number, raw in enumerate(text.splitlines(), 1):
        line = " ".join(raw.split()).strip(" •\t")
        if not line: continue
        day, span = _date_from_match(line)
        if not day: continue
        remainder = re.sub(r"\s+", " ", (line[:span[0]] + " " + line[span[1]:]).strip(" :-|,\t"))
        if not remainder:
            warnings.append(f"Line {number}: date found without a schedule item: {line[:180]}")
            continue
        raw_rows.append({"date": day.isoformat(), "text": remainder, "source_line": number})
        if TEST_WORDS.search(remainder):
            qpt = QPT_WORD.search(remainder)
            events.append({"name": f"QPT {qpt[1]}" if qpt else remainder[:100],
                "date": day.isoformat(), "kind": "qpt" if qpt else ("aits-main" if AITS_MAIN.search(remainder) else "test"),
                "source_line": number, "source_text": line})
        elif any(s.lower() in remainder.lower() for s in SUBJECTS):
            daily.append({"date": day.isoformat(), "chapters": [remainder], "source_line": number, "source_text": line})
        else:
            warnings.append(f"Line {number}: date row could not be classified; review manually: {line[:180]}")
    return daily, events, warnings, raw_rows

def _date_key(value):
    if isinstance(value, datetime): return value.date().isoformat()
    if isinstance(value, date): return value.isoformat()
    return str(value)[:10]

def compare_with_authoritative(daily, events, plan=None, tests=None):
    plan = plan if plan is not None else (yaml.safe_load(PLAN.read_text(encoding="utf-8")) or {})
    tests = tests if tests is not None else (yaml.safe_load(TESTS.read_text(encoding="utf-8")) or {})
    existing_daily = {str(k): v for k, v in (plan.get("daily") or {}).items()}
    daily_changes = []
    for item in daily:
        old, proposed = existing_daily.get(item["date"]), item["chapters"]
        if old != proposed:
            daily_changes.append({"date": item["date"], "existing": old, "proposed": proposed,
                                  "change": "add" if old is None else "compare/replace"})
    existing_events = tests.get("tests") or []
    existing_by_date = {}
    for item in existing_events: existing_by_date.setdefault(_date_key(item.get("date")), []).append(item)
    test_changes = []
    for item in events:
        same_day = existing_by_date.get(item["date"], [])
        match = any(str(e.get("name", "")).lower() == item["name"].lower() for e in same_day)
        test_changes.append({**item,
            "existing_on_date": [{"name": e.get("name"), "kind": e.get("kind")} for e in same_day],
            "change": "already-listed" if match else ("date-conflict-review" if same_day else "new-test-proposal")})
    conflicts, proposed_by_date = [], {}
    for item in events: proposed_by_date.setdefault(item["date"], []).append(item)
    for day in sorted(set(existing_by_date) | set(proposed_by_date)):
        existing, proposed = existing_by_date.get(day, []), proposed_by_date.get(day, [])
        sunday = date.fromisoformat(day).weekday() == 6
        existing_main = any(str(e.get("kind", "")).lower() == "aits-main" for e in existing)
        proposed_main = any(str(e.get("kind", "")).lower() == "aits-main" or AITS_MAIN.search(str(e.get("name", ""))) for e in proposed)
        qpts = [e for e in existing + proposed if str(e.get("kind", "")).lower() == "qpt"]
        if sunday and (existing_main or proposed_main) and qpts:
            conflicts.append({"date": day, "rule": "No QPT on an AITS Main Sunday",
                "existing": [e.get("name") for e in existing], "proposed": [e.get("name") for e in proposed]})
    cycle7 = []
    for e in existing_events + events:
        if str(e.get("kind", "")).lower() == "qpt":
            d = _date_key(e.get("date"))
            if "2026-12-25" <= d <= "2027-01-03": cycle7.append({"date": d, "name": e.get("name")})
    unique = {(x["date"], str(x["name"]).lower()): x for x in cycle7}
    if len(unique) > 1:
        conflicts.append({"date_range": "2026-12-25..2027-01-03", "rule": "Cycle 7 allows only one QPT", "qpts": list(unique.values())})
    return daily_changes, test_changes, conflicts

def build_proposal(path):
    daily, events, warnings, raw_rows = parse_schedule_text(extract_pdf(path))
    daily_changes, test_changes, conflicts = compare_with_authoritative(daily, events)
    return {"schema_version": 1, "status": "awaiting_owner_approval", "source_file": path.name,
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "generated_at_utc": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "extracted_daily_chapters": daily, "extracted_test_events": events,
        "daily_changes": daily_changes, "test_changes": test_changes, "conflicts": conflicts,
        "warnings": warnings, "unclassified_date_rows": raw_rows,
        "authoritative_files_modified": False, "approval_required_before_any_change": True}

def render_markdown(p):
    lines = ["# LifeOS schedule proposal", "", f"- Status: {p['status']}",
      f"- Source: {p['source_file']}", f"- SHA-256: {p['source_sha256']}",
      "- Safety: config/plan.yml and config/tests.yml were not modified.",
      "- Action required: review every row and explicitly approve exact changes before applying anything.",
      "", "## Daily chapter differences"]
    lines += [f"- {x['date']} ({x['change']}): existing={x['existing']!r}; proposed={x['proposed']!r}" for x in p["daily_changes"]] or ["- No daily chapter rows were confidently extracted."]
    lines += ["", "## Test events"]
    for x in p["test_changes"]:
        lines.append(f"- {x['date']} — {x['name']} ({x['kind']}, {x['change']})")
        if x["existing_on_date"]: lines.append("  - Already scheduled: " + ", ".join(e["name"] for e in x["existing_on_date"]))
    if not p["test_changes"]: lines.append("- No test events were confidently extracted.")
    lines += ["", "## Rule conflicts"]
    lines += [f"- {c.get('date', c.get('date_range'))}: {c['rule']} — {json.dumps(c, ensure_ascii=False)}" for c in p["conflicts"]] or ["- No conflicts detected by automated checks."]
    lines += ["", "## Warnings"] + [f"- {w}" for w in p["warnings"]]
    if not p["warnings"]: lines.append("- None.")
    lines += ["", "## Approval gate", "Nothing has been applied. Do not edit the authoritative plan until the owner approves the exact changes.", ""]
    return "\n".join(lines)

def process(path):
    p = build_proposal(path)
    STATE.mkdir(parents=True, exist_ok=True)
    PROPOSAL_JSON.write_text(json.dumps(p, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    PROPOSAL_MD.write_text(render_markdown(p), encoding="utf-8")
    return p

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", help="Specific PDF path; relative paths resolve from repository root")
    args = parser.parse_args()
    if args.file:
        path = Path(args.file)
        if not path.is_absolute(): path = ROOT / path
        if path.suffix.lower() != ".pdf": raise SystemExit("Only PDF files are accepted.")
    else:
        INBOX.mkdir(parents=True, exist_ok=True)
        pdfs = sorted(INBOX.glob("*.pdf"))
        if not pdfs: raise SystemExit("No PDFs found in inbox/schedules/. Add a PDF and run again.")
        path = pdfs[-1]
    p = process(path)
    print(f"Proposal written for {path.name}; authoritative config untouched.")
    print(f"Daily changes: {len(p['daily_changes'])}; test rows: {len(p['test_changes'])}; conflicts: {len(p['conflicts'])}")

if __name__ == "__main__": main()
