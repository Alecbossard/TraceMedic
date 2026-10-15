"""Create a reproducible local model alias with valid JSON tool serialization."""

import hashlib
import json
from pathlib import Path

import httpx

BASE = "qwen3:4b-instruct-2507-q4_K_M"
ALIAS = "tracemedic-qwen3:4b"
with httpx.Client(base_url="http://127.0.0.1:11434", timeout=120) as client:
    show = client.post("/api/show", json={"model": BASE})
    show.raise_for_status()
    # Explicit Go template: valid JSON tool schemas and no thinking prefill.
    template = """{{- if or .System .Tools }}<|im_start|>system
{{ .System }}
{{- if .Tools }}
# Tools
You must respond with exactly one function call inside <tool_call> tags.
<tools>
{{- range .Tools }}
{"type":"function","function":{{ .Function | json }}}
{{- end }}
</tools>
For each call output <tool_call>{"name":"function_name","arguments":{}}</tool_call> with valid arguments.
{{- end }}<|im_end|>
{{ end }}
{{- range .Messages }}<|im_start|>{{ .Role }}
{{ .Content }}<|im_end|>
{{ end }}<|im_start|>assistant
"""
    result = client.post(
        "/api/create", json={"model": ALIAS, "from": BASE, "template": template, "stream": False}
    )
    result.raise_for_status()
    tags = client.get("/api/tags").json()["models"]
    version = client.get("/api/version").json()
metadata = {
    "alias": ALIAS,
    "base": BASE,
    "ollama": version,
    "models": [m for m in tags if m["name"] in (BASE, ALIAS)],
    "template_sha256": hashlib.sha256(template.encode()).hexdigest(),
    "patch": "serialize .Function through json; upstream issue https://github.com/ollama/ollama/issues/14601",
}
Path(".runtime/model-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
print(json.dumps(metadata, indent=2))
