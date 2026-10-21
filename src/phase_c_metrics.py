"""Evidence-based Phase C metrics for LifeOS app monitoring and optimisation."""
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBSERVATIONS = ROOT / "state/observations"
FEEDBACK = ROOT / "inbox/feedback"
DEPLOYMENTS = ROOT / "state/deployments"
REPORT = ROOT / "state/phase_c_optimisation.md"


def parse_time(value):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed
    except (TypeError, ValueError):
        return None


def read_records(directory):
    records = []
    if not directory.exists():
        return records
    for path in sorted(directory.glob("*.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            batch = value if isinstance(value, list) else [value]
            for item in batch:
                if isinstance(item, dict):
                    row = dict(item)
                    row.setdefault("source_file", str(path.relative_to(ROOT)))
                    records.append(row)
        except (OSError, json.JSONDecodeError):
            # Broken evidence is excluded, never silently turned into a success.
            continue
    return records


def status_of(row):
    status = str(row.get("status", "")).strip().lower()
    if status in {"ok", "healthy", "success", "passed"}:
        return "healthy"
    if status in {"incident", "error", "failure", "failed", "unhealthy"}:
        return "failure"
    return "unknown"


def build_report(observations, feedback, deployments, now=None, days=7):
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    recent = []
    for row in observations:
        stamp = parse_time(row.get("observed_at") or row.get("timestamp") or row.get("date"))
        if stamp and cutoff <= stamp <= now and status_of(row) in {"healthy", "failure"}:
            recent.append((stamp, row, status_of(row)))
    recent.sort(key=lambda x: x[0])

    healthy = sum(1 for _, _, status in recent if status == "healthy")
    failures = sum(1 for _, _, status in recent if status == "failure")
    total = healthy + failures
    lines = [
        "# LifeOS Phase C — production feedback and optimisation",
        "",
        f"Generated: {now.astimezone(timezone.utc).isoformat()}",
        f"Window: last {days} days",
        "",
        "## Reliability signals",
        "",
    ]
    if total:
        lines.append(f"- **Sampled HTTP health success rate:** {healthy}/{total} checks ({healthy / total * 100:.1f}%). This is a sample-based indicator, not an SLA uptime measurement.")
        lines.append(f"- **Failed health checks:** {failures}")
    else:
        lines.append("- **Sampled HTTP health success rate:** unavailable — no timestamped healthy/failure samples in this window.")
        lines.append("- **Failed health checks:** unavailable — absence of records is not evidence of zero failures.")

    by_project = defaultdict(list)
    for stamp, row, status in recent:
        project = str(row.get("project") or row.get("project_name") or "unspecified-project")[:100]
        by_project[project].append((stamp, row, status))

    repeat = []
    recovery_intervals = []
    for project, items in by_project.items():
        incident_keys = defaultdict(int)
        last_failure = None
        for stamp, row, status in items:
            if status == "failure":
                key = str(row.get("category") or row.get("title") or "unspecified-incident")[:120]
                incident_keys[key] += 1
                last_failure = stamp
            elif status == "healthy" and last_failure is not None:
                recovery_intervals.append((project, (stamp - last_failure).total_seconds() / 3600))
                last_failure = None
        for key, count in incident_keys.items():
            if count >= 2:
                repeat.append((project, key, count))

    lines += ["", "## Recurrence and recovery", ""]
    if repeat:
        for project, key, count in sorted(repeat, key=lambda item: (-item[2], item[0]))[:10]:
            lines.append(f"- **Recurring signal:** {project} — {key} observed {count} times.")
    else:
        lines.append("- No repeated incident category was demonstrated by the available timestamped samples." if recent else "- Recurrence unavailable because no valid health samples were recorded.")

    if recovery_intervals:
        mean_hours = sum(item[1] for item in recovery_intervals) / len(recovery_intervals)
        lines.append(f"- **Observed recovery interval:** mean {mean_hours:.1f} hours across {len(recovery_intervals)} failure-to-next-healthy sample transition(s). This is a sampling interval, not the exact incident duration.")
    else:
        lines.append("- **Observed recovery interval:** unavailable — no failure followed by a later healthy sample in this window.")

    valid_feedback = []
    for row in feedback:
        stamp = parse_time(row.get("created_at") or row.get("observed_at") or row.get("date"))
        if stamp and cutoff <= stamp <= now:
            valid_feedback.append(row)
    categories = defaultdict(list)
    for row in valid_feedback:
        category = str(row.get("category") or row.get("type") or "uncategorised feedback")[:100]
        categories[category].append(row)
    lines += ["", "## Feedback themes", ""]
    if categories:
        for category, rows in sorted(categories.items(), key=lambda item: (-len(item[1]), item[0]))[:10]:
            lines.append(f"- **{category}** — {len(rows)} item(s); evidence: " + ", ".join(str(r.get("source_file", "provided feedback"))[:100] for r in rows[:3]))
    else:
        lines.append("- No timestamped feedback items found in the reporting window; user sentiment/trends are unavailable.")

    deployment_rows = []
    for row in deployments:
        stamp = parse_time(row.get("deployed_at") or row.get("observed_at") or row.get("timestamp") or row.get("date"))
        status = status_of(row)
        if stamp and cutoff <= stamp <= now and status in {"healthy", "failure"}:
            deployment_rows.append((stamp, status, row))
    lines += ["", "## Deployment signals", ""]
    if deployment_rows:
        deploy_failures = sum(1 for _, status, _ in deployment_rows if status == "failure")
        lines.append(f"- **Recorded deployment failure rate:** {deploy_failures}/{len(deployment_rows)} ({deploy_failures / len(deployment_rows) * 100:.1f}%) across {len(deployment_rows)} timestamped deployment records.")
    else:
        lines.append("- Deployment failure rate unavailable — no timestamped deployment records found. Configure an evidence source before drawing conclusions.")

    lines += [
        "",
        "## Prioritised optimisation queue",
        "",
    ]
    queue = []
    for project, key, count in repeat:
        queue.append((0, f"Investigate recurring {project} signal: {key} ({count} observations).", "timestamped health observations"))
    if failures:
        queue.append((1, f"Review {failures} failed health check(s), reproduce the issue, and add a regression check.", "timestamped health observations"))
    if valid_feedback:
        top = sorted(categories.items(), key=lambda item: (-len(item[1]), item[0]))[0]
        queue.append((2, f"Review feedback theme '{top[0]}' ({len(top[1])} item(s)) and validate with the owner.", "timestamped feedback"))
    if not queue:
        queue.append((3, "Improve observability: add timestamped health, deployment, or feedback evidence before prioritising product changes.", "data coverage gap"))
    for i, (_, recommendation, evidence) in enumerate(sorted(queue, key=lambda item: (item[0], item[1]))[:10], 1):
        lines.append(f"{i}. {recommendation} Evidence: {evidence}.")
    lines += [
        "",
        "## Guardrails",
        "",
        "- Recommendations are advisory. No source code, permissions, secrets, or production configuration were changed by this report.",
        "- Production changes require owner approval, regression tests, review, and post-release verification.",
        "- Analytics and deployment rates are marked unavailable unless timestamped records exist; no metrics are inferred from missing data.",
        "",
    ]
    return "\n".join(lines)


def main():
    observations = read_records(OBSERVATIONS)
    feedback = read_records(FEEDBACK)
    deployments = read_records(DEPLOYMENTS)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    content = build_report(observations, feedback, deployments)
    REPORT.write_text(content, encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)} from {len(observations)} health observation(s), {len(feedback)} feedback item(s), and {len(deployments)} deployment record(s).")


if __name__ == "__main__":
    main()
