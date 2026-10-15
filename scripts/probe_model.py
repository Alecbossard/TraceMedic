import json
from pathlib import Path

import httpx

from tracemedic.prompts import DELEGATE, FINISH, PROMPTS

payload = {
    "model": "qwen3:4b",
    "messages": [
        {"role": "system", "content": PROMPTS["coordinator"]},
        {
            "role": "user",
            "content": "Investigate database connection refusal. Delegate to investigator. /no_think",
        },
    ],
    "tools": [DELEGATE, FINISH],
    "stream": False,
    "think": False,
    "options": {"temperature": 0, "num_ctx": 8192, "num_predict": 1200},
}
response = httpx.post("http://127.0.0.1:11434/api/chat", json=payload, timeout=100)
Path(".runtime/model-probe.json").write_text(
    json.dumps(response.json(), indent=2), encoding="utf-8"
)
print(json.dumps(response.json(), indent=2))
