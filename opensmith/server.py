from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from opensmith.storage import Storage
from opensmith.websocket_manager import ConnectionManager


UI_DIR = Path(__file__).parent / "ui"
INDEX_HTML = UI_DIR / "index.html"

storage = Storage()
manager = ConnectionManager()
last_seen_timestamp = 0.0

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


@app.on_event("startup")
async def startup() -> None:
    global last_seen_timestamp

    last_seen_timestamp = _current_latest_timestamp()
    asyncio.create_task(_poll_new_traces())


async def _poll_new_traces() -> None:
    global last_seen_timestamp

    while True:
        await asyncio.sleep(2)

        traces = storage.get_traces(limit=100)
        new_traces = [
            trace
            for trace in traces
            if _trace_timestamp(trace) > last_seen_timestamp
        ]

        if not new_traces:
            continue

        new_traces.sort(key=_trace_timestamp)

        for trace in new_traces:
            await manager.broadcast(
                {
                    "type": "trace_new",
                    "trace": trace,
                }
            )

        last_seen_timestamp = max(_trace_timestamp(trace) for trace in new_traces)


def _current_latest_timestamp() -> float:
    traces = storage.get_traces(limit=1)
    if not traces:
        return 0.0
    return _trace_timestamp(traces[0])


def _trace_timestamp(trace: dict[str, Any]) -> float:
    value = trace.get("created_at") or trace.get("start_time") or 0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


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
def get_traces(
    limit: int = 50,
    q: str | None = None,
    tags: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    parsed_tags = _parse_tags(tags)
    return storage.get_traces(
        limit=limit,
        tags=parsed_tags,
        q=q,
        status=status,
    )


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


def _parse_tags(tags: str | None) -> list[str] | None:
    if not tags:
        return None

    parsed = [tag.strip() for tag in tags.split(",") if tag.strip()]
    return parsed or None
