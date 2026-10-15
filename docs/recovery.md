# Persistence, cancellation and restart recovery

Keep both `audit.db` and `checkpoints.db` in the selected data directory. A run uses its ID as the LangGraph `thread_id`. The audit database contains captured evidence, measured events and the operation ledger. Copying a JSON report alone does not reproduce resumable checkpoints.

## Reproduce a boundary pause

```powershell
.\.venv\Scripts\tracemedic.exe run case-01 --pause-after 4
# Exit the CLI completely; use the printed ID in a new process.
.\.venv\Scripts\tracemedic.exe resume <run-id>
.\.venv\Scripts\tracemedic.exe show <run-id>
```

The event trail contains `resumed` and any reused model/tool decision. Stable evidence IDs refer to the same captured bytes. `--pause-after` is a deliberate checkpoint pause, not the hard-crash proof below.

## Reproduce the hard-crash proof

```powershell
.\.venv\Scripts\python.exe scripts/prove_recovery.py
```

The script starts a real LLM CLI worker, waits for a real fixture-check result, hard-kills the process, then invokes `resume` in a new process with the same ID and data directory. It asserts completion, retention of all prior evidence snapshots, and one fixture execution ledger row/tool-result event. The committed [real proof](evidence/real-recovery.json) records actual process IDs, provider-reported usage, events and the resumed diagnosis. The ordinary CI test `tests/test_restart.py` performs a similar abrupt kill with an explicitly deterministic provider; it is a separate validation class.

This proves the tested crash point, not every machine/power-failure timing. The audit ledger and LangGraph checkpoint are separate transactions. If the graph re-enters an already completed operation, it reuses the ledger. If a fixture was claimed but its completion is unknown, `run_check` returns `indeterminate` rather than executing it again. The test suite explicitly exercises that window. Fixture execution is read-only/pure; no production repair is attempted.

## Cancellation and errors

The browser's Cancel control sets a durable request flag. The current model/tool action finishes, its checkpoint is written, and the runner stops with `cancelled`. Resume clears the flag and advances from that saved action boundary. The real browser trace includes cancellation and resumption, not an animated placeholder.

A temporary provider outage receives at most three attempts with bounded backoff and then becomes `error`, preserving a resumable next action. Malformed/unauthorized actions are rejected with feedback; three consecutive rejections become `failed`. `budget_exhausted` and `failed` are terminal and require a new run. They are not reported as successful diagnoses or correct benchmark abstentions. A tool that is unavailable returns a typed error/unavailable record; the agent must either gather other evidence or conclude insufficient.

OS locks stop two processes from executing one investigation concurrently. After a hard crash, a stale `running` UI status is changed to interrupted on API startup. The checkpoint and lock are the source of execution truth. Active CLI workers still hold their OS lock even if an API restart relabels their presentation status.

Model calls have no external write effect, but a crash during inference can consume tokens without a recorded response. Such usage stays incomplete. The system does not claim exactly-once provider billing, universal exactly-once execution, or atomicity across both SQLite files.
