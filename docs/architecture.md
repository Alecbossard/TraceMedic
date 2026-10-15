# Architecture and reasoning boundaries

This page documents the preserved **V1 reference workflow**. The default **V2** has [a separate contract, inference and tool description](v2_architecture.md). Saved V1 records continue to use this runner.

TraceMedic separates orchestration, model decisions, protocol transport and durable records. The graph is intentionally small enough to explain and modify in an interview.

## State graph

`engine.py` builds a real `StateGraph` with coordinator, investigator, verifier and single-agent nodes. Each visit performs one LLM decision. Conditional edges use the next role from the validated decision. A node is not an entire fixed prompt pipeline: the investigator can select different reads/searches, the verifier can reject hypotheses or request another round, and the coordinator can delegate targeted follow-up tasks or synthesize. One invocation interrupts after a node and waits for synchronous checkpoint durability before the outer runner advances.

The policy bounds this freedom. Before a final multi-agent conclusion, both specialists must be visited. The first delegation targets investigation; after initial findings the first review is mandatory. The investigator has six collection decisions before a findings submission is required. The verifier has three tool decisions before a review is required. Near the overall call limit, the coordinator's allowed action becomes synthesis. The single-agent comparator has six initial collection decisions and then records findings, check, review and synthesis in the same context. These policies prevent a small model from spending the entire budget rereading files. They are visible implementation constraints, not learned planning abilities.

| Role | Receives | Tool permissions | Output contract |
|---|---|---|---|
| Coordinator | Incident summary, typed findings/review, evidence index, checks, delegation history | `delegate`, `finish` only | `Delegation`, `Diagnostic` |
| Investigator | Current task, saved source snapshots, own tool observations and review feedback | `list_files`, `read_file`, `search_trace`, `get_test_report`, `submit_findings` | `Findings` with proposed `HypothesisDraft`s |
| Verifier | Hypotheses, current task, saved source snapshots, check records, own observations | `read_file`, `get_test_report`, `run_check`, `submit_review` | `Review` / `Verdict` (confirmed, rejected, unresolved) |
| Single comparator | One context for all responsibilities | Union of incident tools and output contracts | Same findings/review/diagnosis schemas |

All three multi-agent roles are actual LLM calls using native function calling. The MCP schemas are discovered at runtime and exposed through the provider adapter. Control schemas are derived from Pydantic; nested `$ref`s are inlined for Ollama compatibility. Available evidence/hypothesis/check IDs are listed in the schema. Runtime validation remains authoritative even when a model ignores those constraints.

## Shared data and evidence

Roles do not exchange entire conversation histories. They share JSON contracts with stable IDs. Evidence IDs hash incident ID, file path, file hash and captured line range. Hypothesis IDs hash claims; check IDs include the run's operation key. A captured evidence object stores exact text, line numbers and SHA-256. The coordinator sees the evidence index rather than raw source payloads.

The graph stores proposed and reviewed hypotheses, tool observations, checks, delegations, role visits, counters and final diagnosis. The audit database keeps source snapshots and events independently, including native model actions, measured usage, errors and cache reuse. Tool output is data; injected role text is never promoted into a system message.

Structural support guards reject unknown evidence IDs, unknown hypotheses/checks, a confirmation without a completed independent check, or a supported final diagnosis without a confirmed selected hypothesis. They do not prove that prose semantically follows from a cited source. The verifier can still be wrong. This is why the UI exposes source text and the benchmark uses a separate oracle rather than verifier agreement.

## Real MCP boundary

The official `mcp==2.3.0` SDK runs a stdio server in a separate Python process. A `Client(StdioServerParameters(...))` discovers and calls its tools through JSON-RPC. The current SDK's protocol revision does not require the older session initialization handshake. `tests/test_protocol.py` sends an unknown JSON-RPC method and checks the actual `-32601` response.

The subprocess is bound to one incident using host-supplied environment variables. The model cannot change the incident, database, executable or operation key. Only five neutral file names are readable. Reads are limited to 100 lines and 64 KB files; literal search returns at most 12 excerpts. Paths outside that allowlist and symlinks are rejected. The oracle directory is not a server resource.

`run_check` starts a stdlib-only worker with a fixed executable and fixed argument structure, a 3-second timeout, immutable fixture hashes, 64 KB input-file limits and a 32 KB output limit. The 21 executable fixture programs contain finite operations and no network/subprocess calls. Linux also sets 2-second CPU and 256 MB address-space limits. Windows uses the time/input/output and immutable-program bounds; it does not claim an OS memory sandbox. A supplied report is evidence, not a new execution.

## Durability and failure semantics

The graph uses `AsyncSqliteSaver` with a durable `thread_id` equal to the investigation ID. A separate WAL-mode SQLite audit ledger caches completed model decisions and tool results. A pure read can be replayed safely; saved results are reused. A fixture operation is atomically claimed before execution. If it was completed, subsequent requests return its saved result; if it was interrupted in the uncertain window, it is not executed again and returns `indeterminate`.

OS-backed file locks prevent concurrent CLI/API runners for one ID and release on process death. Store `running` can be stale after a crash; it is a presentation status, not the concurrency authority. The runner resumes from the graph checkpoint and reconciles the audit projection at the next boundary. A process dying after a remote request but before recording its response can consume unreported tokens; the journal marks usage incomplete rather than estimating it.

Retries are bounded to three provider attempts with 0.5/1-second backoff, within the global call budget. Invalid decisions/tool exceptions generate feedback and stop after three consecutive failures. A temporary model outage is resumable. Call, tool, role-turn and graph-step limits end explicitly. Cooperative cancellation and graceful process interruption preserve the next graph action. See `docs/recovery.md` for executable proofs and edge cases.

## Local application

FastAPI serves JSON endpoints and the built React/TypeScript UI. The UI polls persisted run data every 1.2 seconds. Activity indicators derive from actual running status and pending model attempts. Metrics are counts from recorded events, provider token fields and finished runner-session durations. There are no calibrated confidence probabilities or synthetic progress percentages. The API has no automatic repair, external messaging or general shell endpoint.
