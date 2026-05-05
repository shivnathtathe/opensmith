# opensmith v0.1.2 Launch Content

## 1. Medium / Dev.to Article

# I Built a Local-First LangSmith Alternative in Python (No Cloud, No Setup)

LLM apps are getting more complex. A simple prompt call turns into a pipeline: embed the query, retrieve documents, call a model, parse the answer, maybe call tools, then run a second model pass. When something breaks, the terminal logs are usually not enough.

That is where tracing tools help. They show the full pipeline, each step, latency, token usage, errors, and inputs and outputs. LangSmith does this well, but it comes with tradeoffs that do not fit every project.

## The problem with LangSmith

LangSmith is powerful, but it is cloud-first and most natural inside the LangChain ecosystem. That is fine for many teams. It is not ideal when I want to debug a local prototype, keep sensitive prompts on my machine, or add tracing to a plain Python pipeline without signing up for another service.

For a lot of projects, I do not need a hosted observability platform. I need something that starts instantly, stores data locally, and works with normal Python functions.

I wanted a tool with a very small promise:

```bash
pip install opensmith
```

No Docker. No account. No config required. No trace data leaving the machine.

## What I built

opensmith is a local-first LLM pipeline tracer for Python.

It stores traces in SQLite at `~/.opensmith/traces.db` and serves a local dashboard at `localhost:7823`. The dashboard shows traces, nested steps, inputs, outputs, errors, latency, token usage, cost estimates, and live updates.

The latest v0.1.2 release adds:

- Async tracing support
- Tags for filtering traces
- Console output mode
- `opensmith.json` project config
- WebSocket live updates using SQLite polling
- Token and cost rollups from steps to trace rows
- Search and status filters on `/api/traces`
- A rebuilt dashboard with charts, model column, search bar, filter pills, and a LIVE indicator

GitHub: https://github.com/shivnathtathe/opensmith

PyPI: https://pypi.org/project/opensmith/

## How it works

The simplest way to use opensmith is the `@trace` decorator.

```python
from opensmith import trace


@trace(tags=["production", "rag"])
def rag_pipeline(question: str):
    docs = search_docs(question)
    return call_llm(docs + question)
```

It captures function name, inputs, output, errors, latency, and parent-child relationships for nested traced functions.

Async functions work too:

```python
from opensmith import trace


@trace(tags=["async", "openai"])
async def call_llm(prompt: str):
    response = await openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return response
```

There is also a context manager when you want to manually log values:

```python
from opensmith import trace


with trace("my_pipeline", tags=["debug"]) as t:
    t.log("query", query)
    response = call_model(query)
    t.log("response", response)
```

For zero-code-change tracing, opensmith can monkey-patch supported SDKs:

```python
from opensmith import autopatch


autopatch()
autopatch(only=["openai"])
autopatch(exclude=["chromadb"])
```

Current autopatch targets include OpenAI, Anthropic, LiteLLM, Qdrant, ChromaDB, and Pinecone. If a client is not installed, opensmith skips it silently.

For terminal-first workflows, v0.1.1 added console mode:

```python
from opensmith import set_console_mode, trace


set_console_mode(True)


@trace
def classify_intent(text: str):
    return classifier(text)
```

This prints traces as they finish:

```text
✓ classify_intent  245ms  [42 tokens  $0.000105]
```

You can also add a project-level `opensmith.json`:

```json
{
  "db_path": "./my_traces.db",
  "console_mode": false,
  "autopatch": ["openai", "qdrant"]
}
```

## Dashboard screenshot

The dashboard is fully local and runs on `localhost:7823`.

