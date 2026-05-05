from __future__ import annotations

import time
from typing import Any

import click
import uvicorn
from rich.console import Console
from rich.table import Table

from opensmith.storage import Storage


console = Console()


@click.group(name="opensmith")
def cli() -> None:
    """Local-first LLM pipeline tracer."""


@cli.command()
@click.option("--port", default=7823, show_default=True, type=int)
@click.option("--host", default="127.0.0.1", show_default=True)
def ui(port: int, host: str) -> None:
    """Start the local dashboard."""
    click.echo(f"opensmith UI running at http://{host}:{port}")
    click.echo("Press Ctrl+C to stop")
    uvicorn.run("opensmith.server:app", host=host, port=port)


@cli.command()
def clear() -> None:
    """Clear all traces."""
    if not click.confirm("Clear all traces?", default=False):
        return

    Storage().delete_all()
    click.echo("Cleared all traces.")


@cli.command()
def stats() -> None:
    """Show trace statistics."""
    data = Storage().get_stats()

    table = Table(title="opensmith stats")
    table.add_column("Metric")
    table.add_column("Value", justify="right")

    table.add_row("Total traces", str(data["total_traces"]))
    table.add_row("Total steps", str(data["total_steps"]))
    table.add_row("Total tokens", str(data["total_tokens"]))
    table.add_row("Total cost (USD)", f"${float(data['total_cost_usd']):.6f}")

    console.print(table)


@cli.command()
@click.option("--limit", default=20, show_default=True, type=int)
def traces(limit: int) -> None:
    """List recent traces."""
    rows = Storage().get_traces(limit=limit)

    table = Table(title="opensmith traces")
    table.add_column("id")
    table.add_column("name")
    table.add_column("latency_ms", justify="right")
    table.add_column("error")
    table.add_column("created_at")

    for row in rows:
        table.add_row(
            str(row.get("id", ""))[:8],
            str(row.get("name") or ""),
            _format_latency(row.get("latency_ms")),
            "yes" if row.get("error") else "no",
            _format_timestamp(row.get("created_at")),
        )

    console.print(table)


def _format_latency(value: Any) -> str:
    if value is None:
        return ""
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return ""


def _format_timestamp(value: Any) -> str:
    if value is None:
        return ""
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(value)))
    except (TypeError, ValueError, OSError):
        return ""
