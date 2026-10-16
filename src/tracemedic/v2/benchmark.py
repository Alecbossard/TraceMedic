"""Frozen V2 comparison: original rules/V1 vs V2 single/multi, no LLM judge."""

import argparse
import asyncio
import hashlib
import json
import platform
import random
import shutil
import statistics
import sys
import time
from collections import Counter

import httpx

from tracemedic.benchmark import deterministic
from tracemedic.config import ROOT, Settings
from tracemedic.engine import Engine as V1Engine
from tracemedic.v2.engine import Engine as V2Engine

SUITE = ROOT / "benchmarks" / "v2"
RESULTS = SUITE / "results"
IMPLEMENTATION_PATHS = [
    "src/tracemedic/engine.py",
    "src/tracemedic/prompts.py",
    "src/tracemedic/models.py",
    "src/tracemedic/provider.py",
    "src/tracemedic/benchmark.py",
    "src/tracemedic/store.py",
    "src/tracemedic/config.py",
    "src/tracemedic/mcp_server.py",
    "src/tracemedic/mcp_client.py",
    "src/tracemedic/fixture_worker.py",
    "src/tracemedic/experiment_worker.py",
    "src/tracemedic/interventions.py",
    "src/tracemedic/locking.py",
    "src/tracemedic/v2/engine.py",
    "src/tracemedic/v2/contracts.py",
    "src/tracemedic/v2/prompts.py",
    "src/tracemedic/v2/provider.py",
    "src/tracemedic/v2/benchmark.py",
]


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )


def verify_hashes(files):
    for relative, digest in files.items():
        if hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() != digest:
            raise ValueError("Frozen file changed: " + relative)


def schedule(protocol):
    cases = [(c, 1) for c in protocol["held_out"]] + [(c, 2) for c in protocol["repeated_cases"]]
    jobs = [
        {"method": method, "incident_id": case, "repetition": repetition}
        for method in protocol["methods"]
        for case, repetition in cases
    ]
    random.Random(protocol["seed"]).shuffle(jobs)
    return jobs


def freeze():
    path = SUITE / "implementation.json"
    if path.exists():
        raise ValueError("Implementation already frozen; refuse to overwrite")
    verify_hashes(json.loads((SUITE / "frozen_manifest.json").read_text()))
    verify_hashes(json.loads((ROOT / "benchmarks/implementation.json").read_text())["files"])
    settings = Settings()
    tags = httpx.get(settings.model_url.rstrip("/") + "/api/tags", timeout=10).json()
    model = next(m for m in tags["models"] if m["name"] == settings.model)
    reference = json.loads((ROOT / "benchmarks/implementation.json").read_text())["model"][
        "models"
    ][0]
    if model["digest"] != reference["digest"]:
        raise ValueError("Model alias differs from V1 comparison")
    protocol = json.loads((SUITE / "protocol.json").read_text())
    if (
        settings.max_calls,
        settings.max_tools,
        settings.max_output_tokens,
        settings.seed,
        settings.temperature,
    ) != (
        protocol["llm_call_limit"],
        protocol["tool_call_limit"],
        protocol["max_output_tokens_per_call"],
        protocol["seed"],
        0,
    ):
        raise ValueError("Current settings differ from the frozen comparison budgets")
    write_json(
        path,
        {
            "files": {
                p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in IMPLEMENTATION_PATHS
            },
            "model": model,
            "ollama": httpx.get(settings.model_url.rstrip("/") + "/api/version").json(),
            "settings": settings.model_dump(mode="json", exclude={"api_key", "root", "data_dir"}),
            "python": sys.version,
            "platform": platform.platform(),
            "schedule": schedule(protocol),
            "development": "Original cases 01, 04, 16, 19, 20, 22 used for V2 development/regression; no sample-* model responses inspected before freeze.",
        },
    )
    print(f"Implementation frozen; {len(schedule(protocol))} scheduled runs")


def dataset_view():
    """Both engines receive identical bytes; old catalog is preserved in the repository."""
    root = ROOT / ".runtime" / "v2-evaluation-inputs"
    root.mkdir(parents=True, exist_ok=True)
    catalog = json.loads((SUITE / "catalog.json").read_text())
    write_json(root / "corpus/catalog.json", catalog)
    for incident in catalog:
        shutil.copytree(
            ROOT / "corpus" / incident["id"], root / "corpus" / incident["id"], dirs_exist_ok=True
        )
    return root


