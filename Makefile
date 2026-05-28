# ============================================================
# OmniSLM — Makefile
# Common development commands
# ============================================================

.PHONY: help dev up down logs test lint format migrate seed clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---- Development ----

dev: ## Run API server locally (requires Poetry install)
	uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug

up: ## Start all services with Docker Compose
	docker compose up -d

down: ## Stop all services
	docker compose down

logs: ## Follow API logs
	docker compose logs -f api

restart: ## Restart API service
	docker compose restart api

# ---- Database ----

migrate: ## Run database migrations
	alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MSG="add_xyz")
	alembic revision --autogenerate -m "$(MSG)"

seed: ## Seed database with test data
	python scripts/seed.py

# ---- Testing ----

test: ## Run all tests
	pytest -v --tb=short

test-cov: ## Run tests with coverage
	pytest -v --tb=short --cov=src --cov-report=term-missing --cov-report=html

test-unit: ## Run unit tests only
	pytest tests/unit -v --tb=short

test-integration: ## Run integration tests only
	pytest tests/integration -v --tb=short

# ---- Code Quality ----

lint: ## Run linter
	ruff check src tests

format: ## Format code
	ruff format src tests
	ruff check src tests --fix

typecheck: ## Run type checker
	mypy src

# ---- Docker ----

build: ## Build Docker images
	docker compose build

build-prod: ## Build production Docker image
	docker build -f docker/Dockerfile.api -t omnislm/api:latest .

# ---- Cleanup ----

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov .coverage dist build *.egg-info
