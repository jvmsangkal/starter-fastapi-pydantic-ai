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
app/main.py               FastAPI app: lifespan creates tables; /health, /chat, /items
app/agent.py              Pydantic AI agent (model check deferred; no API key needed to boot)
app/db.py                 SQLModel engine from DATABASE_URL + SessionDep dependency
app/models.py             SQLModel table models
tests/                    pytest; conftest.py blocks real model requests, uses in-memory SQLite
Makefile                  dev workflow targets (`make help`)
.agents/skills/           Library Skills symlinks into .venv (Cursor and other agents)
.claude/skills/           same Library Skills symlinks for Claude Code
.cursor/hooks.json        Cursor afterFileEdit hook -> ruff fix, ruff format, pyrefly on the edited .py file
.claude/settings.json     Claude Code PostToolUse hook -> same; pyrefly errors returned as additionalContext
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
- New table models go in `app/models.py` (imported by `app/main.py` so `create_all` sees them).
  There are no migrations yet; tables are created on startup.
- Keep it minimal: don't add infrastructure (Docker, auth, observability, migrations) unless asked.
