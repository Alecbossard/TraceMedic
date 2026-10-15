# TraceMedic V2: smaller contexts, reviewable causal claims

## Decision

Prioritize diagnosis reliability and measured efficiency. V1's three-agent method scored 9/14 automatic outcomes versus 10/14 for a single agent, with median wall time 39.46s versus 28.24s. Adding agents is not the improvement hypothesis.

V2 keeps Python, LangGraph, the real MCP subprocess and SQLite. It changes the information contracts and tools, while preserving V1 code/results as a reproducible comparison. No hosted service, new account or paid model is required.

## Concrete changes

1. **A causal record instead of independent paragraphs.** Investigator proposes trigger, mechanism, effect and captured line references. Host attaches exact quoted source text; the model never writes quotation text. Verifier reviews that same record. The final finding is rendered from the reviewed record; coordinator selects it and proposes next actions, but cannot introduce a new factual explanation during synthesis. Current execution and unknown deployment history are separated. Recommendations remain model-authored and require human judgment.
2. **Compact, addressable context.** Captured excerpts appear once, with short stable aliases for model-facing references. The audit keeps original hash-based IDs. A bounded MCP `read_bundle` collects selected files in one round trip. The same toolset is available to V2's single and multi-agent comparators.
3. **Checks that can discriminate.** In addition to replaying an unchanged fixture, verifier may request an isolated configuration/input intervention on an authorized immutable fixture. Source files and the supplied expected result cannot be edited. The tool records baseline/trial results and changed JSON pointers, without applying a repair to the incident. An intervention is evidence under controlled assumptions, not proof of a production root cause.
4. **Insufficient evidence terminates as uncertainty.** A confirmation with unavailable checks is blocked and retained as unresolved, rather than repeatedly asking the model to make the same invalid confirmation until the run fails. Unknown references and fabricated quotes remain hard validation errors.
5. **A versioned product and experiment.** Existing V1 traces remain readable/resumable with their original runner. CLI/UI identify V1/V2. A fresh reserved suite is frozen before V2 prompt tuning; old cases are now regression/development data, never newly claimed held out.

## Evaluation before promotion

Use the same local Qwen3 4B alias, seed, top-level call/tool budgets and generated-token limit. Compare deterministic rules, original V1 multi-agent, V2 single-agent and V2 multi-agent on the same new reserved cases. Publish every scheduled result, failures, wall time, calls, reported tokens and protocol/sandbox errors. Do not compare a new score directly to the old 9/14 under a changed scorer.

The new rubric checks mechanism concepts in the final reviewed finding, literal citation validity and executed checks; it does not require identifiers to be repeated verbatim inside every hypothesis. Explicit contradictory claims are penalized. The oracle and all case hashes are frozen first. This is still a limited synthetic evaluation, not semantic proof or production accuracy. Keep a separate adversarial regression set for the V1 failures.

## Boundaries

No extra agents, RAG/vector database, SaaS deployment, open shell, arbitrary Python patch execution or calibrated confidence percentages. Arbitrary incident-folder ingestion and model-size upgrades are separate extensions, not hidden confounders in this comparison.

## Research behind the choices

- [LangGraph workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents): explicit routing and bounded evaluator/optimizer loops are supported patterns; success must come from our own evaluation.
- [Anthropic, Building effective agents](https://www.anthropic.com/engineering/building-effective-agents): prefer simple composable workflows and improve tool ergonomics before adding complexity. This is engineering guidance, not evidence that V2 will win.
- [Anthropic, Multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system): independent contexts/tool design and delegation matter, with substantial token overhead; broad parallel research differs from this small diagnostic task. Their reported gains are not transferable to TraceMedic.
- [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs): schemas constrain output form, not factual truth. Runtime source/reference validation remains necessary.

## Acceptance

Preserve all V1 artifacts. Pass literal-citation, no-new-final-claim, unavailable-check, MCP intervention-boundary, cancellation and new-process recovery tests. Execute a real V2 CLI/browser run and all scheduled reserved trials. Promote only after the comparison is reported honestly; a loss remains a useful result.

Development finding: character-for-character quotation generation and native control argument counts were fragile on the 4B model. V2 therefore selects stable line handles (`E2:L3`) and uses Ollama JSON-schema decoding when only one control contract is permitted. The schema is also included in the prompt. MCP collection/experiment calls and action choices remain native function calls. OpenAI-compatible endpoints keep native calls for all decisions. No model response from the new reserved cases was used to make these changes.
