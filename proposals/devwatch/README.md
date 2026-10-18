# DevWatch proposal (inert until approved)

Read-only nightly GitHub checks: workflow failures from the last 24h, failing/error combined status on default-branch HEAD, and open PRs older than seven days. Telegram is silent when green; a compact one-line state/dev.json summary is written for snapshot consumers.

Move src/devwatch.py to src/devwatch.py, repos.yml to config/repos.yml, and devwatch.yml to .github/workflows/devwatch.yml after review. The workflow runs at 22:00 IST and shares the life-os-state concurrency group with poll.yml. Set GH_PAT to a read-only token with Actions, Contents, Pull requests and Commit statuses access; existing Telegram secrets are reused. Fixture test uses DEVWATCH_FIXTURE and DEVWATCH_REPOS; add its invocation to the existing tests/run_dry.sh, do not replace that suite.

Code has not been run in this environment. Nothing activates until files are moved. No app repo is written, no merge occurs, and no production migration is applied.
