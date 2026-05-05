from __future__ import annotations

from rich.console import Console
from rich.text import Text

from opensmith.models import Trace


_console_mode = False
_console = Console()


def set_console_mode(enabled: bool) -> None:
    global _console_mode
    _console_mode = enabled


def is_console_mode() -> bool:
    return _console_mode


def print_trace(trace: Trace) -> None:
    latency = _format_latency(trace.latency_ms)
    tokens = _trace_tokens(trace)
    cost = _trace_cost(trace)

    if trace.error:
        text = Text()
        text.append("✗", style="red")
        text.append(f" {trace.name}  {latency}")
        text.append(f"  ERROR: {trace.error}", style="red")
        _console.print(text)
        return

    text = Text()
    text.append("✓", style="green")
    text.append(f" {trace.name}  {latency}")

    summary = _format_summary(tokens, cost)
    if summary:
        text.append(f"  [{summary}]")

    _console.print(text)


def _format_latency(value: float | None) -> str:
    if value is None:
        return "0ms"
    return f"{value:.0f}ms"


def _trace_tokens(trace: Trace) -> int | None:
    total = 0
    for step in trace.steps:
        total += step.tokens_total or 0
    return total or None


def _trace_cost(trace: Trace) -> float | None:
    total = 0.0
    for step in trace.steps:
        total += step.cost_usd or 0.0
    return total or None


def _format_summary(tokens: int | None, cost: float | None) -> str:
    parts: list[str] = []
    if tokens is not None:
        parts.append(f"{tokens} tokens")
    if cost is not None:
        parts.append(f"${cost:.6f}")
    return "  ".join(parts)
