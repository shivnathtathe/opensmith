from __future__ import annotations

from opensmith import autopatch


def main() -> None:
    autopatch()
    autopatch(only=["openai"])
    autopatch(exclude=["chromadb"])

    # Your existing SDK calls can run here without additional tracing code.


if __name__ == "__main__":
    main()
