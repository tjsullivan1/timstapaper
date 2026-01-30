# --- Configuration ---
SRC_DIR := src
APP_DIR := $(SRC_DIR)/app
COMPOSE := docker compose
UV := $(shell command -v uv 2> /dev/null)

.PHONY: help setup sync test lint up down clean

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

test: ## Run tests
	uv run --project $(APP_DIR) pytest tests/ --cov=.

up: ## Start containers
	$(COMPOSE) up -d --build

down: ## Stop containers
	$(COMPOSE) down

clean: ## Remove local artifacts
	rm -rf .venv .uv .pytest_cache .ruff_cache
	$(COMPOSE) down -v
	find . -type d -name "__pycache__" -exec rm -rf {} +
