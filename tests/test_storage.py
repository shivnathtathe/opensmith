from __future__ import annotations

from opensmith.models import Step, Trace
from opensmith.storage import Storage


def test_save_trace_saves_to_sqlite(tmp_storage: Storage, sample_trace: Trace) -> None:
    tmp_storage.save_trace(sample_trace)

    trace, steps = tmp_storage.get_trace(sample_trace.id)

    assert trace["id"] == sample_trace.id
    assert trace["name"] == sample_trace.name
    assert steps == []


def test_get_traces_returns_saved_traces(
    tmp_storage: Storage,
    sample_trace: Trace,
) -> None:
    tmp_storage.save_trace(sample_trace)

    traces = tmp_storage.get_traces()

    assert len(traces) == 1
    assert traces[0]["id"] == sample_trace.id


def test_get_trace_returns_trace_and_steps(
    tmp_storage: Storage,
    sample_trace: Trace,
    sample_step: Step,
) -> None:
    sample_step.trace_id = sample_trace.id
    sample_trace.steps.append(sample_step)

    tmp_storage.save_trace(sample_trace)

    trace, steps = tmp_storage.get_trace(sample_trace.id)

    assert trace["id"] == sample_trace.id
    assert len(steps) == 1
    assert steps[0]["id"] == sample_step.id


def test_save_step_saves_step_with_trace_id(
    tmp_storage: Storage,
    sample_trace: Trace,
    sample_step: Step,
) -> None:
    tmp_storage.save_trace(sample_trace)
    sample_step.trace_id = sample_trace.id

    tmp_storage.save_step(sample_step)

    _, steps = tmp_storage.get_trace(sample_trace.id)

    assert len(steps) == 1
    assert steps[0]["trace_id"] == sample_trace.id


def test_delete_all_clears_both_tables(
    tmp_storage: Storage,
    sample_trace: Trace,
    sample_step: Step,
) -> None:
    sample_step.trace_id = sample_trace.id
    sample_trace.steps.append(sample_step)
    tmp_storage.save_trace(sample_trace)

    tmp_storage.delete_all()

    assert tmp_storage.get_traces() == []
    assert tmp_storage.get_stats()["total_steps"] == 0


def test_get_stats_returns_correct_counts(
    tmp_storage: Storage,
    sample_trace: Trace,
    sample_step: Step,
) -> None:
    sample_step.trace_id = sample_trace.id
    sample_step.cost_usd = 0.25
    sample_trace.steps.append(sample_step)

    tmp_storage.save_trace(sample_trace)

    stats = tmp_storage.get_stats()

    assert stats["total_traces"] == 1
    assert stats["total_steps"] == 1
    assert stats["total_tokens"] == 30
    assert stats["total_cost_usd"] == 0.25


def test_get_traces_respects_limit_param(tmp_storage: Storage) -> None:
    for index in range(3):
        tmp_storage.save_trace(
            Trace(
                name=f"trace-{index}",
                start_time=float(index),
            )
        )

    traces = tmp_storage.get_traces(limit=2)

    assert len(traces) == 2
