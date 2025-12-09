# Makefile for Legacy Code Modernizer

.PHONY: help install test lint format clean docker-build docker-up docker-down deploy

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

install: ## Install dependencies using UV
	uv sync

install-dev: ## Install dev dependencies
	uv sync --dev

test: ## Run tests
	uv run pytest tests/ -v

test-cov: ## Run tests with coverage
	uv run pytest tests/ -v --cov=src --cov-report=html --cov-report=term

test-integration: ## Run integration tests (requires AWS)
	uv run pytest tests/ -v --run-integration

lint: ## Run linting
	uv run ruff check src/ tests/

format: ## Format code
	uv run ruff format src/ tests/

type-check: ## Run type checking
	uv run mypy src/

clean: ## Clean build artifacts
	rm -rf build dist *.egg-info
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	rm -rf htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-build: ## Build Docker image
	docker build -t legacy-code-modernizer:latest .

docker-up: ## Start Docker Compose services
	docker-compose up -d

docker-down: ## Stop Docker Compose services
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

deploy: ## Deploy to AWS Fargate
	./deploy.sh

run-scout: ## Run Code Scout example
	uv run python examples/code_scout_example.py

run-crew: ## Run Refactoring Crew example
	uv run python examples/refactoring_crew_example.py

run-server: ## Run MCP server
	uv run python -m src.mcp_server.server

setup-env: ## Setup environment file
	cp .env.example .env
	@echo "Please edit .env with your AWS credentials"

check: lint type-check test ## Run all checks

all: clean install check ## Clean, install, and check everything
