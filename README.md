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
curl http://127.0.0.1:8000/health   # {"status":"ok"}
```

The app starts without any secrets:

- **Database:** `DATABASE_URL` defaults to a local SQLite file, `sqlite:///./app.db`.
  `make migrate` creates it. Point it at another database with `DATABASE_URL=...`.
- **Agent:** `POST /chat` needs `OPENAI_API_KEY` set to actually call the model.

Environment variables are declared and validated once, at import, in `app/env.py` (a
pydantic-settings `Settings` class, in the spirit of t3-env). They come from the process
environment or an optional `.env` in the working directory (gitignored; copy
`.env.example`). App code reads them with `from app.env import env`, never `os.environ`. A
set but invalid variable stops startup with one message that lists every problem:

```text
Invalid environment variables:
  DATABASE_URL: Value error, not a valid SQLAlchemy database URL
  OPENAI_API_KEY: Value error, must not be empty (leave it unset instead)
See .env.example.
```

```bash
curl -X POST http://127.0.0.1:8000/items -H 'content-type: application/json' -d '{"name": "first"}'
curl -X POST http://127.0.0.1:8000/chat -H 'content-type: application/json' -d '{"prompt": "Hello"}'
```

## Database migrations

[Alembic](https://alembic.sqlalchemy.org/) owns the schema. The app no longer creates tables
on startup. `migrations/env.py` reads `DATABASE_URL` from `app.env` and compares against
`SQLModel.metadata`.

```bash
make migrate                      # alembic upgrade head
make migration m="add item price" # alembic revision --autogenerate -m "add item price"
```

After you change a model in `app/models.py`, run `make migration`, review the new file in
`migrations/versions/`, and commit it. Autogenerate misses some changes, such as table
renames. `tests/test_migrations.py` fails if the models and the migrations disagree.

If your `app.db` was created by an older version of this starter, which created tables on
startup, run `uv run alembic stamp head` once instead of `make migrate`.

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
