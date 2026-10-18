import asyncio
import time

from fastapi.testclient import TestClient

from tracemedic.engine import Engine
from tracemedic.factory import build_engine
from tracemedic.testing import ScriptedProvider


def test_resume_selects_saved_provider_before_constructing_a_test_double(settings):
    real_settings = settings.model_copy(update={"provider": "ollama"})
    real = build_engine(real_settings, workflow="v2")
    real_id = real.create("case-01")
    resumed = build_engine(settings, run_id=real_id)
    assert resumed.settings.provider == "ollama"
    assert type(resumed.provider).__module__ == "tracemedic.v2.provider"
    scripted = build_engine(settings, workflow="v2")
    scripted_id = scripted.create("case-01")
    resumed = build_engine(real_settings, run_id=scripted_id)
    assert resumed.settings.provider == "scripted"
    assert type(resumed.provider).__module__ == "tracemedic.v2.testing"


def test_api_creates_v2_and_resumes_original_v1_with_saved_runner(settings, monkeypatch):
    from tracemedic import api

    legacy = Engine(settings, ScriptedProvider())
    old_id = legacy.create("case-01")
    assert asyncio.run(legacy.run(old_id, pause_after=2))["status"] == "interrupted"
    monkeypatch.setattr(api, "settings", settings)
    monkeypatch.setattr(api, "engine", legacy)
    monkeypatch.setattr(api, "tasks", {})

    with TestClient(api.app) as client:
        assert client.post(f"/api/runs/{old_id}/resume").status_code == 200
        response = client.post("/api/runs", json={"incident_id": "case-01", "workflow": "v2"})
        assert response.status_code == 201
        new_id = response.json()["id"]
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            old, new = [client.get(f"/api/runs/{key}").json() for key in (old_id, new_id)]
            if old["status"] == new["status"] == "completed":
                break
            time.sleep(0.05)
        else:
            raise AssertionError((old["status"], new["status"]))
        assert old["state"].get("engine_version", "v1") == "v1"
        assert new["state"]["engine_version"] == "v2"
        assert (
            old["state"]["diagnostic"]["outcome"]
            == new["state"]["diagnostic"]["outcome"]
            == "supported"
        )
        versions = {r["id"]: r["engine_version"] for r in client.get("/api/runs").json()}
        assert versions[old_id] == "v1" and versions[new_id] == "v2"
        assert client.post(f"/api/runs/{new_id}/resume").status_code == 409
        assert client.get("/api/benchmark?version=v1").json()["total_runs"] == 42
        assert client.get("/api/benchmark?version=unknown").status_code == 422
