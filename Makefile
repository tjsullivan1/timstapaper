# --- Configuration ---
SRC_DIR := src
APP_DIR := $(SRC_DIR)/app
COMPOSE := docker compose -f $(SRC_DIR)/docker-compose.yml
UV := $(shell command -v uv 2> /dev/null)
TEST_DB_NAME := timstapaper_test

.PHONY: help setup sync test test-db lint up down clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Install uv and create venv
	@if [ -z "$(UV)" ]; then echo "Installing uv..."; curl -LsSf https://astral.sh/uv/install.sh | sh; fi
	uv venv

sync: ## Sync local dependencies
	uv sync --project $(APP_DIR) --dev

lint: ## Run ruff on the app directory
	uv run --project $(APP_DIR) ruff check .
	uv run --project $(APP_DIR) ruff format --check .

test-db: ## Start PostgreSQL and create test database
	$(COMPOSE) up -d db
	@echo "Waiting for PostgreSQL to be ready..."
	@until $(COMPOSE) exec -T db pg_isready -U timstapaper > /dev/null 2>&1; do sleep 1; done
	@$(COMPOSE) exec -T db psql -U timstapaper -tc "SELECT 1 FROM pg_database WHERE datname = '$(TEST_DB_NAME)'" | grep -q 1 || \
		$(COMPOSE) exec -T db psql -U timstapaper -c "CREATE DATABASE $(TEST_DB_NAME);"
	@echo "Test database ready."

test: test-db ## Run tests (starts PostgreSQL if needed)
	uv run --project $(APP_DIR) pytest tests/ -v

up: ## Start containers
	$(COMPOSE) up -d --build

down: ## Stop containers
	$(COMPOSE) down

clean: ## Remove local artifacts
	rm -rf .venv .uv .pytest_cache .ruff_cache
	$(COMPOSE) down -v
	find . -type d -name "__pycache__" -exec rm -rf {} +
