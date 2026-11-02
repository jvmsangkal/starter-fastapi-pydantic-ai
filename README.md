# starter-fastapi-pydantic-ai

Minimal starter template: a **FastAPI** app with one **Pydantic AI** agent, on Python 3.15.
Tooling: **uv** (deps + lockfile), **ruff** (lint + format), **pyrefly** (types), **pytest**,
**pre-commit**, GitHub Actions CI, and Cursor / Claude Code hooks that run ruff after agent edits.

## Setup

Install [uv](https://docs.astral.sh/uv/), then:

```bash
uv sync
```

## Run

```bash
uv run fastapi dev
curl http://127.0.0.1:8000/health   # {"status":"ok"}
```

The app starts without any secrets. To actually call the model via `POST /chat`, set
`OPENAI_API_KEY` first:

```bash
curl -X POST http://127.0.0.1:8000/chat -H 'content-type: application/json' -d '{"prompt": "Hello"}'
```

## Lint, format, typecheck, test

```bash
uv run ruff check --fix
uv run ruff format
uv run pyrefly check
uv run pytest
```

Tests use Pydantic AI's `TestModel`, so they need no API key.

## Pre-commit hooks

```bash
uv run pre-commit install
uv run pre-commit run --all-files   # optional: run on everything once
```

## Editor

Open in VS Code / Cursor and install the recommended extensions (ruff, pyrefly).
Format and fix-on-save are configured in `.vscode/settings.json`.
