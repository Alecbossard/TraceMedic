"""Real-model smoke/regression checks on seen V1 cases only; not the reserved benchmark."""

import asyncio
import json

from tracemedic.config import ROOT, Settings
from tracemedic.v2.engine import Engine


async def main():
    engine = Engine(Settings(data_dir=ROOT / "data/v2-development"))
    rows = []
    for case, mode in [
        ("case-16", "multi"),
        ("case-04", "multi"),
        ("case-20", "multi"),
        ("case-22", "single"),
        ("case-19", "single"),
    ]:
        run = engine.create(case, mode)
        result = await engine.run(run)
        row = {
            "id": run,
            "incident_id": case,
            "mode": mode,
            "status": result["status"],
            "diagnostic": result["state"].get("diagnostic"),
            "metrics": engine.store.metrics(run),
            "rejections": [
                e["message"] for e in engine.store.events(run) if e["kind"] == "action_rejected"
            ],
        }
        rows.append(row)
        (ROOT / "docs/evidence/v2-development.json").write_text(
            json.dumps(rows, indent=2) + "\n", encoding="utf-8", newline="\n"
        )
        print(
            json.dumps({k: row[k] for k in ("incident_id", "mode", "status", "metrics")}),
            flush=True,
        )


if __name__ == "__main__":
    asyncio.run(main())
