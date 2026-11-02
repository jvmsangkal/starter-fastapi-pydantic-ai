# AGENTS.md

Guide for coding agents working in this repo.

## Stack

- Python 3.15 (pinned in `.python-version`), dependencies managed by **uv** (`uv.lock` is committed).
- **FastAPI** web app, **Pydantic AI** agent (OpenAI provider via `pydantic-ai-slim[openai]`),
  **SQLModel** ORM (SQLite by default).
- **ruff** (lint + format), **pyrefly** (type checking), **pytest** (tests), **pre-commit**.
- Tool config lives in `pyproject.toml`; common commands are `make` targets.

## Layout

```
app/main.py               FastAPI app: lifespan sets up logging, opens resources, creates tables; /health, /chat, /items
app/env.py                pydantic-settings schema; `env = load_env()` validates env/.env at import
app/logging.py            setup_logging(): loguru to stderr at LOG_LEVEL, stdlib logging routed into it
app/request_log.py        ASGI middleware: x-request-id in every log line and the response; one access line per request
app/agent.py              Pydantic AI agent (model check deferred; no API key needed to boot)
app/db.py                 engine factory from env.DATABASE_URL + SessionDep (reads app.state.engine)
app/resources.py          open_resources(): engine on app.state + agent HTTP client, closed on shutdown
app/models.py             SQLModel table models
tests/                    pytest; conftest.py blocks real model requests, uses in-memory SQLite
Makefile                  dev workflow targets (`make help`)
.agents/skills/           Library Skills symlinks into .venv (Cursor and other agents)
.agents/ruff_after_edit.py  Agent hook: ruff fix + format on edited .py files
.claude/skills/           same Library Skills symlinks for Claude Code
.cursor/hooks.json        Cursor afterFileEdit hook -> .agents/ruff_after_edit.py
.claude/settings.json     Claude Code PostToolUse hook -> .agents/ruff_after_edit.py
.github/workflows/ci.yml  CI: sync, lint, format check, typecheck, test
```

## Commands

```bash
make dev         # uv sync + pre-commit install
make run         # fastapi dev server with reload on http://127.0.0.1:8000
make lint        # ruff check + ruff format --check
make format      # pre-commit on all files (ruff --fix, ruff format, pyrefly, hygiene)
make typecheck   # pyrefly check
make test        # pytest
make check       # lint + typecheck + test (what CI runs)
make lock        # refresh uv.lock
make skills      # install/refresh Library Skills after dependency changes
make clean       # remove caches and bytecode
```

Before finishing a change, run `make check`; CI runs the same checks and must stay green.

## Conventions

- Add dependencies with `uv add <pkg>` (or `uv add --dev <pkg>`); never edit `uv.lock` by hand or use `pip`.
- Ruff formats with single quotes; let `make format` / the agent hooks fix style instead of hand-formatting.
- Type-annotate all functions; `pyrefly check` must report 0 errors.
- Tests must never call a real LLM: override the agent with `TestModel`/`FunctionModel`
  (`with agent.override(model=TestModel()): ...`). Real requests are blocked in `tests/conftest.py`.
- Tests must never touch `app.db`: use the `session`/`client` fixtures, which override
  `get_session` with an in-memory SQLite engine.
- The app must boot without secrets. `DATABASE_URL` defaults to `sqlite:///./app.db`;
  `OPENAI_API_KEY` is only needed to actually call the model.
- Read config only via `from app.env import env`, never `os.environ`/`os.getenv`. Add a new
  variable as a typed field on `Settings` in `app/env.py` (secrets as `SecretStr`) and
  document it in `.env.example`.
- Open shared clients (DB engine, HTTP clients) in `open_resources` in `app/resources.py`,
  never at import; put the ones routes need on `app.state`.
- Log with `from loguru import logger`, not `logging.getLogger`. Keep the `setup_logging()` call
  in the lifespan: `fastapi run app/main.py` imports the app before uvicorn applies its log
  config, which would undo a setup done at import.
- New table models go in `app/models.py` (imported by `app/main.py` so `create_all` sees them).
  There are no migrations yet; tables are created on startup.
- Keep it minimal: don't add infrastructure (Docker, auth, observability, migrations) unless asked.
