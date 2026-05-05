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

## Context Manager

```python
from opensmith import trace


with trace("my_pipeline") as t:
    t.log("query", query)
    response = call_model(query)
    t.log("response", response)
```

## Dashboard

```bash
opensmith ui
```

Open `http://localhost:7823`.
