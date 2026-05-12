# CLI Reference

## `opensmith init`

Create a starter `opensmith.json` config in the current directory.

```bash
opensmith init
```

If `opensmith.json` already exists, opensmith asks before overwriting it.

## `opensmith ui`

Start the local dashboard. If the requested port is in use, opensmith automatically tries the next available port.

```bash
opensmith ui --host 127.0.0.1 --port 7823
```

Disable automatic port selection:

```bash
opensmith ui --no-auto-port
```

## `opensmith traces`

List recent traces.

```bash
opensmith traces --limit 20
```

Filter traces by search text, status, and tags:

```bash
opensmith traces --q rag --status err --tags production --limit 20
opensmith traces --tags rag,production
```

`--q` searches trace name, input, and output. `--status` accepts `ok` or `err`. `--tags` accepts comma-separated tags.

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
