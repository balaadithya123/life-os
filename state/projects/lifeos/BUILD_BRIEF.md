# LifeOS — build package

## Idea
Personal Telegram-based study and workflow assistant with scheduled briefs, revision support, and command-based task tracking.

## Context
- Target users: Personal workflow user
- Platform: Cloudflare Worker with Telegram integration
- Build tool: Cloudflare Workers
- Repository: balaadithya123/life-os
- Published URL: https://life-os.balaadithya74.workers.dev

## Features
- Telegram task and study commands
- Scheduled workflow briefs
- JEE revision schedule support
- Read-only public endpoint monitoring

## Success metrics
- Public endpoint availability
- HTTP response status
- Recurring uptime incidents
- Daily read-only health check for the deployed Worker

## Constraints
- Monitoring is read-only and must not submit user data
- Never change production state or deploy automatically
- Production fixes require explicit owner approval

## Acceptance criteria to define
- Core features have observable pass/fail criteria.
- Key flows specify loading, empty, success and failure states.
- Authentication, permissions and data access are reviewed before release.
- Primary user journeys have regression tests.
- Production release requires owner approval.

## Lifecycle checklist
1. **Research alternatives and user complaints** — ready
2. **Write product specification and acceptance criteria** — ready
3. **Choose architecture, data model, integrations and deployment target** — ready
4. **Prepare user flows, screen list and build prompts** — ready
5. **Check repository, environment, permissions and test strategy** — ready
6. **Build the application in the selected tool** — done (manual step)
7. **Run acceptance checks and fix launch-blocking issues** — done
8. **Publish the app and register its production URL** — done (manual step)
9. **Enable uptime, deployment and feedback monitoring** — ready
10. **Review trends and prioritise tested improvements** — blocked_by_manual_publish

## Human-in-the-loop boundary
LifeOS prepares plans and coordinates checks. The owner executes the actual build and publishing steps. Production, destructive, permission and secret changes require explicit approval.
