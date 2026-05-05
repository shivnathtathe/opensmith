from __future__ import annotations

from opensmith.console import is_console_mode, print_trace, set_console_mode
from opensmith.models import Step, Trace
from opensmith.storage import Storage
from opensmith.tracer import trace


def test_console_mode_off_by_default() -> None:
    set_console_mode(False)

    assert is_console_mode() is False


def test_set_console_mode_true() -> None:
    set_console_mode(True)

    assert is_console_mode() is True

    set_console_mode(False)


def test_set_console_mode_false() -> None:
    set_console_mode(True)
    set_console_mode(False)

    assert is_console_mode() is False


def test_print_trace_success(monkeypatch) -> None:
    calls: list[object] = []

    class FakeConsole:
        def print(self, value: object) -> None:
            calls.append(value)

    monkeypatch.setattr("opensmith.console._console", FakeConsole())

    trace = Trace(
        name="my_func",
        latency_ms=245.0,
        steps=[
            Step(
                name="llm",
                tokens_total=42,
                cost_usd=0.000105,
            )
        ],
    )

    print_trace(trace)

    assert len(calls) == 1
    output = calls[0].plain
    assert "✓" in output
    assert "my_func" in output
    assert "245ms" in output
    assert "42 tokens" in output
    assert "$0.000105" in output


def test_print_trace_error(monkeypatch) -> None:
    calls: list[object] = []

    class FakeConsole:
        def print(self, value: object) -> None:
            calls.append(value)

    monkeypatch.setattr("opensmith.console._console", FakeConsole())

    trace = Trace(
        name="my_func",
        latency_ms=120.0,
        error="ValueError: boom",
    )

    print_trace(trace)

    assert len(calls) == 1
    output = calls[0].plain
    assert "✗" in output
    assert "my_func" in output
    assert "120ms" in output
    assert "ERROR: ValueError: boom" in output


def test_console_prints_after_trace(monkeypatch, tmp_storage: Storage) -> None:
    calls: list[object] = []

    class FakeConsole:
        def print(self, value: object) -> None:
            calls.append(value)

    monkeypatch.setattr("opensmith.tracer.Storage", lambda: tmp_storage)
    monkeypatch.setattr("opensmith.console._console", FakeConsole())
    set_console_mode(True)

    @trace
    def sample() -> str:
        return "ok"

    try:
        sample()
    finally:
        set_console_mode(False)

    assert len(calls) == 1
    output = calls[0].plain
    assert "✓" in output
    assert "sample" in output
