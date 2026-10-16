# V2 comparison: causal records and compact tools

All **56/56** predeclared outcomes are published: 12 new reserved cases, one execution each, plus a second execution of sample-02 and sample-11, for each of four methods. All original 24 cases were seen development/regression data for V2. No reserved-response prompt tuning occurred.

Same Qwen3 4B Instruct Q4_K_M alias/digest, seed 17, temperature 0, 18 model calls, 14 tool calls, 1200 generated tokens per call and 8192-token context. All inference was serial on the same Windows/RTX 4060 Laptop machine. Order was seeded and interleaved; local cache/system load still affect timings. V1 retains its original engine/prompts/provider and five tools. Both V2 methods share seven tools and schema-decoded control phases. This compares complete workflows; only the two V2 variants isolate agent-count differences.

## Automatic outcomes

| Method | Correct total | Supported correct | Correct abstentions | Unsupported by rubric | Completed | Median wall time | Model calls | Tool successes/calls |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| deterministic | 3/14 | 0 | 3 | 0 | 14 | 1.917s | 0 | 82/84 |
| v1-multi | 7/14 | 5 | 2 | 3 | 13 | 37.424s | 200 | 118/120 |
| v2-single | 6/14 | 3 | 3 | 7 | 13 | 11.528s | 73 | 27/27 |
| v2-multi | 8/14 | 5 | 3 | 2 | 14 | 14.011s | 99 | 28/28 |

These counts use the same frozen scorer for all four methods. Supported outcomes require all mechanism concept groups in the final explanation, valid captured source references, a selected confirmed hypothesis and a reproduced baseline. Explicit abstention is correct only on ambiguous cases. Controlled failures and budget stops are incorrect. The rubric does not require identifier repetition inside both a hypothesis and final paragraph as V1's older scorer did; **do not compare these counts to the old 9/14**.

## Usage and guard activity

| Method | Reported input tokens | Reported output tokens | Invalid actions | Blocked confirmations |
|---|---:|---:|---:|---:|
| deterministic | 0 | 0 | 0 | 0 |
| v1-multi | incomplete (known 437,805) | incomplete (known 23,149) | 4 | 0 |
| v2-single | 107,706 | 6,884 | 7 | 1 |
| v2-multi | 129,409 | 7,974 | 1 | 1 |

Tokens are provider-reported. Missing usage is never estimated. Costs, energy and hardware utilization are unmeasured. Tool success means a typed tool result with `ok=true`; a partial bundle can legitimately report a missing file. Tool transport failures and schema rejections remain in the event ledger.

## Every scheduled case

S = correct supported, A = correct abstention, U = supported but rejected by rubric, M = completed but missed expected outcome, F = system stop/error. Values include measured wall seconds. Each cell links to the corresponding raw ledger row.

