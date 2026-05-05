from __future__ import annotations

import builtins

from opensmith.tokens import count_tokens, estimate_cost


def test_estimate_cost_returns_zero_for_unknown_model() -> None:
    assert estimate_cost(1000, 1000, "unknown-model") == 0.0


def test_estimate_cost_correct_for_gpt_4o() -> None:
    assert estimate_cost(1_000_000, 1_000_000, "gpt-4o") == 12.5


def test_estimate_cost_correct_for_gpt_4o_mini() -> None:
    assert estimate_cost(1_000_000, 1_000_000, "gpt-4o-mini") == 0.75


def test_count_tokens_fallback_without_tiktoken(monkeypatch) -> None:
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "tiktoken":
            raise ImportError
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    assert count_tokens("one two three four", "gpt-4o") == int(4 * 1.3)


def test_partial_model_name_matching() -> None:
    assert estimate_cost(1_000_000, 1_000_000, "gpt-4o-mini-2024-07-18") == 0.75
