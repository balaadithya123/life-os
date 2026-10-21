"""Human-in-the-loop app lifecycle pipeline: intake packs and evidence-based trend reports."""
import argparse, hashlib, json, os, re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT_INBOX = ROOT / "inbox/projects"
FEEDBACK_INBOX = ROOT / "inbox/feedback"
OBSERVATION_INBOX = ROOT / "inbox/observations"
PROJECT_STATE = ROOT / "state/projects"
REPORT_PATH = ROOT / "state/optimisation_report.md"
STOP = {"about","after","again","also","been","being","could","from","have","into","just","more","most","need","only","other","should","that","their","there","these","this","those","what","when","where","which","with","would","your","project","users"}

def slugify(value):
    slug = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")[:60].rstrip("-")
    if not slug: raise ValueError("Project name/id must contain letters or numbers")
    return slug

def read_json(path):
    try: return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc: raise ValueError(f"Invalid JSON at {path}: {exc}") from exc

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def validate_project(raw):
    if not isinstance(raw, dict): raise ValueError("Project intake must be a JSON object")
    name, idea = str(raw.get("name", "")).strip(), str(raw.get("idea", "")).strip()
    if not name: raise ValueError("Missing required field: name")
    if not idea: raise ValueError("Missing required field: idea")
    for key in ("features", "success_metrics", "constraints"):
        if key in raw and not isinstance(raw[key], list): raise ValueError(f"{key} must be a JSON array")
    return {"id": str(raw.get("id") or slugify(name)), "name": name, "idea": idea,
        "target_users": str(raw.get("target_users", "Not specified")),
        "platform": str(raw.get("platform", "Web app / PWA (confirm during planning)")),
        "build_tool": str(raw.get("build_tool", "Not selected")),
        "repository": str(raw.get("repository", "")).strip(),
        "published_url": str(raw.get("published_url", "")).strip(),
        "features": [str(x) for x in raw.get("features", [])],
        "success_metrics": [str(x) for x in raw.get("success_metrics", [])],
        "constraints": [str(x) for x in raw.get("constraints", [])],
        "status": "planning", "manual_build_required": True, "manual_publish_required": True,
        "production_changes_require_approval": True, "created_at": str(raw.get("created_at") or datetime.now(timezone.utc).isoformat()),
        "source_file": str(raw.get("_source_file", ""))}

def build_tasks():
    rows = [
        ("research","Research alternatives and user complaints","research",False),
        ("spec","Write product specification and acceptance criteria","planning",False),
        ("architecture","Choose architecture, data model, integrations and deployment target","planning",False),
        ("ux","Prepare user flows, screen list and build prompts","design",False),
        ("readiness","Check repository, environment, permissions and test strategy","readiness",False),
        ("manual_build","Build the application in the selected tool","manual",True),
        ("verification","Run acceptance checks and fix launch-blocking issues","verification",False),
        ("manual_publish","Publish the app and register its production URL","manual",True),
        ("monitoring","Enable uptime, deployment and feedback monitoring","post-release",False),
        ("improve","Review trends and prioritise tested improvements","post-release",False)]
    return [{"id":k,"title":t,"stage":s,"status":"blocked_by_manual_build" if k in {"verification","manual_publish","monitoring","improve"} else "ready","requires_user_action":manual} for k,t,s,manual in rows]

def render_brief(p, tasks):
    def bullets(items): return "\n".join("- "+x for x in items) if items else "- Not specified; decide during planning"
    checklist = "\n".join(f"{i}. **{t['title']}** — {t['status']}" + (" (manual step)" if t["requires_user_action"] else "") for i,t in enumerate(tasks,1))
    return f"""# {p['name']} — build package

## Idea
{p['idea']}

## Context
- Target users: {p['target_users']}
- Platform: {p['platform']}
- Build tool: {p['build_tool']}
- Repository: {p['repository'] or 'Not linked yet'}
- Published URL: {p['published_url'] or 'Not published yet'}

## Features
{bullets(p['features'])}

## Success metrics
{bullets(p['success_metrics'])}

## Constraints
{bullets(p['constraints'])}

## Acceptance criteria to define
- Core features have observable pass/fail criteria.
- Key flows specify loading, empty, success and failure states.
- Authentication, permissions and data access are reviewed before release.
- Primary user journeys have regression tests.
- Production release requires owner approval.

## Lifecycle checklist
{checklist}

## Human-in-the-loop boundary
LifeOS prepares plans and coordinates checks. The owner executes the actual build and publishing steps. Production, destructive, permission and secret changes require explicit approval.
"""

