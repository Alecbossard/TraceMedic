# Frozen benchmark report — v1

Recorded runs: **42 / 42 planned**. Status: **complete**. The raw file contains every scheduled result recorded so far, including failures. No held-out prompts were tuned after the implementation freeze.

## Setup and interpretation

All incidents are authored synthetic fixtures with injected bugs or intentionally incomplete evidence. The 12 even-numbered cases are held out; case-08 and case-20 receive a second repetition per method. The model is Qwen3 4B Instruct 2507 Q4_K_M via the pinned `tracemedic-qwen3:4b` alias on Ollama 0.40.4. Hardware: Windows, RTX 4060 Laptop 8 GB, 16 GB system RAM. See `implementation.json` for digests/source hashes and `protocol.md` for the scoring definition.

Both LLM methods have 18 model attempts, 14 uncached MCP calls and 1,200 generated tokens per call. Multi-agent has separate role contexts, collection/review permissions, mandatory initial delegation/review and synthesis reservation. Single-agent uses the union of tools and the same output contracts in one context. Actual usage differs; budget equivalence does not mean equal token consumption. Latency is end-to-end wall time including MCP startup, validation and checkpoint work. The model was not unloaded between runs; LLM order alternates by incident. Documentation and environment checks also ran on the workstation, so these timings describe this run rather than an isolated hardware benchmark.

Automatic correctness requires expected concept groups in final prose and a confirmed hypothesis, valid captured file/line evidence and a reproduced fixture check. Ambiguous cases must complete with explicit insufficiency. A `supported` conclusion failing those rules is counted as unsupported **by the automatic evaluator**. These are keyword/reference/execution checks, not semantic entailment or expert adjudication; inspect raw disputed cases. Errors/budget stops count as failures, including on ambiguous cases. No LLM judge or agent agreement is used.

## Measured totals

| Method | Runs | Correct supported | Correct abstentions | Correct total | Unsupported by scorer | Completed | Median seconds | Model calls | MCP calls / successful |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| deterministic | 14 | 3 | 2 | 5 | 0 | 14 | 1.84 | 0 | 84 / 82 |
| single | 14 | 9 | 1 | 10 | 3 | 13 | 28.24 | 137 | 91 / 91 |
| multi | 14 | 8 | 1 | 9 | 3 | 13 | 39.46 | 198 | 122 / 120 |

| Method | Reported input tokens | Reported output tokens | Measured monetary cost |
|---|---:|---:|---|
| deterministic | 0 | 0 | Not measured |
| single | 348729 | 14321 | Not measured |
| multi | 450622 recorded; total unknown | 21615 recorded; total unknown | Not measured |

The case-02 multi-agent run has 15 attempts and 14 recorded responses, including a bounded provider-unavailable retry. The missing response usage makes the aggregate unknown; known provider token fields are reported without estimating that call. Zero tokens for the deterministic method means zero model requests. Local inference has no metered provider charge; hardware and electricity costs were not measured, so no dollar saving is claimed.

## Every scheduled result

CS = correct supported, CA = correct abstention, U = unsupported by automatic scorer, F = other failure/incorrect abstention. Repetitions are shown separately; no successful-only selection.

