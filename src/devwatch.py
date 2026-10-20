"""Autonomous read-only DevWatch: CI failures, stale PRs, scheduled-run freshness, and site uptime.

Alerts only for new/changed incidents; sends a recovery notice when the system returns to green.
Never writes to monitored application repositories.
"""
import json
import os
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
import yaml
from common import DRY, ROOT, load, now, save, tg

GH = "https://api.github.com"
TIMEOUT = 12
HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "LifeOS-DevWatch/1.0",
}
TOKEN = os.getenv("GH_PAT") or os.getenv("GITHUB_TOKEN")
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def load_config():
    path = ROOT / "config" / "repos.yml"
    if not path.exists():
        return {"repos": [], "sites": []}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {"repos": [], "sites": []}


def gh_get(path, params=None, fixture=None):
    """GET a GitHub API path with bounded retry for rate-limited responses."""
    fixture_path = fixture or os.getenv("DEVWATCH_FIXTURE")
    if fixture_path:
        data = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
        if path in data:
            return data[path]
        raise KeyError(f"Fixture has no response for {path}")
    last_response = None
    for attempt in range(3):
        response = requests.get(GH + path, headers=HEADERS, params=params or {}, timeout=TIMEOUT)
        last_response = response
        if response.status_code == 403 and attempt < 2:
            retry_after = response.headers.get("Retry-After")
            remaining = response.headers.get("X-RateLimit-Remaining")
            reset = response.headers.get("X-RateLimit-Reset")
            delay = None
            if retry_after:
                try: delay = float(retry_after)
                except ValueError: delay = None
            elif remaining == "0" and reset:
                try: delay = max(0, float(reset) - time.time())
                except ValueError: delay = None
            if delay is not None:
                time.sleep(min(5.0, max(0.25, delay)))
                continue
        if response.status_code == 401:
            raise PermissionError("GitHub API returned 401; check token validity")
        if response.status_code == 403:
            raise PermissionError("GitHub API returned 403; check GH_PAT permissions or API rate limits")
        if response.status_code == 404:
            raise FileNotFoundError("GitHub API returned 404; repository or resource may be private/missing")
        response.raise_for_status()
        return response.json()
    if last_response is not None:
        last_response.raise_for_status()
    raise RuntimeError("GitHub API request failed after bounded retries")


def gh_get_all(path, params=None, fixture=None, collection=None, max_pages=10):
    """Fetch paginated API collections; fixtures remain single-response and offline."""
    fixture_path = fixture or os.getenv("DEVWATCH_FIXTURE")
    first = gh_get(path, params, fixture)
    if fixture_path:
        return first.get(collection, []) if collection and isinstance(first, dict) else first
    def unpack(payload):
        return payload.get(collection, []) if collection and isinstance(payload, dict) else payload
    items = list(unpack(first) or [])
    page_size = int((params or {}).get("per_page", 100))
    if len(items) < page_size:
        return items
    for page in range(2, max_pages + 1):
        query = {**(params or {}), "page": page, "per_page": page_size}
        payload = gh_get(path, query, fixture)
        page_items = list(unpack(payload) or [])
        items.extend(page_items)
        if len(page_items) < page_size:
            break
    return items

