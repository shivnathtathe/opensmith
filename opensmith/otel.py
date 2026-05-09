from __future__ import annotations

import os
from typing import Any

from opensmith.models import Trace


_PROVIDER_INITIALIZED = False
_TRACER: Any | None = None
_METER: Any | None = None
_TOKEN_COUNTER: Any | None = None
_COST_COUNTER: Any | None = None
_LATENCY_HISTOGRAM: Any | None = None


def is_otel_enabled() -> bool:
    return bool(os.getenv("OPENSMITH_OTEL_ENDPOINT"))


def export_trace(trace: Trace) -> None:
    if not is_otel_enabled():
        return

    tracer = _get_tracer()
    if tracer is None:
        return

    with tracer.start_as_current_span(trace.name) as span:
        _set_trace_attributes(span, trace)

        if trace.error:
            span.record_exception(Exception(trace.error))
            span.set_attribute("error", True)
            span.set_attribute("opensmith.error", trace.error)

        _record_trace_metrics(trace)

        for step in trace.steps:
            with tracer.start_as_current_span(step.name) as step_span:
                _set_step_attributes(step_span, step)

                if step.error:
                    step_span.record_exception(Exception(step.error))
                    step_span.set_attribute("error", True)
                    step_span.set_attribute("opensmith.error", step.error)


def _get_tracer() -> Any | None:
    global _TRACER

    if _TRACER is not None:
        return _TRACER

    if not _PROVIDER_INITIALIZED:
        _initialize_provider()

    return _TRACER


def _initialize_provider() -> None:
    global _PROVIDER_INITIALIZED, _TRACER, _METER
    global _TOKEN_COUNTER, _COST_COUNTER, _LATENCY_HISTOGRAM

    _PROVIDER_INITIALIZED = True

    endpoint = os.getenv("OPENSMITH_OTEL_ENDPOINT")
    if not endpoint:
        return

    try:
        from importlib.metadata import version

        svc_version = version("opensmith")
    except Exception:
        svc_version = "unknown"

    try:
        from opentelemetry import metrics, trace
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
            OTLPMetricExporter,
        )
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        return

    base_endpoint = endpoint.rstrip("/")
    resource = Resource.create(
        {
            "service.name": os.getenv("OTEL_SERVICE_NAME", "opensmith"),
            "service.version": svc_version,
            "environment": os.getenv("OPENSMITH_ENVIRONMENT", "local"),
        }
    )

    trace_provider = TracerProvider(resource=resource)
    trace_provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(endpoint=f"{base_endpoint}/v1/traces")
        )
    )
    trace.set_tracer_provider(trace_provider)
    _TRACER = trace.get_tracer("opensmith")

    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=f"{base_endpoint}/v1/metrics")
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)
    _METER = metrics.get_meter("opensmith")

    _TOKEN_COUNTER = _METER.create_counter(
        "opensmith.token_count",
        unit="tokens",
        description="Total tokens captured by opensmith traces.",
    )
    _COST_COUNTER = _METER.create_counter(
        "opensmith.cost_usd",
        unit="USD",
        description="Estimated trace cost in USD.",
    )
    _LATENCY_HISTOGRAM = _METER.create_histogram(
        "opensmith.latency_ms",
        unit="ms",
        description="Trace and step latency in milliseconds.",
    )


def _set_trace_attributes(span: Any, trace: Trace) -> None:
    span.set_attribute("opensmith.trace.id", trace.id)
    span.set_attribute("opensmith.trace.name", trace.name)
    span.set_attribute("opensmith.trace.tags", ",".join(trace.tags))
    span.set_attribute("opensmith.trace.latency_ms", trace.latency_ms or 0.0)
    span.set_attribute("opensmith.tokens_total", _trace_tokens(trace))
    span.set_attribute("opensmith.cost_usd", _trace_cost(trace))


def _set_step_attributes(span: Any, step: Any) -> None:
    span.set_attribute("opensmith.step.id", step.id)
    span.set_attribute("opensmith.step.name", step.name)
    span.set_attribute("opensmith.step.type", step.step_type or "")
    span.set_attribute("opensmith.step.model", step.model or "")
    span.set_attribute("opensmith.step.latency_ms", step.latency_ms or 0.0)
    span.set_attribute("opensmith.tokens_input", step.tokens_input or 0)
    span.set_attribute("opensmith.tokens_output", step.tokens_output or 0)
    span.set_attribute("opensmith.tokens_total", step.tokens_total or 0)
    span.set_attribute("opensmith.cost_usd", step.cost_usd or 0.0)

    attrs = {"type": step.step_type or ""}
    _record_metric(_TOKEN_COUNTER, step.tokens_total or 0, attrs)
    _record_metric(_COST_COUNTER, step.cost_usd or 0.0, attrs)
    _record_histogram(_LATENCY_HISTOGRAM, step.latency_ms or 0.0, attrs)


def _record_trace_metrics(trace: Trace) -> None:
    attrs = {"type": "trace"}
    _record_metric(_TOKEN_COUNTER, _trace_tokens(trace), attrs)
    _record_metric(_COST_COUNTER, _trace_cost(trace), attrs)
    _record_histogram(_LATENCY_HISTOGRAM, trace.latency_ms or 0.0, attrs)


def _trace_tokens(trace: Trace) -> int:
    return sum(step.tokens_total or 0 for step in trace.steps)


def _trace_cost(trace: Trace) -> float:
    return sum(step.cost_usd or 0.0 for step in trace.steps)


def _record_metric(metric: Any | None, value: int | float, attrs: dict[str, str]) -> None:
    if metric is None or not value:
        return
    try:
        metric.add(value, attrs)
    except Exception:
        return


def _record_histogram(
    histogram: Any | None,
    value: int | float,
    attrs: dict[str, str],
) -> None:
    if histogram is None:
        return
    try:
        histogram.record(value, attrs)
    except Exception:
        return