| Incident | Method | Rep | Status / outcome | Result | Seconds | Model calls | MCP calls |
|---|---|---:|---|---|---:|---:|---:|
| case-02 · Nightly ingestion | deterministic | 1 | completed / supported | CS | 1.96 | 0 | 6 |
| case-02 · Nightly ingestion | multi | 1 | completed / supported | CS | 57.54 | 15 | 9 |
| case-02 · Nightly ingestion | single | 1 | completed / supported | CS | 21.69 | 9 | 6 |
| case-04 · Packet exporter | deterministic | 1 | completed / insufficient | F | 1.84 | 0 | 6 |
| case-04 · Packet exporter | multi | 1 | completed / insufficient | F | 41.38 | 14 | 9 |
| case-04 · Packet exporter | single | 1 | completed / supported | CS | 21.67 | 10 | 6 |
| case-06 · Archive writer | deterministic | 1 | completed / supported | CS | 1.81 | 0 | 6 |
| case-06 · Archive writer | multi | 1 | completed / supported | CS | 47.33 | 14 | 8 |
| case-06 · Archive writer | single | 1 | completed / supported | CS | 18.39 | 8 | 5 |
| case-08 · Event scheduler | deterministic | 1 | completed / insufficient | F | 1.82 | 0 | 6 |
| case-08 · Event scheduler | multi | 1 | completed / supported | CS | 38.05 | 14 | 9 |
| case-08 · Event scheduler | single | 1 | completed / supported | CS | 29.86 | 10 | 7 |
| case-08 · Event scheduler | deterministic | 2 | completed / insufficient | F | 1.90 | 0 | 6 |
| case-08 · Event scheduler | multi | 2 | completed / supported | CS | 35.89 | 14 | 9 |
| case-08 · Event scheduler | single | 2 | completed / supported | CS | 29.31 | 10 | 7 |
| case-10 · Signal statistics | deterministic | 1 | completed / supported | CS | 1.83 | 0 | 6 |
| case-10 · Signal statistics | multi | 1 | completed / supported | CS | 45.13 | 14 | 9 |
| case-10 · Signal statistics | single | 1 | completed / supported | CS | 25.46 | 10 | 7 |
| case-12 · Batch consumer | deterministic | 1 | completed / insufficient | F | 1.84 | 0 | 6 |
| case-12 · Batch consumer | multi | 1 | completed / supported | CS | 41.26 | 14 | 9 |
| case-12 · Batch consumer | single | 1 | completed / supported | CS | 29.14 | 9 | 6 |
| case-14 · Transient fetch | deterministic | 1 | completed / insufficient | F | 1.80 | 0 | 6 |
| case-14 · Transient fetch | multi | 1 | completed / supported | U | 41.11 | 14 | 9 |
| case-14 · Transient fetch | single | 1 | completed / supported | CS | 25.43 | 9 | 6 |
| case-16 · Resource resolver | deterministic | 1 | completed / insufficient | F | 2.18 | 0 | 6 |
| case-16 · Resource resolver | multi | 1 | completed / supported | U | 38.73 | 14 | 9 |
| case-16 · Resource resolver | single | 1 | completed / supported | U | 27.34 | 9 | 6 |
| case-18 · Ledger sink | deterministic | 1 | completed / insufficient | F | 1.94 | 0 | 6 |
| case-18 · Ledger sink | multi | 1 | completed / supported | CS | 40.20 | 14 | 9 |
| case-18 · Ledger sink | single | 1 | completed / supported | CS | 31.55 | 10 | 7 |
| case-20 · Partner callback | deterministic | 1 | completed / insufficient | CA | 1.84 | 0 | 6 |
| case-20 · Partner callback | multi | 1 | failed / insufficient | F | 31.19 | 15 | 7 |
| case-20 · Partner callback | single | 1 | completed / insufficient | CA | 33.85 | 12 | 7 |
| case-20 · Partner callback | deterministic | 2 | completed / insufficient | CA | 1.86 | 0 | 6 |
| case-20 · Partner callback | multi | 2 | completed / insufficient | CA | 31.87 | 14 | 8 |
| case-20 · Partner callback | single | 2 | failed / insufficient | F | 30.80 | 11 | 7 |
| case-22 · Sensor watchdog | deterministic | 1 | completed / insufficient | F | 1.85 | 0 | 6 |
| case-22 · Sensor watchdog | multi | 1 | completed / supported | U | 35.30 | 14 | 9 |
| case-22 · Sensor watchdog | single | 1 | completed / supported | U | 23.43 | 10 | 7 |
| case-24 · Tenant cache | deterministic | 1 | completed / insufficient | F | 1.83 | 0 | 6 |
| case-24 · Tenant cache | multi | 1 | completed / supported | CS | 35.22 | 14 | 9 |
| case-24 · Tenant cache | single | 1 | completed / supported | U | 29.47 | 10 | 7 |

