from __future__ import annotations

import json
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

    def _init_db(self) -> None:
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
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO traces (
                    id,
                    name,
                    input,
                    output,
                    error,
                    start_time,
                    end_time,
                    latency_ms,
                    parent_id,
                    run_id,
                    metadata,
                    created_at,
                    tags
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
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
                ),
            )

            for step in trace.steps:
                if step.trace_id is None:
                    step.trace_id = trace.id
                conn.execute(
                    """
                    INSERT OR REPLACE INTO steps (
                        id,
                        trace_id,
                        name,
                        input,
                        output,
                        error,
                        start_time,
                        end_time,
                        latency_ms,
                        tokens_input,
                        tokens_output,
                        tokens_total,
                        model,
                        cost_usd,
                        step_type,
                        metadata
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
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
                    ),
                )

    def save_step(self, step: Step) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO steps (
                    id,
                    trace_id,
                    name,
                    input,
                    output,
                    error,
                    start_time,
                    end_time,
                    latency_ms,
                    tokens_input,
                    tokens_output,
                    tokens_total,
                    model,
                    cost_usd,
                    step_type,
                    metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
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
                ),
            )

    def get_traces(
        self,
        limit: int = 50,
        tags: list[str] | None = None,
        q: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        conditions: list[str] = []
        params: list[Any] = []

        if q:
            search = f"%{q}%"
            conditions.append(
                """
                (
                    traces.name LIKE ?
                    OR traces.input LIKE ?
                    OR traces.output LIKE ?
                    OR traces.error LIKE ?
                    OR traces.metadata LIKE ?
                )
                """
            )
            params.extend([search, search, search, search, search])

        if status == "ok":
            conditions.append("(traces.error IS NULL OR traces.error = '')")
        elif status == "err":
            conditions.append("(traces.error IS NOT NULL AND traces.error != '')")

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with self._connect() as conn:
            rows = conn.execute(
                f"""
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
                """,
                params,
            ).fetchall()

        traces = [self._trace_row_to_dict(row) for row in rows]

        if tags:
            tag_set = set(tags)
            traces = [
                trace
                for trace in traces
                if tag_set.intersection(trace.get("tags") or [])
            ]

        return traces[:limit]

    def get_trace(self, trace_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        with self._connect() as conn:
            trace_row = conn.execute(
                """
                SELECT
                    traces.*,
                    COALESCE(SUM(steps.tokens_total), 0) AS tokens_total,
                    COALESCE(SUM(steps.cost_usd), 0) AS cost_usd,
                    MAX(steps.model) AS model
                FROM traces
                LEFT JOIN steps ON steps.trace_id = traces.id
                WHERE traces.id = ?
                GROUP BY traces.id
                """,
                (trace_id,),
            ).fetchone()
            step_rows = conn.execute(
                """
                SELECT *
                FROM steps
                WHERE trace_id = ?
                ORDER BY COALESCE(start_time, 0) ASC
                """,
                (trace_id,),
            ).fetchall()

        trace = self._trace_row_to_dict(trace_row) if trace_row else {}
        steps = [self._step_row_to_dict(row) for row in step_rows]
        return trace, steps

    def delete_all(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM steps")
            conn.execute("DELETE FROM traces")

    def get_stats(self) -> dict[str, Any]:
        with self._connect() as conn:
            trace_count = conn.execute("SELECT COUNT(*) FROM traces").fetchone()[0]
            step_stats = conn.execute(
                """
                SELECT
                    COUNT(*) AS total_steps,
                    COALESCE(SUM(tokens_total), 0) AS total_tokens,
                    COALESCE(SUM(cost_usd), 0) AS total_cost_usd
                FROM steps
                """
            ).fetchone()

        return {
            "total_traces": trace_count,
            "total_steps": step_stats["total_steps"],
            "total_tokens": step_stats["total_tokens"],
            "total_cost_usd": step_stats["total_cost_usd"],
        }

    def _trace_row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["input"] = self._from_json(data["input"])
        data["output"] = self._from_json(data["output"])
        data["metadata"] = self._from_json(data["metadata"])
        data["tags"] = self._from_json(data.get("tags")) or []
        data["tokens_total"] = data.get("tokens_total") or 0
        data["cost_usd"] = data.get("cost_usd") or 0.0
        data["model"] = data.get("model")
        return data

    def _step_row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
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
