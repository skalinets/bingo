.PHONY: install run test test-watch lint lint-fix format check docker docker-watch

install:
	uv sync

run:
	uv run ./src/main.py

test:
	cd src && uv run pytest

test-watch:
	cd src && uv run pytest-watcher .

lint:
	uv run ruff check src/

lint-fix:
	uv run ruff check --fix src/

format:
	uv run black src/

check: lint
	uv run black --check src/

docker:
	docker compose up

docker-watch:
	docker compose watch

# Shell completion: run `eval "$(make completion)"` or add to shell profile
completion:
	@echo 'complete -W "install run test test-watch lint lint-fix format check docker docker-watch" make'