def score(record, oracle, root=ROOT):
    state, diagnostic = record["state"], record["state"].get("diagnostic", {})
    evidence = {e["id"]: e for e in record["evidence"]}
    valid = []
    for key in diagnostic.get("evidence_ids", []):
        e = evidence.get(key)
        if not e or e["path"] not in {
            "runtime.log",
            "service.py",
            "settings.json",
            "input.json",
            "report.json",
        }:
            valid.append(False)
            continue
        blob = (root / "corpus" / record["incident_id"] / e["path"]).read_bytes()
        valid.append(
            hashlib.sha256(blob).hexdigest() == e["sha256"]
            and "\n".join(blob.decode().splitlines()[e["start_line"] - 1 : e["end_line"]])
            == e["excerpt"]
        )
    valid_citations = bool(valid) and all(valid)
    text = diagnostic.get("summary", "").casefold()
    mechanism = all(
        any(term.casefold() in text for term in group) for group in oracle["concept_groups"]
    )
    contradiction = any(term.casefold() in text for term in oracle.get("prohibited", []))
    confirmed = [
        h
        for h in state.get("hypotheses", [])
        if h["status"] == "confirmed" and h["id"] in diagnostic.get("hypothesis_ids", [])
    ]
    checks = {c["check_id"]: c for c in state.get("checks", [])}
    reproduced = any(
        checks.get(key, {}).get("status") == "reproduced"
        and checks.get(key, {}).get("kind") != "intervention"
        for h in confirmed
        for key in h.get("check_ids", [])
    )
    source_cited = any(
        evidence.get(key, {}).get("path") == "service.py"
        for key in diagnostic.get("evidence_ids", [])
    )
    supported = diagnostic.get("outcome") == "supported"
    completed = record["status"] == "completed"
    correct_supported = bool(
        completed
        and supported
        and not oracle["abstain"]
        and mechanism
        and not contradiction
        and valid_citations
        and source_cited
        and confirmed
        and reproduced
    )
    abstention_correct = (
        completed
        and not supported
        and diagnostic.get("outcome") == "insufficient"
        and oracle["abstain"]
    )
    literal_quotes = []
    for h in confirmed:
        for quote in h.get("citations", []):
            e = evidence.get(quote["evidence_id"])
            index = quote["line"] - e["start_line"] if e else -1
            lines = e["excerpt"].splitlines() if e else []
            literal_quotes.append(0 <= index < len(lines) and quote["quote"] in lines[index])
    return {
        "correct": correct_supported or abstention_correct,
        "correct_supported": correct_supported,
        "abstention_correct": abstention_correct,
        "unsupported": completed and supported and not correct_supported,
        "completed": completed,
        "valid_citations": valid_citations,
        "mechanism_concepts": mechanism,
        "reproduced": reproduced,
        "literal_quotes_valid": all(literal_quotes) if literal_quotes else None,
        "literal_quotes_count": len(literal_quotes),
    }


def summarize(rows, protocol):
    methods = []
    for method in protocol["methods"]:
        subset = [r for r in rows if r["method"] == method]
        if not subset:
            continue
        usage = all(r["metrics"]["usage_complete"] for r in subset)
        methods.append(
            {
                "method": method,
                "runs": len(subset),
                **{
                    key: sum(r["score"][key] for r in subset)
                    for key in (
                        "correct",
                        "correct_supported",
                        "abstention_correct",
                        "unsupported",
                        "completed",
                    )
                },
                "median_latency_s": round(statistics.median(r["latency_s"] for r in subset), 3),
                "model_calls": sum(r["metrics"]["model_calls"] for r in subset),
                "tool_calls": sum(r["metrics"]["tool_calls"] for r in subset),
                "tool_successes": sum(r["metrics"]["tool_successes"] for r in subset),
                "input_tokens": sum(r["metrics"]["input_tokens"] or 0 for r in subset)
                if usage
                else None,
                "output_tokens": sum(r["metrics"]["output_tokens"] or 0 for r in subset)
                if usage
                else None,
                "known_input_tokens": sum(r["metrics"]["input_tokens"] or 0 for r in subset),
                "known_output_tokens": sum(r["metrics"]["output_tokens"] or 0 for r in subset),
                "usage_complete": usage,
                "cost_usd": None,
                "invalid_actions": sum(
                    e["kind"] == "action_rejected" for r in subset for e in r["events"]
                ),
                "blocked_confirmations": sum(
                    e["kind"] == "confirmation_blocked" for r in subset for e in r["events"]
                ),
                "statuses": dict(Counter(r["status"] for r in subset)),
            }
        )
    return {
        "status": "complete" if len(rows) == len(schedule(protocol)) else "partial",
        "version": "v2",
        "model": protocol["model"],
        "total_runs": len(rows),
        "scheduled_runs": len(schedule(protocol)),
        "methods": methods,
    }


