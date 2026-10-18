# life-os

Runs by itself on GitHub Actions (free). After the one-time setup you never open GitHub again:
you only talk to a Telegram bot, and your AI chats (Claude, ChatGPT, Grok) read and write through the hub.
No Supabase, no database, no website. Your data is a few small JSON files in `state/`, versioned by git.

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
| 07:00 daily | Morning brief: today's picks (max 3), countdown, radar items with 👍/👎 buttons |
| hourly 06-23 | Reads your Telegram commands and any `inbox/` files left by an AI chat, replies |
| Sunday 07:30 | Weekly learning pass: updates your profile, queues a practice-set request for your weakest chapter |
| on every push | `selfcheck`: validates config and tells you what is missing |

Commands: `/today /done /test /mistake /ok /addchapter /status` (send `/help`).

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
`proposals/devwatch/SPEC.md` describes a nightly check of your GitHub repos (failed runs, open PRs, deploy status).
It is a spec for an agent to build; it is not active until its files are moved into place.

## Limits to know
- Free quotas (GitHub Actions minutes, Gemini, Groq) change. Check current limits. Hourly polling uses roughly 550 min/month.
- Telegram replies can lag up to an hour. GitHub also delays scheduled runs by several minutes at busy times.
- Gemini and Groq can get hard JEE math wrong. Treat generated solutions as drafts and verify them.
- `tests/run_dry.sh` wipes `state/`. Run it only before going live.
