# TraceMedic project status

Updated: 2026-10-16. This file is the resumption entry point.

## Current state

- UI refresh requested after the V2 delivery: graphite navigation, self-hosted Geist typography, compact incident rail, Overview/Activity/Sources views, immutable source viewer, keyboard command menu, filtered history and interactive benchmark comparison. Motion and Radix are integrated; reduced motion, focus management and mobile navigation are covered. See `docs/ui_refresh.md`. New artifacts are isolated in `docs/evidence/ui-refresh/`; historical evidence and benchmark files are preserved.
- UI validation: production build and dependency audit passed, original V1 replay passed, 11 automated accessibility views and 10 responsive overflow checks passed. Fresh real browser run `05b6e162-4d7b-4e8b-8e01-e29ece068e57` cancelled/resumed/completed through the redesigned UI with no page errors; full proof is in `docs/evidence/ui-refresh/real-session/`. An earlier completed run whose capture hit a transition-timing assertion is retained too. Current-head hosted checks remain the delivery source of truth below.
- Cold-start regression: a cold-load exit-transition race exposed by CI retained the empty panel after run data loaded. Entry transitions now render data immediately. A test holds the animation feature download and verifies deep-link finding/source navigation before releasing it; Edge and Chromium pass. Initial incident/history/result requests no longer wait for model health. Browser workflow artifacts include diagnostics for failed runs.
- Reserved suite/protocol were frozen first at `cb6a5b4`. Initial implementation `0eecb43` was mechanically corrected after visual/portability QA found Windows cp1252 reads and UI mojibake. All 24 completed preliminary outcomes plus the interrupted trace are preserved in `benchmarks/v2/invalidated-encoding/`; they are excluded from final results. Prompts/model/cases/scorer/settings did not change. A regression test now checks isolated-process UTF-8 decoding.
- Corrected implementation frozen at `f56fc7b`: **56/56 scheduled runs complete**, no prompt/model/scorer changes. Rules **3/14**, V1 multi **7/14**, V2 single **6/14**, V2 multi **8/14** automatic outcomes. Median wall seconds **1.917 / 37.424 / 11.528 / 14.011**; model calls **0 / 200 / 73 / 99**. All raw outcomes, failures and a post hoc semantic audit are in `benchmarks/v2/`. The audit identifies false positives; semantic reliability improvement is not established.
- V2 multi completed all 14 runs and correctly abstained on all three ambiguous trials. V2 single failed one citation-validation sequence. One V1 provider retry leaves its token aggregate incomplete. No benchmark run selected the optional experiment tool; its separate real native MCP integration passed with reproduced baseline and passing trial (`docs/evidence/v2/real-experiment.json`).
- Actual V2 browser run `22ccf4b6-449c-4c56-9442-dbec22e91d60`: cancelled/resumed same ID, all three real roles, source-line highlighting, no JS errors or overflow at 1440/900/390px. Fresh inference proof and separate replay metadata are in `docs/evidence/v2/`. The first browser trace is also preserved. V1 replay compatibility passes.
- Fresh Git archive/new environment validation on `d0d8698`: **37 passed, 2 opt-in real skipped**; Ruff checks/formatting, pip check, npm ci/build/audit and both recorded-trace imports passed. The actual V2 model test then passed from that fresh environment (**1 passed, 1 deselected in 22.97s**). The initial attempt found the external provider stopped after session interruption; its failure is retained alongside the successful retry and verified model digest in `docs/evidence/v2/clean-install.json`.
- Real V2 kill/new-process resume completed with five snapshots and aliases preserved, one baseline execution/event: `docs/evidence/v2/real-recovery.json`.

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
- Semantic unsupported claims can survive typed/reference guards; keyword evaluation has false positives and false negatives and does not prove entailment. V1's original multi-agent study scored below its single agent; the new V2 automatic scores do not establish a semantic reliability improvement. The author-assisted semantic audit is not an independent blind review.
- One transient provider-unavailable retry leaves one run's token total incomplete. Known usage is retained, missing usage is not estimated. Monetary/hardware costs are unmeasured.
- Cooperative cancellation, separate SQLite transactions, and explicit indeterminate fixture operations; no universal exactly-once or Windows OS memory-sandbox claim.

## Delivery and review

The requested V2 implementation and local validation are complete. Review branch: `codex/v2-evidence`, targeting the preserved V1 default `codex/tracemedic`; V1 is also tagged `v0.1.0`. See `docs/v2_proposal.md`, `docs/v2_architecture.md`, the full benchmark and semantic audit. Current-head hosted checks are tracked by [GitHub Actions](https://github.com/Alecbossard/TraceMedic/actions/workflows/ci.yml) and checked at handoff. Review the causal explanations and limitations before extending beyond the shipped synthetic corpus. Development candidates (including failures) remain in `docs/evidence/v2-development*.json`; their subset is not a new accuracy estimate. Recommendations remain unvalidated model text; exact citations do not establish entailment.

The local UI uses `data/app`; server PID 26892 and portable Ollama PID 8044 at the last restart. Restart the UI with `python -m tracemedic.cli --data-dir data/app serve`; open `http://127.0.0.1:8000/?run=05b6e162-4d7b-4e8b-8e01-e29ece068e57`. Import the completed V2 audit elsewhere with `scripts/import_demo.py --workflow v2` (not resumable checkpoints). The `.runtime/` model/runtime and local databases remain intentionally untracked.