## Failure and disagreement audit

### case-04 / deterministic / repetition 1

Run `ca25ce15-aad4-4d69-865e-c2ffda56a1a3`: `completed`. Automatic score: `{"completed": true, "correct": false, "correct_abstention": false, "correct_supported": false, "expected_abstention": false, "independent_check": true, "unsupported_conclusion": false, "valid_citations": true}`.

The deterministic symptom rules do not establish a root cause from the supplied evidence.

### case-04 / multi / repetition 1

Run `b54162fb-946c-42aa-96b4-9710229b3af6`: `completed`. Automatic score: `{"completed": true, "correct": false, "correct_abstention": false, "correct_supported": false, "expected_abstention": false, "independent_check": true, "unsupported_conclusion": false, "valid_citations": true}`.

The packet exporter failure post-dependency update is attributed to a missing 'decode_bytes' method in the Encoder class. While the synthetic reproduction confirms the absence of this method in the current implementation, and the settings.json file explicitly lists only 'loads' as an available method, the original service contract specification and a pre-update version of service.py are missing. Without these, the claim that 'decode_bytes' was part of the original interface or that it was removed in the dependency update cannot be independently verified. The hypothesis that the service.py file contains a hardcoded reference to 'decode_bytes' remains unconfirmed due to the absence of a pre-update source comparison. Thus, the root cause remains unresolved.

### case-08 / deterministic / repetition 1

Run `cca59be4-bd98-431c-b3c1-6b7af41edc4e`: `completed`. Automatic score: `{"completed": true, "correct": false, "correct_abstention": false, "correct_supported": false, "expected_abstention": false, "independent_check": true, "unsupported_conclusion": false, "valid_citations": true}`.

The deterministic symptom rules do not establish a root cause from the supplied evidence.

### case-12 / deterministic / repetition 1

Run `c460cc60-9e32-466e-b1d6-747173c777f5`: `completed`. Automatic score: `{"completed": true, "correct": false, "correct_abstention": false, "correct_supported": false, "expected_abstention": false, "independent_check": true, "unsupported_conclusion": false, "valid_citations": true}`.

The deterministic symptom rules do not establish a root cause from the supplied evidence.

### case-14 / deterministic / repetition 1

Run `68d08cab-4cd5-4655-b25c-a74fb39b1f7c`: `completed`. Automatic score: `{"completed": true, "correct": false, "correct_abstention": false, "correct_supported": false, "expected_abstention": false, "independent_check": true, "unsupported_conclusion": false, "valid_citations": true}`.

The deterministic symptom rules do not establish a root cause from the supplied evidence.

### case-14 / multi / repetition 1

Run `5656323f-b535-4d69-902d-6b91f0b89eac`: `completed`. Automatic score: `{"completed": true, "correct": false, "correct_abstention": false, "correct_supported": false, "expected_abstention": false, "independent_check": true, "unsupported_conclusion": true, "valid_citations": true}`.

The incident is supported by evidence showing that the service configuration sets max_attempts to 1 and transient_failures to 2, leading to the client exhausting retries before recovery. The runtime.log confirms a TimeoutError with attempts=1 and failures before recovery=2, matching the service configuration. The configuration does not allow sufficient retries to recover from transient failures, resulting in the observed outcome.

### case-16 / deterministic / repetition 1

Run `b3ecffaf-92e4-4f3e-aa06-552875df9473`: `completed`. Automatic score: `{"completed": true, "correct": false, "correct_abstention": false, "correct_supported": false, "expected_abstention": false, "independent_check": true, "unsupported_conclusion": false, "valid_citations": true}`.

The deterministic symptom rules do not establish a root cause from the supplied evidence.

### case-16 / multi / repetition 1

Run `e81ac6f4-e3cd-40e8-9697-e6a5d391fc6e`: `completed`. Automatic score: `{"completed": true, "correct": false, "correct_abstention": false, "correct_supported": false, "expected_abstention": false, "independent_check": true, "unsupported_conclusion": true, "valid_citations": true}`.

