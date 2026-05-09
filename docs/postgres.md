# Postgres

SQLite remains the default storage backend. Use Postgres only when you explicitly opt in with `OPENSMITH_DB_URL`.

Install the optional dependency:

```bash
pip install "opensmith[postgres]"
```

Set the database URL:

```bash
export OPENSMITH_DB_URL="postgresql://user:pass@localhost:5432/opensmith"
```

When `OPENSMITH_DB_URL` is set, `Storage()` writes traces and steps to Postgres using the same API. If the variable is not set, opensmith uses local SQLite at `~/.opensmith/traces.db`.
