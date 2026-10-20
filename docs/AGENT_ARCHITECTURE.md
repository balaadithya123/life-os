# LifeOS agent architecture

This is the operating map for LifeOS. The source of truth remains the existing repository and its JEE v5 config; agents must not create a second data store or overwrite the approved schedule.

## Agent responsibilities

| Agent | Owns | Trigger | Writes | Guardrails |
|---|---|---|---|---|
| Planner / daily brief | Today's chapter picks, completion-aware load, test countdown, carryover signal | Cloudflare's existing brief trigger; GitHub manual fallback | state/today.json, profile and snapshot | Max 3 topics; config/plan.yml and config/tests.yml remain authoritative |
| Study / spaced revision | Weakness scores, mistakes, interval spacing, test history | Telegram commands + weekly learning pass | state/chapters.json, profile, JSONL history | Does not silently rewrite the schedule |
| Radar | New RSS / official-page updates ranked from feedback | Existing scheduled radar job | state/radar_items.json, state/seen.json, feedback state | Compact digest; no repeat of seen items |
| DevWatch | Failed CI runs, bad default-branch status, stale PRs, scheduled-workflow freshness, production URL health | Nightly at 22:00 IST + manual dry run | state/dev.json | Read-only against watched repos; only alerts on new/changed incidents and recovery |
| Schedule intake (parallel task to Claude) | Extract PDF schedule into a proposed diff | Separate inbox / explicit processing | Proposal JSON + Markdown | Approval-first; never overwrites config/plan.yml or config/tests.yml automatically |
| Hub task router | Routes substantial work to specialist AI agents | Handoff Hub tasks / inbox requests | Hub task records and inbox/ completion files | No secrets in prompts; keep task result auditable |

## DevWatch configuration

config/repos.yml defines read-only repositories, scheduled workflow freshness thresholds, and public production URLs. A private monitored repository requires a narrowly scoped GH_PAT; public repositories can be checked anonymously within GitHub API rate limits.

The devwatch workflow is scheduled for 22:00 Asia/Kolkata. It persists the current incident set in state/dev.json, so the same incident is not re-alerted every night. When the incident clears, it sends a recovery message.

## Verification and migration rule

The agent-regression-tests workflow runs offline fixtures for DevWatch. A successful CI run proves the fixture tests passed; it does not prove live Telegram delivery, live GitHub API access, or that the nightly cron has executed successfully. Keep existing GitHub Actions and Cloudflare triggers until equivalent jobs have been exercised end-to-end and duplicate-message behavior is checked. Do not disable either runtime merely because a deployment succeeded.