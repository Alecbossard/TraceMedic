"""Render the frozen V2 ledger without changing scores or selecting runs."""

import json
from pathlib import Path

from tracemedic.v2.benchmark import schedule, score, summarize, verify_hashes

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "benchmarks/v2"


def main():
    implementation = json.loads((FOLDER / "implementation.json").read_text(encoding="utf-8"))
    verify_hashes(implementation["files"])
    protocol = json.loads((FOLDER / "protocol.json").read_text(encoding="utf-8"))
    oracle = json.loads((FOLDER / "oracle.json").read_text(encoding="utf-8"))
    rows = [
        json.loads(line)
        for line in (FOLDER / "results/raw.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    expected = {(j["method"], j["incident_id"], j["repetition"]) for j in schedule(protocol)}
    actual = {(r["method"], r["incident_id"], r["repetition"]) for r in rows}
    if actual != expected or len(rows) != len(expected):
        raise ValueError("Cannot report complete results: missing/duplicate scheduled rows")
    for row in rows:
        assert row["score"] == score(row, oracle[row["incident_id"]]), row["id"]
    summary = summarize(rows, protocol)
    assert summary == json.loads((FOLDER / "results/summary.json").read_text(encoding="utf-8"))
    lines = [
        "# V2 comparison: causal records and compact tools",
        "",
        "All **56/56** predeclared outcomes are published: 12 new reserved cases, one execution each, plus a second execution of sample-02 and sample-11, for each of four methods. All original 24 cases were seen development/regression data for V2. No reserved-response prompt tuning occurred.",
        "",
        "Same Qwen3 4B Instruct Q4_K_M alias/digest, seed 17, temperature 0, 18 model calls, 14 tool calls, 1200 generated tokens per call and 8192-token context. All inference was serial on the same Windows/RTX 4060 Laptop machine. Order was seeded and interleaved; local cache/system load still affect timings. V1 retains its original engine/prompts/provider and five tools. Both V2 methods share seven tools and schema-decoded control phases. This compares complete workflows; only the two V2 variants isolate agent-count differences.",
        "",
        "## Automatic outcomes",
        "",
        "| Method | Correct total | Supported correct | Correct abstentions | Unsupported by rubric | Completed | Median wall time | Model calls | Tool successes/calls |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for method in summary["methods"]:
        m = method
        lines.append(
            f"| {m['method']} | {m['correct']}/{m['runs']} | {m['correct_supported']} | {m['abstention_correct']} | {m['unsupported']} | {m['completed']} | {m['median_latency_s']:.3f}s | {m['model_calls']} | {m['tool_successes']}/{m['tool_calls']} |"
        )
    lines += [
        "",
        "These counts use the same frozen scorer for all four methods. Supported outcomes require all mechanism concept groups in the final explanation, valid captured source references, a selected confirmed hypothesis and a reproduced baseline. Explicit abstention is correct only on ambiguous cases. Controlled failures and budget stops are incorrect. The rubric does not require identifier repetition inside both a hypothesis and final paragraph as V1's older scorer did; **do not compare these counts to the old 9/14**.",
        "",
        "## Usage and guard activity",
        "",
        "| Method | Reported input tokens | Reported output tokens | Invalid actions | Blocked confirmations |",
        "|---|---:|---:|---:|---:|",
    ]
    for m in summary["methods"]:
        input_tokens = (
            f"{m['input_tokens']:,}"
            if m["input_tokens"] is not None
            else f"incomplete (known {m['known_input_tokens']:,})"
        )
        output_tokens = (
            f"{m['output_tokens']:,}"
            if m["output_tokens"] is not None
            else f"incomplete (known {m['known_output_tokens']:,})"
        )
        lines.append(
            f"| {m['method']} | {input_tokens} | {output_tokens} | {m['invalid_actions']} | {m['blocked_confirmations']} |"
        )
    lines += [
        "",
        "Tokens are provider-reported. Missing usage is never estimated. Costs, energy and hardware utilization are unmeasured. Tool success means a typed tool result with `ok=true`; a partial bundle can legitimately report a missing file. Tool transport failures and schema rejections remain in the event ledger.",
        "",
        "## Every scheduled case",
        "",
        "S = correct supported, A = correct abstention, U = supported but rejected by rubric, M = completed but missed expected outcome, F = system stop/error. Values include measured wall seconds. Each cell links to the corresponding raw ledger row.",
        "",
        "| Case / repetition | deterministic | v1-multi | v2-single | v2-multi |",
        "|---|---|---|---|---|",
    ]
    indexed = {
        (r["method"], r["incident_id"], r["repetition"]): (i + 1, r) for i, r in enumerate(rows)
    }
    cases = [(c, 1) for c in protocol["held_out"]] + [(c, 2) for c in protocol["repeated_cases"]]
    for case, rep in cases:
        cells = []
        for method in protocol["methods"]:
            index, r = indexed[method, case, rep]
            s = r["score"]
            label = (
                "S"
                if s["correct_supported"]
                else "A"
                if s["abstention_correct"]
                else "F"
                if not s["completed"]
                else "U"
                if s["unsupported"]
                else "M"
            )
            cells.append(f"[{label} · {r['latency_s']:.2f}s](results/raw.jsonl#L{index})")
        lines.append(f"| {case} / {rep} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "## Reproduction and limits",
        "",
        "- [Protocol](protocol.json), [case/oracle hashes](frozen_manifest.json), [implementation/model/settings/schedule](implementation.json), [all raw runs](results/raw.jsonl), [summary](results/summary.json). No LLM judge is used.",
        "- The first partial attempt was invalidated by an independently discovered Windows UTF-8 reading bug. Its 24 completed rows and one interrupted trace are retained in [invalidated-encoding](invalidated-encoding/README.md). All 56 jobs were restarted after the mechanical correction; prompts, cases, model, scorer and budgets did not change. None of those 24 rows contribute to this table.",
        "- Literal source-line quotations in V2 are attached by the host and validated against captured ranges. This prevents fabricated quotation text; it does not prove that a line supports the proposed mechanism. The verifier uses the same model and can share its errors. Interventions remain controlled synthetic observations, not production repair evidence.",
        "- Small authored synthetic suite, limited repeats, correlated cases and keyword concepts. Automatic correctness can miss paraphrases or accept an explanation containing an unsupported extra assertion. Consult the separate semantic audit before interpreting scores. Proposed next actions are not scored and can be weak.",
        "- `python -m tracemedic.v2.benchmark` verifies frozen files/model and skips existing rows. To reproduce a fresh experiment, use a separate checkout/data directory and preserve published results first. `python scripts/report_v2_benchmark.py` verifies the ledger and regenerates this table without inference.",
        "",
    ]
    (FOLDER / "report.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    start, end = "<!-- V2_RESULTS_START -->", "<!-- V2_RESULTS_END -->"
    table = [
        "All **56/56** scheduled runs are recorded on twelve fresh reserved cases (four methods, fourteen runs each). Same model and top-level budgets; V2 improves contracts, context and tools.",
        "",
        "| Method | Correct automatic outcomes | Median wall time | Model calls across 14 runs |",
        "|---|---:|---:|---:|",
    ]
    for m in summary["methods"]:
        table.append(
            f"| {m['method']} | {m['correct']} / {m['runs']} | {m['median_latency_s']:.2f} s | {m['model_calls']} |"
        )
    table += [
        "",
        "These are automatic synthetic-suite outcomes, not production accuracy or semantic proof. Read the [full V2 comparison](benchmarks/v2/report.md), [semantic audit](benchmarks/v2/semantic_audit.md) and [all raw runs](benchmarks/v2/results/raw.jsonl). The invalidated preliminary attempt is preserved separately. The old V1 score below uses a different set/rubric and is not a V2 improvement baseline.",
    ]
    before, remainder = text.split(start, 1)
    _, after = remainder.split(end, 1)
    readme.write_text(
        before + start + "\n" + "\n".join(table) + "\n" + end + after,
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
