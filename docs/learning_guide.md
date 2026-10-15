# Learn, modify and explain TraceMedic

## Follow one investigation

Run `tracemedic run case-01`, then `tracemedic show <id>`. Match native actions to `Engine.node`: coordinator delegation; MCP reads and source snapshots; `submit_findings`; verifier check and verdicts; final synthesis or an explicit system stop. Predict which data each role should see, then inspect `Engine.context`. The coordinator receives typed findings and an evidence index, not the investigator's entire history.

**Explain aloud:** Why do three prompts alone fail to demonstrate orchestration? Which decisions came from the LLM, and which are host policy? Why reserve synthesis calls? Avoid describing the constrained policy as learned planning.

## Inspect the protocol boundary

Run `tracemedic tools case-01`. Compare discovered JSON schemas and the server PID to the caller. The agent does not call server Python functions directly: the official client sends JSON-RPC to another process. Run `pytest -q tests/test_mcp.py tests/test_protocol.py` and inspect why an oracle path is denied even if a log tells the model to open it. Content visibility grants no permission.

**Exercise:** Add a read-only `summarize_log_levels` tool returning literal counts and source lines. Keep incident binding host-controlled, limit file size/output, return a typed result, and treat text as data. Add a subprocess discovery/call test and denied input. Update role permissions and docs. Do not expose a general shell.

## Understand checkpoint versus audit durability

Pause after four steps, exit completely and resume. Then run `scripts/prove_recovery.py` for an abrupt kill. Compare graph state in `checkpoints.db` with evidence/events/operations in `audit.db`: what runs next versus what happened.

Draw crash windows before claim, after claim/before completion, and after completion/before checkpoint. An uncertain fixture is not rerun; a completed operation is reused. OS locks release when a process dies; stale lock files alone mean nothing.

**Explain aloud:** Why is universal exactly-once execution not promised? Why can token usage be incomplete after a crash? Which effects are protected? Name the tested crash point and its limits.

## Challenge the diagnosis

Read a hypothesis and its source before the verdict. Does the source prove a mechanism, show only a symptom, or suggest a possibility? Run ambiguous development case `case-19` or `case-21`. Compare a completed insufficient conclusion with a budget stop. The schema rejects invented IDs, not all invalid reasoning. A fixture does not prove production state, and same-model agreement is not an independent check.

**Exercise:** In a new corpus/protocol version, add contradictory evidence and an alternative hypothesis. Record whether the verifier rejects, asks for more information, or overstates a finding. Preserve failures. Do not tune the published held-out set under its old label.

## Reproduce the comparison

Read protocol, oracle, implementation hashes, raw rows and report. Compare correctness, unsupported conclusions, appropriate abstention, completed runs, tool success, latency, calls and reported tokens. Both LLM methods have the same model and top-level budgets; contexts and policy overhead differ.

The evaluator matches expected concepts and requires citations plus execution. It is reproducible but imperfect: keywords can occur without entailment, and a valid paraphrase can miss a keyword. Inspect disputed rows. Two repeated cases probe variability; they do not establish confidence intervals or calibrated probabilities.

**Explain aloud:** When does one agent suffice? What review evidence do three roles add, at what cost? If the multi-agent method loses, what did the experiment teach? Separate measured overhead from speculative production benefit.

## Verify your changes

Schema changes need reference/validation tests; MCP tools need actual subprocess calls and denied inputs; recovery changes need process kill/resume; UI changes need desktop/mobile browser inspection. Real-provider tests remain opt-in and explicitly labeled. Update `PROJECT_STATUS.md` with evidence and remaining work so a later session can resume honestly.
