"""Hard-kill a real-model worker and resume it in a completely new process."""

import argparse
import json
import os
import subprocess
import sys
import time
import uuid

from tracemedic.config import ROOT
from tracemedic.store import Store

parser = argparse.ArgumentParser()
parser.add_argument("--workflow", choices=["v1", "v2"], default="v1")
args = parser.parse_args()
data = ROOT / "data" / "recovery-proof" / args.workflow
data.mkdir(parents=True, exist_ok=True)
store = Store(data / "audit.db")
run = "real-recovery-" + str(uuid.uuid4())[:8]
output = (ROOT / ".runtime" / f"recovery-worker-{args.workflow}.txt").open("w", encoding="utf-8")
command = [
    sys.executable,
    "-m",
    "tracemedic.cli",
    "--workflow",
    args.workflow,
    "--data-dir",
    str(data),
    "run",
    "case-01",
    "--run-id",
    run,
    "--step-delay",
    "0.8",
]
worker = subprocess.Popen(
    command,
    stdout=output,
    stderr=output,
    **({"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}),
)
try:
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        if any(
            e["kind"] == "tool_result" and e["data"].get("tool") == "run_check"
            for e in store.events(run)
        ):
            break
        if worker.poll() is not None:
            raise RuntimeError(
                "Worker exited before the fixture check; inspect .runtime/recovery-worker.txt"
            )
        time.sleep(0.05)
    else:
        raise TimeoutError("Real worker did not reach the checkpoint boundary")
    before = store.evidence(run)
    aliases_before = store.run(run)["state"].get("evidence_aliases", {})
    previous_calls = store.metrics(run)
    old_pid = worker.pid
    worker.kill()
    worker.wait(timeout=15)
finally:
    if worker.poll() is None:
        worker.kill()
        worker.wait(timeout=15)
    output.close()
resumed = subprocess.run(
    [sys.executable, "-m", "tracemedic.cli", "--data-dir", str(data), "resume", run],
    capture_output=True,
    text=True,
    timeout=180,
)
after = store.evidence(run)
with store.connect() as db:
    operation_count = db.execute(
        "SELECT count(*) FROM operations WHERE run_id=? AND key LIKE 'fixture:%'", (run,)
    ).fetchone()[0]
record = store.run(run)
proof = {
    "provider": record["provider"],
    "model": record["model"],
    "engine_version": record["state"].get("engine_version", "v1"),
    "run_id": run,
    "terminated_pid": old_pid,
    "hard_kill": True,
    "resume_exit_code": resumed.returncode,
    "status": record["status"],
    "evidence_before": len(before),
    "evidence_after": len(after),
    "all_snapshots_preserved": all(e in after for e in before),
    "aliases_preserved": aliases_before == record["state"].get("evidence_aliases", {}),
    "fixture_execution_records": operation_count,
    "fixture_tool_result_events": sum(
        e["kind"] == "tool_result" and e["data"].get("tool") == "run_check"
        for e in store.events(run)
    ),
    "metrics_before": previous_calls,
    "metrics_after": store.metrics(run),
    "events": store.events(run),
    "diagnostic": record["state"].get("diagnostic"),
}
destination = ROOT / "docs" / "evidence"
if args.workflow == "v2":
    destination = destination / "v2"
destination = destination / "real-recovery.json"
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(json.dumps(proof, indent=2) + "\n")
print(json.dumps({k: v for k, v in proof.items() if k not in ("events", "diagnostic")}, indent=2))
assert resumed.returncode == 0 and record["status"] == "completed"
assert (
    proof["all_snapshots_preserved"]
    and proof["aliases_preserved"]
    and operation_count == 1
    and proof["fixture_tool_result_events"] == 1
)
