# Reading the score alongside the trace

The v1 scores remain frozen. These observations explain limits and failures without relabeling selected outcomes as successes. They are source/trace inspection by the development agent, not independent expert adjudication.

## A plausible final paragraph is not enough

In case-14, the multi-agent summary identifies `max_attempts=1` and two transient failures. Its confirmed typed hypothesis says only that the report shows a TimeoutError and an expected/observed mismatch. That is a symptom, not the expected retry mechanism. The scorer rejects it because the causal hypothesis lacks the required concepts. A verifier can confirm a well-cited symptom while the coordinator supplies a more specific explanation. Structural schemas do not prevent this semantic gap.

Case-22's single-agent run has a similar generic confirmed hypothesis about a validation failure. Inspect source, final prose and typed hypothesis rather than treating a shared status as proof of a causal explanation.

## The keyword score can be too strict

In case-16, the single-agent diagnosis explains that `service-db` is absent and `service_db` is the supplied mapping. Its confirmed hypothesis states a general missing-entry mechanism without both identifiers. The frozen concept-group rule fails it. This is a plausible false negative of scoring. The published score stays unchanged; it is not a calibrated count of all semantically unsupported prose.

The multi-agent result for the same case introduces an inaccurate **case-sensitive** explanation and confuses which file supplies the registry. The actual difference is a hyphen versus an underscore; both strings are lowercase. Correct citations and a reproduced failure do not establish every sentence. A revised evaluator should add independent claim-level adjudication under a newly frozen protocol.

## Safe uncertainty can miss the expected mechanism

In case-04, the multi-agent system abstains because it lacks pre-update source/interface artifacts. Those would be needed to prove historical removal of a method, but not to establish the current fixture's call to a nonexistent method. It conflates the current mechanism with the narrative's history and counts as a missed diagnosis under this task.

## Guarded failure differs from appropriate abstention

In case-20's first multi-agent run, the verifier repeatedly attempts confirmation despite unavailable independent reproduction. The host rejects it three times and terminates `failed`. This demonstrates controlled error handling; it is **not** a completed, correct insufficient-evidence conclusion. Both repetitions remain in the report/raw file.

These examples support reading traces and limits, not selectively increasing scores after evaluation. The experiment exposes coordination overhead and semantic failures even when three roles do not outperform one agent.