async def run_all():
    implementation = json.loads((SUITE / "implementation.json").read_text())
    verify_hashes(implementation["files"])
    verify_hashes(json.loads((SUITE / "frozen_manifest.json").read_text()))
    protocol, oracle = [
        json.loads((SUITE / f"{name}.json").read_text()) for name in ("protocol", "oracle")
    ]
    tags = httpx.get(
        implementation["settings"]["model_url"].rstrip("/") + "/api/tags", timeout=10
    ).json()
    if not any(
        m["name"] == implementation["model"]["name"]
        and m["digest"] == implementation["model"]["digest"]
        for m in tags["models"]
    ):
        raise ValueError("Frozen model digest is not available")
    root = dataset_view()
    data_dir = ROOT / "data" / "v2-benchmark"
    settings = Settings(**implementation["settings"], root=root, data_dir=data_dir)
    RESULTS.mkdir(parents=True, exist_ok=True)
    raw = RESULTS / "raw.jsonl"
    rows = (
        [json.loads(line) for line in raw.read_text(encoding="utf-8").splitlines()]
        if raw.exists()
        else []
    )
    done = {(r["method"], r["incident_id"], r["repetition"]) for r in rows}
    for job in implementation["schedule"]:
        key = job["method"], job["incident_id"], job["repetition"]
        if key in done:
            continue
        started = time.perf_counter()
        recovered = False
        if job["method"] == "deterministic":
            engine, run = await deterministic(settings, job["incident_id"])
        else:
            engine = (V1Engine if job["method"] == "v1-multi" else V2Engine)(settings)
            run = f"v2-{job['method']}-{job['incident_id']}-r{job['repetition']}"
            try:
                engine.store.run(run)
                recovered = True
            except KeyError:
                engine.create(
                    job["incident_id"], "single" if job["method"] == "v2-single" else "multi", run
                )
            await engine.run(run)
        record = {
            **engine.store.run(run),
            **job,
            "events": engine.store.events(run),
            "evidence": engine.store.evidence(run),
            "metrics": engine.store.metrics(run),
            "latency_s": round(time.perf_counter() - started, 3),
            "recovered_job": recovered,
        }
        record["score"] = score(record, oracle[job["incident_id"]])
        if recovered:
            record["latency_s"] = round(
                sum(
                    e["data"].get("elapsed_ms", 0)
                    for e in record["events"]
                    if e["kind"] == "session_end"
                )
                / 1000,
                3,
            )
            record["latency_note"] = (
                "Sum of recorded completed runner sessions; hard-killed session time may be unavailable"
            )
        with raw.open("a", encoding="utf-8", newline="\n") as output:
            output.write(json.dumps(record, ensure_ascii=False) + "\n")
            output.flush()
        rows.append(record)
        done.add(key)
        write_json(RESULTS / "summary.json", summarize(rows, protocol))
        print(
            f"{len(rows)}/{len(implementation['schedule'])} {job['method']} {job['incident_id']} r{job['repetition']} {record['status']} {record['latency_s']}s",
            flush=True,
        )
    print("All scheduled runs recorded", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", action="store_true")
    args = parser.parse_args()
    if args.freeze:
        freeze()
    else:
        asyncio.run(run_all())


if __name__ == "__main__":
    main()
