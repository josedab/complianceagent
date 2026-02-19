# ComplianceAgent Makefile
# Run `make help` to see available commands

.DEFAULT_GOAL := help
.PHONY: help install dev dev-down run-backend run-frontend run-workers test test-backend test-frontend lint lint-backend lint-frontend format type-check migrate migrate-new build up down logs clean pre-commit docker-build docker-push seed status check doctor check-all

# Colors for terminal output
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RESET := \033[0m

##@ General

help: ## Show this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\n$(BLUE)Usage:$(RESET)\n  make $(GREEN)<target>$(RESET)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(RESET)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development Setup

install: ## Install all dependencies (backend + frontend)
	@echo "$(BLUE)Installing backend dependencies...$(RESET)"
	cd backend && uv venv && uv pip install -e ".[dev]"
	@echo "$(BLUE)Installing frontend dependencies...$(RESET)"
	cd frontend && npm install
	@echo "$(GREEN)✓ All dependencies installed$(RESET)"

install-backend: ## Install backend dependencies only
	cd backend && uv venv && uv pip install -e ".[dev]"

install-frontend: ## Install frontend dependencies only
	cd frontend && npm install

install-hooks: ## Install pre-commit hooks
	pip install pre-commit
	pre-commit install
	pre-commit install --hook-type commit-msg
	@echo "$(GREEN)✓ Pre-commit hooks installed$(RESET)"

doctor: ## Diagnose common setup issues
	@echo "$(BLUE)🔍 Running ComplianceAgent diagnostics...$(RESET)"
	@echo ""
	@echo "$(YELLOW)Prerequisites:$(RESET)"
	@command -v python3 >/dev/null 2>&1 && echo "  ✅ Python: $$(python3 --version)" || echo "  ❌ Python 3 not found"
	@python3 -c 'import sys; exit(0 if sys.version_info >= (3,12) else 1)' 2>/dev/null && echo "  ✅ Python version ≥ 3.12" || echo "  ❌ Python 3.12+ required (install: pyenv install 3.12)"
	@command -v node >/dev/null 2>&1 && echo "  ✅ Node.js: $$(node -v)" || echo "  ❌ Node.js not found"
	@command -v docker >/dev/null 2>&1 && echo "  ✅ Docker: $$(docker --version | head -1)" || echo "  ❌ Docker not found"
	@command -v uv >/dev/null 2>&1 && echo "  ✅ uv: $$(uv --version)" || echo "  ⚠️  uv not found (optional, speeds up pip installs)"
	@echo ""
	@echo "$(YELLOW)Environment:$(RESET)"
	@test -f .env && echo "  ✅ .env file exists" || echo "  ❌ .env missing (run: cp .env.example .env)"
	@test -d backend/.venv && echo "  ✅ Backend venv exists" || echo "  ❌ Backend venv missing (run: make install-backend)"
	@test -d frontend/node_modules && echo "  ✅ Frontend node_modules exists" || echo "  ❌ Frontend deps missing (run: make install-frontend)"
	@echo ""
	@echo "$(YELLOW)Services:$(RESET)"
	@docker compose -f docker/docker-compose.yml ps --format '{{.Name}} {{.Status}}' 2>/dev/null | grep -q "running" && echo "  ✅ Docker services running" || echo "  ⚠️  Docker services not running (run: make dev)"
	@curl -sf http://localhost:8000/health >/dev/null 2>&1 && echo "  ✅ Backend API responding" || echo "  ⚠️  Backend not running (run: make run-backend)"
	@curl -sf -o /dev/null http://localhost:3000 2>/dev/null && echo "  ✅ Frontend responding" || echo "  ⚠️  Frontend not running (run: make run-frontend)"
	@echo ""
	@echo "$(GREEN)✓ Diagnostics complete$(RESET)"

##@ Development Environment

dev: ## Start development infrastructure (postgres, redis, elasticsearch, minio)
	docker compose -f docker/docker-compose.yml up -d postgres redis elasticsearch minio
	@echo "$(GREEN)✓ Development infrastructure started$(RESET)"
	@echo "$(BLUE)Waiting for services to be ready...$(RESET)"
	@sleep 5
	@echo "$(GREEN)✓ Services ready$(RESET)"

dev-minimal: ## Start minimal infrastructure (postgres + redis only — faster, less RAM)
	docker compose -f docker/docker-compose.minimal.yml up -d
	@echo "$(GREEN)✓ Minimal infrastructure started (Postgres + Redis)$(RESET)"
	@echo "$(YELLOW)Note: Elasticsearch and MinIO not running. Some features may be limited.$(RESET)"

dev-down: ## Stop development infrastructure
	docker compose -f docker/docker-compose.yml down
	@echo "$(GREEN)✓ Development infrastructure stopped$(RESET)"

dev-logs: ## Show development infrastructure logs
	docker compose -f docker/docker-compose.yml logs -f

status: ## Show status of development infrastructure services
	@echo "$(BLUE)Docker services:$(RESET)"
	@docker compose -f docker/docker-compose.yml ps 2>/dev/null || echo "  No services running (run 'make dev' to start)"
	@echo ""
	@echo "$(BLUE)Backend:$(RESET)"
	@curl -s http://localhost:8000/health 2>/dev/null && echo "" || echo "  Backend not running (run 'make run-backend')"
	@echo ""
	@echo "$(BLUE)Frontend:$(RESET)"
	@curl -s -o /dev/null -w "  Frontend responding (HTTP %{http_code})" http://localhost:3000 2>/dev/null && echo "" || echo "  Frontend not running (run 'make run-frontend')"

run-backend: ## Run backend API server (requires dev infrastructure)
	cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000

run-frontend: ## Run frontend development server
	cd frontend && npm run dev

run-workers: ## Run Celery workers
	cd backend && source .venv/bin/activate && celery -A app.workers worker --loglevel=info

run-beat: ## Run Celery beat scheduler
	cd backend && source .venv/bin/activate && celery -A app.workers beat --loglevel=info

##@ Testing

test: test-backend test-frontend ## Run all tests

test-backend: ## Run backend tests with coverage
	cd backend && source .venv/bin/activate && pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=xml

test-backend-fast: ## Run backend tests without coverage (faster)
	cd backend && source .venv/bin/activate && pytest tests/ -v -x

test-frontend: ## Run frontend tests with coverage
	cd frontend && npm test -- --coverage --passWithNoTests

test-frontend-watch: ## Run frontend tests in watch mode
	cd frontend && npm run test:watch

test-e2e: ## Run end-to-end tests (requires all services running)
	cd backend && source .venv/bin/activate && pytest tests/e2e/ -v --timeout=60
	@echo "$(GREEN)✓ E2E tests passed$(RESET)"

##@ Code Quality

lint: lint-backend lint-frontend ## Run all linters

lint-backend: ## Lint backend code with ruff
	cd backend && source .venv/bin/activate && ruff check .
	cd backend && source .venv/bin/activate && ruff format --check .

lint-frontend: ## Lint frontend code with ESLint
	cd frontend && npm run lint

format: format-backend format-frontend ## Format all code

format-backend: ## Format backend code with ruff
	cd backend && source .venv/bin/activate && ruff format .
	cd backend && source .venv/bin/activate && ruff check --fix .

format-frontend: ## Format frontend code with Prettier
	cd frontend && npx prettier --write 'src/**/*.{ts,tsx,js,jsx,json,css}'

type-check: type-check-backend type-check-frontend ## Run all type checkers

type-check-backend: ## Type check backend with mypy
	cd backend && source .venv/bin/activate && mypy app --ignore-missing-imports

type-check-frontend: ## Type check frontend with TypeScript
	cd frontend && npm run type-check

security-check: ## Run security checks (bandit)
	cd backend && source .venv/bin/activate && bandit -r app -c pyproject.toml

pre-commit: ## Run pre-commit on all files
	pre-commit run --all-files

check: lint type-check test ## Run all checks (lint + type-check + test)

check-all: lint type-check security-check test ## Run all checks including security (pre-commit)

##@ Database

migrate: ## Run database migrations
	cd backend && source .venv/bin/activate && alembic upgrade head
	@echo "$(GREEN)✓ Migrations applied$(RESET)"

migrate-new: ## Create new migration (usage: make migrate-new MSG="description")
	@if [ -z "$(MSG)" ]; then echo "$(YELLOW)Usage: make migrate-new MSG=\"description\"$(RESET)"; exit 1; fi
	cd backend && source .venv/bin/activate && alembic revision --autogenerate -m "$(MSG)"
	@echo "$(GREEN)✓ Migration created$(RESET)"

migrate-down: ## Rollback last migration
	cd backend && source .venv/bin/activate && alembic downgrade -1
	@echo "$(GREEN)✓ Migration rolled back$(RESET)"

migrate-history: ## Show migration history
	cd backend && source .venv/bin/activate && alembic history

migrate-current: ## Show current migration revision
	cd backend && source .venv/bin/activate && alembic current

seed: ## Seed database with demo data (users, orgs, regulations)
	cd backend && source .venv/bin/activate && python ../scripts/seed.py
	@echo "$(GREEN)✓ Demo data seeded (run 'make db-reset && make migrate' to start fresh)$(RESET)"

db-reset: ## Reset database (WARNING: destroys all data)
	@echo "$(YELLOW)WARNING: This will destroy all data in the database$(RESET)"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ]
	cd backend && source .venv/bin/activate && alembic downgrade base && alembic upgrade head
	@echo "$(GREEN)✓ Database reset$(RESET)"

