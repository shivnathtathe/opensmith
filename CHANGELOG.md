# Changelog

## 0.1.5 - 2026-05-09

- Added `opensmith init` command for creating a starter `opensmith.json` config.
- Added `opensmith traces --q --status --tags` filters.
- Added `@trace(token_budget=N)` alerts with warning metadata.
- Added auto port detection for `opensmith ui`.

## 0.1.4 - 2026-05-09

- Added ASCII banner to the CLI when running `opensmith` without a subcommand.
- Added `pip install "opensmith[all]"` optional dependency group for OpenTelemetry and Postgres support together.

## 0.1.3 - 2026-05-09

- Added optional OpenTelemetry export via `OPENSMITH_OTEL_ENDPOINT` and `opensmith[otel]`.
- Added optional Postgres storage via `OPENSMITH_DB_URL` and `opensmith[postgres]`.
- Added `opensmith export` for JSON trace exports with nested steps and CSV trace exports.
- Kept SQLite as the default storage backend with no cloud or service required.

## 0.1.2 - 2026-05-05

- Added WebSocket live updates via SQLite polling.
- Added token and cost rollups from steps to the trace list.
- Added search and status filters on `/api/traces`.
- Rebuilt the dashboard with charts, model column, search bar, filter pills, and LIVE indicator.

## 0.1.1 - 2026-05-05

- Added async function support for `@trace`.
- Added trace tags for decorators, context managers, SQLite storage, and `Storage.get_traces(tags=[...])` filtering.
- Added console output mode with `set_console_mode(True)`.
- Added `opensmith.json` project config for `db_path`, `console_mode`, and automatic `autopatch` backends.
- Added configurable default SQLite path via `set_default_db_path()`.

## 0.1.0 - 2026-05-05

Initial public release of opensmith.

- Added local SQLite trace storage at `~/.opensmith/traces.db`.
- Added `@trace` decorator and context manager.
- Added autopatch support for OpenAI, Anthropic, LiteLLM, Qdrant, ChromaDB, and Pinecone.
- Added local FastAPI dashboard at `localhost:7823`.
- Added CLI commands for UI, traces, stats, and clearing data.
- Published the first PyPI release.
