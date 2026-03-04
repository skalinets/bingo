# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bingo card generator web app built with Python (FastHTML framework), Redis for storage. No JS/HTML — everything is Python-only using FastHTML's HTMX integration. Created as part of a Ukrainian-language Twitch stream series "Стартап за дві години".

## Tech Stack

- **Python ≥3.12**, **FastHTML** (python-fasthtml), **Redis** (async)
- **Package manager:** uv
- **Styling:** PicoCSS + Flexbox Grid

## Development

Use Docker Compose for development — it runs the app and Redis together:

```bash
docker compose watch    # recommended: app + Redis with live file sync
docker compose up       # or without watch mode
```

The app is available at `http://localhost:5001`. Redis is exposed on `localhost:6379`.

## Commands

A `Makefile` wraps all common tasks:

| Command | Description |
|---|---|
| `make install` | Install dependencies (`uv sync`) |
| `make run` | Run the app locally (requires Redis separately) |
| `make test` | Run all tests |
| `make test-watch` | Re-run tests on file changes |
| `make lint` | Lint with ruff |
| `make lint-fix` | Lint and auto-fix |
| `make format` | Format with black |
| `make check` | Lint + format check (CI-friendly) |
| `make docker` | `docker compose up` |
| `make docker-watch` | `docker compose watch` |

Run a single test:
```bash
cd src && uv run pytest -k "test_name"
```

**Important:** Tests must be run from the `src/` directory. They require Redis on `localhost:6379` (provided by `docker compose up`). Tests use Redis database 1 (not 0) for isolation and flush it before/after each test.

## Architecture

Single-file monolith: all application logic lives in `src/main.py` (~290 lines). Tests in `src/test_tests.py`.

### Data Model (Redis)

- **Templates:** hash `template:{id}` (cols, rows) + list `template_items:{id}` (text items)
- **Bingo instances:** hash `bingo:{id}` (template_id, cols, rows) + set `selected_items:{id}` (toggled cells)
- IDs auto-increment via `INCR` on `template_id` / `bingo_id` keys

### Routes

- `GET /` — home page with template creation form
- `POST /change_rows` — HTMX: dynamically update grid size
- `POST /create_template` — create template in Redis
- `GET /template/{id}` — view template
- `POST /create_bingo` — create bingo instance from template
- `GET /edit_bingo` — interactive bingo card (toggle cells via HTMX)
- `POST /trigger` — HTMX: toggle a bingo cell
- `POST /publish_bingo` — redirect to show view
- `GET /show_bingo/{id}` — public view of a bingo card

### Key Patterns

- All DB-touching handlers are **async**
- Grid rendering uses **factory functions** (`create_bingo_inpput`, `create_bingo_text`, `create_bingo_text2`) that produce different cell types for different contexts (editing template vs playing bingo)
- HTMX attributes (`hx_post`, `hx_target`, `hx_trigger`) drive all dynamic interactions without page reloads
- `ft.serve()` starts the ASGI server; Redis connection is set up after it (lines 204-206) since requests are processed lazily

## Linting & Formatting

- **Ruff:** lints for errors, warnings, and import sorting (`E`, `F`, `I`, `W` rules)
- **Black:** code formatter (line length 88)
- Use `make check` to verify both pass without modifying files

## E2E Testing

Use `playwright-cli` for end-to-end testing and UI investigation. The app must be running (`docker compose up` or `make run`) before using these commands.

```bash
playwright-cli open http://localhost:5001    # open the app in a browser
playwright-cli snapshot                       # capture current page state
playwright-cli click e3                       # interact using ref ids from snapshot
playwright-cli fill e5 "my bingo item"        # fill form fields
playwright-cli screenshot                     # take a screenshot for verification
playwright-cli close                          # close the browser
```

Typical e2e workflow: `open` → `snapshot` → interact (`click`/`fill`/`select`) → `snapshot` to verify → `close`.
