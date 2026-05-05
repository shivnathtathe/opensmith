from __future__ import annotations


PRICING_PER_1M_TOKENS: dict[str, tuple[float, float]] = {
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1": (2.00, 8.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-3.5-turbo": (0.50, 1.50),
    "claude-sonnet-4": (3.00, 15.00),
    "claude-opus-4": (15.00, 75.00),
    "claude-haiku-4": (0.80, 4.00),
    "claude-3-5-sonnet": (3.00, 15.00),
    "claude-3-5-haiku": (0.80, 4.00),
    "claude-3-opus": (15.00, 75.00),
    "text-embedding-3-small": (0.02, 0.0),
    "text-embedding-3-large": (0.13, 0.0),
}


def count_tokens(text: str, model: str) -> int:
    try:
        import tiktoken
    except ImportError:
        return int(len(text.split()) * 1.3)

    try:
        encoding = tiktoken.encoding_for_model(model)
    except Exception:
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            return int(len(text.split()) * 1.3)

    return len(encoding.encode(text))


def estimate_cost(
    tokens_input: int,
    tokens_output: int,
    model: str,
) -> float:
    pricing = _get_pricing(model)
    if pricing is None:
        return 0.0

    input_price, output_price = pricing
    input_cost = (tokens_input / 1_000_000) * input_price
    output_cost = (tokens_output / 1_000_000) * output_price
    return input_cost + output_cost


def _get_pricing(model: str) -> tuple[float, float] | None:
    normalized_model = model.lower()

    for known_model, pricing in PRICING_PER_1M_TOKENS.items():
        if known_model in normalized_model:
            return pricing

    return None
