.PHONY: help test test-fast test-integration test-coverage lint format install install-hooks setup-test-env clean

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install all dependencies
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov pytest-xdist ruff black pre-commit

install-dev: ## Install development dependencies
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

install-hooks: ## Install pre-commit hooks
	pre-commit install
	@echo "✓ Pre-commit hooks installed"

setup-test-env: ## Set up test environment (Docker + databases)
	./scripts/setup-test-env.sh

test: ## Run full test suite with coverage
	./scripts/run-tests.sh

test-fast: ## Run fast unit tests only
	./scripts/run-tests-fast.sh

test-integration: ## Run integration tests
	./scripts/run-tests-integration.sh

test-coverage: ## Run tests and open HTML coverage report
	./scripts/run-tests.sh
	@echo "Opening coverage report..."
	@open htmlcov/index.html 2>/dev/null || xdg-open htmlcov/index.html 2>/dev/null || echo "Coverage report: htmlcov/index.html"

test-watch: ## Run tests in watch mode
	pytest-watch

lint: ## Run linting checks
	ruff check agent ingestion
	black --check agent ingestion

lint-fix: ## Run linting and auto-fix issues
	ruff check --fix agent ingestion
	black agent ingestion

format: ## Format code with black
	black agent ingestion tests

type-check: ## Run type checking with mypy
	mypy agent ingestion --ignore-missing-imports

clean: ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov .coverage coverage.xml
	@echo "✓ Cleaned up generated files"

docker-up: ## Start Docker services (PostgreSQL + Neo4j)
	docker compose up -d

docker-down: ## Stop Docker services
	docker compose down

docker-logs: ## Show Docker logs
	docker compose logs -f

docker-reset: ## Reset Docker services (removes volumes)
	docker compose down -v
	docker compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 10

ci-local: ## Run CI checks locally (mimics GitHub Actions)
	@echo "Running linting..."
	make lint
	@echo "\nRunning tests..."
	make test
	@echo "\n✓ All CI checks passed!"

check: ## Quick check before committing (fast tests + lint)
	make lint
	make test-fast

pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

serve-api: ## Start the API server
	python -m agent.api

serve-dashboard: ## Start the Streamlit dashboard
	streamlit run webui.py --server.port 8012

serve-all: ## Start all services (requires tmux)
	@echo "Starting all services in tmux..."
	tmux new-session -d -s rag-services 'make docker-up; make serve-api'
	tmux split-window -h 'sleep 2; make serve-dashboard'
	tmux attach-session -t rag-services

ingest: ## Run document ingestion
	python -m ingestion.ingest

backup-db: ## Backup PostgreSQL database
	./scripts/backup-database.sh

backup-neo4j: ## Backup Neo4j database
	./scripts/backup-neo4j.sh

migrate: ## Run database migrations
	./scripts/run-migrations.sh

update-deps: ## Update dependencies
	pip list --outdated
	@echo "\nTo update: pip install --upgrade <package>"

security-scan: ## Run security scan
	pip-audit || echo "Install pip-audit: pip install pip-audit"

stats: ## Show project statistics
	@echo "Project Statistics:"
	@echo "==================="
	@echo "Lines of code:"
	@find agent ingestion tests -name "*.py" -exec wc -l {} + | tail -1
	@echo "\nTest files:"
	@find tests -name "test_*.py" | wc -l
	@echo "\nPython files:"
	@find agent ingestion -name "*.py" | wc -l
	@echo "\nDocker containers:"
	@docker ps --format "table {{.Names}}\t{{.Status}}"
