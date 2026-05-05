# Quickstart

opensmith traces Python LLM pipelines locally and stores results in SQLite.

## Install

```bash
pip install opensmith
```

## Decorator

```python
from opensmith import trace


@trace
def call_llm(prompt: str):
    return openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
```

Async functions work the same way:

```python
from opensmith import trace


@trace(tags=["production", "rag"])
async def call_llm(prompt: str):
    return await openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
```

## Context Manager

```python
from opensmith import trace


with trace("my_pipeline", tags=["debug"]) as t:
    t.log("query", query)
    response = call_model(query)
    t.log("response", response)
```

## Console Mode

```python
from opensmith import set_console_mode


set_console_mode(True)
```

When enabled, opensmith prints each completed trace to the terminal.

## Configuration

Create `opensmith.json` in your project directory:

```json
{
  "db_path": "./my_traces.db",
  "console_mode": false,
  "autopatch": ["openai", "qdrant"]
}
```

## Dashboard

```bash
opensmith ui
```

Open `http://localhost:7823`.
