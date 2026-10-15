"""Download a portable local model runtime exclusively into this checkout."""

import json
import os
import subprocess
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
runtime = ROOT / ".runtime"
runtime.mkdir(exist_ok=True)
with urllib.request.urlopen(
    "https://api.github.com/repos/ollama/ollama/releases/latest"
) as response:
    release = json.load(response)
asset = next(a for a in release["assets"] if a["name"] == "ollama-windows-amd64.zip")
archive = runtime / asset["name"]
print(json.dumps({"version": release["tag_name"], "bytes": asset["size"]}), flush=True)
if not archive.exists() or archive.stat().st_size != asset["size"]:
    urllib.request.urlretrieve(asset["browser_download_url"], archive)
target = runtime / "ollama"
with zipfile.ZipFile(archive) as bundle:
    bundle.extractall(target)
env = dict(
    os.environ,
    OLLAMA_MODELS=str(runtime / "models"),
    OLLAMA_HOST="127.0.0.1:11434",
    OLLAMA_NUM_PARALLEL="1",
)
log = (runtime / "ollama.log").open("a", encoding="utf-8")
process = subprocess.Popen(
    [str(target / "ollama.exe"), "serve"],
    env=env,
    stdout=log,
    stderr=log,
    creationflags=subprocess.CREATE_NO_WINDOW,
)
(runtime / "ollama.pid").write_text(str(process.pid))
(runtime / "runtime.json").write_text(
    json.dumps({"release": release["tag_name"], "asset": asset["name"]}, indent=2)
)
print(f"Ollama server started: {process.pid}", flush=True)
