from __future__ import annotations

import pytest

from opensmith.storage import Storage
from opensmith.tracer import TraceCallable, trace


def test_trace_captures_function_name(monkeypatch, tmp_storage: Storage) -> None:
    monkeypatch.setattr("opensmith.tracer.Storage", lambda: tmp_storage)

    @trace
    def sample() -> str:
        return "ok"

    sample()

    traces = tmp_storage.get_traces()
    assert traces[0]["name"] == "sample"


def test_trace_captures_input_args(monkeypatch, tmp_storage: Storage) -> None:
    monkeypatch.setattr("opensmith.tracer.Storage", lambda: tmp_storage)

    @trace
    def sample(value: int, *, label: str) -> str:
        return label

    sample(123, label="abc")

    traces = tmp_storage.get_traces()
    assert traces[0]["input"] == {
        "args": ["123"],
        "kwargs": {"label": "abc"},
    }


def test_trace_captures_output(monkeypatch, tmp_storage: Storage) -> None:
    monkeypatch.setattr("opensmith.tracer.Storage", lambda: tmp_storage)

    @trace
    def sample() -> str:
        return "ok"

    sample()

    traces = tmp_storage.get_traces()
    assert traces[0]["output"] == {"result": "ok"}


def test_trace_captures_latency_ms(monkeypatch, tmp_storage: Storage) -> None:
    monkeypatch.setattr("opensmith.tracer.Storage", lambda: tmp_storage)

    @trace
    def sample() -> str:
        return "ok"

    sample()

    traces = tmp_storage.get_traces()
    assert traces[0]["latency_ms"] >= 0


def test_trace_saves_to_storage(monkeypatch, tmp_storage: Storage) -> None:
    monkeypatch.setattr("opensmith.tracer.Storage", lambda: tmp_storage)

    @trace
    def sample() -> str:
        return "ok"

    sample()

    assert len(tmp_storage.get_traces()) == 1


def test_trace_re_raises_exceptions(monkeypatch, tmp_storage: Storage) -> None:
    monkeypatch.setattr("opensmith.tracer.Storage", lambda: tmp_storage)

    @trace
    def sample() -> None:
        raise ValueError("boom")

    with pytest.raises(ValueError):
        sample()

    traces = tmp_storage.get_traces()
    assert "ValueError" in traces[0]["error"]


def test_trace_custom_name_uses_custom_name(monkeypatch, tmp_storage: Storage) -> None:
    monkeypatch.setattr("opensmith.tracer.Storage", lambda: tmp_storage)

    @trace(name="custom")
    def sample() -> str:
        return "ok"

    sample()

    traces = tmp_storage.get_traces()
    assert traces[0]["name"] == "custom"


def test_context_manager_captures_input_via_log(tmp_storage: Storage) -> None:
    local_trace = TraceCallable(storage=tmp_storage)

    with local_trace("context") as t:
        t.log("query", "hello")

    traces = tmp_storage.get_traces()
    assert traces[0]["name"] == "context"
    assert traces[0]["input"] == {"query": "hello"}


def test_nested_trace_sets_parent_id_correctly(monkeypatch, tmp_storage: Storage) -> None:
    monkeypatch.setattr("opensmith.tracer.Storage", lambda: tmp_storage)

    @trace
    def inner() -> str:
        return "inner"

    @trace
    def outer() -> str:
        return inner()

    outer()

    traces = tmp_storage.get_traces()
    outer_trace = next(item for item in traces if item["name"] == "outer")
    inner_trace = next(item for item in traces if item["name"] == "inner")

    assert inner_trace["parent_id"] == outer_trace["id"]
