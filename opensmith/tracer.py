from __future__ import annotations

import functools
import threading
import time
from collections.abc import Callable
from types import TracebackType
from typing import Any, ParamSpec, TypeVar

from opensmith.models import Trace
from opensmith.storage import Storage


P = ParamSpec("P")
R = TypeVar("R")

_state = threading.local()


def _trace_stack() -> list[str]:
    stack = getattr(_state, "trace_stack", None)
    if stack is None:
        stack = []
        _state.trace_stack = stack
    return stack


def _current_trace_id() -> str | None:
    stack = _trace_stack()
    if not stack:
        return None
    return stack[-1]


class TraceContext:
    def __init__(
        self,
        name: str,
        metadata: dict[str, Any] | None = None,
        storage: Storage | None = None,
    ) -> None:
        self.storage = storage or Storage()
        self.trace = Trace(
            name=name,
            input={},
            metadata=metadata,
            parent_id=_current_trace_id(),
        )

    def __enter__(self) -> TraceContext:
        self.trace.start_time = time.time()
        _trace_stack().append(self.trace.id)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        self.trace.end_time = time.time()
        if self.trace.start_time is not None:
            self.trace.latency_ms = (self.trace.end_time - self.trace.start_time) * 1000

        if exc_value is not None:
            self.trace.error = repr(exc_value)

        stack = _trace_stack()
        if stack and stack[-1] == self.trace.id:
            stack.pop()

        self.storage.save_trace(self.trace)
        return False

    def log(self, key: str, value: Any) -> None:
        if self.trace.input is None or not isinstance(self.trace.input, dict):
            self.trace.input = {}
        self.trace.input[key] = value


class TraceCallable:
    def __init__(self, storage: Storage | None = None) -> None:
        self.storage = storage

    def __call__(
        self,
        func_or_name: Callable[P, R] | str | None = None,
        *,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Callable[[Callable[P, R]], Callable[P, R]] | Callable[P, R] | TraceContext:
        if callable(func_or_name):
            return self._decorate(func_or_name, name=name, metadata=metadata)

        if isinstance(func_or_name, str) and name is None:
            return TraceContext(
                name=func_or_name,
                metadata=metadata,
                storage=self.storage,
            )

        def decorator(func: Callable[P, R]) -> Callable[P, R]:
            return self._decorate(func, name=name, metadata=metadata)

        return decorator

    def _decorate(
        self,
        func: Callable[P, R],
        *,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Callable[P, R]:
        trace_name = name or func.__name__

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            storage = self.storage or Storage()
            trace_record = Trace(
                name=trace_name,
                input={
                    "args": [str(a) for a in args],
                    "kwargs": {k: str(v) for k, v in kwargs.items()},
                },
                metadata=metadata,
                parent_id=_current_trace_id(),
                start_time=time.time(),
            )

            _trace_stack().append(trace_record.id)

            try:
                result = func(*args, **kwargs)
                trace_record.output = {"result": result}
                return result
            except Exception as exc:
                trace_record.error = repr(exc)
                raise
            finally:
                trace_record.end_time = time.time()
                trace_record.latency_ms = (
                    trace_record.end_time - trace_record.start_time
                ) * 1000

                stack = _trace_stack()
                if stack and stack[-1] == trace_record.id:
                    stack.pop()

                storage.save_trace(trace_record)

        return wrapper


trace = TraceCallable()