##@ Docker

build: ## Build all Docker images
	docker compose -f docker/docker-compose.yml build
	@echo "$(GREEN)✓ Docker images built$(RESET)"

up: ## Start all services with Docker Compose
	docker compose -f docker/docker-compose.yml up -d
	@echo "$(GREEN)✓ All services started$(RESET)"
	@echo "$(BLUE)Frontend: http://localhost:3000$(RESET)"
	@echo "$(BLUE)Backend API: http://localhost:8000$(RESET)"
	@echo "$(BLUE)API Docs: http://localhost:8000/api/docs$(RESET)"

down: ## Stop all Docker services
	docker compose -f docker/docker-compose.yml down
	@echo "$(GREEN)✓ All services stopped$(RESET)"

logs: ## View Docker logs (all services)
	docker compose -f docker/docker-compose.yml logs -f

logs-backend: ## View backend logs only
	docker compose -f docker/docker-compose.yml logs -f backend

logs-frontend: ## View frontend logs only
	docker compose -f docker/docker-compose.yml logs -f frontend

docker-build: ## Build Docker images for production
	docker build -f docker/Dockerfile.backend -t complianceagent-backend:latest .
	docker build -f docker/Dockerfile.frontend -t complianceagent-frontend:latest .
	@echo "$(GREEN)✓ Production images built$(RESET)"

