# LifeOS Agent Office — foundation MVP

This is the first reviewable foundation for the AI-employee-office plan. It is intentionally separate from the existing Cloudflare Telegram Worker runtime. It is not deployed and does not replace the existing bot or GitHub Actions.

## Implemented in this branch
- `providers.py`: provider router for local/private Ollama, Cloudflare Workers AI, and Gemini. Routine tasks prefer Ollama; complex tasks try hosted providers first.
- `engine.py`: strict declarative workflow validation, read-only UTC/file tools, project-root path confinement, SQLite task/run history, and approval gates for Telegram/GitHub side effects.
- `tests/test_engine.py`: offline tests for validation, approval gates, path confinement, and persistence.

## Run tests
`python -m unittest discover -s agent_office/tests -v`

## Configuration
- `OLLAMA_BASE_URL` (default `http://127.0.0.1:11434`), `OLLAMA_MODEL` (default `qwen2.5:3b`).
- Optional `CF_ACCOUNT_ID`, `CF_API_TOKEN`, `CF_MODEL` (default `@cf/meta/llama-3.1-8b-instruct`).
- Optional `GEMINI_API_KEY`, `GEMINI_MODEL` (default `gemini-2.5-flash`).

The Ollama URL may point to a private server you control, but do not expose port 11434 publicly. Put remote access behind authenticated private networking or a protected gateway. Hosted inference quota is not the same as a free, persistent Ollama VM.

## Not implemented yet
There is no visual n8n-style editor, agent factory, parallel worker pool, Telegram inbound bridge, Handoff Hub adapter, schedule service, or cloud deployment in this slice. There is no arbitrary shell tool. Side-effecting tools remain disabled pending explicit approval integration. Production deploys, repository writes, and merges remain owner-approved. GitHub/Drive store code/files but do not provide a free always-on Ollama server.
