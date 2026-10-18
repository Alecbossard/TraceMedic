"""Audit completeness and source integrity of the published experiment, not new inference."""

import json

from tracemedic.config import ROOT
from tracemedic.v2.benchmark import schedule, score, summarize, verify_hashes


def test_every_published_v2_job_matches_frozen_inputs_scores_and_summary():
    folder = ROOT / "benchmarks/v2"
    protocol = json.loads((folder / "protocol.json").read_text(encoding="utf-8"))
    implementation = json.loads((folder / "implementation.json").read_text(encoding="utf-8"))
    verify_hashes(implementation["files"])
    oracle = json.loads((folder / "oracle.json").read_text(encoding="utf-8"))
    rows = [
        json.loads(line)
        for line in (folder / "results/raw.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    expected = {(j["method"], j["incident_id"], j["repetition"]) for j in schedule(protocol)}
    actual = {(r["method"], r["incident_id"], r["repetition"]) for r in rows}
    assert actual == expected and len(rows) == len(expected) == 56
    assert all(r["provider"] != "scripted" for r in rows)
    for row in rows:
        assert row["score"] == score(row, oracle[row["incident_id"]]), row["id"]
        assert not row["recovered_job"], "Report incomplete killed-session latency explicitly"
    assert summarize(rows, protocol) == json.loads(
        (folder / "results/summary.json").read_text(encoding="utf-8")
    )
