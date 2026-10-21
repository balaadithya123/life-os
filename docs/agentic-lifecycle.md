# Agentic app lifecycle automation

- Failed app-lifecycle/selfcheck runs automatically create or update a GitHub issue.
- Run Actions → Agentic repair proposal and provide an issue number to ask Gemini for a constrained patch. The runner applies it in isolation and runs the full Python test suite.
- A passing candidate becomes a draft PR only. Failed candidates are not proposed for merge. No PR is auto-merged and no production deployment is performed.
- Add GEMINI_API_KEY under repository Settings → Secrets and variables → Actions if it is not already there. A key configured only as a Cloudflare Worker secret is not available to GitHub Actions.
- Allow GitHub Actions to create issues and pull requests in repository settings.
- This repository has no root wrangler.toml/package.json identifying a Worker release target. Deployment automation is intentionally not added until the correct app directory and build command are verified.
- For deployment later, configure a protected GitHub production environment with required reviewers, then add a least-privilege CLOUDFLARE_API_TOKEN secret scoped to that environment. Never put tokens in source, issues, or chat.
