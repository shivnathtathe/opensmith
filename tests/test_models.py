from __future__ import annotations

from uuid import UUID

import pytest
from pydantic import ValidationError

from opensmith.models import Run, Step, Trace


def test_trace_creates_with_uuid_id_by_default() -> None:
    trace = Trace(name="pipeline")

    UUID(trace.id)


def test_step_creates_with_uuid_id_by_default() -> None:
    step = Step(name="llm")

    UUID(step.id)


def test_run_creates_with_uuid_id_and_empty_tags() -> None:
    run = Run()

    UUID(run.id)
    assert run.tags == []


def test_step_type_literal_accepts_valid_values() -> None:
    for step_type in ("llm", "retrieval", "tool", "custom"):
        step = Step(name="step", step_type=step_type)
        assert step.step_type == step_type


def test_step_type_literal_rejects_invalid_values() -> None:
    with pytest.raises(ValidationError):
        Step(name="step", step_type="invalid")


def test_trace_steps_defaults_to_empty_list() -> None:
    trace = Trace(name="pipeline")

    assert trace.steps == []
