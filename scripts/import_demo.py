"""Import an actual recorded, completed trace for inspection without new inference."""

import argparse
import json

from tracemedic.config import ROOT, Settings
from tracemedic.store import Store

parser = argparse.ArgumentParser()
parser.add_argument("--workflow", choices=["v1", "v2"], default="v2")
args = parser.parse_args()
source = ROOT / "docs" / "evidence"
if args.workflow == "v2":
    source = source / "v2"
source = source / "demo-real.json"
record = json.loads(source.read_text(encoding="utf-8"))
assert record["provider"] != "scripted" and record["status"] == "completed"
store = Store(Settings().audit_db)
with store.connect() as db:
    db.execute(
        "INSERT OR IGNORE INTO runs(id,incident_id,mode,provider,model,status,created_at,updated_at,state,cancel_requested) VALUES(?,?,?,?,?,?,?,?,?,0)",
        (
            record["id"],
            record["incident_id"],
            record["mode"],
            record["provider"],
            record["model"],
            record["status"],
            record["created_at"],
            record["updated_at"],
            json.dumps(record["state"]),
        ),
    )
    for event in record["events"]:
        db.execute(
            "INSERT OR IGNORE INTO events(run_id,event_key,timestamp,role,kind,message,data) VALUES(?,?,?,?,?,?,?)",
            (
                record["id"],
                event["event_key"],
                event["timestamp"],
                event["role"],
                event["kind"],
                event["message"],
                json.dumps(event["data"]),
            ),
        )
store.add_evidence(record["id"], record["evidence"])
print(
    f"Imported recorded real-model trace {record['id']}. Open Investigations to inspect it; this import does not run inference or recreate resumable checkpoints."
)
