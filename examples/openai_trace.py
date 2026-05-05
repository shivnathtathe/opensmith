from __future__ import annotations

from opensmith import trace


@trace
def call_openai(prompt: str):
    from openai import OpenAI

    client = OpenAI()
    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )


if __name__ == "__main__":
    call_openai("Explain local-first observability in one sentence.")
