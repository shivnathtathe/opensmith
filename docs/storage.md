# Storage

opensmith stores traces in SQLite at:

```text
~/.opensmith/traces.db
```

## Tables

### `traces`

| Column | Type |
| --- | --- |
| id | TEXT PRIMARY KEY |
| name | TEXT |
| input | TEXT JSON |
| output | TEXT JSON |
| error | TEXT |
| start_time | REAL |
| end_time | REAL |
| latency_ms | REAL |
| parent_id | TEXT |
| run_id | TEXT |
| metadata | TEXT JSON |
| created_at | REAL |

### `steps`

| Column | Type |
| --- | --- |
| id | TEXT PRIMARY KEY |
| trace_id | TEXT |
| name | TEXT |
| input | TEXT JSON |
| output | TEXT JSON |
| error | TEXT |
| start_time | REAL |
| end_time | REAL |
| latency_ms | REAL |
| tokens_input | INTEGER |
| tokens_output | INTEGER |
| tokens_total | INTEGER |
| model | TEXT |
| cost_usd | REAL |
| step_type | TEXT |
| metadata | TEXT JSON |

## Backup

Copy the database file while the dashboard and traced process are stopped:

```bash
cp ~/.opensmith/traces.db traces.backup.db
```

## Clear Data

```bash
opensmith clear
```
