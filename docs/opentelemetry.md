# OpenTelemetry

OpenTelemetry export is opt-in. By default, opensmith does not export traces or metrics outside your machine.

Install the optional dependencies:

```bash
pip install "opensmith[otel]"
```

Set the OTLP HTTP base endpoint:

```bash
export OPENSMITH_OTEL_ENDPOINT="http://localhost:4318"
```

opensmith exports traces to `/v1/traces` and metrics to `/v1/metrics` below that endpoint.

If `OPENSMITH_OTEL_ENDPOINT` is unset, OpenTelemetry export is disabled.
