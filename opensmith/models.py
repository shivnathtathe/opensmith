from __future__ import annotations

import time
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


StepType = Literal["llm", "retrieval", "tool", "custom"]


class Step(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    trace_id: str | None = None
    name: str
    input: Any | None = None
    output: Any | None = None
    error: str | None = None
    start_time: float | None = None
    end_time: float | None = None
    latency_ms: float | None = None
    tokens_input: int | None = None
    tokens_output: int | None = None
    tokens_total: int | None = None
    model: str | None = None
    cost_usd: float | None = None
    step_type: StepType | None = None
    metadata: dict[str, Any] | None = None


class Trace(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    input: Any | None = None
    output: Any | None = None
    error: str | None = None
    start_time: float | None = None
    end_time: float | None = None
    latency_ms: float | None = None
    parent_id: str | None = None
    run_id: str | None = None
    metadata: dict[str, Any] | None = None
    steps: list[Step] = Field(default_factory=list)


class Run(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str | None = None
    tags: list[str] = Field(default_factory=list)
    created_at: float = Field(default_factory=lambda: time.time())
