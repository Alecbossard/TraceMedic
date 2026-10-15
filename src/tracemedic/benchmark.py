"""Frozen, deterministic scoring of complete raw runs; no LLM judge."""

import argparse
import asyncio
import hashlib
import json
import statistics
import time
from pathlib import Path

from tracemedic.config import ROOT, Settings
from tracemedic.engine import Engine
from tracemedic.mcp_client import connect_tools
from tracemedic.models import Diagnostic, Hypothesis
from tracemedic.store import stable_id


async def deterministic(settings, incident_id):
    engine = Engine(settings.model_copy(update={"provider": "deterministic", "model": "rules-v1"}))
    run = engine.create(incident_id)
    observations, check, contents = [], {}, {}
    async with connect_tools(settings, engine.store, run, incident_id) as tools:
        for step, path in enumerate(
            ("runtime.log", "service.py", "settings.json", "input.json", "report.json")
        ):
            result = await tools.call("read_file", {"path": path}, "rules", step)
            observations.append(result.model_dump())
            if result.evidence:
                contents[path] = result.evidence[0].excerpt
        result = await tools.call("run_check", {}, "rules", 5)
        check = result.data if result.ok else {}
    text = contents.get("runtime.log", "")
    config = json.loads(contents.get("settings.json", "{}"))
    inputs = json.loads(contents.get("input.json", "{}"))
    claim = None
    # General symptom rules specified from development cases; no oracle import.
    if "Missing environment variable" in text:
        variable = config.get("connection_variable", "unknown")
        claim = f"The required environment variable {variable} is missing; supplied keys are {list(inputs.get('environment', {}))}. The startup configuration names a different variable."
    elif "ModuleNotFoundError" in text:
        claim = f"The configured module {config.get('driver')} is missing from installed modules {inputs.get('installed_modules')}."
    elif "ZeroDivisionError" in text and inputs.get("samples") == []:
        claim = "An empty samples array makes len(samples) zero and causes division by zero when computing the mean."
    elif "Invalid level" in text:
        claim = f"The configured level {config.get('level')!r} violates the uppercase logging level contract."
    elif "Dependency incompatible" in text:
        claim = f"Installed dependency version {config.get('installed')} is below required version {config.get('minimum')}."
    supported = bool(claim and check.get("status") == "reproduced")
    evidence = engine.store.evidence(run)
    ids = [e["id"] for e in evidence]
    h = (
        Hypothesis(
            id="h-" + stable_id(claim),
            claim=claim,
            evidence_ids=ids,
            next_check="Review the executed fixture",
            status="confirmed",
            reason="Deterministic symptom rule matched captured inputs and the reproduced fixture",
            check_ids=[check["check_id"]],
        ).model_dump()
        if supported
        else None
    )
    diagnostic = Diagnostic(
        outcome="supported" if supported else "insufficient",
        summary=claim
        if supported
        else "The deterministic symptom rules do not establish a root cause from the supplied evidence.",
        hypothesis_ids=[h["id"]] if h else [],
        evidence_ids=ids,
        next_actions=[
            "Inspect the relevant source and reproduce after a proposed change."
            if supported
            else "Collect more discriminating source and runtime evidence."
        ],
        limitations=[
            "Simple deterministic rules; limited coverage of causal mechanisms.",
            "No correction was applied.",
        ],
    )
    state = engine.store.run(run)["state"]
    state.update(
        status="completed",
        role="end",
        hypotheses=[h] if h else [],
        checks=[check] if check else [],
        diagnostic=diagnostic.model_dump(),
        observations=observations,
    )
    engine.store.update(run, status="completed", state=state)
    engine.store.event(
        run, "rules-final", "rules", "diagnostic", diagnostic.summary, diagnostic.model_dump()
    )
    return engine, run


def score(record, oracle, root=ROOT):
    diagnostic = record["state"].get("diagnostic", {})
    selected = diagnostic.get("evidence_ids", [])
    captured = {e["id"]: e for e in record["evidence"]}
    validity = []
    for key in selected:
        e = captured.get(key)
        if not e:
            validity.append(False)
            continue
        blob = (root / "corpus" / record["incident_id"] / e["path"]).read_bytes()
        lines = blob.decode().splitlines()
        validity.append(
            hashlib.sha256(blob).hexdigest() == e["sha256"]
            and "\n".join(lines[e["start_line"] - 1 : e["end_line"]]) == e["excerpt"]
        )
    valid_citations = bool(validity) and all(validity)
    confirmed = [h for h in record["state"].get("hypotheses", []) if h["status"] == "confirmed"]

    def concepts(text):
        return all(
            any(term.lower() in text.lower() for term in group)
            for group in oracle["concept_groups"]
        )

    check = any(c.get("status") == "reproduced" for c in record["state"].get("checks", []))
    complete = record["status"] == "completed"
    correct_abstention = (
        complete
        and oracle["abstain"]
        and diagnostic.get("outcome") == "insufficient"
        and not confirmed
    )
    correct_supported = (
        complete
        and not oracle["abstain"]
        and diagnostic.get("outcome") == "supported"
        and valid_citations
        and check
        and concepts(diagnostic.get("summary", ""))
        and any(concepts(h["claim"]) for h in confirmed)
    )
    return {
        "correct_supported": bool(correct_supported),
        "correct_abstention": bool(correct_abstention),
        "unsupported_conclusion": diagnostic.get("outcome") == "supported"
        and not correct_supported,
        "valid_citations": valid_citations,
        "independent_check": check,
        "expected_abstention": oracle["abstain"],
        "completed": complete,
        "correct": bool(correct_supported or correct_abstention),
    }


