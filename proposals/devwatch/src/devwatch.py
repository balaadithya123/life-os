"""Proposed read-only GitHub health watcher."""
import datetime as dt, json, os, pathlib, sys, requests, yaml
HERE=pathlib.Path(__file__).resolve()
ROOT=HERE.parents[3] if "proposals" in HERE.parts else HERE.parents[1]
sys.path.insert(0,str(ROOT/"src"))
from common import STATE, tg
API="https://api.github.com"
NOW=dt.datetime.now(dt.timezone.utc)
def parse(v): return dt.datetime.fromisoformat(v.replace("Z","+00:00")) if v else None
def main():
    fp=os.getenv("DEVWATCH_FIXTURE")
    fixture=json.loads(pathlib.Path(fp).read_text()) if fp else None
    rp=pathlib.Path(os.getenv("DEVWATCH_REPOS",ROOT/"config/repos.yml"))
    repos=(yaml.safe_load(rp.read_text()) or {}).get("repos",[])
    token=os.getenv("GH_PAT")
    if not repos: raise SystemExit("No repositories configured")
    if not fixture and not token: raise SystemExit("GH_PAT required unless DEVWATCH_FIXTURE is set")
    headers={"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"}
    if token: headers["Authorization"]="Bearer "+token
    def get(path):
        if fixture is not None:
            if path not in fixture: raise KeyError("Missing fixture: "+path)
            return fixture[path]
        r=requests.get(API+"/"+path,headers=headers,timeout=25); r.raise_for_status(); return r.json()
    reports=[]
    for name in repos:
        issues=[]
        try:
            branch=get("repos/"+name)["default_branch"]
            sha=get("repos/"+name+"/commits/"+branch)["sha"]
            runs=get(f"repos/{name}/actions/runs?per_page=100").get("workflow_runs",[])
            cutoff=NOW-dt.timedelta(hours=24)
            failed=[f'{x.get("name","workflow")} #{x.get("run_number","?")} ({x.get("conclusion")})' for x in runs if parse(x.get("created_at")) and parse(x["created_at"])>=cutoff and x.get("conclusion") in ("failure","timed_out","action_required")]
            if failed: issues.append("failed workflow runs (24h): "+", ".join(failed[:8]))
            status=get(f"repos/{name}/commits/{sha}/status")
            state=(status.get("state") or "pending").lower()
            bad=[x.get("context","status") for x in status.get("statuses",[]) if (x.get("state") or "").lower() in ("failure","error")]
            if state in ("failure","error") or bad: issues.append("default-branch HEAD status: "+state+(" ("+", ".join(bad[:6])+")" if bad else ""))
            prs=get(f"repos/{name}/pulls?state=open&per_page=100")
            old=[f'#{p.get("number")} {p.get("title","(untitled)")} ({parse(p.get("created_at")).date()})' for p in prs if parse(p.get("created_at")) and parse(p["created_at"])<NOW-dt.timedelta(days=7)]
            if old: issues.append("PRs open >7 days: "+"; ".join(old[:8]))
            reports.append({"repo":name,"default_branch":branch,"head_sha":sha,"issues":issues,"checked_at":NOW.isoformat()})
        except Exception as e: reports.append({"repo":name,"issues":[f"health check errored: {type(e).__name__}: {e}"],"checked_at":NOW.isoformat()})
    bad=[x for x in reports if x["issues"]]
    summary={"checked_at":NOW.isoformat(),"repos_checked":len(reports),"problem_count":len(bad),"reports":reports}
    STATE.mkdir(parents=True,exist_ok=True)
    (STATE/"dev.json").write_text(json.dumps(summary,separators=(",",":"),ensure_ascii=False)+"\n")
    if bad:
        lines=["LifeOS DevWatch: GitHub issues detected"]
        for x in bad: lines += ["\n"+x["repo"]]+["- "+i for i in x["issues"]]
        tg("\n".join(lines))
    else: print(f"DevWatch: {len(reports)} repositories green; Telegram stays silent.")
if __name__=="__main__": main()
