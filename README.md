# life-os

LifeOS is a hybrid automation system: the existing Cloudflare Worker handles Telegram commands and daily brief/radar/evening triggers; GitHub Actions handles weekly learning, nightly DevWatch, and regression tests. AI chats (Claude, ChatGPT, Grok) coordinate substantial work through Handoff Hub.

The Python learning profile and schedule live in `config/` and `state/` in this repo; Worker-agent task/score/mistake records live in the existing Cloudflare KV namespace. Do not disable either runtime until equivalent automations have passed end-to-end verification.

## One-time setup (about 10 minutes). Do the steps in this order
1. **Telegram bot.** In Telegram open @BotFather, send `/newbot`, copy the token. Send any message to your new bot,
   then open `https://api.telegram.org/bot<TOKEN>/getUpdates` and copy the number after `"chat":{"id":`.
2. **Private GitHub repo** named `life-os` (empty).
3. **Repo Settings > Secrets and variables > Actions**, add:
   `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`, `GEMINI_API_KEY` (free, from aistudio.google.com).
   Optional: `GROQ_API_KEY` (free tier). `OPENAI_API_KEY` and `XAI_API_KEY` cost money, skip them.
4. **Repo Settings > Actions > General > Workflow permissions** > "Read and write permissions".
5. **Upload everything from this zip** into the repo (drag the unzipped contents into the GitHub page, commit).
   Pushing triggers `selfcheck`, and you get "life-os is live" on Telegram, or a list of what is missing.
6. In `config/plan.yml` fill `start` and `end` for each cycle (real dates, no quotes). That makes daily picks follow your cycle.

That is all. Everything below happens on its own.

## What runs, automatically
| When (IST) | What |
|---|---|
| 07:00 daily | Cloudflare Worker: JEE v5 morning brief, today's schedule and radar highlights |
| 12:30 daily | Cloudflare Worker: compact news radar digest |
| 20:00 daily | Cloudflare Worker: evening reminder and tomorrow's schedule |
| Sunday 07:30 | GitHub Actions: weekly learning pass and profile update |
| 22:00 daily | GitHub Actions: DevWatch checks failed CI, default-branch status, stale PRs, scheduled-run freshness and production uptime; alerts only on new/changed incidents |
| on relevant pushes | GitHub Actions: selfcheck and offline agent regression tests |

Commands: `/today /done /test /mistake /ok /addchapter /status` (send `/help`).

### LifeOS Agents (Cloudflare)
- The separate `lifeos-agents` Worker provides Planner, Study, Radar, and Build planning roles.
- Telegram commands: `/agents` lists roles; `/agentstatus` checks the authenticated connection; `/agent planner <task>`, `/agent study <task>`, `/agent radar <task>`, or `/agent build <task>` runs a planning request.
- The `life-os` Worker uses `LIFEOS_AGENTS_API_KEY`; the agent Worker uses `AGENT_API_KEY`. These must be the same private secret. `LIFEOS_AGENTS_URL` is optional; the adapter defaults to the deployed agent Worker URL.
- Keep both secrets private and rotate them together. Agent calls are planning-only and cannot execute shell commands, edit repositories, send messages, or deploy software.

## How it personalises and learns
- Each `/mistake` (concept, silly, time) raises that chapter's weakness and brings its next review sooner.
- `/ok` lowers weakness and spaces reviews further out. Untouched chapters drift back toward neutral.
- Daily load adapts to your real completion rate (never above your cap of 3 topics).
- Picks and nudges follow your dominant mistake type and the hours you actually finish tasks.
- 👍/👎 on radar items shifts keyword and source weights, so news gets tuned to you.
- The model router tracks which provider succeeds per task and reorders itself (free ones first).
- Everything it learned is in `state/profile.json` and `state/chapters.json`.

## Grok, ChatGPT and Claude through the hub
- Add this repo to your hub allowlist once. Then any connected AI can read `state/hub_snapshot.md`
  (your plan, weak chapters, mistake mix, open requests) with the hub's GitHub tools.
- To log something or finish a request, the AI commits a small file to `inbox/` (format is at the bottom of the snapshot).
  The next hourly run executes it and answers on Telegram.
- Heavy work (practice sets, answer checking) is queued for the agent named in `config/agents.yml` (default: grok).
- `HUB_URL` / `HUB_TOKEN` secrets are optional and untested; the snapshot and inbox route needs neither.

## Dev engine
DevWatch is active in `src/devwatch.py` and `.github/workflows/devwatch.yml`. It runs nightly at 22:00 IST, checks read-only GitHub CI/status/PR data and configured production URLs, and alerts only on new or changed incidents. Its first live scheduled run is still needed to verify real API access and Telegram delivery.

## Limits to know
- Free quotas (GitHub Actions minutes, Gemini, Groq) change. Check current limits. Hourly polling uses roughly 550 min/month.
- Telegram replies can lag up to an hour. GitHub also delays scheduled runs by several minutes at busy times.
- Gemini and Groq can get hard JEE math wrong. Treat generated solutions as drafts and verify them.
- `tests/run_dry.sh` wipes `state/`. Run it only before going live.