def process_intakes(inbox=PROJECT_INBOX, output=PROJECT_STATE):
    done=[]
    output.mkdir(parents=True, exist_ok=True)
    if not inbox.exists(): return done
    for path in sorted(inbox.glob("*.json")):
        raw=read_json(path)
        if not isinstance(raw,dict): raise ValueError(f"{path.name}: expected a JSON object")
        raw["_source_file"]=path.name
        target=output/slugify(raw.get("id") or raw.get("name", ""))
        existing=target/"project.json"
        if existing.exists():
            try: raw["created_at"]=read_json(existing).get("created_at")
            except ValueError: pass
        p=validate_project(raw); tasks=build_tasks()
        write_json(target/"project.json",p); write_json(target/"tasks.json",tasks)
        target.mkdir(parents=True,exist_ok=True)
        (target/"BUILD_BRIEF.md").write_text(render_brief(p,tasks),encoding="utf-8")
        done.append(f"{p['name']} -> {target}")
    return done

def read_events(directory, kind):
    out=[]
    if not directory.exists(): return out
    for path in sorted(directory.glob("*.json")):
        raw=read_json(path); batch=raw if isinstance(raw,list) else [raw]
        for item in batch:
            if isinstance(item,dict):
                row=dict(item); row.setdefault("kind",kind); row.setdefault("source_file",path.name); out.append(row)
    return out

def severity(e):
    return {"critical":5,"high":4,"medium":3,"normal":3,"low":2,"info":1}.get(str(e.get("severity","medium")).lower(),3)

def report(events, generated_at=None):
    generated_at=generated_at or datetime.now(timezone.utc).isoformat()
    if not events:
        return f"# LifeOS app optimisation report\n\nGenerated: {generated_at}\n\nNo feedback or observations recorded yet. Add JSON files to inbox/feedback/ or inbox/observations/. No trend is inferred without evidence.\n"
    groups=defaultdict(list)
    for e in events:
        category=str(e.get("category") or e.get("type") or "").strip().lower()
        if not category:
            words=[w for w in re.findall(r"[a-z][a-z0-9_-]{2,}", " ".join(str(e.get(k,"")) for k in ("title","description","message")).lower()) if w not in STOP]
            category=words[0] if words else "uncategorised"
        groups[category].append(e)
    ranked=sorted(groups.items(),key=lambda x:(max(severity(e) for e in x[1]),len(x[1])),reverse=True)
    lines=["# LifeOS app optimisation report","",f"Generated: {generated_at}",f"Evidence items analysed: {len(events)}","","Heuristic triage only. Reproduce bugs before changing production.","","## Prioritised trends",""]
    for i,(cat,items) in enumerate(ranked,1):
        level={5:"CRITICAL",4:"HIGH",3:"MEDIUM",2:"LOW",1:"INFO"}[max(severity(e) for e in items)]
        lines.append(f"{i}. **[{level}] {cat}** — {len(items)} evidence item(s)")
        lines.append("   - Next step: investigate and reproduce; prepare a branch and regression test before proposing a fix.")
        for e in items[:3]:
            label=str(e.get("title") or e.get("description") or e.get("message") or "Untitled observation")
            lines.append(f"   - Evidence: {label[:200]} (source: {str(e.get('source') or e.get('source_file') or 'unspecified')[:100]})")
        if len(items)>3: lines.append(f"   - {len(items)-3} additional related item(s) grouped.")
        lines.append("")
    lines += ["## Safe execution policy","","- Automated: collect, group, rank and recommend based on supplied evidence.","- Before merging: run tests, review diffs and verify acceptance criteria.","- Approval required for production deployments, destructive actions, permissions and secret changes.","- This report only reflects evidence available to this run; analytics are not implied unless connected.",""]
    return "\n".join(lines)

