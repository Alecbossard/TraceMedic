"""Read-only check that the served model matches the published experiment."""

import json
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
expected = json.loads((ROOT / "benchmarks/implementation.json").read_text())["model"]
with httpx.Client(base_url="http://127.0.0.1:11434", timeout=5) as client:
    response = client.get("/api/tags")
    response.raise_for_status()
    actual = {m["name"]: m["digest"] for m in response.json()["models"]}
    version = client.get("/api/version").json()
checks = [
    {
        "name": m["name"],
        "expected_digest": m["digest"],
        "actual_digest": actual.get(m["name"]),
        "matches": actual.get(m["name"]) == m["digest"],
    }
    for m in expected["models"]
]
print(json.dumps({"ollama": version, "models": checks}, indent=2))
if not all(c["matches"] for c in checks):
    raise SystemExit(
        "Model identity differs. Label a new experiment; do not claim reproduction of the published model."
    )