The incident is supported by evidence showing a case-sensitive mismatch between the client's input of 'service-db' and the registry configuration's 'service_db' in the code. The error message confirms the DNS lookup failure due to the registry list not containing 'service-db'. The synthetic fixture reproduces the error, validating the mechanism. The registry configuration in settings.json specifies 'service-db', but the code populates the registry list with 'service_db' (lowercase), leading to a failure in host name resolution.

### case-16 / single / repetition 1

Run `2732379f-c64e-41e9-af01-311e62334308`: `completed`. Automatic score: `{"completed": true, "correct": false, "correct_abstention": false, "correct_supported": false, "expected_abstention": false, "independent_check": true, "unsupported_conclusion": true, "valid_citations": true}`.

The resource resolution failure is caused by a missing host entry in the registry for service-db. The error message in runtime.log and service.py confirms a DNS lookup failure when service-db is not found in the registry. The input.json contains the correct host mapping for service_db with host '127.0.0.1'. The claim is consistent with the observed error and available evidence.

### case-18 / deterministic / repetition 1

Run `d776c41c-c0aa-420e-9943-490ece938d6d`: `completed`. Automatic score: `{"completed": true, "correct": false, "correct_abstention": false, "correct_supported": false, "expected_abstention": false, "independent_check": true, "unsupported_conclusion": false, "valid_citations": true}`.

The deterministic symptom rules do not establish a root cause from the supplied evidence.

### case-20 / multi / repetition 1

Run `c7b3c148-c53d-42cf-9043-9405a7e8d60f`: `failed`. Automatic score: `{"completed": false, "correct": false, "correct_abstention": false, "correct_supported": false, "expected_abstention": true, "independent_check": false, "unsupported_conclusion": false, "valid_citations": false}`.

Three consecutive invalid agent/tool actions; inspect audit events.

- verifier / action_rejected: Action rejected: Confirmation needs source evidence and an executed independent check
- verifier / action_rejected: Action rejected: Confirmation needs source evidence and an executed independent check
- verifier / action_rejected: Action rejected: Confirmation needs source evidence and an executed independent check
- system / failed: Three consecutive invalid agent/tool actions; inspect audit events.

### case-22 / deterministic / repetition 1

Run `1c4e3334-5c46-4c33-89e2-60fa0d76f063`: `completed`. Automatic score: `{"completed": true, "correct": false, "correct_abstention": false, "correct_supported": false, "expected_abstention": false, "independent_check": true, "unsupported_conclusion": false, "valid_citations": true}`.

The deterministic symptom rules do not establish a root cause from the supplied evidence.

### case-22 / single / repetition 1

Run `f85de451-45cf-4528-b87d-822b2944c983`: `completed`. Automatic score: `{"completed": true, "correct": false, "correct_abstention": false, "correct_supported": false, "expected_abstention": false, "independent_check": true, "unsupported_conclusion": true, "valid_citations": true}`.

The hypothesis that the runtime log indicates a mismatch between expected and actual sensor message status, confirming a validation failure, is supported by evidence from the runtime.log and report.json. The error 'expected=False; actual=True' directly shows a validation failure in sensor message freshness evaluation.

### case-22 / multi / repetition 1

Run `53280cad-5f15-4769-9f79-8bcb9dc54a5e`: `completed`. Automatic score: `{"completed": true, "correct": false, "correct_abstention": false, "correct_supported": false, "expected_abstention": false, "independent_check": true, "unsupported_conclusion": true, "valid_citations": true}`.

The freshness check in service.py incorrectly evaluates fresh sensor messages as stale due to a logical error in the comparison between age in milliseconds and the max_age_seconds threshold configured in seconds. The settings.json specifies max_age_seconds=2, and the sensor message age is 500ms (0.5s), which is below the threshold. However, the service.py code compares age_ms > max_age_seconds without unit conversion, resulting in a false positive. This misalignment is confirmed by runtime logs and test reports showing expected=False; actual=True. The mechanism is validated through independent fixture reproduction and evidence review.

