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


def test_save_trace_with_tags(tmp_storage: Storage) -> None:
    trace = Trace(name="tagged", tags=["production", "rag"])

    tmp_storage.save_trace(trace)

    saved, _ = tmp_storage.get_trace(trace.id)
    assert saved["tags"] == ["production", "rag"]


def test_get_traces_filter_by_tag(tmp_storage: Storage) -> None:
    tmp_storage.save_trace(Trace(name="rag", tags=["rag"]))
    tmp_storage.save_trace(Trace(name="debug", tags=["debug"]))

    traces = tmp_storage.get_traces(tags=["rag"])

    assert len(traces) == 1
    assert traces[0]["name"] == "rag"


def test_get_traces_no_tag_filter_returns_all(tmp_storage: Storage) -> None:
    tmp_storage.save_trace(Trace(name="rag", tags=["rag"]))
    tmp_storage.save_trace(Trace(name="debug", tags=["debug"]))

    traces = tmp_storage.get_traces()

    assert len(traces) == 2


def test_get_traces_rolls_up_tokens_and_cost(
    tmp_storage: Storage,
    sample_trace: Trace,
) -> None:
    step_one = Step(
        trace_id=sample_trace.id,
        name="openai.chat.completions.create",
        tokens_total=30,
        cost_usd=0.10,
        model="gpt-4o-mini",
        step_type="llm",
    )
    step_two = Step(
        trace_id=sample_trace.id,
        name="openai.embeddings.create",
        tokens_total=70,
        cost_usd=0.25,
        model="text-embedding-3-small",
        step_type="llm",
    )
    sample_trace.steps.extend([step_one, step_two])

    tmp_storage.save_trace(sample_trace)

    traces = tmp_storage.get_traces()

    assert traces[0]["tokens_total"] == 100
    assert traces[0]["cost_usd"] == 0.35
    assert traces[0]["model"] in {"gpt-4o-mini", "text-embedding-3-small"}


def test_get_traces_search_by_name(tmp_storage: Storage) -> None:
    tmp_storage.save_trace(Trace(name="rag_pipeline"))
    tmp_storage.save_trace(Trace(name="summarize_document"))

    traces = tmp_storage.get_traces(q="rag")

    assert len(traces) == 1
    assert traces[0]["name"] == "rag_pipeline"


def test_get_traces_filter_status_ok(tmp_storage: Storage) -> None:
    tmp_storage.save_trace(Trace(name="ok_trace"))
    tmp_storage.save_trace(Trace(name="err_trace", error="ValueError: boom"))

    traces = tmp_storage.get_traces(status="ok")

    assert len(traces) == 1
    assert traces[0]["name"] == "ok_trace"


def test_get_traces_filter_status_err(tmp_storage: Storage) -> None:
    tmp_storage.save_trace(Trace(name="ok_trace"))
    tmp_storage.save_trace(Trace(name="err_trace", error="ValueError: boom"))

    traces = tmp_storage.get_traces(status="err")

    assert len(traces) == 1
    assert traces[0]["name"] == "err_trace"


def test_get_trace_returns_rollups(
    tmp_storage: Storage,
    sample_trace: Trace,
) -> None:
    sample_trace.steps.append(
        Step(
            trace_id=sample_trace.id,
            name="openai.chat.completions.create",
            tokens_total=42,
            cost_usd=0.000105,
            model="gpt-4o-mini",
            step_type="llm",
        )
    )

    tmp_storage.save_trace(sample_trace)

    trace, _ = tmp_storage.get_trace(sample_trace.id)

    assert trace["tokens_total"] == 42
    assert trace["cost_usd"] == 0.000105
    assert trace["model"] == "gpt-4o-mini"
