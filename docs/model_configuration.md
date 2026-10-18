# Model configuration

V2 uses the same tested alias/digest as the V1 reference. Native function calling selects MCP operations and action choices. For an Ollama phase with exactly one permitted control contract, `v2/provider.py` also supplies its JSON schema in the prompt and `format` field, then validates the result in the runner. This improves output form, not factual correctness. OpenAI-compatible providers keep native function calls for every phase. No additional model, paid endpoint or API key was introduced by V2.

The tested provider is Ollama **0.40.4**, with **Qwen3 4B Instruct 2507 Q4_K_M** and an 8,192-token context. `benchmarks/implementation.json` records exact model digests and the template hash. The same alias serves all three roles and the single-agent comparator. Temperature is zero and the requested seed is 17; deterministic settings do not guarantee bit-identical GPU generation.

## Tested local setup

Start Ollama, pull `qwen3:4b-instruct-2507-q4_K_M`, then run `python scripts/prepare_model.py`. This creates the local alias `tracemedic-qwen3:4b`. It shares the base weights rather than duplicating them. `scripts/bootstrap_local.py` is an optional Windows-only portable runtime installer; its binaries and weights stay ignored under `.runtime/`.

An initial trial of the older `qwen3:4b` tag failed to produce usable native function calls. Inspection showed a thinking-prefill/template serialization issue. The tested alias uses an explicit non-thinking Go template and serializes `.Function` through `json`. This follows the workaround discussed in [Ollama's upstream issue](https://github.com/ollama/ollama/issues/14601). It does not parse reasoning prose as tool calls. `prepare_model.py` reproduces the exact template; its successful response is a real native `tool_calls` message.

Copy `.env.example` to `.env` only if you need overrides. The default configuration already matches the tested alias. `.env`, runtime binaries, databases and model weights are ignored by Git. Do not put credentials in model URLs or source files.

| Variable | Default | Meaning |
|---|---|---|
| `TRACEMEDIC_PROVIDER` | `ollama` | `ollama` or `openai-compatible` |
| `TRACEMEDIC_MODEL` | `tracemedic-qwen3:4b` | Exact served model name |
| `TRACEMEDIC_MODEL_URL` | `http://127.0.0.1:11434` | Ollama base URL; compatible endpoints include `/v1` |
| `TRACEMEDIC_API_KEY` | empty | Optional existing compatible-provider credential |
| `TRACEMEDIC_MODEL_TIMEOUT` | 90 | Seconds per inference request |
| `TRACEMEDIC_TOOL_TIMEOUT` | 15 | Seconds per MCP request |
| `TRACEMEDIC_MAX_CALLS` | 18 | All inference attempts, including retries |
| `TRACEMEDIC_MAX_TOOLS` | 14 | Completed uncached MCP requests |
| `TRACEMEDIC_MAX_STEPS` | 40 | Graph-node visits |
| `TRACEMEDIC_MAX_AGENT_TURNS` | 10 | Total visits per specialist/coordinator; single uses the call limit |
| `TRACEMEDIC_MAX_OUTPUT_TOKENS` | 1200 | Generated-token limit per call |
| `TRACEMEDIC_CONTEXT_TOKENS` | 8192 | Ollama context window |
| `TRACEMEDIC_SEED` / `TEMPERATURE` | 17 / 0 | Requested sampling settings |
| `TRACEMEDIC_DATA_DIR` | checkout `data/` | Durable audit, checkpoints and run locks |

## Existing compatible providers

Set provider to `openai-compatible`, supply a model/base URL and optionally an existing key. The adapter uses `/chat/completions` with native tool calling and reports the returned usage. No hosted account is created, and no hosted provider is claimed tested by the local-model results. Compatibility varies: verify support for required tool choice, seed, generation limits and schema fields. Failed inference becomes an explicit error, never a silent deterministic fallback.

`--provider scripted` selects a shipped **test double** intended for `case-01` integration tests. It does not call a model and must never be described as real inference. The interface's new-run path does not offer this test provider. The deterministic benchmark is separately labeled `rules-v1`.
