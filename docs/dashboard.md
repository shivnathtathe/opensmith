# Dashboard

The dashboard is a local FastAPI app served at `localhost:7823`.

```bash
opensmith ui
```

## Layout

- Top bar with aggregate stats.
- Full-width trace table.
- Inline expanded trace details.
- Nested step table for LLM, retrieval, tool, and custom calls.

## API Endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/` | HTML dashboard |
| GET | `/api/traces?limit=50` | Recent traces |
| GET | `/api/traces/{trace_id}` | One trace and its steps |
| GET | `/api/stats` | Aggregate stats |
| DELETE | `/api/traces` | Clear all traces |

The dashboard only serves local data from SQLite.
