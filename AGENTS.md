# AGENTS.md

Guide for coding agents working in this repo.

## Stack

- Python 3.15 (pinned in `.python-version`), dependencies managed by **uv** (`uv.lock` is committed).
- **FastAPI** web app, **Pydantic AI** agent (OpenAI provider via `pydantic-ai-slim[openai]`).
- **ruff** (lint + format), **pyrefly** (type checking), **pytest** (tests), **pre-commit**.
- All tool config lives in `pyproject.toml`.

## Layout

```
app/main.py                 FastAPI app: GET /health, POST /chat
app/agent.py                Pydantic AI agent (model check deferred; no API key needed to boot)
tests/                      pytest suite; conftest.py blocks real model requests
scripts/ruff_after_edit.py  Agent hook: ruff fix + format on edited .py files
.cursor/hooks.json          Cursor afterFileEdit hook -> scripts/ruff_after_edit.py
.claude/settings.json       Claude Code PostToolUse hook -> scripts/ruff_after_edit.py
.github/workflows/ci.yml    CI: sync, lint, format check, typecheck, test
```

## Commands

```bash
uv sync                      # install/update deps into .venv
uv run fastapi dev           # dev server with reload on http://127.0.0.1:8000
uv run ruff check --fix      # lint (and autofix)
uv run ruff format           # format
uv run pyrefly check         # type check
uv run pytest                # tests
uv run pre-commit run --all-files  # everything pre-commit runs
```

Before finishing a change, run `ruff check`, `ruff format --check`, `pyrefly check`, and `pytest`; CI runs the same and must stay green.

## Conventions

- Add dependencies with `uv add <pkg>` (or `uv add --dev <pkg>`); never edit `uv.lock` by hand or use `pip`.
- Type-annotate all functions; `pyrefly check` must report 0 errors.
- Tests must never call a real LLM: override the agent with `TestModel`/`FunctionModel`
  (`with agent.override(model=TestModel()): ...`). Real requests are blocked in `tests/conftest.py`.
- The app must boot without secrets. `OPENAI_API_KEY` is only needed to actually call the model.
- Keep it minimal: don't add infrastructure (DB, Docker, auth, observability) unless asked.
