.PHONY: dev lint format clean start

dev:
	docker compose up --build --watch

dev-postgres:
	docker compose -f compose.postgres.yml up --build
	@echo "Bot is running with Postgres. Use 'docker compose -f docker-compose.postgres.yml logs -f' to view logs."

start:
	./bin/start.sh

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff check --fix .
	uv run ruff format .

format-docker:
	docker compose -f compose.format.yml run --rm linter ruff format .

clean:
	rm -rf .venv
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.sqlite3" -exec rm -rf {} +
	find . -type f -name "*.pyc" -exec rm -rf {} +
	rm -rf .idea

wipe-docker:
	docker compose down -v
	docker compose -f compose.yml down -v
	docker compose -f compose.postgres.yml down -v

migrate-gen:
	@if [ -z "$(MSG)" ]; then echo "Error: MSG is not set. Usage: make migrate-gen MSG=\"message\""; exit 1; fi
	@echo "Ensuring database is up to date for migration generation..."
	@uv run alembic -c pyproject.toml upgrade head 2>/dev/null || echo "Note: Database may not exist yet, continuing..."
	uv run alembic -c pyproject.toml revision --autogenerate -m "$(MSG)"

migrate-gen-docker:
	@if [ -z "$(MSG)" ]; then echo "Error: MSG is not set. Usage: make migrate-gen-docker MSG=\"message\""; exit 1; fi
	@echo "Ensuring database is up to date for migration generation..."
	@docker compose run --rm bot alembic -c pyproject.toml upgrade head 2>/dev/null || echo "Note: Database may not exist yet, continuing..."
	docker compose run --rm bot alembic -c pyproject.toml revision --autogenerate -m "$(MSG)"

migrate-up:
	uv run alembic -c pyproject.toml upgrade head

migrate-up-docker:
	docker compose run --rm bot alembic -c pyproject.toml upgrade head

migrate-down:
	uv run alembic -c pyproject.toml downgrade -1

migrate-down-docker:
	docker compose run --rm bot alembic -c pyproject.toml downgrade -1

shell-docker:
	docker compose run --rm bot /bin/bash
