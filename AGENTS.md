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
app/main.py               create_app(): lifespan, error handler, middleware, routers (features under /v1); `app = create_app()`
app/core/env.py           pydantic-settings schema; `env = load_env()` validates env/.env at import
app/core/logging.py       setup_logging(): loguru to stderr at LOG_LEVEL (JSON lines if LOG_JSON), stdlib logging routed into it
app/core/errors.py        AppError subclasses (NotFoundError 404, ConflictError 409) + their handler
app/core/resources.py     open_resources(): engine on app.state + agent HTTP client, closed on shutdown
app/core/request_log.py   ASGI middleware: x-request-id in every log line and the response; one access line per request
app/core/probes.py        /live and /ready probes; mark_ready() sets app.state.ready around the lifespan yield
app/db/session.py         engine factory from env.DATABASE_URL + SessionDep (reads app.state.engine)
app/db/base.py            imports every feature's table models; `metadata` for Alembic and the test fixtures
app/agents/chat.py        Pydantic AI chat agent and its INSTRUCTIONS (model check deferred; no API key needed to boot)
app/items/                example feature: models.py (table), schemas.py (ItemCreate), service.py (logic), routes.py (/v1/items)
app/chat/                 schemas.py (ChatRequest, ChatResponse), routes.py (POST /v1/chat)
alembic.ini               Alembic config (file_template, ruff post-write hooks)
migrations/               Alembic env.py (URL from app.core.env, metadata from app.db.base) + versions/
tests/                    pytest, mirroring app/; conftest.py blocks real model requests, uses in-memory SQLite
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
make migrate     # alembic upgrade head
make migration m="msg"  # alembic revision --autogenerate -m "msg"
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
- Tests must never touch the `./app.db` file: use the `session`/`client` fixtures, which override
  `get_session` with an in-memory SQLite engine.
- `tests/` mirrors `app/`: tests for `app/items/` go in `tests/items/`, and so on. Shared fixtures
  go in `tests/conftest.py`. Every test directory has an `__init__.py`, so test files in different
  directories can share a name.
- The app must boot without secrets. `DATABASE_URL` defaults to `sqlite:///./app.db`;
  `OPENAI_API_KEY` is only needed to actually call the model.
- Read config only via `from app.core.env import env`, never `os.environ`/`os.getenv`. Add a new
  variable as a typed field on `Settings` in `app/core/env.py` (secrets as `SecretStr`) and
  document it in `.env.example`.
- To add a feature, copy `app/items/` and rename it. The folder name is the feature name, so
  modules have no prefix (`service.py`, not `item_service.py`):
  - `models.py`: SQLModel table models. Import the module in `app/db/base.py`.
  - `schemas.py`: request and response models. Don't take a table model as a request body:
    table models skip validation, so a bad body reaches the database and returns 500.
  - `service.py`: the logic. Functions take a `Session` and raise `AppError` subclasses.
  - `routes.py`: an `APIRouter` whose routes call the service and do nothing else.
  Then include the router in `create_app()` in `app/main.py` with `prefix='/v1'`.
- App-wide plumbing (settings, logging, errors, middleware, probes, resources) lives in
  `app/core/`. There is no `utils/` folder.
- Each Pydantic AI agent gets one module in `app/agents/`, with its prompts in the same module
  (as `chat.py` keeps `INSTRUCTIONS`) or in a `<agent>_prompts.py` next to it.
- Put a client for an outside API in `app/clients/<vendor>/`: `client.py` for the client class
  and `schemas.py` for its request and response models. Open it in `open_resources` and put it
  on `app.state`. Create the folder with the first client, not before.
- Open shared clients (DB engine, HTTP clients) in `open_resources` in `app/core/resources.py`,
  never at import; put the ones routes need on `app.state`.
- Log with `from loguru import logger`, not `logging.getLogger`. Keep the `setup_logging()` call
  in the lifespan: `fastapi run app/main.py` imports the app before uvicorn applies its log
  config, which would undo a setup done at import.
- Never log raw headers: pass them through `redact_headers()` from `app/core/request_log.py`.
- After changing a table model, run `make migration m="..."`, review the generated file, and
  commit it. `migrations/env.py` reads `metadata` from `app/db/base.py`, so autogenerate sees
  only the models imported there. The app does not create tables on startup;
  `tests/db/test_migrations.py` fails if the models and migrations disagree.
- To return an HTTP error from a route, raise an `AppError` subclass from `app/core/errors.py`,
  not `HTTPException`, and don't catch it in the route. The handler registered in
  `create_app()` returns `{"detail": ...}` with the subclass's `status_code`. For a new status,
  add a subclass.
- Keep it minimal: don't add infrastructure (Docker, auth, observability) unless asked.
