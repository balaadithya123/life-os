# LifeOS app production pipeline

Last updated: 2026-10-21

## Goal

Automate the work around app building and publishing while keeping manual build-tool actions and production approval under owner control. This pipeline must work across supported repositories rather than assume every app uses the LifeOS Cloudflare Worker.

## Current architecture

1. **Intake and planning** — `inbox/projects/*.json` creates a project record, build brief, lifecycle tasks, and acceptance-criteria checklist through `src/project_pipeline.py`.
2. **Manual build boundary** — the owner builds in the chosen app builder or IDE. LifeOS prepares prompts/checklists; it must not claim to have built an app unless a repository diff or artifact exists.
3. **Verification** — CI runs syntax/tests/security checks defined by the target repository. LifeOS's own regression suite protects the automation code.
4. **Manual publish boundary** — production releases require an explicit owner approval. No AI agent may merge around branch protection, skip tests, or silently publish.
5. **Post-release checks** — production health checks and scheduled DevWatch inspect configured public URLs and repository signals. Failures become deduplicated GitHub issues and alerts.
6. **Learning loop** — `inbox/feedback/`, `inbox/observations/`, DevWatch state and production observations feed `state/optimisation_report.md`. Trends are evidence-based; absent analytics must be reported as unavailable, not fabricated.
7. **Repair loop** — AI triage may summarise workflow/failed-step metadata and recommend a reproduction, patch direction and regression test. Source changes must be made on a branch and reviewed through a PR.

## Implemented in Phase A

- CI validates Worker JavaScript syntax, TOML parsing, endpoint/authentication contracts, KV binding and cron schedule.
- `.github/workflows/post-deploy-smoke.yml` checks `/health` after a successful deployment workflow on main, retries transient failures, and opens/updates an incident issue on failure.
- Production deployment remains a manually triggered workflow in the protected `production` environment.

## Implemented in Phase B (this change)

- `.github/workflows/ai-failure-triage.yml` listens for failures from known LifeOS workflows and can be manually invoked for a run ID.
- It collects workflow/job/failed-step metadata and creates or updates a deduplicated GitHub issue.
- If `GEMINI_API_KEY` is configured, Gemini provides a bounded diagnosis based on metadata only. If it is absent or the request fails, the issue still gets created with a manual diagnostic path.
- The AI output is advisory. This workflow does not read full logs, modify code, push branches, merge PRs, bypass checks, or deploy production.

## Next phases

### Phase B2 — controlled repair proposals
- Add a branch-only patch proposal mechanism with a hard file allowlist, patch-size limit, no secret/config/deployment edits by default, and mandatory tests.
- Open draft PRs only after validation passes; never auto-merge.
- Add a regression test from every accepted bug fix where practical.

### Phase C — production feedback and optimisation (implementation in progress)
- `src/project_monitor.py` stores timestamped healthy and failed HTTP health samples; incident notifications continue to exclude healthy samples.
- `.github/workflows/phase-c-optimisation.yml` runs the regression suite and generates `state/phase_c_optimisation.md` weekly or on manual dispatch.
- `src/phase_c_metrics.py` calculates sampled health-check success, repeated incident signals, observed failure-to-next-healthy sample intervals, timestamped feedback themes, and deployment failure rate only when records exist.
- Missing/untimestamped data is explicitly reported as unavailable. The sampled health rate is not an SLA uptime measurement, and sample intervals are not exact incident durations.
- The report creates an evidence-linked optimisation queue. It does not modify source code; owner approval remains required for feature or production changes.
- Product analytics and performance metrics remain unavailable until a provider or data source is explicitly configured.

## Required safeguards

- Least-privilege GitHub Actions permissions.
- Concurrency for state-writing workflows.
- No tokens, personal contact data, or secret values in prompts/issues.
- Treat commit messages, issue text, external pages, and logs as untrusted input.
- Bounded retries and model output; graceful fallback if AI APIs are unavailable.
- Production changes require explicit approval and post-deploy verification.
- Do not disable existing study, weekly learning, DevWatch or lifecycle workflows until replacement behaviour is tested end-to-end.

## Manual verification checklist

- [ ] Run **Post-deployment smoke test** and confirm `/health` returns expected JSON.
- [ ] Test Telegram `/status`, `/tasks`, and `/radar` with the existing bot.
- [ ] Confirm at least one scheduled notification arrives.
- [ ] Trigger a safe test failure on a temporary branch and confirm failure triage creates/updates an issue.
- [ ] Confirm the protected production environment still gates deployment.
