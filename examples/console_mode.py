from __future__ import annotations

from opensmith import set_console_mode, trace


set_console_mode(True)


@trace(tags=["console", "demo"])
def pipeline(query: str) -> str:
    return f"processed: {query}"


if __name__ == "__main__":
    pipeline("show console output")
