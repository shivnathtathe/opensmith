from __future__ import annotations

import time

from opensmith.models import Step, Trace
from opensmith.storage import Storage
from opensmith.tokens import estimate_cost


def make_step(
    trace_id: str,
    name: str,
    step_type: str,
    start_time: float,
    latency_ms: float,
    tokens_input: int | None = None,
    tokens_output: int | None = None,
    model: str | None = None,
) -> Step:
    tokens_total = None
    cost_usd = None
    if tokens_input is not None or tokens_output is not None:
        input_count = tokens_input or 0
        output_count = tokens_output or 0
        tokens_total = input_count + output_count
        if model is not None:
            cost_usd = estimate_cost(input_count, output_count, model)

    return Step(
        trace_id=trace_id,
        name=name,
        input={"demo": True},
        output={"status": "ok"},
        start_time=start_time,
        end_time=start_time + (latency_ms / 1000),
        latency_ms=latency_ms,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        tokens_total=tokens_total,
        model=model,
        cost_usd=cost_usd,
        step_type=step_type,  # type: ignore[arg-type]
    )


def make_trace(
    name: str,
    start_time: float,
    latency_ms: float,
    tags: list[str],
    input_data: dict[str, object],
    output_data: dict[str, object] | None = None,
    error: str | None = None,
) -> Trace:
    return Trace(
        name=name,
        input=input_data,
        output=output_data,
        error=error,
        start_time=start_time,
        end_time=start_time + (latency_ms / 1000),
        latency_ms=latency_ms,
        tags=tags,
        metadata={"source": "seed_demo_data"},
    )


def main() -> None:
    storage = Storage()
    now = time.time()

    rag = make_trace(
        name="rag_pipeline",
        start_time=now - 8,
        latency_ms=1200,
        tags=["production", "rag"],
        input_data={"query": "How do we trace local LLM pipelines?"},
        output_data={"answer": "Use opensmith to capture traces locally in SQLite."},
    )
    rag.steps.extend(
        [
            make_step(
                rag.id,
                "openai.embeddings.create",
                "llm",
                rag.start_time or now,
                150,
                tokens_input=512,
                tokens_output=0,
                model="text-embedding-3-small",
            ),
            make_step(
                rag.id,
                "qdrant.QdrantClient.search",
                "retrieval",
                (rag.start_time or now) + 0.16,
                45,
            ),
            make_step(
                rag.id,
                "openai.chat.completions.create",
                "llm",
                (rag.start_time or now) + 0.22,
                980,
                tokens_input=800,
                tokens_output=350,
                model="gpt-4o-mini",
            ),
        ]
    )
    storage.save_trace(rag)

    summarize = make_trace(
        name="summarize_document",
        start_time=now - 70,
        latency_ms=800,
        tags=["production"],
        input_data={"document_id": "doc_7f2a", "pages": 12},
        output_data={"summary": "The document describes a local tracing workflow."},
    )
    summarize.steps.append(
        make_step(
            summarize.id,
            "openai.chat.completions.create",
            "llm",
            summarize.start_time or now,
            780,
            tokens_input=1200,
            tokens_output=400,
            model="gpt-4o",
        )
    )
    storage.save_trace(summarize)

    classify = make_trace(
        name="classify_intent",
        start_time=now - 180,
        latency_ms=200,
        tags=["production", "classifier"],
        input_data={"message": "Can you reset my workspace?"},
        output_data={"intent": "workspace_reset", "confidence": 0.94},
    )
    classify.steps.append(
        make_step(
            classify.id,
            "openai.chat.completions.create",
            "llm",
            classify.start_time or now,
            195,
            tokens_input=150,
            tokens_output=20,
            model="gpt-4o-mini",
        )
    )
    storage.save_trace(classify)

    extract = make_trace(
        name="extract_entities",
        start_time=now - 320,
        latency_ms=300,
        tags=["debug"],
        input_data={"text": "Large customer support transcript..."},
        output_data=None,
        error="ValueError: response exceeded max tokens",
    )
    storage.save_trace(extract)

    embed = make_trace(
        name="embed_documents",
        start_time=now - 540,
        latency_ms=450,
        tags=["indexing"],
        input_data={"batch_size": 32, "collection": "docs"},
        output_data={"embedded": 32},
    )
    embed.steps.append(
        make_step(
            embed.id,
            "openai.embeddings.create",
            "llm",
            embed.start_time or now,
            440,
            tokens_input=2048,
            tokens_output=0,
            model="text-embedding-3-large",
        )
    )
    storage.save_trace(embed)

    print(f"Seeded {len(storage.get_traces(limit=100))} traces into {storage.db_path}")


if __name__ == "__main__":
    main()
