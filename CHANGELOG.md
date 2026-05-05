# Changelog

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
