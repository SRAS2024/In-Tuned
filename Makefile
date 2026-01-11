# Makefile
# Common development tasks for In-Tuned

.PHONY: help install dev test lint format typecheck security clean docker-build docker-up docker-down migrate shell

# Default target
help:
	@echo "In-Tuned Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install      Install production dependencies"
	@echo "  make dev          Install development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test         Run all tests"
	@echo "  make test-cov     Run tests with coverage report"
	@echo "  make test-fast    Run tests in parallel"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint         Run linter (ruff)"
	@echo "  make format       Format code (black + ruff)"
	@echo "  make typecheck    Run type checker (mypy)"
	@echo "  make security     Run security scan (bandit)"
	@echo "  make check        Run all quality checks"
	@echo ""
	@echo "Database:"
	@echo "  make migrate      Run database migrations"
	@echo "  make migrate-new  Create new migration"
	@echo "  make db-reset     Reset database (DESTRUCTIVE)"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build Build Docker image"
	@echo "  make docker-up    Start all containers"
	@echo "  make docker-down  Stop all containers"
	@echo "  make docker-logs  View container logs"
	@echo ""
	@echo "Utilities:"
	@echo "  make shell        Open Python shell with app context"
	@echo "  make clean        Remove cache and build files"
	@echo "  make run          Run development server"

# Setup targets
install:
	pip install -r requirements.txt

dev:
	pip install -r requirements.txt
	pip install pytest pytest-cov pytest-xdist black ruff mypy bandit safety

# Testing targets
test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html

test-fast:
	pytest tests/ -v -n auto

# Code quality targets
lint:
	ruff check app/ tests/

format:
	black app/ tests/
	ruff check --fix app/ tests/

typecheck:
	mypy app/ --ignore-missing-imports

security:
	bandit -r app/ -ll
	pip-audit || true

check: lint typecheck security
	@echo "All checks passed!"

# Database targets
migrate:
	alembic upgrade head

migrate-new:
	@read -p "Migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

db-reset:
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " confirm; \
	if [ "$$confirm" = "y" ]; then \
		alembic downgrade base && alembic upgrade head; \
	fi

# Docker targets
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-test:
	docker-compose --profile test run --rm test

docker-migrate:
	docker-compose --profile migrate run --rm migrate

# Utility targets
shell:
	FLASK_APP=wsgi.py flask shell

run:
	FLASK_ENV=development FLASK_DEBUG=1 python -m flask --app wsgi:application run --reload --port 5000

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type f -name "coverage.xml" -delete 2>/dev/null || true
	@echo "Cleaned up cache and build files"
