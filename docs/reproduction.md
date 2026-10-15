# Reproduce from a clean checkout

## Prerequisites

- Python 3.13 and Node 24 (tested: 3.13.1 and 24.11.0).
- About 5 GB for the optional portable Windows runtime/model, plus the environment.
- The tested GPU is an RTX 4060 Laptop 8 GB. CPU inference was not used for the reported benchmark.
- Existing GitHub authentication only if pushing. No account is needed for local inference.

## Fresh environment

```powershell
git clone https://github.com/Alecbossard/TraceMedic.git
cd TraceMedic
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m pytest -q
npm ci --prefix frontend
npm run build --prefix frontend
npm audit --prefix frontend --audit-level=high
```

On Linux replace `.venv\Scripts\python.exe` with `.venv/bin/python`. CI uses the pinned dependency closure on Windows and Linux; `pywin32` is Windows-only. LF Git attributes and generated manifests keep fixture hashes consistent. Do not regenerate the corpus to make a broken hash test pass: investigate an input change first.

Configure the [tested model](model_configuration.md), then run:

```powershell
.\.venv\Scripts\python.exe -m tracemedic.cli tools case-01
.\.venv\Scripts\python.exe -m tracemedic.cli run case-01
$env:TRACEMEDIC_REAL_TESTS='1'
.\.venv\Scripts\python.exe -m pytest -q -m real
.\.venv\Scripts\python.exe scripts/prove_recovery.py
.\.venv\Scripts\python.exe -m tracemedic.cli serve
```

The local clean-environment verification is recorded in `docs/evidence/clean-install.json`. CI results belong to the delivered commit. A skipped real test is not a passed real test.

## Recompute the benchmark

`benchmarks/protocol.json`, `oracle.json` and `frozen_manifest.json` define evaluation. `implementation.json` records agent/provider hashes and model digests. Start the model, run `python scripts/verify_model.py`, then `python -m tracemedic.benchmark`. A changed model digest requires a new experiment label. The actual served identities for the delivered experiment are saved in `docs/evidence/model-identity.json`.

The runner skips existing rows identified by method, incident and repetition; it never silently replaces a failure. For a fresh experiment, preserve `benchmarks/results` in a named archive and use a new checkout. Do not rerun only favorable cases and present them as the same experiment. Latency includes MCP startup and model work; GPU cache/system load affect it. See the report for exact counts.

## Regenerate for a new corpus version

`python scripts/generate_corpus.py` regenerates all 24 authored fixtures and freezes metadata. This is a development operation, never an agent tool. A changed incident/oracle invalidates prior results. Preserve old results and label a new protocol instead of treating a changed test set as held out.

## Durable files

- `data/audit.db`: runs, events, evidence and operation ledger.
- `data/checkpoints.db`: graph state and next actions.
- `data/locks/`: OS locks; file existence does not imply a held lock.
- `.runtime/`: optional local binaries, models and developer logs; ignored by Git.
- `docs/evidence/`: actual demonstrations. All benchmark runs are published separately.