### case-24 / deterministic / repetition 1

Run `2de1088e-b1ca-4c8e-927d-9578949f193d`: `completed`. Automatic score: `{"completed": true, "correct": false, "correct_abstention": false, "correct_supported": false, "expected_abstention": false, "independent_check": true, "unsupported_conclusion": false, "valid_citations": true}`.

The deterministic symptom rules do not establish a root cause from the supplied evidence.

### case-24 / single / repetition 1

Run `dfcd1785-a96d-4c4e-a7c7-525df80d5a15`: `completed`. Automatic score: `{"completed": true, "correct": false, "correct_abstention": false, "correct_supported": false, "expected_abstention": false, "independent_check": true, "unsupported_conclusion": true, "valid_citations": true}`.

The cache implementation in service.py stores the first encountered value for each item, leading to both tenants seeing the same cached value for item 7. The east tenant's request for item 7 occurs first, storing 'E' in the cache. The west tenant's request for item 7 is processed later, but since item 7 is already in cache, it returns 'E' instead of 'W'. The reproduced check confirms the output is ['E', 'E'], matching the observed behavior.

### case-08 / deterministic / repetition 2

Run `e14d913e-df0b-4694-9ae3-775a0f146119`: `completed`. Automatic score: `{"completed": true, "correct": false, "correct_abstention": false, "correct_supported": false, "expected_abstention": false, "independent_check": true, "unsupported_conclusion": false, "valid_citations": true}`.

The deterministic symptom rules do not establish a root cause from the supplied evidence.

### case-20 / single / repetition 2

Run `ede750b5-acc3-4efe-9faa-54c7b9c01635`: `failed`. Automatic score: `{"completed": false, "correct": false, "correct_abstention": false, "correct_supported": false, "expected_abstention": true, "independent_check": false, "unsupported_conclusion": false, "valid_citations": false}`.

Three consecutive invalid agent/tool actions; inspect audit events.

- single / action_rejected: Action rejected: Confirmation needs source evidence and an executed independent check
- single / action_rejected: Action rejected: Confirmation needs source evidence and an executed independent check
- single / action_rejected: Action rejected: Confirmation needs source evidence and an executed independent check
- system / failed: Three consecutive invalid agent/tool actions; inspect audit events.

## Recovery and injection evidence

Process recovery is a separate fault experiment, not an inferred success rate for all benchmark cases. The committed `docs/evidence/real-recovery.json` records one real-model hard-kill/restart experiment: all prior evidence retained, same ID, one fixture ledger execution and one tool-result event. `tests/test_restart.py` independently runs a hard-kill/restart with a labeled test double. The uncertain claimed-but-uncompleted fixture operation is tested separately and is not replayed.

Four corpus incidents contain misleading SYSTEM-like log text. MCP path/schema boundaries are tested directly. The held-out raw traces retain any attempted forbidden reads and all tool errors; absence of a forbidden read in these few runs does not demonstrate universal prompt-injection resistance.

## Limits and conclusions

On these recorded runs the single agent has 10/14 correct automatic outcomes; the multi-agent system has 9/14. Median latency is 28.24s versus 39.46s. Multi-agent uses 198 model calls versus 137. These measurements expose review/coordination overhead; they do not establish a production benefit or calibrated accuracy.

The sample is small, synthetic, mostly one repetition per case, and uses a small shared model with correlated role errors. The two extra repeated cases are a limited variability probe. All correctness claims are scoped to the deterministic scoring rule and its stated limitations. Further work should add independently sourced cases, semantic human adjudication and more repeated runs under an isolated timing protocol, with a newly frozen test set before tuning.

See [scoring notes](scoring_notes.md) for concrete examples of over-abstention, a symptom confirmed as a cause, and a possible keyword false negative. Frozen scores are not changed by those observations.

Packaging note: generated catalog/oracle/protocol JSON line endings were canonicalized to LF for Windows/Linux checkout consistency. Incident file bytes, oracle values, scoring and agent/provider source hashes were unchanged during the comparison. No held-out prompt tuning was performed.
