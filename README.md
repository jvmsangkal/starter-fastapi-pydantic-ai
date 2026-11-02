# starter-fastapi-pydantic-ai

Minimal starter template: a **FastAPI** app with one **Pydantic AI** agent and **SQLModel**
for the database, on Python 3.15.
Tooling: **uv** (deps + lockfile), **ruff** (lint + format), **pyrefly** (types), **pytest**,
**pre-commit**, a **Makefile**, GitHub Actions CI, and Cursor / Claude Code hooks that run
ruff on Python files after an agent edits them.

## Setup

Install [uv](https://docs.astral.sh/uv/) and `make`, then:

```bash
make dev   # uv sync + install the pre-commit git hooks
```

Run `make` (or `make help`) to list every target.

## Run

```bash
make migrate   # create or update the database schema
make run
curl http://127.0.0.1:8000/live    # {"status":"ok"}
curl http://127.0.0.1:8000/ready   # {"status":"ok"}
```

`GET /live` always returns 200. `GET /ready` returns 200 after lifespan startup finishes and
503 before then and once shutdown begins. Point liveness and readiness probes at them. Both
are left out of the OpenAPI schema.

The app starts without any secrets:

- **Database:** `DATABASE_URL` defaults to a local SQLite file, `sqlite:///./app.db`.
  `make migrate` creates it. Point it at another database with `DATABASE_URL=...`.
- **Agent:** `POST /v1/chat` needs `OPENAI_API_KEY` set to actually call the model.

Environment variables are declared and validated once, at import, in `app/core/env.py` (a
pydantic-settings `Settings` class, in the spirit of t3-env). They come from the process
environment or an optional `.env` in the working directory (gitignored; copy
`.env.example`). App code reads them with `from app.core.env import env`, never `os.environ`. A
set but invalid variable stops startup with one message that lists every problem:

```text
Invalid environment variables:
  DATABASE_URL: Value error, not a valid SQLAlchemy database URL
  OPENAI_API_KEY: Value error, must not be empty (leave it unset instead)
See .env.example.
```

The feature routes are under `/v1`:

```bash
curl -X POST http://127.0.0.1:8000/v1/items -H 'content-type: application/json' -d '{"name": "first"}'
curl http://127.0.0.1:8000/v1/items
curl http://127.0.0.1:8000/v1/items/1
curl -X POST http://127.0.0.1:8000/v1/chat -H 'content-type: application/json' -d '{"prompt": "Hello"}'
```

## Layout

Each feature has its own folder under `app/`, and app-wide code lives in `app/core/`:

```text
app/
  main.py          create_app(): lifespan, error handler, middleware, routers
  core/            env, logging, errors, resources, request_log, probes
  db/              session.py (engine, SessionDep), base.py (metadata of every table model)
  agents/          chat.py: the Pydantic AI agent and its instructions
  items/           models.py, schemas.py, service.py, routes.py
  chat/            schemas.py, routes.py
migrations/        Alembic env.py and versions/
tests/             mirrors app/ (core/, db/, agents/, items/, chat/) plus conftest.py
```

To add a feature, copy `app/items/` and `tests/items/`, rename them, import the new models
module in `app/db/base.py`, and include the new router in `create_app()` in `app/main.py`.
`AGENTS.md` lists the rules for each file.

## Database migrations

[Alembic](https://alembic.sqlalchemy.org/) owns the schema. The app no longer creates tables
on startup. `migrations/env.py` reads `DATABASE_URL` from `app.core.env` and compares against
the `metadata` in `app/db/base.py`, which imports every feature's table models.

```bash
make migrate                      # alembic upgrade head
make migration m="add item price" # alembic revision --autogenerate -m "add item price"
```

After you change a table model, such as `app/items/models.py`, run `make migration`, review
the new file in `migrations/versions/`, and commit it. Autogenerate misses some changes, such
as table renames. `tests/db/test_migrations.py` fails if the models and the migrations
disagree.

If your `app.db` was created by an older version of this starter, which created tables on
startup, run `uv run alembic stamp head` once instead of `make migrate`.

## Logging

`app/core/logging.py` sets up [loguru](https://loguru.readthedocs.io/) when the app starts and
routes the standard `logging` module into it. Uvicorn, FastAPI, SQLAlchemy, and app code
all print to stderr in loguru's format:

```text
2026-11-02 14:36:06.706 | INFO     | - | uvicorn.lifespan.on:startup:62 - Application startup complete.
2026-11-02 14:36:15.814 | INFO     | demo-123 | app.core.request_log:__call__:56 - POST /v1/items 200 13.8ms
```

- Set the level with `LOG_LEVEL`: `DEBUG`, `INFO` (the default), `WARNING`, `ERROR`, or
  `CRITICAL`.
- Set `LOG_JSON=1` to print one JSON object per line instead, for log collectors. Each
  line has `time`, `level`, `message`, `location`, and `request_id`, plus `exception`
  when there is a traceback:

  ```text
  {"time": "2026-11-02T14:36:31.098166+00:00", "level": "INFO", "message": "GET /v1/items 200 15.2ms", "location": "app.core.request_log:__call__:56", "request_id": "demo-123"}
  ```
- In app code, log with `from loguru import logger`.
- To log request or response headers, pass them through `redact_headers()` from
  `app/core/request_log.py`. It replaces the values of `authorization`, `cookie`, `set-cookie`,
  and `x-api-key` (any case) with `[REDACTED]`.

`RequestLogMiddleware` in `app/core/request_log.py` gives each request an id. It takes the
`x-request-id` request header if the value is 1 to 128 letters, digits, `.`, `_`, `:`, or
`-`, and otherwise generates a UUID4. The response returns the id in `x-request-id`. Every
log line written during the request shows the id after the level, and lines outside a
request show `-`. The middleware also writes one access line per request, as in the second
line above, except for `/live` and `/ready`. Uvicorn's own access log is off, so each
request gets one access line.

The setup runs in the app's lifespan. Uvicorn prints `Started server process` and
`Waiting for application startup.` before the lifespan starts, so those two lines keep
uvicorn's format. The reloader's lines under `make run` keep it too.

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

After an agent edits an existing `.py` file, `.cursor/hooks.json` and `.claude/settings.json`
run `.agents/ruff_after_edit.py`, which runs `ruff check --fix` and `ruff format` on that
file. Other files are skipped, and the script never exits with a blocking code.

## Library skills

`.agents/skills/` (Cursor and other agents) and `.claude/skills/` (Claude Code) hold
[Library Skills](https://library-skills.io/): the official agent skills that fastapi,
pydantic-ai, and sqlmodel ship inside their packages. They are committed as relative
symlinks into `.venv`, so they resolve after `make dev` (or `uv sync`). Run `make skills`
after changing dependencies to add, repair, or remove them (needs `jq`).

## Editor

Open in VS Code / Cursor and install the recommended extensions (ruff, pyrefly).
Format and fix-on-save are configured in `.vscode/settings.json`.