def _created_at(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def check_repo(repo_cfg, fixture=None, clock=None):
    """Return human-readable problems for one repository. Empty means green."""
    full_name = repo_cfg if isinstance(repo_cfg, str) else repo_cfg.get("name", "")
    if not full_name or "/" not in full_name:
        return [f"DevWatch config error: invalid repository entry {full_name!r}"]
    owner, name = full_name.split("/", 1)
    problems = []
    clock = clock or datetime.now(timezone.utc)
    since = (clock - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        runs = gh_get_all(f"/repos/{owner}/{name}/actions/runs",
                          {"status": "completed", "created": f">={since}", "per_page": 100}, fixture,
                          collection="workflow_runs")
        for run in runs:
            if run.get("conclusion") in {"failure", "timed_out", "action_required"}:
                problems.append(
                    f"{full_name}: workflow {run.get('name', 'unknown')} "
                    f"{run.get('conclusion')} ({run.get('html_url', 'no run URL')})"
                )
    except Exception as exc:
        problems.append(f"{full_name}: workflow-run check unavailable ({type(exc).__name__}: {exc})")

    default_branch = "main"
    try:
        info = gh_get(f"/repos/{owner}/{name}", fixture=fixture)
        default_branch = (info.get("default_branch") if isinstance(info, dict) else None) or "main"
        branch = gh_get(f"/repos/{owner}/{name}/branches/{default_branch}", fixture=fixture)
        sha = (branch.get("commit") or {}).get("sha") if isinstance(branch, dict) else None
        if sha:
            status = gh_get(f"/repos/{owner}/{name}/commits/{sha}/status", fixture=fixture)
            state = status.get("state") if isinstance(status, dict) else None
            if state in {"failure", "error"}:
                problems.append(f"{full_name}: default branch {default_branch} combined status is {state}")
            try:
                checks = gh_get_all(f"/repos/{owner}/{name}/commits/{sha}/check-runs",
                                    {"filter": "latest", "per_page": 100}, fixture, collection="check_runs")
                for check in checks:
                    if check.get("conclusion") in {"failure", "timed_out", "action_required", "cancelled"}:
                        problems.append(f"{full_name}: check run {check.get('name', 'unknown')} "
                                        f"{check.get('conclusion')} ({check.get('html_url', 'no check URL')})")
            except KeyError:
                # Older fixtures may only cover the combined-status API.
                pass
    except Exception as exc:
        problems.append(f"{full_name}: default-branch status unavailable ({type(exc).__name__}: {exc})")

    try:
        prs = gh_get_all(f"/repos/{owner}/{name}/pulls", {"state": "open", "per_page": 100}, fixture)
        cutoff = clock - timedelta(days=7)
        for pr in prs if isinstance(prs, list) else []:
            created = _created_at(pr.get("created_at"))
            if created and created < cutoff:
                age = (clock - created).days
                problems.append(
                    f"{full_name}: PR #{pr.get('number')} open {age}d "
                    f"({pr.get('html_url', pr.get('title', 'no URL'))})"
                )
    except Exception as exc:
        problems.append(f"{full_name}: pull-request check unavailable ({type(exc).__name__}: {exc})")

    if isinstance(repo_cfg, dict):
        for wf in repo_cfg.get("scheduled_workflows", []):
            path = wf.get("file")
            max_age = int(wf.get("max_age_hours", 48))
            if not path:
                continue
            try:
                data = gh_get(f"/repos/{owner}/{name}/actions/workflows/{path}/runs",
                              {"per_page": 1}, fixture)
                recent = (data.get("workflow_runs") or []) if isinstance(data, dict) else []
                latest = recent[0] if recent else None
                created = _created_at((latest or {}).get("run_started_at") or (latest or {}).get("created_at"))
                if not created:
                    problems.append(f"{full_name}: scheduled workflow {path} has no recorded runs")
                elif clock - created > timedelta(hours=max_age):
                    problems.append(
                        f"{full_name}: scheduled workflow {path} has not run in {max_age}h "
                        f"(last run {created.isoformat()})"
                    )
                elif latest.get("conclusion") in {"failure", "timed_out", "action_required"}:
                    problems.append(
                        f"{full_name}: latest scheduled workflow {path} failed "
                        f"({latest.get('html_url', 'no run URL')})"
                    )
            except Exception as exc:
                problems.append(f"{full_name}: scheduled workflow {path} check unavailable ({type(exc).__name__}: {exc})")
    return problems


def check_site(site, fixture=None):
    """Check an external production URL without sending credentials or following custom auth."""
    name, url = site.get("name", site.get("url", "unnamed site")), site.get("url", "")
    if not url or urlparse(url).scheme not in {"https", "http"}:
        return [f"Site monitor config error: invalid URL for {name}"]
    if fixture or os.getenv("DEVWATCH_FIXTURE"):
        key = "site:" + url
        data = json.loads(Path(fixture or os.getenv("DEVWATCH_FIXTURE")).read_text(encoding="utf-8"))
        if key not in data:
            return [f"{name}: no site fixture response"]
        site_data = data[key]
        status = int(site_data.get("status", 0))
        if status < 200 or status >= 400:
            return [f"{name}: HTTP {status} at {url}"]
        expected = site.get("expected_text")
        if expected and expected not in str(site_data.get("body", "")):
            return [f"{name}: expected content missing (possible soft-404) at {url}"]
        return []
    try:
        response = requests.get(url, timeout=8, allow_redirects=True,
                                headers={"User-Agent": "LifeOS-DevWatch/1.0"})
        if response.status_code < 200 or response.status_code >= 400:
            return [f"{name}: HTTP {response.status_code} at {url}"]
        expected = site.get("expected_text")
        if expected and expected not in response.text:
            return [f"{name}: expected content missing (possible soft-404) at {url}"]
        return []
    except requests.RequestException as exc:
        return [f"{name}: request failed ({type(exc).__name__}) at {url}"]


def main(fixture=None):
    conf = load_config()
    clock = datetime.now(timezone.utc)
    problems = []
    for repo in conf.get("repos", []):
        problems.extend(check_repo(repo, fixture=fixture, clock=clock))
    for site in conf.get("sites", []):
        problems.extend(check_site(site, fixture=fixture))

    previous = load("dev.json", {})
    old = set(previous.get("problems", []))
    current = set(problems)
    # URLs often change between runs for the same incident. Normalize them for
    # alert comparison while keeping the current full URL in the saved state.
    def incident_key(problem):
        return re.sub(r"https?://\S+", "<url>", problem).strip().lower()
    old_by_key = {incident_key(p): p for p in old}
    current_by_key = {incident_key(p): p for p in current}
    added = sorted(p for key, p in current_by_key.items() if key not in old_by_key)
    recovered = sorted(p for key, p in old_by_key.items() if key not in current_by_key)
    status = {
        "at": now().isoformat(),
        "summary": "green" if not problems else f"{len(problems)} issue(s)",
        "problems": sorted(problems),
        "new_problems": added,
        "recovered": recovered,
    }
    # Save only after notification succeeds. If Telegram fails, the old state remains
    # so the next run retries instead of silently losing the alert.
    if added:
        tg("LIFEOS DEVWATCH — new/changed issue(s)\n" + "\n".join(f"• {p}" for p in added))
    elif recovered and not problems:
        tg("LIFEOS DEVWATCH — recovered\nAll monitored repositories and sites are green again.")
    elif recovered:
        tg("LIFEOS DEVWATCH — resolved issue(s)\n" + "\n".join(f"• {p}" for p in recovered))
    elif DRY:
        print("[devwatch] no new incidents; current:", status["summary"])
    save("dev.json", status)
    return status


if __name__ == "__main__":
    import sys
    fixture_arg = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "--fixture" else None
    main(fixture_arg)
