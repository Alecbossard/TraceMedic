# Invalidated partial comparison — encoding correction

The first V2 attempt was stopped during independent visual/portability QA. Windows Python 3.13 in isolated mode defaults to cp1252; fixture workers read UTF-8 JSON without an explicit encoding. The Unicode-label fixture would therefore be decoded differently on Windows and Linux. A separate UI editing error had introduced mojibake in labels.

All 24 completed rows from that partial attempt remain in `raw.jsonl`, with their original implementation snapshot and partial summary. An interrupted runner snapshot is also retained. These rows are **excluded** from the final comparison. No reserved model explanation or scoring result was inspected to tune prompts. Only progress/status/latency was monitored. The correction explicitly specifies UTF-8 in both fixture workers, the MCP server and the V2 catalog reader; prompts, model, protocol, case bytes, scorer and settings remain unchanged.

After the correction the implementation was frozen again, all prior run databases isolated, and the **entire** predeclared 56-run schedule restarted. This is not a rerun of selected failures. See the final results directory and report for the valid experiment.
