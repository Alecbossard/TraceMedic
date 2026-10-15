# Post hoc source-level inspection

The frozen automatic result is **7/14 V1 multi, 6/14 V2 single, 8/14 V2 multi**. Those numbers are unchanged. After all 56 runs finished, the implementation agent inspected all 42 LLM final outputs, selected hypotheses, source semantics and proposed actions. This is an LLM-assisted engineering inspection by the author, **not** independent human annotation, a blind evaluation or a replacement gold standard. Its purpose is to expose counterexamples to the automatic rubric.

## False positives and incomplete explanations

- **sample-03, V1 multi** ([raw row 39](results/raw.jsonl#L39)): automatically accepted because identifiers/numbers satisfy the concept groups, but it calls `now_seconds + ttl_ms` correct and blames the fixture. [The source](../../corpus/sample-03/service.py) directly adds milliseconds to seconds. The arithmetic mismatch is a symptom; the missing unit conversion is the mechanism. This is a clear automatic false positive.
- **sample-03, V2 single** ([row 5](results/raw.jsonl#L5)): automatically accepted, but merely restates `1000 + 30000 = 31000` and calls it misaligned inputs/configuration. It does not explain conversion from milliseconds to seconds. The identifier `ttl_ms` plus the literal `1000` makes the loose rubric pass an incomplete explanation.
- **sample-08, V2 multi** ([row 1](results/raw.jsonl#L1)): automatically accepted, but cites the transient-failure condition and says the error occurs before the retry loop executes. The loop has already started. [The distinguishing defect](../../corpus/sample-08/service.py) is the immediate bare `raise` inside `except TimeoutError`. The record and verifier reason fail to isolate that handler behavior. Baseline reproduction and two valid citations did not prevent confirmation of an incomplete mechanism.
- **sample-08, V2 single** ([row 26](results/raw.jsonl#L26)): identifies immediate re-raising/no subsequent retries, but also says the attempt counter is not incremented. The code increments it before raising. The scorer accepts the main concept while missing this unsupported extra assertion.

Consequently **8/14 versus 7/14 is not evidence of a demonstrated semantic reliability improvement**. Structural guards improved and measured runtime fell substantially; source entailment remains unresolved.

## Keyword misses and mixed claims

- **sample-05, both V2 methods**: explain the zero/default fallback but omit the exact words `false/falsy/truth`, so the rubric rejects them. They also wrongly extend the behavior to an *absent* key; `d["count"]` would raise `KeyError` before `or`. This is a keyword miss combined with a real unsupported extension, not an unqualified correct answer.
- **sample-09, V1 multi**: identifies assignment of the endpoint string to the adapter variable, but lacks the oracle's overwrite/reassign/shadow/replace verbs. The causal explanation is substantially closer than the score suggests. Its proposal to put an Adapter instance into JSON configuration is not an executable repair.
- **sample-10, V1 multi** ([row 52](results/raw.jsonl#L52)): identifies the distinct requested/stored keys and missing normalization, but uses `diacritics`, which the frozen concept alternatives omit. It also introduces case comparison unnecessarily. **V2 single** ([row 10](results/raw.jsonl#L10)) describes a key mismatch without identifying canonical Unicode composition. **V2 multi** ([row 54](results/raw.jsonl#L54)) wrongly attributes it to case-sensitive matching. [The actual distinction](../../corpus/sample-10/input.json) is composed `é` versus `e` plus combining acute accent; both spellings have the same case.

## Complete case review

The [automatic per-run matrix](report.md#every-scheduled-case) links every output to its raw row. Repeated sample-02 and sample-11 runs were also inspected.

| Case | V1 multi | V2 single | V2 multi |
|---|---|---|---|
| 01 · string boolean | Correct main mechanism; test wording in advice is muddled | Wrongly treats empty input as missing configuration and undefined access as false | Explains nonempty string truthiness |
| 02 · string version comparison, both repetitions | Misses configuration/input distinction; abstains with unsupported reasons | Applies numeric ordering to string comparison; confirms a contradictory explanation | Abstains instead of establishing lexical comparison |
| 03 · mixed time units | Automatic false positive, fixture blame | Automatic false positive, arithmetic mismatch without conversion | Abstains; causal unit explanation not established |
| 04 · mutable default | Explains retained list state | Explains retained list state | Explains retained list state |
| 05 · legitimate zero | Explains falsy fallback | Correct zero fallback plus false absent-key generalization | Correct zero fallback plus false absent-key generalization |
| 06 · access rule | Explains admin short-circuit; advice leaves the defect unchanged | Controlled failure after three invalid cross-file citation proposals | Explains admin bypass of active/scope check |
| 07 · removed empty field | Describes shifted field without isolating `filter(None, ...)` | Incorrectly says empty fields are not skipped; recommends the operation already causing the defect | Abstains; filtering mechanism not established |
| 08 · immediate re-raise | Abstains with wrong attempt-counter speculation | Main retry defect plus false counter assertion | Incomplete causal record approved; does not isolate the `except` re-raise |
| 09 · overwritten object | Substantially identifies assignment; keyword miss and unworkable advice | Confuses configuration with empty input, invents `None` | Explains object replacement by string |
| 10 · canonical Unicode | Normalization/key mismatch, imprecise language and keyword miss | Key mismatch without canonical representation explanation | Adds wrong case-sensitive explanation |
| 11 · contradictory untimed evidence, both repetitions | First fails confirmation guard; repeat abstains with speculation | Abstains both times | Abstains both times |
| 12 · healthy captured fixture | Abstains with unsupported missing-field/data speculation | Abstains | Abstains |

## What the tools and guards actually demonstrated

All 14 V2 multi runs completed; V2 single had one controlled failure. Both V2 variants correctly abstained in all three ambiguous trials. The host's literal line references prevent quotation fabrication and its baseline guard blocks confirmation from passed/unavailable checks. They do not validate meaning, variable provenance, units or completeness. Some next actions contain wrong line references, unsupported premises or tests of already captured facts; those free-form recommendations are **not scored**.

No final V2 benchmark run selected `run_experiment`. Therefore the benchmark demonstrates no benefit attributable to controlled interventions. The separate [real native tool integration](../../docs/evidence/v2/real-experiment.json) uses one task-directed real model decision and a real MCP process: it selects `/settings/port = 5432`, observes reproduced baseline then passing trial, and changes no incident file. It is explicitly separate from a full autonomous investigation or an extra benchmark success. The ordinary integration tests exercise intervention bounds, tampering, idempotence and uncertain claims.

One V1 sample-06 model request needed a provider-unavailable retry: 15 attempts, 14 recorded responses. Its aggregate usage stays incomplete; known totals are retained. No missing tokens or monetary savings are inferred.

## Product decision

Keep V2 multi as the default demonstrator for its separate review, stronger trace contracts, 14 completed runs and lower measured overhead. Keep V2 single and the V1 reference selectable. Present this as a portfolio system with observable limitations, not an automated root-cause authority. A stronger model, a preregistered entailment rubric and a new independently reserved suite are future experiments; none were silently substituted after seeing these outcomes.
