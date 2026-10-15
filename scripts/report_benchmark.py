"""Render all published raw rows without rerunning, filtering or rescoring them."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
records = [
    json.loads(line)
    for line in (ROOT / "benchmarks/results/raw.jsonl").read_text(encoding="utf-8").splitlines()
]
summary = json.loads((ROOT / "benchmarks/results/summary.json").read_text())
catalog = {c["id"]: c for c in json.loads((ROOT / "corpus/catalog.json").read_text())}
lines = [
    "# Frozen benchmark report — v1",
    "",
    f"Recorded runs: **{len(records)} / 42 planned**. Status: **{summary['status']}**. The raw file contains every scheduled result recorded so far, including failures. No held-out prompts were tuned after the implementation freeze.",
    "",
    "## Setup and interpretation",
    "",
    "All incidents are authored synthetic fixtures with injected bugs or intentionally incomplete evidence. The 12 even-numbered cases are held out; case-08 and case-20 receive a second repetition per method. The model is Qwen3 4B Instruct 2507 Q4_K_M via the pinned `tracemedic-qwen3:4b` alias on Ollama 0.40.4. Hardware: Windows, RTX 4060 Laptop 8 GB, 16 GB system RAM. See `implementation.json` for digests/source hashes and `protocol.md` for the scoring definition.",
    "",
    "Both LLM methods have 18 model attempts, 14 uncached MCP calls and 1,200 generated tokens per call. Multi-agent has separate role contexts, collection/review permissions, mandatory initial delegation/review and synthesis reservation. Single-agent uses the union of tools and the same output contracts in one context. Actual usage differs; budget equivalence does not mean equal token consumption. Latency is end-to-end wall time including MCP startup, validation and checkpoint work. The model was not unloaded between runs; LLM order alternates by incident. Documentation and environment checks also ran on the workstation, so these timings describe this run rather than an isolated hardware benchmark.",
    "",
    "Automatic correctness requires expected concept groups in final prose and a confirmed hypothesis, valid captured file/line evidence and a reproduced fixture check. Ambiguous cases must complete with explicit insufficiency. A `supported` conclusion failing those rules is counted as unsupported **by the automatic evaluator**. These are keyword/reference/execution checks, not semantic entailment or expert adjudication; inspect raw disputed cases. Errors/budget stops count as failures, including on ambiguous cases. No LLM judge or agent agreement is used.",
    "",
    "## Measured totals",
    "",
    "| Method | Runs | Correct supported | Correct abstentions | Correct total | Unsupported by scorer | Completed | Median seconds | Model calls | MCP calls / successful |",
    "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
]
for m in summary["methods"]:
    lines.append(
        f"| {m['method']} | {m['runs']} | {m['correct_supported']} | {m['abstention_correct']} | {m['correct_total']} | {m['unsupported']} | {m['completed']} | {m['median_latency_s']:.2f} | {m['model_calls']} | {m['tool_calls']} / {m['tool_successes']} |"
    )
lines += [
    "",
    "| Method | Reported input tokens | Reported output tokens | Measured monetary cost |",
    "|---|---:|---:|---|",
]
for m in summary["methods"]:
    lines.append(
        f"| {m['method']} | {m['input_tokens'] if m['input_tokens'] is not None else str(sum(row['run']['metrics']['input_tokens'] or 0 for row in records if row['method'] == m['method'])) + ' recorded; total unknown'} | {m['output_tokens'] if m['output_tokens'] is not None else str(sum(row['run']['metrics']['output_tokens'] or 0 for row in records if row['method'] == m['method'])) + ' recorded; total unknown'} | Not measured |"
    )
lines += [
    "",
    "The case-02 multi-agent run has 15 attempts and 14 recorded responses, including a bounded provider-unavailable retry. The missing response usage makes the aggregate unknown; known provider token fields are reported without estimating that call. Zero tokens for the deterministic method means zero model requests. Local inference has no metered provider charge; hardware and electricity costs were not measured, so no dollar saving is claimed.",
    "",
    "## Every scheduled result",
    "",
    "CS = correct supported, CA = correct abstention, U = unsupported by automatic scorer, F = other failure/incorrect abstention. Repetitions are shown separately; no successful-only selection.",
    "",
    "| Incident | Method | Rep | Status / outcome | Result | Seconds | Model calls | MCP calls |",
    "|---|---|---:|---|---|---:|---:|---:|",
]
for row in sorted(records, key=lambda r: (r["incident_id"], r["repetition"], r["method"])):
    r, score = row["run"], row["score"]
    tag = (
        "CS"
        if score["correct_supported"]
        else "CA"
        if score["correct_abstention"]
        else "U"
        if score["unsupported_conclusion"]
        else "F"
    )
    outcome = r["state"].get("diagnostic", {}).get("outcome", "none")
    lines.append(
        f"| {row['incident_id']} · {catalog[row['incident_id']]['title']} | {row['method']} | {row['repetition']} | {r['status']} / {outcome} | {tag} | {row['latency_s']:.2f} | {r['metrics']['model_calls']} | {r['metrics']['tool_calls']} |"
    )
lines += ["", "## Failure and disagreement audit", ""]
for row in records:
    if row["score"]["correct"]:
        continue
    r = row["run"]
    diagnostic = r["state"].get("diagnostic", {})
    lines += [
        f"### {row['incident_id']} / {row['method']} / repetition {row['repetition']}",
        "",
        f"Run `{r['id']}`: `{r['status']}`. Automatic score: `{json.dumps(row['score'], sort_keys=True)}`.",
        "",
        diagnostic.get("summary", "No diagnostic produced."),
        "",
    ]
    rejected = [
        e
        for e in r["events"]
        if e["kind"] in ("action_rejected", "error", "budget_exhausted", "failed")
    ]
    for e in rejected:
        lines.append(f"- {e['role']} / {e['kind']}: {e['message']}")
    if rejected:
        lines.append("")
lines += [
    "## Recovery and injection evidence",
    "",
    "Process recovery is a separate fault experiment, not an inferred success rate for all benchmark cases. The committed `docs/evidence/real-recovery.json` records one real-model hard-kill/restart experiment: all prior evidence retained, same ID, one fixture ledger execution and one tool-result event. `tests/test_restart.py` independently runs a hard-kill/restart with a labeled test double. The uncertain claimed-but-uncompleted fixture operation is tested separately and is not replayed.",
    "",
    "Four corpus incidents contain misleading SYSTEM-like log text. MCP path/schema boundaries are tested directly. The held-out raw traces retain any attempted forbidden reads and all tool errors; absence of a forbidden read in these few runs does not demonstrate universal prompt-injection resistance.",
    "",
    "## Limits and conclusions",
    "",
]
methods = {m["method"]: m for m in summary["methods"]}
if all(k in methods for k in ("single", "multi")):
    s, m = methods["single"], methods["multi"]
    lines.append(
        f"On these recorded runs the single agent has {s['correct_total']}/{s['runs']} correct automatic outcomes; the multi-agent system has {m['correct_total']}/{m['runs']}. Median latency is {s['median_latency_s']:.2f}s versus {m['median_latency_s']:.2f}s. Multi-agent uses {m['model_calls']} model calls versus {s['model_calls']}. These measurements expose review/coordination overhead; they do not establish a production benefit or calibrated accuracy."
    )
lines += [
    "",
    "The sample is small, synthetic, mostly one repetition per case, and uses a small shared model with correlated role errors. The two extra repeated cases are a limited variability probe. All correctness claims are scoped to the deterministic scoring rule and its stated limitations. Further work should add independently sourced cases, semantic human adjudication and more repeated runs under an isolated timing protocol, with a newly frozen test set before tuning.",
    "",
]
lines += [
    "See [scoring notes](scoring_notes.md) for concrete examples of over-abstention, a symptom confirmed as a cause, and a possible keyword false negative. Frozen scores are not changed by those observations.",
    "",
]
lines += [
    "Packaging note: generated catalog/oracle/protocol JSON line endings were canonicalized to LF for Windows/Linux checkout consistency. Incident file bytes, oracle values, scoring and agent/provider source hashes were unchanged during the comparison. No held-out prompt tuning was performed.",
    "",
]
(ROOT / "benchmarks/report.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
print(f"Wrote report for {len(records)} recorded runs")
