.PHONY: help clean dev lock skills run migrate migration format lint typecheck test check
.DEFAULT_GOAL := help

help: ## Display this help message
	@echo "Please use \`make <target>\` where <target> is one of"
	@awk -F ':.*?## ' '/^[a-zA-Z]/ && NF==2 {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

clean: ## Remove general artifact files
	find . -path ./.venv -prune -o -name '*.pyc' -print | xargs rm -f
	find . -path ./.venv -prune -o -name '*.pyo' -print | xargs rm -f
	find . -path ./.venv -prune -o -name '__pycache__' -type d -print | xargs rm -rf
	rm -rf .pytest_cache .ruff_cache

dev: ## Install dependencies for dev and the pre-commit git hooks
	uv sync
	uv run pre-commit install

lock: ## Update uv.lock after editing dependencies in pyproject.toml
	uv lock

# --yes alone only repairs/removes managed links, and --all also pulls in transitive
# deps, so pass the direct-dependency skills from `scan` explicitly.
skills: ## Install/refresh library agent skills in .agents/skills and .claude/skills
	uvx library-skills --yes --claude $$(uvx library-skills scan --json | jq -r '.skills[].name | "--skill=\(.)"')

run: ## Run the FastAPI dev server with auto-reload
	uv run fastapi dev

migrate: ## Apply all pending database migrations (alembic upgrade head)
	uv run alembic upgrade head

migration: ## Autogenerate a migration from model changes: make migration m="add item price"
	@test -n "$(m)" || { echo 'usage: make migration m="message"'; exit 1; }
	uv run alembic revision --autogenerate -m "$(m)"

format: ## Scan and format all files with pre-commit
	uv run pre-commit run --all-files

lint: ## Lint with ruff and check formatting
	uv run ruff check
	uv run ruff format --check

typecheck: ## Type check with pyrefly
	uv run pyrefly check

test: ## Run all tests
	uv run pytest -v

check: lint typecheck test ## Run everything CI runs
