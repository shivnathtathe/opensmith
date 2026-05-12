from __future__ import annotations

import csv
import io
import json
import sys
import time
from pathlib import Path
from typing import Any

import click
import uvicorn
from rich.console import Console
from rich.table import Table

from opensmith.storage import Storage


console = Console(
    file=io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace"),
    legacy_windows=False,
)


def _get_version() -> str:
    try:
        from importlib.metadata import version

        return version("opensmith")
    except Exception:
        return "0.1.3"


def _print_banner() -> None:
    console.print("""     [bold #888888]╔═╗╔═╗╔═╗╔╗╔[/bold #888888][bold #ededec]╔═╗╔╦╗╦╔╦╗╦ ╦[/bold #ededec]
     [bold #888888]║ ║╠═╝║╣ ║║║[/bold #888888][bold #ededec]╚═╗║║║║ ║ ╠═╣[/bold #ededec]
     [bold #888888]╚═╝╩  ╚═╝╝╚╝[/bold #888888][bold #ededec]╚═╝╩ ╩╩ ╩ ╩ ╩[/bold #ededec]""")
    console.print(
        "[#888888]Local-first LLM pipeline tracer  "
        "[#d29922]v" + _get_version() + "[/#d29922]\n"
    )


@click.group(name="opensmith", invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Local-first LLM pipeline tracer."""
    if ctx.invoked_subcommand is None:
        _print_banner()
        click.echo(ctx.get_help())


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


@cli.command(name="export")
@click.option(
    "--format",
    "export_format",
    default="json",
    show_default=True,
    type=click.Choice(["json", "csv"]),
)
@click.option("--output", default=None)
@click.option("--limit", default=None, type=int)
def export_traces(
    export_format: str,
    output: str | None,
    limit: int | None,
) -> None:
    """Export traces to JSON or CSV."""
    storage = Storage()
    trace_limit = limit if limit is not None else 1_000_000
    traces = storage.get_traces(limit=trace_limit)
    output_path = Path(output or f"opensmith-export.{export_format}")

    if export_format == "json":
        payload = []
        for trace in traces:
            _, steps = storage.get_trace(trace["id"])
            trace_with_steps = dict(trace)
            trace_with_steps["steps"] = steps
            payload.append(trace_with_steps)

        output_path.write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
    else:
        with output_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "id",
                    "name",
                    "latency_ms",
                    "tokens_total",
                    "cost_usd",
                    "error",
                    "tags",
                    "created_at",
                    "model",
                ],
            )
            writer.writeheader()

            for trace in traces:
                writer.writerow(
                    {
                        "id": trace.get("id", ""),
                        "name": trace.get("name", ""),
                        "latency_ms": trace.get("latency_ms", ""),
                        "tokens_total": trace.get("tokens_total", ""),
                        "cost_usd": trace.get("cost_usd", ""),
                        "error": trace.get("error", ""),
                        "tags": ",".join(trace.get("tags") or []),
                        "created_at": trace.get("created_at", ""),
                        "model": trace.get("model", ""),
                    }
                )

    click.echo(f"Exported {len(traces)} traces to {output_path}")


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
