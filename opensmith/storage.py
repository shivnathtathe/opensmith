from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from opensmith.models import Step, Trace


_default_db_path: Path | None = None


def set_default_db_path(path: str | Path) -> None:
    global _default_db_path
    _default_db_path = Path(path).expanduser()


class Storage:
    def __init__(self, db_path: Path | str | None = None) -> None:
        db_url = os.getenv("OPENSMITH_DB_URL")
        if db_url:
            self._backend = "postgres"
            self._db_url = db_url
            self.db_path = None
            self._init_db()
            return

        self._backend = "sqlite"
        self._db_url = None

        if db_path is None:
            db_path = _default_db_path

        if db_path is None:
            db_path = Path.home() / ".opensmith" / "traces.db"

        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _connect_pg(self) -> Any:
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
        except ImportError as exc:
            raise RuntimeError(
                "Postgres backend requires optional dependency: "
                "pip install opensmith[postgres]"
            ) from exc

        return psycopg2.connect(self._db_url, cursor_factory=RealDictCursor)

    def _init_db(self) -> None:
        if self._backend == "postgres":
            self._init_postgres()
            return
        self._init_sqlite()

    def _init_sqlite(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS traces (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    input TEXT,
                    output TEXT,
                    error TEXT,
                    start_time REAL,
                    end_time REAL,
                    latency_ms REAL,
                    parent_id TEXT,
                    run_id TEXT,
                    metadata TEXT,
                    created_at REAL,
                    tags TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS steps (
                    id TEXT PRIMARY KEY,
                    trace_id TEXT,
                    name TEXT,
                    input TEXT,
                    output TEXT,
                    error TEXT,
                    start_time REAL,
                    end_time REAL,
                    latency_ms REAL,
                    tokens_input INTEGER,
                    tokens_output INTEGER,
                    tokens_total INTEGER,
                    model TEXT,
                    cost_usd REAL,
                    step_type TEXT,
                    metadata TEXT,
                    FOREIGN KEY(trace_id) REFERENCES traces(id)
                )
                """
            )
            self._ensure_column(conn, "traces", "tags", "TEXT")

    def _init_postgres(self) -> None:
        with self._connect_pg() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS traces (
                        id TEXT PRIMARY KEY,
                        name TEXT,
                        input TEXT,
                        output TEXT,
                        error TEXT,
                        start_time DOUBLE PRECISION,
                        end_time DOUBLE PRECISION,
                        latency_ms DOUBLE PRECISION,
                        parent_id TEXT,
                        run_id TEXT,
                        metadata TEXT,
                        created_at DOUBLE PRECISION,
                        tags TEXT
                    )
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS steps (
                        id TEXT PRIMARY KEY,
                        trace_id TEXT,
                        name TEXT,
                        input TEXT,
                        output TEXT,
                        error TEXT,
                        start_time DOUBLE PRECISION,
                        end_time DOUBLE PRECISION,
                        latency_ms DOUBLE PRECISION,
                        tokens_input INTEGER,
                        tokens_output INTEGER,
                        tokens_total INTEGER,
                        model TEXT,
                        cost_usd DOUBLE PRECISION,
                        step_type TEXT,
                        metadata TEXT,
                        FOREIGN KEY(trace_id) REFERENCES traces(id)
                    )
                    """
                )
            conn.commit()

    def _ensure_column(
        self,
        conn: sqlite3.Connection,
        table: str,
        column: str,
        column_type: str,
    ) -> None:
        columns = conn.execute(f"PRAGMA table_info({table})").fetchall()
        if any(row["name"] == column for row in columns):
            return
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")

    def save_trace(self, trace: Trace) -> None:
        if self._backend == "postgres":
            self._save_trace_pg(trace)
        else:
            self._save_trace_sqlite(trace)

        from opensmith.otel import export_trace

        export_trace(trace)

    def _save_trace_sqlite(self, trace: Trace) -> None:
        with self._connect() as conn:
            conn.execute(self._sqlite_trace_upsert_sql(), self._trace_values(trace))

            for step in trace.steps:
                if step.trace_id is None:
                    step.trace_id = trace.id
                conn.execute(self._sqlite_step_upsert_sql(), self._step_values(step))

    def _save_trace_pg(self, trace: Trace) -> None:
        with self._connect_pg() as conn:
            with conn.cursor() as cur:
                cur.execute(self._pg_trace_upsert_sql(), self._trace_values(trace))
                for step in trace.steps:
                    if step.trace_id is None:
                        step.trace_id = trace.id
                    cur.execute(self._pg_step_upsert_sql(), self._step_values(step))
            conn.commit()

    def save_step(self, step: Step) -> None:
        if self._backend == "postgres":
            with self._connect_pg() as conn:
                with conn.cursor() as cur:
                    cur.execute(self._pg_step_upsert_sql(), self._step_values(step))
                conn.commit()
            return

        with self._connect() as conn:
            conn.execute(self._sqlite_step_upsert_sql(), self._step_values(step))

    def get_traces(
        self,
        limit: int = 50,
        tags: list[str] | None = None,
        q: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        if self._backend == "postgres":
            return self._get_traces_pg(limit=limit, tags=tags, q=q, status=status)
        return self._get_traces_sqlite(limit=limit, tags=tags, q=q, status=status)

    def _get_traces_sqlite(
        self,
        limit: int,
        tags: list[str] | None,
        q: str | None,
        status: str | None,
    ) -> list[dict[str, Any]]:
        conditions, params = self._trace_filters(q=q, status=status, placeholder="?")
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with self._connect() as conn:
            rows = conn.execute(self._trace_rollup_sql(where_clause), params).fetchall()

        return self._filter_and_limit_traces(rows, tags=tags, limit=limit)

    def _get_traces_pg(
        self,
        limit: int,
        tags: list[str] | None,
        q: str | None,
        status: str | None,
    ) -> list[dict[str, Any]]:
        conditions, params = self._trace_filters(q=q, status=status, placeholder="%s")
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with self._connect_pg() as conn:
            with conn.cursor() as cur:
                cur.execute(self._trace_rollup_sql(where_clause), params)
                rows = cur.fetchall()

        return self._filter_and_limit_traces(rows, tags=tags, limit=limit)

    def get_trace(self, trace_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        if self._backend == "postgres":
            return self._get_trace_pg(trace_id)
        return self._get_trace_sqlite(trace_id)

    def _get_trace_sqlite(self, trace_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        with self._connect() as conn:
            trace_row = conn.execute(self._single_trace_rollup_sql("?"), (trace_id,)).fetchone()
            step_rows = conn.execute(self._steps_for_trace_sql("?"), (trace_id,)).fetchall()

        trace = self._trace_row_to_dict(trace_row) if trace_row else {}
        steps = [self._step_row_to_dict(row) for row in step_rows]
        return trace, steps

    def _get_trace_pg(self, trace_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        with self._connect_pg() as conn:
            with conn.cursor() as cur:
                cur.execute(self._single_trace_rollup_sql("%s"), (trace_id,))
                trace_row = cur.fetchone()
                cur.execute(self._steps_for_trace_sql("%s"), (trace_id,))
                step_rows = cur.fetchall()

        trace = self._trace_row_to_dict(trace_row) if trace_row else {}
        steps = [self._step_row_to_dict(row) for row in step_rows]
        return trace, steps

    def delete_all(self) -> None:
        if self._backend == "postgres":
            with self._connect_pg() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM steps")
                    cur.execute("DELETE FROM traces")
                conn.commit()
            return

        with self._connect() as conn:
            conn.execute("DELETE FROM steps")
            conn.execute("DELETE FROM traces")

    def get_stats(self) -> dict[str, Any]:
        if self._backend == "postgres":
            with self._connect_pg() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) AS count FROM traces")
                    trace_count = cur.fetchone()["count"]
                    cur.execute(self._step_stats_sql())
                    step_stats = cur.fetchone()
        else:
            with self._connect() as conn:
                trace_count = conn.execute("SELECT COUNT(*) FROM traces").fetchone()[0]
                step_stats = conn.execute(self._step_stats_sql()).fetchone()

        return {
            "total_traces": trace_count,
            "total_steps": step_stats["total_steps"],
            "total_tokens": step_stats["total_tokens"],
            "total_cost_usd": step_stats["total_cost_usd"],
        }

    def _filter_and_limit_traces(
        self,
        rows: list[Any],
        tags: list[str] | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        traces = [self._trace_row_to_dict(row) for row in rows]

        if tags:
            tag_set = set(tags)
            traces = [
                trace
                for trace in traces
                if tag_set.intersection(trace.get("tags") or [])
            ]

        return traces[:limit]

    def _trace_filters(
        self,
        q: str | None,
        status: str | None,
        placeholder: str,
    ) -> tuple[list[str], list[Any]]:
        conditions: list[str] = []
        params: list[Any] = []

        if q:
            search = f"%{q}%"
            operator = "ILIKE" if placeholder == "%s" else "LIKE"
            conditions.append(
                f"""
                (
                    traces.name {operator} {placeholder}
                    OR traces.input {operator} {placeholder}
                    OR traces.output {operator} {placeholder}
                    OR traces.error {operator} {placeholder}
                    OR traces.metadata {operator} {placeholder}
                )
                """
            )
            params.extend([search, search, search, search, search])

        if status == "ok":
            conditions.append("(traces.error IS NULL OR traces.error = '')")
        elif status == "err":
            conditions.append("(traces.error IS NOT NULL AND traces.error != '')")

        return conditions, params

    def _trace_values(self, trace: Trace) -> tuple[Any, ...]:
        return (
            trace.id,
            trace.name,
            self._to_json(trace.input),
            self._to_json(trace.output),
            trace.error,
            trace.start_time,
            trace.end_time,
            trace.latency_ms,
            trace.parent_id,
            trace.run_id,
            self._to_json(trace.metadata),
            trace.start_time,
            self._to_json(trace.tags),
        )

    def _step_values(self, step: Step) -> tuple[Any, ...]:
        return (
            step.id,
            step.trace_id,
            step.name,
            self._to_json(step.input),
            self._to_json(step.output),
            step.error,
            step.start_time,
            step.end_time,
            step.latency_ms,
            step.tokens_input,
            step.tokens_output,
            step.tokens_total,
            step.model,
            step.cost_usd,
            step.step_type,
            self._to_json(step.metadata),
        )

    def _sqlite_trace_upsert_sql(self) -> str:
        return """
            INSERT OR REPLACE INTO traces (
                id, name, input, output, error, start_time, end_time,
                latency_ms, parent_id, run_id, metadata, created_at, tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

    def _pg_trace_upsert_sql(self) -> str:
        return """
            INSERT INTO traces (
                id, name, input, output, error, start_time, end_time,
                latency_ms, parent_id, run_id, metadata, created_at, tags
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                input = EXCLUDED.input,
                output = EXCLUDED.output,
                error = EXCLUDED.error,
                start_time = EXCLUDED.start_time,
                end_time = EXCLUDED.end_time,
                latency_ms = EXCLUDED.latency_ms,
                parent_id = EXCLUDED.parent_id,
                run_id = EXCLUDED.run_id,
                metadata = EXCLUDED.metadata,
                created_at = EXCLUDED.created_at,
                tags = EXCLUDED.tags
        """

    def _sqlite_step_upsert_sql(self) -> str:
        return """
            INSERT OR REPLACE INTO steps (
                id, trace_id, name, input, output, error, start_time, end_time,
                latency_ms, tokens_input, tokens_output, tokens_total, model,
                cost_usd, step_type, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

    def _pg_step_upsert_sql(self) -> str:
        return """
            INSERT INTO steps (
                id, trace_id, name, input, output, error, start_time, end_time,
                latency_ms, tokens_input, tokens_output, tokens_total, model,
                cost_usd, step_type, metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                trace_id = EXCLUDED.trace_id,
                name = EXCLUDED.name,
                input = EXCLUDED.input,
                output = EXCLUDED.output,
                error = EXCLUDED.error,
                start_time = EXCLUDED.start_time,
                end_time = EXCLUDED.end_time,
                latency_ms = EXCLUDED.latency_ms,
                tokens_input = EXCLUDED.tokens_input,
                tokens_output = EXCLUDED.tokens_output,
                tokens_total = EXCLUDED.tokens_total,
                model = EXCLUDED.model,
                cost_usd = EXCLUDED.cost_usd,
                step_type = EXCLUDED.step_type,
                metadata = EXCLUDED.metadata
        """

    def _trace_rollup_sql(self, where_clause: str) -> str:
        return f"""
            SELECT
                traces.*,
                COALESCE(SUM(steps.tokens_total), 0) AS tokens_total,
                COALESCE(SUM(steps.cost_usd), 0) AS cost_usd,
                MAX(steps.model) AS model
            FROM traces
            LEFT JOIN steps ON steps.trace_id = traces.id
            {where_clause}
            GROUP BY traces.id
            ORDER BY COALESCE(traces.created_at, traces.start_time, 0) DESC
        """

    def _single_trace_rollup_sql(self, placeholder: str) -> str:
        return f"""
            SELECT
                traces.*,
                COALESCE(SUM(steps.tokens_total), 0) AS tokens_total,
                COALESCE(SUM(steps.cost_usd), 0) AS cost_usd,
                MAX(steps.model) AS model
            FROM traces
            LEFT JOIN steps ON steps.trace_id = traces.id
            WHERE traces.id = {placeholder}
            GROUP BY traces.id
        """

    def _steps_for_trace_sql(self, placeholder: str) -> str:
        return f"""
            SELECT *
            FROM steps
            WHERE trace_id = {placeholder}
            ORDER BY COALESCE(start_time, 0) ASC
        """

    def _step_stats_sql(self) -> str:
        return """
            SELECT
                COUNT(*) AS total_steps,
                COALESCE(SUM(tokens_total), 0) AS total_tokens,
                COALESCE(SUM(cost_usd), 0) AS total_cost_usd
            FROM steps
        """

    def _row_to_dict(self, row: Any) -> dict[str, Any]:
        return dict(row)

    def _trace_row_to_dict(self, row: Any) -> dict[str, Any]:
        data = self._row_to_dict(row)
        data["input"] = self._from_json(data["input"])
        data["output"] = self._from_json(data["output"])
        data["metadata"] = self._from_json(data["metadata"])
        data["tags"] = self._from_json(data.get("tags")) or []
        data["tokens_total"] = data.get("tokens_total") or 0
        data["cost_usd"] = data.get("cost_usd") or 0.0
        data["model"] = data.get("model")
        return data

    def _step_row_to_dict(self, row: Any) -> dict[str, Any]:
        data = self._row_to_dict(row)
        data["input"] = self._from_json(data["input"])
        data["output"] = self._from_json(data["output"])
        data["metadata"] = self._from_json(data["metadata"])
        return data

    def _to_json(self, value: Any) -> str | None:
        if value is None:
            return None
        try:
            return json.dumps(value, default=str)
        except TypeError:
            return json.dumps(str(value))

    def _from_json(self, value: str | None) -> Any:
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
