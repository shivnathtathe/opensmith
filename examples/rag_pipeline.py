from __future__ import annotations

from opensmith import trace


def search_docs(question: str) -> list[str]:
    return [
        "opensmith stores traces locally in SQLite.",
        "The dashboard runs on localhost via FastAPI.",
    ]


@trace
def generate_answer(context: str, question: str) -> str:
    return f"Question: {question}\nContext: {context}\nAnswer: opensmith traces locally."


@trace
def rag_pipeline(question: str) -> str:
    docs = search_docs(question)
    context = "\n".join(docs)
    return generate_answer(context, question)


if __name__ == "__main__":
    print(rag_pipeline("Where does opensmith store traces?"))
