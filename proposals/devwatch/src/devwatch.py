"""Nightly read-only check of repos in config/repos.yml.
Messages Telegram only when something is wrong. Writes one-line summary to state/dev.json.
Inert until moved from proposals/devwatch/ into place.
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
import yaml

# Allow running from proposals/devwatch/src/ or after move to src/
ROOT = Path(__file__).resolve().parent.parent
if (ROOT / "src" / "common.py").exists():
    sys.path.insert(0, str(ROOT / "src"))
else:
    # still under proposals/
    sys.path.insert(0, str(ROOT.parent.parent / "src"))

from common import DRY, IST, now, save, tg  # noqa: E402

GH = "https://api.github.com"
TOKEN = os.getenv("GH_PAT") or os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def load_repos():
    # Prefer local config next to this file (proposals layout), else repo config/
    for p in [
        Path(__file__).resolve().parent.parent / "repos.yml",
        ROOT / "config" / "repos.yml",
        ROOT / "repos.yml",
    ]:
        if p.exists():
            data = yaml.safe_load(p.read_text()) or {}
            return data.get("repos") or []
    return ["balaadithya123/App_1"]


def gh_get(url, params=None):
    if os.getenv("DEVWATCH_FIXTURE"):
        fixture_path = Path(os.getenv("DEVWATCH_FIXTURE"))
        data = json.loads(fixture_path.read_text())
        # Simple path-keyed fixture: key = path after api.github.com
        key = url.replace(GH, "")
        if key in data:
            return data[key]
        # fallback: try full url
        if url in data:
            return data[url]
        return []
    r = requests.get(url, headers=HEADERS, params=params or {}, timeout=30)
    r.raise_for_status()
    return r.json()


def check_repo(full_name: str) -> list:
    """Return list of problem strings (empty => green)."""
    problems = []
    owner, repo = full_name.split("/", 1)
    since = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")

    # (a) failed workflow runs in last 24h
    runs = gh_get(
        f"{GH}/repos/{owner}/{repo}/actions/runs",
        {"status": "completed", "created": f">={since}", "per_page": 30},
    )
    for run in (runs.get("workflow_runs") or []) if isinstance(runs, dict) else []:
        if run.get("conclusion") == "failure":
            problems.append(
                f"{full_name}: workflow '{run.get('name')}' failed "
                f"({run.get('html_url') or run.get('id')})"
            )

    # (b) combined status on default branch HEAD
    repo_info = gh_get(f"{GH}/repos/{owner}/{repo}")
    default = (repo_info.get("default_branch") if isinstance(repo_info, dict) else None) or "main"
    branch = gh_get(f"{GH}/repos/{owner}/{repo}/branches/{default}")
    sha = (branch.get("commit") or {}).get("sha") if isinstance(branch, dict) else None
    if sha:
        status = gh_get(f"{GH}/repos/{owner}/{repo}/commits/{sha}/status")
        state = status.get("state") if isinstance(status, dict) else None
        if state in ("failure", "error"):
            problems.append(
                f"{full_name}: HEAD status on {default} is {state} "
                f"(Vercel / CI may be red)"
            )

    # (c) PRs open > 7 days
    prs = gh_get(
        f"{GH}/repos/{owner}/{repo}/pulls",
        {"state": "open", "per_page": 50},
    )
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    for pr in prs if isinstance(prs, list) else []:
        created = pr.get("created_at")
        if not created:
            continue
        try:
            created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
        except ValueError:
            continue
        if created_dt < cutoff:
            age = (datetime.now(timezone.utc) - created_dt).days
            problems.append(
                f"{full_name}: PR #{pr.get('number')} open {age}d "
                f"({pr.get('html_url') or pr.get('title')})"
            )

    return problems


def main():
    repos = load_repos()
    all_problems = []
    for name in repos:
        try:
            all_problems.extend(check_repo(name))
        except Exception as e:
            all_problems.append(f"{name}: check failed ({type(e).__name__}: {e})")

    summary = "green" if not all_problems else f"{len(all_problems)} issue(s)"
    # Write one-line summary for snapshot.py (only when running from live tree)
    try:
        save("dev.json", {"at": now().isoformat(), "summary": summary, "problems": all_problems})
    except Exception:
        # under proposals/ the state/ path may not exist; ignore
        pass

    if all_problems:
        body = "devwatch ⚠️\n" + "\n".join(f"• {p}" for p in all_problems)
        tg(body)
    else:
        # silent when green (per SPEC)
        if DRY:
            print("[devwatch] all green")
    return 0 if not all_problems else 1


if __name__ == "__main__":
    sys.exit(main() or 0)
