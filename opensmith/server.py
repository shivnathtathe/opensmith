from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from opensmith.storage import Storage


UI_DIR = Path(__file__).parent / "ui"
INDEX_HTML = UI_DIR / "index.html"

storage = Storage()

app = FastAPI(title="opensmith", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:7823",
        "http://127.0.0.1:7823",
    ],
    allow_credentials=False,
    allow_methods=["GET", "DELETE"],
    allow_headers=["*"],
)

if UI_DIR.exists():
    app.mount("/static", StaticFiles(directory=UI_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    if INDEX_HTML.exists():
        return HTMLResponse(INDEX_HTML.read_text(encoding="utf-8"))

    return HTMLResponse(
        """
        <!doctype html>
        <html>
            <head>
                <title>opensmith</title>
            </head>
            <body>
                <h1>opensmith UI loading...</h1>
            </body>
        </html>
        """
    )


@app.get("/api/traces")
def get_traces(limit: int = 50) -> list[dict[str, Any]]:
    return storage.get_traces(limit=limit)


@app.get("/api/traces/{trace_id}")
def get_trace(trace_id: str) -> dict[str, Any]:
    trace, steps = storage.get_trace(trace_id)
    return {
        "trace": trace,
        "steps": steps,
    }


@app.delete("/api/traces")
def delete_traces() -> dict[str, str]:
    storage.delete_all()
    return {"status": "cleared"}


@app.get("/api/stats")
def get_stats() -> dict[str, Any]:
    return storage.get_stats()
