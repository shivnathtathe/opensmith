from __future__ import annotations

import builtins

from opensmith.models import Step, Trace
from opensmith.otel import export_trace, is_otel_enabled


def test_otel_disabled_without_env(monkeypatch) -> None:
    monkeypatch.delenv("OPENSMITH_OTEL_ENDPOINT", raising=False)

    assert is_otel_enabled() is False


def test_otel_enabled_with_env(monkeypatch) -> None:
    monkeypatch.setenv("OPENSMITH_OTEL_ENDPOINT", "http://localhost:4318")

    assert is_otel_enabled() is True


def test_export_trace_noops_without_env(monkeypatch) -> None:
    monkeypatch.delenv("OPENSMITH_OTEL_ENDPOINT", raising=False)

    export_trace(Trace(name="pipeline"))


def test_export_trace_noops_if_otel_missing(monkeypatch) -> None:
    monkeypatch.setenv("OPENSMITH_OTEL_ENDPOINT", "http://localhost:4318")
    monkeypatch.setattr("opensmith.otel._PROVIDER_INITIALIZED", False)
    monkeypatch.setattr("opensmith.otel._TRACER", None)

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("opentelemetry"):
            raise ImportError
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    export_trace(
        Trace(
            name="pipeline",
            steps=[
                Step(
                    name="openai.chat.completions.create",
                    step_type="llm",
                    tokens_total=42,
                    cost_usd=0.0001,
                )
            ],
        )
    )
