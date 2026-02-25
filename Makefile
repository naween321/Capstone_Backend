# Makefile for LifeLog Django Project

# Variables
DEV_COMPOSE = docker compose --env-file .env -f docker/lifelog_dev/docker-compose.yml
PROD_COMPOSE = docker compose --env-file .env -f docker/lifelog_prod/docker-compose.yml

# Default target (runs when you type just 'make')
.DEFAULT_GOAL := help

# Phony targets (not actual files)
.PHONY: help dev-build dev-up dev-down dev-restart dev-logs dev-shell dev-migrate prod-build prod-up prod-down

# ===========================
# DEVELOPMENT COMMANDS
# ===========================

dev-build:
	@echo "Building development images..."
	$(DEV_COMPOSE) build

dev-up:
	@echo "Starting development environment..."
	$(DEV_COMPOSE) up

dev-up-d:
	@echo "Starting development in background..."
	$(DEV_COMPOSE) up -d

dev-down:
	@echo "Stopping development environment..."
	$(DEV_COMPOSE) down

dev-down-v:
	@echo "Stopping and removing volumes..."
	$(DEV_COMPOSE) down -v

dev-restart:
	@echo "Restarting development containers..."
	$(DEV_COMPOSE) restart

dev-rebuild:
	@echo "Rebuilding and restarting development..."
	$(DEV_COMPOSE) up --build

dev-fresh:
	@echo "Fresh start (removing all volumes)..."
	$(DEV_COMPOSE) down -v
	$(DEV_COMPOSE) up --build

dev-logs:
	@echo "Showing development logs..."
	$(DEV_COMPOSE) logs -f

dev-logs-web:
	@echo "Showing web container logs..."
	$(DEV_COMPOSE) logs -f web

dev-logs-db:
	@echo "Showing database logs..."
	$(DEV_COMPOSE) logs -f db

dev-shell:
	@echo "Opening Django shell..."
	$(DEV_COMPOSE) exec web uv run python manage.py shell

dev-bash:
	@echo "Opening bash shell..."
	$(DEV_COMPOSE) exec web bash

dev-db-shell:
	@echo "Opening PostgreSQL shell..."
	$(DEV_COMPOSE) exec db psql -U ts_library -d ts_library_db

dev-migrate:
	@echo "Running migrations..."
	$(DEV_COMPOSE) exec web uv run python manage.py migrate

dev-makemigrations:
	@echo "Creating migrations..."
	$(DEV_COMPOSE) exec web uv run python manage.py makemigrations

dev-superuser:
	@echo "Creating superuser..."
	$(DEV_COMPOSE) exec web uv run python manage.py createsuperuser

dev-test:
	@echo "Running tests..."
	$(DEV_COMPOSE) exec web uv run pytest

dev-collectstatic:
	@echo "Collecting static files..."
	$(DEV_COMPOSE) exec web uv run python manage.py collectstatic --noinput

dev-ps:
	@echo "Showing running containers..."
	$(DEV_COMPOSE) ps


# Help command - shows all available commands
help:
	@echo "=================================="
	@echo "TS User Project - Make Commands"
	@echo "=================================="
	@echo ""
	@echo "Development Commands:"
	@echo "  make dev-build          - Build development Docker images"
	@echo "  make dev-up             - Start development environment"
	@echo "  make dev-down           - Stop development environment"
	@echo "  make dev-restart        - Restart development containers"
	@echo "  make dev-rebuild        - Rebuild and restart development"
	@echo "  make dev-fresh          - Fresh start (removes all data)"
	@echo "  make dev-logs           - View development logs"
	@echo "  make dev-shell          - Open Django shell"
	@echo "  make dev-bash           - Open bash in web container"
	@echo "  make dev-migrate        - Run migrations"
	@echo "  make dev-makemigrations - Create new migrations"
	@echo "  make dev-superuser      - Create Django superuser"
	@echo "  make dev-test           - Run tests"
	@echo ""