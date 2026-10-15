import asyncio
import json
from contextlib import asynccontextmanager
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from tracemedic.config import Settings
from tracemedic.engine import Engine
from tracemedic.factory import build_engine

settings = Settings()
engine = Engine(settings)
tasks: dict[str, asyncio.Task] = {}


@asynccontextmanager
async def lifespan(app):
    # An OS lock still prevents concurrent resume if a separate CLI worker is active.
    for run in engine.store.runs():
        if run["status"] in ("running", "queued"):
            engine.store.update(run["id"], status="interrupted")
    yield
    for task in tasks.values():
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks.values(), return_exceptions=True)


app = FastAPI(title="TraceMedic", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class CreateRun(BaseModel):
    incident_id: str
    mode: Literal["multi", "single"] = "multi"
    workflow: Literal["v1", "v2"] = "v2"


def get_run(run_id):
    try:
        return engine.store.run(run_id)
    except KeyError:
        raise HTTPException(404, "Investigation not found") from None


def dispatch(run_id):
    if run_id in tasks and not tasks[run_id].done():
        raise HTTPException(409, "Investigation already active")

    async def work():
        # A fresh Engine per runner keeps each run's saved configuration isolated.
        try:
            await build_engine(settings, run_id=run_id).run(run_id)
        except Exception as exc:
            engine.store.event(run_id, "dispatch-error", "system", "error", str(exc)[:500])

    tasks[run_id] = asyncio.create_task(work())


@app.get("/api/health")
async def health():
    available, detail = False, "Model endpoint unavailable"
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            if settings.provider == "ollama":
                response = await client.get(settings.model_url.rstrip("/") + "/api/tags")
                response.raise_for_status()
                available = any(
                    m["name"] == settings.model for m in response.json().get("models", [])
                )
                detail = "Local model ready" if available else "Configured model is not installed"
            else:
                response = await client.get(
                    settings.model_url.rstrip("/") + "/models",
                    headers={"Authorization": f"Bearer {settings.api_key}"}
                    if settings.api_key
                    else {},
                )
                response.raise_for_status()
                available, detail = True, "Provider endpoint reachable; inference not checked"
    except (httpx.HTTPError, ValueError):
        pass
    return {
        "provider": settings.provider,
        "model": settings.model,
        "available": available,
        "detail": detail,
        "transport": "MCP · stdio",
        "persistence": "SQLite checkpoints",
        "limits": {"model_calls": settings.max_calls, "tool_calls": settings.max_tools},
        "workflows": ["v1", "v2"],
        "default_workflow": "v2",
    }


@app.get("/api/incidents")
def incidents():
    return json.loads((settings.root / "corpus" / "v2_catalog.json").read_text())


@app.get("/api/runs")
def list_runs():
    return [
        {
            **{k: v for k, v in r.items() if k != "state"},
            "engine_version": r["state"].get("engine_version", "v1"),
        }
        for r in engine.store.runs()
    ]


@app.post("/api/runs", status_code=201)
async def create_run(body: CreateRun):
    try:
        run_id = build_engine(settings, body.workflow).create(body.incident_id, body.mode)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    dispatch(run_id)
    return {"id": run_id}


@app.get("/api/runs/{run_id}")
def run_detail(run_id: str):
    return {
        **get_run(run_id),
        "events": engine.store.events(run_id),
        "evidence": engine.store.evidence(run_id),
        "metrics": engine.store.metrics(run_id),
    }


@app.post("/api/runs/{run_id}/cancel")
async def cancel(run_id: str):
    run = get_run(run_id)
    if run["status"] not in ("queued", "running"):
        raise HTTPException(409, "Investigation is not running")
    engine.store.update(run_id, cancel=True)
    return {"message": "Cancellation requested; stopping after the current durable action"}


@app.post("/api/runs/{run_id}/resume")
async def resume(run_id: str):
    run = get_run(run_id)
    if run["status"] not in ("interrupted", "cancelled", "error"):
        raise HTTPException(409, "This investigation is not resumable")
    dispatch(run_id)
    return {"id": run_id}


@app.get("/api/benchmark")
def benchmark(version: Literal["v1", "v2"] = "v2"):
    folder = settings.root / "benchmarks"
    if version == "v2":
        folder = folder / "v2"
    path = folder / "results" / "summary.json"
    return (
        json.loads(path.read_text())
        if path.exists()
        else {"status": "pending", "message": "No real-model benchmark has been published yet."}
    )


build = settings.root / "frontend" / "dist"
if build.exists():
    app.mount("/", StaticFiles(directory=build, html=True), name="frontend")
