"""Import an actual recorded, completed trace for inspection without new inference."""

import json

from tracemedic.config import ROOT, Settings
from tracemedic.store import Store

source = ROOT / "docs" / "evidence" / "demo-real.json"
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
