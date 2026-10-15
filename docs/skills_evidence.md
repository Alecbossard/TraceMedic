# Skills and concrete evidence

This is a robotics/AI portfolio learning artifact. These links show implemented and exercised work, not prior mastery or production validation.

| Skill | Implementation | Executed evidence | Limit |
|---|---|---|---|
| LangGraph orchestration | `engine.py`: typed state, conditional edges, bounded role visits | `tests/test_engine.py`; native delegation events in `evidence/demo-real.json` | Constrained policy, small graph |
| Distinct LLM roles | `prompts.py`, `models.py`, separate tools/contexts | Real coordinator/investigator/verifier actions in demo and raw runs | Same model; correlated errors remain |
| Real MCP | `mcp_server.py`, `mcp_client.py`: official SDK and stdio subprocess | `test_mcp.py`, `test_protocol.py`; actual reads/checks and PID separation | Local stdio only |
| Evidence-grounded analysis | Typed snapshots, hypotheses, review, stable IDs | Source citations, checks and complete raw traces | Reference validation does not prove semantic entailment |
| Durable recovery | `AsyncSqliteSaver`, `store.py`, `locking.py`, operation ledger | `test_restart.py` with double; `evidence/real-recovery.json` with real LLM | Separate transactions; uncertain operations are not replayed |
| Error/resource handling | Timeouts/backoff, output/reference validation, allowlist and budgets | Outage, malformed action, cancellation, changed fixture and protocol tests | Finite fixtures; no general Windows OS sandbox claim |
| Real model integration | `provider.py`, `scripts/prepare_model.py` | Native calls, reported tokens, real CLI/browser runs | Only tested local provider/model validated |
| Comparative evaluation | `benchmark.py`, frozen oracle/protocol/manifest | All rows in `benchmarks/results/raw.jsonl`, report and summary | Small synthetic corpus; keyword scoring |
| Product interface | React/TypeScript, FastAPI, timeline, sources and resume | Responsive screenshots and browser QA against actual API | Local polling app, not a multi-user service |
| Reproducibility | Pinned closure/package lock, CI, clean guide | `evidence/clean-install.json`, final commit's Actions | Real-provider tests intentionally opt-in |

## Interview order

Start with a real trace and source citation. Distinguish a supplied report from a newly executed check. Show delegation, review, and an unresolved/rejected outcome. Kill/resume the worker and explain the uncertain-operation window. Finish with the simpler single-agent comparison, including latency/call overhead and failures. Use artifacts to support claims instead of presenting a technology list as proof of mastery.
