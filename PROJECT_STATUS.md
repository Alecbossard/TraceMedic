# TraceMedic project status

Updated: 2026-10-15. This file is the resumption entry point.

## Current state

- Inspected the existing checkout: empty Git repository, no user files or commits.
- Remote `https://github.com/Alecbossard/TraceMedic.git` now contains the delivered project; default branch is `codex/tracemedic`.
- V1 delivery: `aba50e7` on `codex/tracemedic`. Active V2 branch: `codex/v2-evidence`; Windows, Python 3.13.1, Node 24.11.0, RTX 4060 Laptop 8 GB, 16 GB RAM.
- Repository-local Ollama 0.40.4 and Qwen3 4B Instruct Q4_K_M are running. Alias `tracemedic-qwen3:4b` uses an explicit template that serializes native tools as JSON.
- Official LangGraph persistence/durable execution, MCP SDK and Ollama tool/structured-output documentation consulted before implementation.

## Completion evidence

- Real CLI multi-agent investigation: `real-dev-09`, completed with supported diagnosis, 14 model calls, 9 tool calls, provider-reported tokens.
- Real single-agent development case: `real-dev-single-02`, completed with supported diagnosis; ambiguous development case-19 completed insufficient.
- Browser run `16f5146c-d649-40e4-8baa-fce5381c373f`: actual model, cancelled then resumed and completed. Export: `docs/evidence/demo-real.json`.
- MCP discovery, schema errors, forbidden paths, real reads and fixture execution tested through stdio subprocesses.
- Real hard kill and new-process resume: `docs/evidence/real-recovery.json`; same run ID, all prior evidence preserved, one fixture execution record and one corresponding tool-result event.
- Browser inspected at 1440, 900 and 390 pixels; captures in `docs/evidence`; no browser JS errors or horizontal overflow in checks.
- Fresh Git archive/new Python environment/npm ci verified on commit `5437a83`: 18 tests passed; ruff, formatting, pip check, frontend build and npm audit passed. The opt-in real test then ran from that clean environment: **1 passed**, with the actual local model. Evidence: `docs/evidence/clean-install.json`.
- Additional actual HTTP malformed-response/timeout and MCP-process-loss tests pass. Latest complete local suite: **21 passed, one opt-in real test skipped**; the separately executed real test passed as stated above.
- Frozen comparison finished: **42/42 runs**, 14 per method. Correct automatic outcomes: deterministic **5/14**, single **10/14**, multi **9/14**. Median wall time: **1.841 / 28.236 / 39.463 seconds**. All raw results and failures are in `benchmarks/results/raw.jsonl`; report and scoring caveats are published. No held-out prompt tuning occurred.
- GitHub push is authorized and working. Verified CI run `38787268218` on `5437a83` passed all four jobs: Windows backend, Linux backend, frontend and browser replay. Delivery status for the current HEAD is tracked by [GitHub Actions](https://github.com/Alecbossard/TraceMedic/actions/workflows/ci.yml), and checked at handoff.

## Known limits

- Shipped synthetic corpus only; no general incident-directory ingestion or production-resource checks.
- Semantic unsupported claims can survive typed/reference guards; keyword evaluation has false negatives and does not prove entailment. Multi-agent did not outperform the simpler agent here.
- One transient provider-unavailable retry leaves one run's token total incomplete. Known usage is retained, missing usage is not estimated. Monetary/hardware costs are unmeasured.
- Cooperative cancellation, separate SQLite transactions, and explicit indeterminate fixture operations; no universal exactly-once or Windows OS memory-sandbox claim.

## Next actions

User requested V2. See `docs/v2_proposal.md`: causal records with literal citations, bounded bundle reads and controlled JSON interventions, compact contexts, versioned runners/UI. Preserve all V1 frozen inputs, code and 42 results. Twelve new reserved cases and the 56-run comparison protocol are frozen in `benchmarks/v2/` before V2 prompt development. All original cases are now development/regression data for V2. Next: implement V2 MCP/contracts/runner, test recovery, tune only on original cases, freeze implementation, execute every reserved trial, inspect UI and publish results/CI. No V2 performance result exists yet.

The local UI uses `data/app` for its real demo trace. Restart it with `python -m tracemedic.cli --data-dir data/app serve`; open `http://127.0.0.1:8000`. The recorded completed trace can also be imported into another selected data directory with `scripts/import_demo.py`. The `.runtime/` model/runtime and local databases remain intentionally untracked.
