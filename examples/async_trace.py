from __future__ import annotations

import asyncio

from opensmith import trace


@trace(tags=["async", "demo"])
async def call_model(prompt: str) -> str:
    await asyncio.sleep(0.01)
    return f"response for: {prompt}"


async def main() -> None:
    print(await call_model("hello"))


if __name__ == "__main__":
    asyncio.run(main())