def export(engine, run):
    return {
        **engine.store.run(run),
        "events": engine.store.events(run),
        "evidence": engine.store.evidence(run),
        "metrics": engine.store.metrics(run),
    }


def summarize(records, model):
    methods = []
    for method in ("deterministic", "single", "multi"):
        rows = [r for r in records if r["method"] == method]
        if not rows:
            continue
        metrics = [r["run"]["metrics"] for r in rows]
        methods.append(
            {
                "method": method,
                "runs": len(rows),
                "correct_supported": sum(r["score"]["correct_supported"] for r in rows),
                "unsupported": sum(r["score"]["unsupported_conclusion"] for r in rows),
                "abstention_correct": sum(r["score"]["correct_abstention"] for r in rows),
                "correct_total": sum(r["score"]["correct"] for r in rows),
                "completed": sum(r["score"]["completed"] for r in rows),
                "median_latency_s": round(statistics.median(r["latency_s"] for r in rows), 3),
                "model_calls": sum(m["model_calls"] for m in metrics),
                "tool_calls": sum(m["tool_calls"] for m in metrics),
                "tool_successes": sum(m["tool_successes"] for m in metrics),
                "input_tokens": sum(m["input_tokens"] or 0 for m in metrics)
                if all(m["usage_complete"] for m in metrics)
                else None,
                "output_tokens": sum(m["output_tokens"] or 0 for m in metrics)
                if all(m["usage_complete"] for m in metrics)
                else None,
                "cost_usd": None,
            }
        )
    return {
        "status": "complete" if len(records) == 42 else "in_progress",
        "model": model,
        "total_runs": len(records),
        "protocol_version": 1,
        "methods": methods,
        "limitations": [
            "Small synthetic fixture corpus; keyword-based scoring is not semantic proof.",
            "One repetition per held-out case plus two repeated cases per method; not a statistical production estimate.",
            "Local hardware/electricity cost not measured.",
        ],
    }


async def run_benchmark(args):
    settings = Settings(data_dir=Path(args.data_dir).resolve())
    protocol = json.loads((ROOT / "benchmarks" / "protocol.json").read_text())
    oracle = json.loads((ROOT / "benchmarks" / "oracle.json").read_text())
    frozen = json.loads((ROOT / "benchmarks" / "frozen_manifest.json").read_text())
    for path, sha in frozen.items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != sha:
            raise ValueError(f"Frozen protocol/input changed: {path}")
    output = ROOT / "benchmarks" / "results"
    output.mkdir(exist_ok=True)
    raw_path = output / "raw.jsonl"
    records = (
        [json.loads(line) for line in raw_path.read_text().splitlines()]
        if raw_path.exists()
        else []
    )
    jobs = [(case, 1) for case in protocol["held_out"]] + [
        (case, 2) for case in protocol["repeated_cases"]
    ]
    for index, (case, repetition) in enumerate(jobs):
        # Alternate model method order to reduce systematic warm/cold cache bias.
        methods = [
            "deterministic",
            *(["single", "multi"] if index % 2 == 0 else ["multi", "single"]),
        ]
        for method in methods:
            if any(
                r["method"] == method and r["incident_id"] == case and r["repetition"] == repetition
                for r in records
            ):
                continue
            started = time.perf_counter()
            if method == "deterministic":
                engine, run = await deterministic(settings, case)
            else:
                engine = Engine(settings)
                run = engine.create(case, mode=method)
                await engine.run(run)
            record = export(engine, run)
            row = {
                "method": method,
                "incident_id": case,
                "repetition": repetition,
                "latency_s": round(time.perf_counter() - started, 3),
                "score": score(record, oracle[case]),
                "run": record,
            }
            records.append(row)
            with raw_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            (output / "summary.json").write_text(
                json.dumps(summarize(records, settings.model), indent=2) + "\n"
            )
            print(json.dumps({k: v for k, v in row.items() if k != "run"}), flush=True)
    (output / "summary.json").write_text(
        json.dumps(summarize(records, settings.model), indent=2) + "\n"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=str(ROOT / "data" / "benchmark"))
    args = parser.parse_args()
    asyncio.run(run_benchmark(args))


if __name__ == "__main__":
    main()