docker-push: ## Push Docker images to registry (requires REGISTRY env var)
	@if [ -z "$(REGISTRY)" ]; then echo "$(YELLOW)Set REGISTRY env var$(RESET)"; exit 1; fi
	docker tag complianceagent-backend:latest $(REGISTRY)/complianceagent-backend:latest
	docker tag complianceagent-frontend:latest $(REGISTRY)/complianceagent-frontend:latest
	docker push $(REGISTRY)/complianceagent-backend:latest
	docker push $(REGISTRY)/complianceagent-frontend:latest
	@echo "$(GREEN)✓ Images pushed to $(REGISTRY)$(RESET)"

##@ Cleanup

clean: ## Clean up generated files and caches
	@echo "$(BLUE)Cleaning Python caches...$(RESET)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(BLUE)Cleaning Node.js caches...$(RESET)"
	find . -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
	rm -rf frontend/coverage 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete$(RESET)"

clean-all: clean ## Clean everything including node_modules and .venv
	@echo "$(YELLOW)Removing virtual environments and node_modules...$(RESET)"
	rm -rf backend/.venv 2>/dev/null || true
	rm -rf frontend/node_modules 2>/dev/null || true
	@echo "$(GREEN)✓ Full cleanup complete$(RESET)"

clean-docker: ## Remove Docker volumes and images
	docker compose -f docker/docker-compose.yml down -v --rmi local
	@echo "$(GREEN)✓ Docker cleanup complete$(RESET)"

##@ Release

version: ## Show current version
	@grep -m1 'version' backend/pyproject.toml | cut -d'"' -f2

changelog: ## Generate changelog (requires git-cliff)
	@command -v git-cliff >/dev/null 2>&1 || { echo "$(YELLOW)Install git-cliff: cargo install git-cliff$(RESET)"; exit 1; }
	git-cliff -o CHANGELOG.md
	@echo "$(GREEN)✓ Changelog generated$(RESET)"

##@ Documentation

export-openapi: ## Export OpenAPI spec to docs/api/openapi.json
	@mkdir -p docs/api
	cd backend && source .venv/bin/activate && python -c \
		"import json; from app.main import app; print(json.dumps(app.openapi(), indent=2))" \
		> ../docs/api/openapi.json
	@echo "$(GREEN)✓ OpenAPI spec exported to docs/api/openapi.json$(RESET)"
	@echo "$(BLUE)Import into Postman: File → Import → docs/api/openapi.json$(RESET)"