![opensmith dashboard](https://raw.githubusercontent.com/shivnathtathe/opensmith/main/docs/dashboard.png)

It now includes search, status filters, tag filters, model names, token and cost rollups, latency charts, token charts, and a LIVE WebSocket indicator.

## How to install and use

Install:

```bash
pip install opensmith
```

Trace a function:

```python
from opensmith import trace


@trace
def my_pipeline(query: str):
    return run_pipeline(query)
```

Start the dashboard:

```bash
opensmith ui
```

Open:

```text
http://localhost:7823
```

Everything is stored locally in SQLite unless you configure another local path.

## What's next

opensmith is still early. The core goal is to keep it small, local-first, and easy to adopt.

Some things I want to explore next:

- Better cost tables for more model providers
- More SDK autopatch targets
- Trace export and import
- Better support for long-running traces
- More dashboard filtering and comparison views
- OpenTelemetry-compatible export without making cloud required

If you are building LLM apps in Python and want tracing without sending data to a hosted service, I would love feedback.

GitHub: https://github.com/shivnathtathe/opensmith

Install: `pip install opensmith`

## 2. LinkedIn Post

I just launched opensmith v0.1.2, a local-first LLM pipeline tracer for Python.

The idea is simple: debugging LLM pipelines should not require a cloud account, Docker setup, or rewriting your app around a specific framework.

With opensmith you can:

- Install with `pip install opensmith`
- Trace sync and async Python functions with `@trace`
- Use a context manager for manual logging
- Autopatch OpenAI, Anthropic, LiteLLM, Qdrant, ChromaDB, and Pinecone
- Store everything locally in SQLite
- Open a local dashboard at `localhost:7823`
- Search, filter, inspect steps, view token and cost rollups, and see live updates

Example:

```python
from opensmith import trace

@trace(tags=["production", "rag"])
def pipeline(query):
    return run_pipeline(query)
```

No cloud. No account. No setup. Your traces stay on your machine.

GitHub: https://github.com/shivnathtathe/opensmith

What would you want from a local-first tracing tool for AI pipelines?

## 3. LinkedIn Newsletter Edition

# The Dev Pulse: Building Local-First AI Tools

AI tooling has moved fast, but much of it assumes a cloud-first workflow. That is reasonable for teams that need shared observability and hosted infrastructure. But for local development, prototypes, private datasets, and quick debugging, it can feel heavier than necessary.

This week I launched opensmith v0.1.2, a local-first LLM pipeline tracer for Python.

The goal is not to replace every enterprise observability platform. The goal is to make tracing available with one command:

```bash
pip install opensmith
```

opensmith stores traces locally in SQLite and runs a dashboard on `localhost:7823`. No Docker, no account, and no trace data leaves your machine.

The basic API is a decorator:

```python
from opensmith import trace


@trace(tags=["production", "rag"])
def rag_pipeline(question: str):
    docs = search_docs(question)
    return call_llm(docs + question)
```

Async functions are supported too:

```python
@trace(tags=["async"])
async def call_llm(prompt: str):
    return await openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
```

For manual logging, there is a context manager:

```python
from opensmith import trace


with trace("pipeline", tags=["debug"]) as t:
    t.log("query", query)
    response = call_model(query)
    t.log("response", response)
```

For existing codebases, autopatch can trace common SDK calls:

```python
from opensmith import autopatch


autopatch(only=["openai", "qdrant"])
```

v0.1.2 focuses on making the dashboard feel like a real product. It adds WebSocket live updates via SQLite polling, token and cost rollups from steps, search and status filters, model names, filter pills, latency charts, token charts, and a LIVE indicator.

There is also project config:

```json
{
  "db_path": "./my_traces.db",
  "console_mode": false,
  "autopatch": ["openai", "qdrant"]
}
```

The broader theme here is local-first AI tooling. Not every workflow needs to start with a hosted service. Sometimes the best developer experience is a small local database, a local dashboard, and a simple Python API.

GitHub: https://github.com/shivnathtathe/opensmith

If you are building AI apps, where do you prefer traces to live: local-first by default, or cloud-first from day one?

## 4. Reddit Post: r/LocalLLaMA

Title: Built a local-first LLM pipeline tracer for Python, no cloud required

When debugging LLM pipelines, I kept running into the same problem: logs were too flat, but full hosted tracing tools felt heavy for local work.

I wanted something closer to this:

```bash
pip install opensmith
```

Then:

```python
from opensmith import trace

@trace(tags=["rag"])
def rag_pipeline(query):
    docs = retrieve(query)
    return generate(docs, query)
```

opensmith stores traces locally in SQLite at `~/.opensmith/traces.db` and runs a local dashboard at `localhost:7823`. No account, no Docker, no trace data leaving the machine.

v0.1.2 adds:

- Async tracing
- Tags
- Console mode
- `opensmith.json` config
- WebSocket live updates via SQLite polling
- Token and cost rollups
- Search and status filtering
- Dashboard with charts, model column, filter pills, and trace detail views

It can also autopatch OpenAI, Anthropic, LiteLLM, Qdrant, ChromaDB, and Pinecone. If a package is not installed, it skips it.

This is still early and Python-focused, but I would like it to stay simple and local-first.

GitHub: https://github.com/shivnathtathe/opensmith

Curious if local tracing is useful to people here, especially for RAG and local model workflows.

## 5. Reddit Post: r/Python

Title: I built a local-first Python tracing tool for LLM pipelines

I have been working on a small Python package called opensmith. It is a local-first tracer for LLM-style pipelines, but it works with normal Python functions too.

The motivation was simple: I wanted structured traces while developing locally without signing up for a hosted service or running Docker.

Install:

```bash
pip install opensmith
```

Usage:

```python
from opensmith import trace

@trace(tags=["production"])
def pipeline(query: str):
    return run_pipeline(query)
```

Async is supported:

```python
@trace
async def call_api(prompt: str):
    return await client.generate(prompt)
```

It stores traces in SQLite at `~/.opensmith/traces.db` and serves a local FastAPI dashboard at `localhost:7823`.

v0.1.2 includes search, status filters, token and cost rollups, live updates via WebSocket plus SQLite polling, and a rebuilt dashboard with charts.

It also has a console mode:

```python
from opensmith import set_console_mode
set_console_mode(True)
```

The package is typed, uses Pydantic v2, FastAPI, SQLite, Click, and Rich.

GitHub: https://github.com/shivnathtathe/opensmith

Feedback from Python developers would be very helpful, especially around API design and packaging.

## 6. Hacker News Show HN

Title: Show HN: opensmith, local-first LLM pipeline tracer, no cloud required

Body:

I built opensmith, a small Python package for tracing LLM pipelines locally.

It stores traces in SQLite at `~/.opensmith/traces.db` and serves a FastAPI dashboard on `localhost:7823`. It supports sync and async `@trace`, context manager logging, tags, console output, and optional autopatching for OpenAI, Anthropic, LiteLLM, Qdrant, ChromaDB, and Pinecone.

v0.1.2 adds WebSocket live updates via SQLite polling, token and cost rollups, search and status filters, model columns, and SVG charts in the dashboard.

Install:

```bash
pip install opensmith
```

The goal is a lightweight local alternative to hosted tracing tools when you do not want trace data leaving your machine.

GitHub: https://github.com/shivnathtathe/opensmith

## 7. Product Hunt

Tagline:

Local-first LLM pipeline tracing for Python

Description:

opensmith is a local-first LLM pipeline tracer for Python. It helps developers debug AI pipelines without creating a cloud account, running Docker, or sending trace data to a hosted service.

Install it with `pip install opensmith`, add `@trace` to sync or async functions, and open a local dashboard at `localhost:7823`. Traces are stored in SQLite at `~/.opensmith/traces.db` by default.

opensmith supports decorators, context managers, console output mode, project config through `opensmith.json`, and optional autopatching for OpenAI, Anthropic, LiteLLM, Qdrant, ChromaDB, and Pinecone.

The v0.1.2 dashboard includes WebSocket live updates via SQLite polling, search, status filters, tag filters, model names, token and cost rollups, nested step inspection, latency charts, token charts, and a LIVE indicator.

It is designed for developers who want practical observability while building locally, prototyping RAG systems, debugging agents, or working with private data.

First comment from maker:

I built opensmith because I wanted LLM tracing without starting from a hosted service. Tools like LangSmith are powerful, but sometimes I just want to debug a Python pipeline locally and keep all prompts, outputs, and metadata on my own machine.

The first version was simple: decorator, SQLite storage, and a local dashboard. v0.1.2 makes the dashboard much more useful with live updates, filters, charts, token rollups, and better trace details.

I would love feedback from anyone building RAG pipelines, agents, or LLM products in Python. What would make local tracing more useful for your workflow?

## 8. Twitter / X Thread

Tweet 1:

I built opensmith: a local-first LangSmith alternative for Python.

No cloud.
No account.
No Docker.
No setup.

Just local LLM pipeline tracing with SQLite and a dashboard.

Tweet 2:

Install:

```bash
pip install opensmith
```

Start the dashboard:

```bash
opensmith ui
```

Open `localhost:7823`.

Tweet 3:

Trace any Python function:

```python
from opensmith import trace

@trace(tags=["rag"])
def pipeline(query):
    docs = search_docs(query)
    return call_llm(docs, query)
```

Tweet 4:

Async works too:

```python
@trace(tags=["async"])
async def call_llm(prompt):
    return await openai.chat.completions.create(...)
```

Nested traces, errors, latency, inputs, and outputs are captured automatically.

Tweet 5:

Zero-code-change tracing with autopatch:

```python
from opensmith import autopatch

autopatch(only=["openai", "qdrant"])
```

Supports OpenAI, Anthropic, LiteLLM, Qdrant, ChromaDB, and Pinecone.

Tweet 6:

v0.1.2 adds a much better dashboard:

- Live updates via WebSocket + SQLite polling
- Search + status filters
- Token and cost rollups
- Model column
- Charts
- Inline trace and step details

Everything stays local.

Tweet 7:

Use project config with `opensmith.json`:

```json
{
  "db_path": "./my_traces.db",
  "console_mode": false,
  "autopatch": ["openai"]
}
```

Tweet 8:

GitHub: https://github.com/shivnathtathe/opensmith

PyPI: https://pypi.org/project/opensmith/

If you build LLM apps in Python, I would love feedback. What would you want in a local-first tracing tool?

## 9. Awesome List PR Description

### awesome-python

One-line list description:

opensmith: Local-first LLM pipeline tracing for Python with SQLite storage and a local dashboard.

PR title:

Add opensmith to debugging and tracing tools

PR body:

This PR adds opensmith, a local-first Python package for tracing LLM pipelines and AI workflows.

It provides sync and async decorators, context manager logging, SQLite storage, a FastAPI dashboard, console output mode, and optional autopatching for common LLM and vector database SDKs. It is useful for Python developers who want local tracing without sending data to a hosted service.

Repository: https://github.com/shivnathtathe/opensmith

PyPI: https://pypi.org/project/opensmith/

### awesome-llm

One-line list description:

opensmith: Local-first LLM pipeline tracer with decorators, autopatching, SQLite storage, and a localhost dashboard.

PR title:

Add opensmith as a local-first LLM tracing tool

PR body:

This PR adds opensmith, a local-first LLM pipeline tracer for Python.

opensmith helps developers inspect prompts, outputs, errors, latency, token usage, and cost estimates locally. It supports decorators, async functions, context managers, console output, project config, and autopatching for OpenAI, Anthropic, LiteLLM, Qdrant, ChromaDB, and Pinecone.

It stores traces in SQLite and runs a dashboard on localhost, so no cloud service is required.

Repository: https://github.com/shivnathtathe/opensmith

PyPI: https://pypi.org/project/opensmith/
