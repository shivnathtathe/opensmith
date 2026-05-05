<div align="center">

<pre style="font-family: monospace; font-size: 18px; 
line-height: 1.2; color: #ededec; background: #0a0a0a; 
padding: 20px; display: inline-block;">
 ██████  ██████  ███████ ███    ██ ███████ ███    ███ ██ ████████ ██   ██ 
██    ██ ██   ██ ██      ████   ██ ██      ████  ████ ██    ██    ██   ██ 
██    ██ ██████  █████   ██ ██  ██ ███████ ██ ████ ██ ██    ██    ███████ 
██    ██ ██      ██      ██  ██ ██      ██ ██  ██  ██ ██    ██    ██   ██ 
 ██████  ██      ███████ ██   ████ ███████ ██      ██ ██    ██    ██   ██ 
</pre>

**The open-source, local-first alternative to LangSmith.**

![PyPI](https://img.shields.io/pypi/v/opensmith)
![Python](https://img.shields.io/pypi/pyversions/opensmith)
![License](https://img.shields.io/github/license/shivnathtathe/opensmith)
![Downloads](https://img.shields.io/pypi/dm/opensmith)
![Stars](https://img.shields.io/github/stars/shivnathtathe/opensmith)
![CI](https://github.com/shivnathtathe/opensmith/actions/workflows/ci.yml/badge.svg)

</div>

# opensmith

The open-source, local-first alternative to LangSmith.

> opensmith is to LangSmith what Ollama is to OpenAI — the local-first, privacy-first alternative.

## Why opensmith?

| | LangSmith | opensmith |
|--|-----------|-----------|
| Setup | Cloud account required | pip install opensmith |
| Data privacy | Sends traces to cloud | 100% local, SQLite only |
| Framework | Best with LangChain | Works with any Python code |
| Cost | Free tier then paid | Free forever, open source |
| Offline | No | Yes |
| Docker | No | No |
| Dashboard | Hosted | localhost:7823 |

## Why opensmith

LangSmith is powerful, but it is built around cloud-hosted tracing and is most natural inside the LangChain ecosystem. opensmith is a local-first alternative: install it with `pip`, use it with any Python LLM pipeline, and inspect traces on your machine without accounts, hosted services, Docker, or configuration. No trace data leaves your machine.

## Install

```bash
pip install opensmith
```

## Quickstart

### Example 1: `@trace` decorator

```python
from opensmith import trace


@trace
def call_llm(prompt: str):
    return openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )


@trace
def my_pipeline(question: str):
    # search_docs is your own retrieval function
    docs = search_docs(question)
    return call_llm(docs + question)
```

Async functions are supported:

```python
from opensmith import trace


@trace(tags=["production", "rag"])
async def call_llm(prompt: str):
    return await openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
```

### Example 2: context manager

```python
from opensmith import trace


with trace("my_pipeline", tags=["debug"]) as t:
    t.log("query", query)
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": query}],
    )
    t.log("response", response)
```

### Example 3: `autopatch()` zero code changes

```python
from opensmith import autopatch


autopatch()
```

Patch only selected backends:

```python
from opensmith import autopatch


autopatch(only=["openai"])
```

Patch everything except selected backends:

```python
from opensmith import autopatch


autopatch(exclude=["chromadb"])
```

## Console mode

Print trace results to the terminal as they complete:

```python
from opensmith import set_console_mode, trace


set_console_mode(True)


@trace
def my_func():
    return "ok"
```

## Configuration

opensmith reads `opensmith.json` from the current working directory on import:

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

![dashboard](docs/dashboard.png)

## CLI reference

| Command | Description |
| --- | --- |
| `opensmith ui` | Start the local dashboard at `localhost:7823`. |
| `opensmith traces` | List recent traces in the terminal. |
| `opensmith stats` | Show aggregate trace, step, token, and cost statistics. |
| `opensmith clear` | Delete all locally stored traces after confirmation. |

## Supported backends

| Backend | Package | Status |
|---------|---------|--------|
| openai | openai | ✅ |
| anthropic | anthropic | ✅ |
| litellm | litellm | ✅ |
| qdrant | qdrant-client | ✅ |
| chromadb | chromadb | ✅ |
| pinecone | pinecone-client | ✅ |

## Storage

Traces are stored locally at `~/.opensmith/traces.db` unless overridden with `opensmith.json` or `set_default_db_path()`.

## Star History

[![Star History Chart](https://api.star-history.com/chart?repos=shivnathtathe/opensmith&type=date&legend=top-left)](https://www.star-history.com/?repos=shivnathtathe%2Fopensmith&type=date&legend=top-left)

## License

MIT
