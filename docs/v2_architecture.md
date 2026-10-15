# V2: causal records and constrained synthesis

V2 is a versioned workflow, not a new framework. `v2/engine.py` subclasses the V1 engine's lock/termination helpers but has its own state schema, prompts and persisted graph. `factory.py` selects the saved version on resume. Records without `engine_version` remain V1. The original V1 engine, provider, prompts, contracts and evaluator still match their published hashes.

## Information contract

Investigator submits one focused record per round: captured **trigger → mechanism → observed effect**, line references, next discriminating check and unknowns. At most two investigation rounds can add/refine records. A proposal requires a code line and a second file; missing source produces no causal proposal. The model selects short source-line handles such as `E2:L3`. Host code validates the captured range and attaches up to 240 characters of exact source text (truncation is recorded). The inspector opens the full captured line. The model cannot supply quotation text.

The verifier reviews that same record, with its own context and execution tools. It can reject it, leave it unresolved or request a targeted second investigation. Confirmation requires cited source plus another file and a cited **reproduced baseline** check. Passed, unavailable and indeterminate checks cannot satisfy this guard. An invalid attempt to confirm with those checks is recorded as `confirmation_blocked` and applied as unresolved. Unknown IDs, invalid line ranges and unauthorized tool calls remain hard errors.

Coordinator has no file tools. It defines tasks and chooses continuation or final selection. `finish` has no free-form factual summary field: the displayed finding is assembled from selected confirmed records. This prevents a new explanation from being introduced at the final summary step. It does **not** establish semantic entailment of the original record. Proposed actions, unknowns and verifier reasons remain LLM text and can still be weak or wrong. There are no confidence percentages.

## Context and inference

Persistent maps translate short `E1`, `H1`, `C1` aliases into original hash-based IDs. Assignment order is checkpointed and survives restart. Excerpts are sent in the source collection, with line handles; recent action records contain metadata rather than copies of excerpts. Coordinator receives source metadata and causal records. Each role has its own prompt, tools and context; no transcript is blindly copied between roles.

Ollama uses native function calling to select and invoke MCP tools and whenever a choice of actions is available. If a phase permits exactly one control contract, V2 uses Ollama JSON-schema decoding, with the schema included in the prompt. Runtime Pydantic/reference checks still apply. Every decision is a real model call counted against the same budget; no rules infer the diagnosis. OpenAI-compatible endpoints retain native function calling throughout. This is constrained orchestration, with explicit phase gates, not unrestricted autonomy.

## Seven real MCP tools

The original five tools remain available through the V1 adapter. V2 adds:

| Tool | Boundary |
|---|---|
| `read_bundle` | 1–5 distinct allowlisted filenames, ≤40 lines each / 200 total, ≤64 KB per file; explicit per-file errors and truncation. Follow-up reads can inspect truncated content. |
| `run_experiment` | 1–2 replacements of existing `/settings/...` or `/input/...` JSON values; ≤4 nested path levels, 4096 serialized bytes, bounded replacement depth/size/numbers, at most two distinct experiments per run. |

Experiment worker runs in a new `python -I` subprocess after validating every fixture file against shipped hashes. It evaluates baseline and trial in separate fresh namespaces, keeping source and expected result unchanged. It writes no incident files. The 3-second wall timeout and output bounds apply; Unix also has CPU/address-space limits. Windows has no claimed OS memory sandbox. Only authored trusted fixtures execute, never uploaded customer code or model-generated source. A replacement that makes the test pass is a controlled observation, not an applied repair or proof of production causality.

Tool operation keys are adapter-owned, not model-controlled. Baseline and experiment executions use a durable claim/result ledger. Completed results are reused; an interrupted claimed operation returns indeterminate. The experiment cap is claimed under a SQLite write transaction. Audit and graph checkpoint transactions remain separate; there is no universal exactly-once claim.

## Reproduce

```powershell
python -m tracemedic.cli --workflow v2 run case-01
python -m tracemedic.cli --workflow v1 run case-01
python -m tracemedic.cli resume <saved-id>
python scripts/prove_recovery.py --workflow v2
python scripts/import_demo.py --workflow v2
```

The UI labels the workflow, displays causal fields and exact source citations, highlights selected lines, and distinguishes baseline checks from isolated trials. The benchmark selector preserves both studies. See [the V2 proposal](v2_proposal.md) for primary research sources and [the frozen comparison](../benchmarks/v2/protocol.json). The old 24 cases are development/regression data for V2; the new 12 cases are reserved for the new study.
