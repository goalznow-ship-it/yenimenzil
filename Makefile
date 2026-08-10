.PHONY: help infra-up infra-down infra-logs api-install api-dev api-test api-lint db-migrate db-revision seed dev

API_DIR := apps/api

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

infra-up: ## Start PostgreSQL (PostGIS) and Redis
	docker compose up -d postgres redis

infra-down: ## Stop infra containers
	docker compose stop postgres redis

infra-logs: ## Follow infra logs
	docker compose logs -f postgres redis

api-install: ## Install backend dependencies (editable, dev extras)
	python3 -m venv $(API_DIR)/.venv
	$(API_DIR)/.venv/bin/pip install -U pip
	$(API_DIR)/.venv/bin/pip install -e "$(API_DIR)[dev]"

api-dev: ## Run FastAPI dev server on :8000 with reload
	$(API_DIR)/.venv/bin/uvicorn app.main:app --app-dir $(API_DIR) --reload --port 8000

api-test: ## Run backend tests
	$(API_DIR)/.venv/bin/pytest $(API_DIR)/app/tests -q

api-lint: ## Lint backend with ruff
	$(API_DIR)/.venv/bin/ruff check $(API_DIR)/app

db-migrate: ## Apply migrations
	cd $(API_DIR) && .venv/bin/alembic upgrade head

db-revision: ## Create new migration (usage: make db-revision MSG="add x")
	cd $(API_DIR) && .venv/bin/alembic revision --autogenerate -m "$(MSG)"

seed: ## Seed the database from frontend demo listings
	cd $(API_DIR) && .venv/bin/python -m scripts.seed

dev: infra-up ## Start everything for local development
	@echo "Run 'pnpm dev' in another terminal, then 'make api-dev'."
