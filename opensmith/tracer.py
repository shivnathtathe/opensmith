from __future__ import annotations

import functools
import inspect
import threading
import time
from collections.abc import Awaitable, Callable
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


def _maybe_print_trace(trace_record: Trace) -> None:
    from opensmith.console import is_console_mode, print_trace

    if is_console_mode():
        print_trace(trace_record)


class TraceContext:
    def __init__(
        self,
        name: str,
        metadata: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        storage: Storage | None = None,
    ) -> None:
        self.storage = storage or Storage()
        self.trace = Trace(
            name=name,
            input={},
            metadata=metadata,
            tags=tags or [],
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
        _maybe_print_trace(self.trace)
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
        tags: list[str] | None = None,
    ) -> Callable[[Callable[P, R]], Callable[P, R]] | Callable[P, R] | TraceContext:
        if callable(func_or_name):
            return self._decorate(
                func_or_name,
                name=name,
                metadata=metadata,
                tags=tags,
            )

        if isinstance(func_or_name, str) and name is None:
            return TraceContext(
                name=func_or_name,
                metadata=metadata,
                tags=tags,
                storage=self.storage,
            )

        def decorator(func: Callable[P, R]) -> Callable[P, R]:
            return self._decorate(func, name=name, metadata=metadata, tags=tags)

        return decorator

    def _decorate(
        self,
        func: Callable[P, R],
        *,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
        tags: list[str] | None = None,
    ) -> Callable[P, R]:
        trace_name = name or func.__name__

        if inspect.iscoroutinefunction(func):
            return self._decorate_async(
                func,
                name=trace_name,
                metadata=metadata,
                tags=tags,
            )

        return self._decorate_sync(
            func,
            name=trace_name,
            metadata=metadata,
            tags=tags,
        )

    def _create_trace(
        self,
        trace_name: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        metadata: dict[str, Any] | None,
        tags: list[str] | None,
    ) -> Trace:
        return Trace(
            name=trace_name,
            input={
                "args": [str(a) for a in args],
                "kwargs": {k: str(v) for k, v in kwargs.items()},
            },
            metadata=metadata,
            tags=tags or [],
            parent_id=_current_trace_id(),
            start_time=time.time(),
        )

    def _finish_trace(
        self,
        trace_record: Trace,
        storage: Storage,
    ) -> None:
        trace_record.end_time = time.time()
        if trace_record.start_time is not None:
            trace_record.latency_ms = (
                trace_record.end_time - trace_record.start_time
            ) * 1000

        stack = _trace_stack()
        if stack and stack[-1] == trace_record.id:
            stack.pop()

        storage.save_trace(trace_record)
        _maybe_print_trace(trace_record)

    def _decorate_sync(
        self,
        func: Callable[P, R],
        *,
        name: str,
        metadata: dict[str, Any] | None = None,
        tags: list[str] | None = None,
    ) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            storage = self.storage or Storage()
            trace_record = self._create_trace(
                name,
                args,
                kwargs,
                metadata,
                tags,
            )

            _trace_stack().append(trace_record.id)

            try:
                result = func(*args, **kwargs)
            except Exception as exc:
                trace_record.error = repr(exc)
                self._finish_trace(trace_record, storage)
                raise

            if inspect.isawaitable(result):
                async def await_and_finish() -> Any:
                    try:
                        awaited_result = await result
                        trace_record.output = {"result": awaited_result}
                        return awaited_result
                    except Exception as exc:
                        trace_record.error = repr(exc)
                        raise
                    finally:
                        self._finish_trace(trace_record, storage)

                return await_and_finish()

            trace_record.output = {"result": result}
            self._finish_trace(trace_record, storage)
            return result

        return wrapper

    def _decorate_async(
        self,
        func: Callable[P, Awaitable[R]],
        *,
        name: str,
        metadata: dict[str, Any] | None = None,
        tags: list[str] | None = None,
    ) -> Callable[P, Awaitable[R]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            storage = self.storage or Storage()
            trace_record = self._create_trace(
                name,
                args,
                kwargs,
                metadata,
                tags,
            )


            _trace_stack().append(trace_record.id)

            try:
                result = await func(*args, **kwargs)
                trace_record.output = {"result": result}
                return result
            except Exception as exc:
                trace_record.error = repr(exc)
                raise
            finally:
                self._finish_trace(trace_record, storage)

        return wrapper


trace = TraceCallable()
