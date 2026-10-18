# devwatch spec (inert until moved into place)

Goal: a nightly, read-only check of the repos in `config/repos.yml` that messages Telegram ONLY when something is wrong.

Build as:
- `src/devwatch.py`: for each `owner/repo`, call the GitHub REST API with secret `GH_PAT` (fine-grained, read-only:
  Actions, Contents, Pull requests, Commit statuses). Report (a) workflow runs that failed in the last 24h,
  (b) failing or errored combined status on the default branch HEAD (Vercel deploys show here), (c) PRs open more than 7 days.
  Send one Telegram message via `common.tg`. Also write a one-line summary to `state/dev.json` for `snapshot.py`.
- `.github/workflows/devwatch.yml`: cron `30 16 * * *` (22:00 IST), same commit-state step and concurrency group as `poll.yml`.
- `config/repos.yml`: `repos: [balaadithya123/App_1]` (add others later).
- Tests: a fixture JSON of API responses plus a `DRY_RUN` path, wired into `tests/run_dry.sh`.

Rules: no writes to any app repo, no merges, no secrets in files, silent when everything is green.
Commit the finished files under `proposals/devwatch/` first. The owner moves them into place after reading them.
