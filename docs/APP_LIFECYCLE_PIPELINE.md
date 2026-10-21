# App lifecycle pipeline

## Current MVP
- Project intake JSON becomes a structured project record, build brief and ordered task plan.
- Manual build and publishing are explicit gates; LifeOS does not claim to do them.
- Feedback and production observations are grouped by category and prioritised by severity and repetition.
- A weekly workflow refreshes the trend report and runs regression tests.
- DevWatch incidents are included when state/dev.json exists.

## Use
1. Add an idea JSON file to `inbox/projects/`.
2. GitHub Actions validates it, runs tests and creates `state/projects/<id>/BUILD_BRIEF.md`, `project.json` and `tasks.json`.
3. Build manually with the brief; then register the repository and published URL in the project record.
4. Add evidence to `inbox/feedback/` and `inbox/observations/`; the weekly report ranks recurring issues.
5. Implement proposed fixes on branches, test and review them. Production deployment is not automated by this workflow.

## Boundaries / next slice
This is deterministic heuristic triage, not an LLM claim. It does not yet auto-create GitHub issues/PRs or send Telegram approval buttons. Analytics trends require real analytics data. Keep the existing Worker and study/DevWatch workflows running until replacements pass end-to-end checks.
