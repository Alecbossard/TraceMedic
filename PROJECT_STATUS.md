# TraceMedic project status

Updated: 2026-10-15. This file is the resumption entry point.

## Current state

- Inspected the existing checkout: empty Git repository, no user files or commits.
- Remote `https://github.com/Alecbossard/TraceMedic.git` is reachable and empty.
- Working branch: `codex/tracemedic`; Windows, Python 3.13.1, Node 24.11.0, RTX 4060 Laptop 8 GB, 16 GB RAM.
- Repository-local Ollama 0.40.4 and Qwen3 4B Instruct Q4_K_M are running. Alias `tracemedic-qwen3:4b` uses an explicit template that serializes native tools as JSON.
- Official LangGraph persistence/durable execution, MCP SDK and Ollama tool/structured-output documentation consulted before implementation.

## Completion evidence

- Real CLI multi-agent investigation: `real-dev-09`, completed with supported diagnosis, 14 model calls, 9 tool calls, provider-reported tokens.
- Real single-agent development case: `real-dev-single-02`, completed with supported diagnosis; ambiguous development case-19 completed insufficient.
- Browser run `16f5146c-d649-40e4-8baa-fce5381c373f`: actual model, cancelled then resumed and completed. Export: `docs/evidence/demo-real.json`.
- MCP discovery, schema errors, forbidden paths, real reads and fixture execution tested through stdio subprocesses.
- Real hard kill and new-process resume: `docs/evidence/real-recovery.json`; same run ID, all prior evidence preserved, one fixture execution record and one corresponding tool-result event.
- Browser inspected at 1440, 900 and 390 pixels; captures in `docs/evidence`; no browser JS errors or horizontal overflow in checks.
- Frontend build and npm audit passed. Latest full test result pending collection (earlier 14 fast tests passed; more protocol/scoring tests added).
- Frozen benchmark running in `.runtime/benchmark-progress.jsonl`; raw results append to `benchmarks/results/raw.jsonl`. No held-out prompt tuning is allowed.
- First implementation commit `cbd33ee`; clean-install verification, final documentation, results report and GitHub delivery pending.

## Next actions

1. Finish the frozen benchmark without tuning against its results.
2. Canonicalize generated metadata to LF for identical Windows/Linux checkouts; incident source bytes remain unchanged.
3. Finish architecture, model/recovery/reproduction, portfolio and learning documentation.
4. Verify install in a clean environment, rerun required checks, publish raw results, commit and push, inspect CI.
