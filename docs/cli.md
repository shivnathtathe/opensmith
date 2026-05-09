# CLI Reference

## `opensmith ui`

Start the local dashboard.

```bash
opensmith ui --host 127.0.0.1 --port 7823
```

## `opensmith traces`

List recent traces.

```bash
opensmith traces --limit 20
```

## `opensmith stats`

Print aggregate trace statistics.

```bash
opensmith stats
```

## `opensmith export`

Export traces to JSON or CSV.

```bash
opensmith export --format json --output traces.json
opensmith export --format csv --output traces.csv
```

JSON exports include each trace with its nested `steps`. CSV exports include a flat trace list with `id`, `name`, `latency_ms`, `tokens_total`, `cost_usd`, `error`, `tags`, `created_at`, and `model` columns.

Limit the number of exported traces:

```bash
opensmith export --limit 100
```

## `opensmith clear`

Delete all stored traces after confirmation.

```bash
opensmith clear
```

## Console Mode

Console mode is configured from Python code or `opensmith.json`, not a CLI command.

```python
from opensmith import set_console_mode


set_console_mode(True)
```
