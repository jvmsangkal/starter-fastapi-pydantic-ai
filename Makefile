.PHONY: help clean dev lock run format lint typecheck test check
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

run: ## Run the FastAPI dev server with auto-reload
	uv run fastapi dev

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
