# ==============================================================================
# Makefile: Automation for Local Development, Testing, and Container Lifecycle
# ==============================================================================

.PHONY: help up down build restart logs status test test-backend clean

help:
	@echo "Available commands:"
	@echo "  make up           - Build and start full stack (backend: 8000, frontend: 3000)"
	@echo "  make down         - Stop and remove all containers and networks"
	@echo "  make build        - Rebuild all container images"
	@echo "  make restart      - Restart the running stack"
	@echo "  make logs         - View live logs from all containers"
	@echo "  make status       - View status and health of all containers"
	@echo "  make test         - Run all backend automated tests"
	@echo "  make clean        - Stop containers and remove temporary build artifacts"

up:
	docker compose up --build -d

down:
	docker compose down

build:
	docker compose build

restart:
	docker compose restart

logs:
	docker compose logs -f

status:
	docker compose ps

test: test-backend

test-backend:
	cd backend && python -m pytest tests -v

clean:
	docker compose down --remove-orphans
