from __future__ import annotations

import pytest

from opensmith.models import Step, Trace
from opensmith.storage import Storage


@pytest.fixture
def tmp_storage(tmp_path) -> Storage:
    return Storage(tmp_path / "traces.db")


@pytest.fixture
def sample_trace() -> Trace:
    return Trace(
        name="sample_trace",
        input={"question": "hello"},
        output={"answer": "world"},
        start_time=100.0,
        end_time=100.25,
        latency_ms=250.0,
    )


@pytest.fixture
def sample_step() -> Step:
    return Step(
        trace_id="trace-1",
        name="openai.chat.completions.create",
        input={"prompt": "hello"},
        output={"content": "world"},
        start_time=100.0,
        end_time=100.1,
        latency_ms=100.0,
        tokens_input=10,
        tokens_output=20,
        tokens_total=30,
        model="gpt-4o",
        step_type="llm",
    )
