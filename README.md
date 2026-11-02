# starter-fastapi-pydantic-ai

Minimal starter template: a **FastAPI** app with one **Pydantic AI** agent and **SQLModel**
for the database, on Python 3.15.
Tooling: **uv** (deps + lockfile), **ruff** (lint + format), **pyrefly** (types), **pytest**,
**pre-commit**, a **Makefile**, GitHub Actions CI, and Cursor / Claude Code hooks that run
pre-commit on files after an agent edits them.

## Setup

Install [uv](https://docs.astral.sh/uv/) and `make`, then:

```bash
make dev   # uv sync + install the pre-commit git hooks
```

Run `make` (or `make help`) to list every target.

## Run

```bash
make run
curl http://127.0.0.1:8000/health   # {"status":"ok"}
```

The app starts without any secrets:

- **Database:** `DATABASE_URL` defaults to a local SQLite file, `sqlite:///./app.db`, created
  on startup. Point it at another database with `DATABASE_URL=...`.
- **Agent:** `POST /chat` needs `OPENAI_API_KEY` set to actually call the model.

```bash
curl -X POST http://127.0.0.1:8000/items -H 'content-type: application/json' -d '{"name": "first"}'
curl -X POST http://127.0.0.1:8000/chat -H 'content-type: application/json' -d '{"prompt": "Hello"}'
```

## Lint, format, typecheck, test

```bash
make lint        # ruff check + ruff format --check
make format      # run all pre-commit hooks (ruff fix + format, pyrefly, hygiene) on every file
make typecheck   # pyrefly check
make test        # pytest
make check       # lint + typecheck + test, same as CI
```

Tests use Pydantic AI's `TestModel` and an in-memory SQLite database, so they need no API
key and no database.

## Agent hooks

`.cursor/hooks.json` and `.claude/settings.json` run `pre-commit run --files <edited file>`
after every agent edit. They need `jq` on your `PATH`; without it they silently do nothing.

## Editor

Open in VS Code / Cursor and install the recommended extensions (ruff, pyrefly).
Format and fix-on-save are configured in `.vscode/settings.json`.
