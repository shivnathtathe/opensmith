from __future__ import annotations

import functools
import importlib
import time
from collections.abc import Callable
from typing import Any

from opensmith.models import Step
from opensmith.storage import Storage
from opensmith.tracer import _current_trace_id


PATCH_TARGETS: dict[str, list[dict[str, Any]]] = {
    "openai": [
        {
            "module": "openai",
            "path": ["chat", "completions", "create"],
            "name": "chat.completions.create",
            "step_type": "llm",
        },
        {
            "module": "openai",
            "path": ["embeddings", "create"],
            "name": "embeddings.create",
            "step_type": "llm",
        },
    ],
    "anthropic": [
        {
            "module": "anthropic",
            "path": ["messages", "create"],
            "name": "messages.create",
            "step_type": "llm",
        },
    ],
    "litellm": [
        {
            "module": "litellm",
            "path": ["completion"],
            "name": "completion",
            "step_type": "llm",
        },
        {
            "module": "litellm",
            "path": ["embedding"],
            "name": "embedding",
            "step_type": "llm",
        },
    ],
    "qdrant": [
        {
            "module": "qdrant_client",
            "path": ["QdrantClient", "search"],
            "name": "QdrantClient.search",
            "step_type": "retrieval",
        },
        {
            "module": "qdrant_client",
            "path": ["QdrantClient", "upsert"],
            "name": "QdrantClient.upsert",
            "step_type": "retrieval",
        },
    ],
    "chromadb": [
        {
            "module": "chromadb.api.models.Collection",
            "path": ["Collection", "query"],
            "name": "Collection.query",
            "step_type": "retrieval",
        },
        {
            "module": "chromadb.api.models.Collection",
            "path": ["Collection", "add"],
            "name": "Collection.add",
            "step_type": "retrieval",
        },
    ],
    "pinecone": [
        {
            "module": "pinecone",
            "path": ["Index", "query"],
            "name": "Index.query",
            "step_type": "retrieval",
        },
        {
            "module": "pinecone",
            "path": ["Index", "upsert"],
            "name": "Index.upsert",
            "step_type": "retrieval",
        },
    ],
}

_patched: dict[tuple[str, tuple[str, ...]], tuple[Any, str, Callable[..., Any]]] = {}


def autopatch(
    only: list[str] | None = None,
    exclude: list[str] | None = None,
    storage: Storage | None = None,
) -> None:
    selected = set(only) if only is not None else set(PATCH_TARGETS)
    excluded = set(exclude or [])
    active_storage = storage or Storage()

    for client_name in selected:
        if client_name in excluded:
            continue

        for target in PATCH_TARGETS.get(client_name, []):
            _patch_target(client_name, target, active_storage)


def unpatch() -> None:
    for owner, attr_name, original in _patched.values():
        setattr(owner, attr_name, original)
    _patched.clear()


def _patch_target(
    client_name: str,
    target: dict[str, Any],
    storage: Storage,
) -> None:
    module_name = target["module"]
    path = tuple(target["path"])
    key = (module_name, path)

    if key in _patched:
        return

    try:
        module = importlib.import_module(module_name)
        owner, attr_name, original = _resolve_target(module, path)
    except Exception:
        return

    if not callable(original):
        return

    wrapped = _wrap_method(
        original=original,
        storage=storage,
        step_name=f"{client_name}.{target['name']}",
        step_type=target["step_type"],
    )

    try:
        setattr(owner, attr_name, wrapped)
    except Exception:
        return

    _patched[key] = (owner, attr_name, original)


def _resolve_target(module: Any, path: tuple[str, ...]) -> tuple[Any, str, Callable[..., Any]]:
    owner = module
    for part in path[:-1]:
        owner = getattr(owner, part)

    attr_name = path[-1]
    original = getattr(owner, attr_name)
    return owner, attr_name, original


def _wrap_method(
    original: Callable[..., Any],
    storage: Storage,
    step_name: str,
    step_type: str,
) -> Callable[..., Any]:
    @functools.wraps(original)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        step = Step(
            trace_id=_current_trace_id(),
            name=step_name,
            input={
                "args": [str(arg) for arg in args],
                "kwargs": {key: str(value) for key, value in kwargs.items()},
            },
            start_time=start_time,
            model=str(kwargs["model"]) if "model" in kwargs else None,
            step_type=step_type,  # type: ignore[arg-type]
        )

        try:
            result = original(*args, **kwargs)
            step.output = _serialize_output(result)
            _apply_usage(step, result)
            return result
        except Exception as exc:
            step.error = repr(exc)
            raise
        finally:
            step.end_time = time.time()
            step.latency_ms = (step.end_time - start_time) * 1000
            storage.save_step(step)

    return wrapper


def _serialize_output(value: Any) -> Any:
    if isinstance(value, str | int | float | bool | list | tuple | dict) or value is None:
        return value
    if hasattr(value, "model_dump"):
        try:
            return value.model_dump()
        except Exception:
            pass
    if hasattr(value, "dict"):
        try:
            return value.dict()
        except Exception:
            pass
    return str(value)


def _apply_usage(step: Step, result: Any) -> None:
    usage = _get_value(result, "usage")
    if usage is None:
        return

    tokens_input = (
        _get_value(usage, "prompt_tokens")
        or _get_value(usage, "input_tokens")
        or _get_value(usage, "tokens_input")
    )
    tokens_output = (
        _get_value(usage, "completion_tokens")
        or _get_value(usage, "output_tokens")
        or _get_value(usage, "tokens_output")
    )
    tokens_total = _get_value(usage, "total_tokens") or _get_value(
        usage,
        "tokens_total",
    )

    step.tokens_input = _to_int(tokens_input)
    step.tokens_output = _to_int(tokens_output)
    step.tokens_total = _to_int(tokens_total)

    if step.tokens_total is None:
        input_count = step.tokens_input or 0
        output_count = step.tokens_output or 0
        total = input_count + output_count
        step.tokens_total = total if total else None


def _get_value(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        return value.get(key)
    return getattr(value, key, None)


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