| Case / repetition | deterministic | v1-multi | v2-single | v2-multi |
|---|---|---|---|---|
| sample-01 / 1 | [M · 1.97s](results/raw.jsonl#L8) | [S · 38.03s](results/raw.jsonl#L12) | [U · 11.88s](results/raw.jsonl#L30) | [S · 13.93s](results/raw.jsonl#L46) |
| sample-02 / 1 | [M · 2.44s](results/raw.jsonl#L43) | [M · 50.44s](results/raw.jsonl#L42) | [U · 11.87s](results/raw.jsonl#L15) | [M · 13.91s](results/raw.jsonl#L4) |
| sample-03 / 1 | [M · 2.01s](results/raw.jsonl#L20) | [S · 36.63s](results/raw.jsonl#L39) | [S · 18.90s](results/raw.jsonl#L5) | [M · 15.62s](results/raw.jsonl#L28) |
| sample-04 / 1 | [M · 1.90s](results/raw.jsonl#L34) | [S · 48.20s](results/raw.jsonl#L45) | [S · 13.28s](results/raw.jsonl#L6) | [S · 13.96s](results/raw.jsonl#L49) |
| sample-05 / 1 | [M · 1.96s](results/raw.jsonl#L31) | [S · 45.38s](results/raw.jsonl#L51) | [U · 10.62s](results/raw.jsonl#L38) | [U · 14.06s](results/raw.jsonl#L33) |
| sample-06 / 1 | [M · 1.85s](results/raw.jsonl#L9) | [S · 52.68s](results/raw.jsonl#L53) | [F · 12.61s](results/raw.jsonl#L56) | [S · 14.12s](results/raw.jsonl#L2) |
| sample-07 / 1 | [M · 1.92s](results/raw.jsonl#L24) | [U · 36.59s](results/raw.jsonl#L37) | [U · 14.83s](results/raw.jsonl#L47) | [M · 15.02s](results/raw.jsonl#L48) |
| sample-08 / 1 | [M · 1.97s](results/raw.jsonl#L44) | [M · 38.66s](results/raw.jsonl#L25) | [S · 10.54s](results/raw.jsonl#L26) | [S · 13.42s](results/raw.jsonl#L1) |
| sample-09 / 1 | [M · 1.91s](results/raw.jsonl#L35) | [U · 36.50s](results/raw.jsonl#L29) | [U · 10.69s](results/raw.jsonl#L7) | [S · 14.41s](results/raw.jsonl#L14) |
| sample-10 / 1 | [M · 1.91s](results/raw.jsonl#L19) | [U · 34.59s](results/raw.jsonl#L52) | [U · 13.77s](results/raw.jsonl#L10) | [U · 17.02s](results/raw.jsonl#L54) |
| sample-11 / 1 | [A · 1.84s](results/raw.jsonl#L23) | [F · 34.78s](results/raw.jsonl#L41) | [A · 9.05s](results/raw.jsonl#L13) | [A · 11.21s](results/raw.jsonl#L17) |
| sample-12 / 1 | [A · 1.91s](results/raw.jsonl#L50) | [A · 43.02s](results/raw.jsonl#L36) | [A · 11.19s](results/raw.jsonl#L22) | [A · 13.25s](results/raw.jsonl#L11) |
| sample-02 / 2 | [M · 1.93s](results/raw.jsonl#L32) | [M · 36.82s](results/raw.jsonl#L55) | [U · 11.01s](results/raw.jsonl#L3) | [M · 16.92s](results/raw.jsonl#L40) |
| sample-11 / 2 | [A · 1.91s](results/raw.jsonl#L18) | [A · 35.30s](results/raw.jsonl#L27) | [A · 8.86s](results/raw.jsonl#L16) | [A · 10.30s](results/raw.jsonl#L21) |

## Reproduction and limits

- [Protocol](protocol.json), [case/oracle hashes](frozen_manifest.json), [implementation/model/settings/schedule](implementation.json), [all raw runs](results/raw.jsonl), [summary](results/summary.json). No LLM judge is used.
- The first partial attempt was invalidated by an independently discovered Windows UTF-8 reading bug. Its 24 completed rows and one interrupted trace are retained in [invalidated-encoding](invalidated-encoding/README.md). All 56 jobs were restarted after the mechanical correction; prompts, cases, model, scorer and budgets did not change. None of those 24 rows contribute to this table.
- Literal source-line quotations in V2 are attached by the host and validated against captured ranges. This prevents fabricated quotation text; it does not prove that a line supports the proposed mechanism. The verifier uses the same model and can share its errors. Interventions remain controlled synthetic observations, not production repair evidence.
- Small authored synthetic suite, limited repeats, correlated cases and keyword concepts. Automatic correctness can miss paraphrases or accept an explanation containing an unsupported extra assertion. Consult the separate semantic audit before interpreting scores. Proposed next actions are not scored and can be weak.
- `python -m tracemedic.v2.benchmark` verifies frozen files/model and skips existing rows. To reproduce a fresh experiment, use a separate checkout/data directory and preserve published results first. `python scripts/report_v2_benchmark.py` verifies the ledger and regenerates this table without inference.
