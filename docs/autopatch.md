# Autopatch

`autopatch()` monkey-patches supported SDK methods so you can trace calls without changing pipeline code.

## Usage

```python
from opensmith import autopatch


autopatch()
```

Patch only selected backends:

```python
autopatch(only=["openai"])
```

Patch everything except selected backends:

```python
autopatch(exclude=["chromadb"])
```

Restore original methods:

```python
from opensmith import unpatch


unpatch()
```

## Supported Backends

| Backend | Package | Methods |
| --- | --- | --- |
| openai | openai | `chat.completions.create`, `embeddings.create` |
| anthropic | anthropic | `messages.create` |
| litellm | litellm | `completion`, `embedding` |
| qdrant | qdrant-client | `QdrantClient.search`, `QdrantClient.upsert` |
| chromadb | chromadb | `Collection.query`, `Collection.add` |
| pinecone | pinecone-client | `Index.query`, `Index.upsert` |

If a backend is not installed, opensmith skips it silently.

## Configuration

Autopatch can be enabled automatically from `opensmith.json`:

```json
{
  "autopatch": ["openai", "qdrant"]
}
```

The package applies this on import by calling `autopatch(only=[...])`.
