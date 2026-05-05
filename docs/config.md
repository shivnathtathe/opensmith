# Configuration

opensmith reads `opensmith.json` from the current working directory on import.

```json
{
  "db_path": "./my_traces.db",
  "console_mode": false,
  "autopatch": ["openai", "qdrant"]
}
```

## Keys

| Key | Type | Description |
| --- | --- | --- |
| `db_path` | string | Custom SQLite database path |
| `console_mode` | boolean | Print completed traces to the terminal |
| `autopatch` | list of strings | Backends to patch automatically |

Malformed config files are ignored after printing a warning.