def collect_events():
    events=read_events(FEEDBACK_INBOX,"feedback")+read_events(OBSERVATION_INBOX,"observation")
    # Daily historical production-health snapshots support recurrence analysis.
    events += read_events(ROOT/"state/observations","production-monitor")
    events = [e for e in events if str(e.get("status", "")).lower() not in {"ok", "healthy", "success"}]
    dev=ROOT/"state/dev.json"
    if dev.exists():
        try:
            for problem in read_json(dev).get("problems",[]): events.append({"category":"deployment-health","title":str(problem),"severity":"high","source":"state/dev.json"})
        except ValueError: events.append({"category":"monitoring-data","title":"Could not parse state/dev.json","severity":"medium"})
    return events

def run_review():
    events=collect_events()
    REPORT_PATH.parent.mkdir(parents=True,exist_ok=True)
    text=report(events); REPORT_PATH.write_text(text,encoding="utf-8"); return text

def notify_digest():
    # Ensure the workflow's tracked state path exists even when sending is suppressed.
    state_path=ROOT/"state/optimisation_digest.json"
    if not state_path.exists(): write_json(state_path,{})
    # Notify only when the CURRENT incident set changes; don't send a nightly duplicate.
    if os.getenv("DRY_RUN") == "1":
        print("Dry run: Telegram digest suppressed.")
        return
    token, chat = os.getenv("TELEGRAM_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("Telegram credentials unavailable; digest not sent or marked delivered.")
        return
    events=collect_events()
    latest_files=sorted((ROOT/"state/observations").glob("*.json")) if (ROOT/"state/observations").exists() else []
    current=[]
    if latest_files:
        current=read_events(ROOT/"state/observations","production-monitor")
        # Only current-day monitor findings participate in incident notifications.
        latest_name=latest_files[-1].name
        current=[e for e in current if e.get("source_file")==latest_name]
    dev=ROOT/"state/dev.json"
    if dev.exists():
        try:
            current += [{"category":"deployment-health","title":str(x),"severity":"high","source":"state/dev.json"} for x in read_json(dev).get("problems",[])]
        except ValueError:
            current.append({"category":"monitoring-data","title":"Could not parse state/dev.json","severity":"medium"})
    current=[e for e in current if str(e.get("status","")).lower() not in {"ok","healthy","success"}]
    signature_data=sorted((str(e.get("category") or e.get("type") or "incident"),str(e.get("severity") or "medium"),str(e.get("title") or e.get("message") or "")[:240]) for e in current)
    signature=hashlib.sha256(json.dumps(signature_data,ensure_ascii=False).encode()).hexdigest()
    previous=read_json(state_path) if state_path.exists() else {}
    if signature==previous.get("signature"):
        print("Incident set unchanged; Telegram notification suppressed.")
        return
    from common import tg
    if current:
        lines=["LifeOS production-monitor update",f"Active incidents: {len(current)}",""]
        for item in current[:8]:
            lines.append(f"[{str(item.get('severity','medium')).upper()}] {item.get('project_name') or item.get('category') or 'App'}: {item.get('title') or item.get('message') or 'Incident detected'}")
        if len(current)>8: lines.append(f"+ {len(current)-8} additional incident(s). See state/optimisation_report.md.")
        lines.append("\nNo production changes were made. Investigate, test and approve fixes before release.")
    elif previous.get("had_incidents"):
        lines=["LifeOS production-monitor recovery","Previously reported active incidents are no longer present in the latest checks."]
    else:
        print("No active incidents; no Telegram notification needed.")
        write_json(state_path,{"signature":signature,"had_incidents":False})
        return
    tg("\n".join(lines))
    write_json(state_path,{"signature":signature,"had_incidents":bool(current),"updated_at":datetime.now(timezone.utc).isoformat()})

def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("mode",choices=("intake","review","notify","all"),nargs="?",default="all"); mode=parser.parse_args().mode
    if mode in {"intake","all"}:
        rows=process_intakes(); print("\n".join(rows) if rows else "No project intake JSON files found.")
    if mode in {"review","all"}: print(run_review())
    if mode in {"notify","all"}: notify_digest()
    return 0

if __name__=="__main__": raise SystemExit(main())
