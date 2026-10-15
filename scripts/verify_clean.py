"""Verify a Git archive in a fresh checkout/environment inside this repository."""

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--workflow", choices=["v1", "v2"], default="v2")
args = parser.parse_args()
folder = ROOT / ".runtime" / ("clean-" + str(uuid.uuid4())[:8])
folder.mkdir(parents=True)
archive = folder / "source.zip"
subprocess.run(["git", "archive", "HEAD", "-o", str(archive)], cwd=ROOT, check=True)
with zipfile.ZipFile(archive) as bundle:
    bundle.extractall(folder)
python = folder / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
steps = []


def run(command):
    started = time.perf_counter()
    result = subprocess.run(command, cwd=folder, capture_output=True, text=True, timeout=900)
    entry = {
        "command": command,
        "exit_code": result.returncode,
        "seconds": round(time.perf_counter() - started, 2),
        "stdout_tail": result.stdout[-5000:],
        "stderr_tail": result.stderr[-1000:],
    }
    steps.append(entry)
    print(
        json.dumps({k: v for k, v in entry.items() if k not in ("stdout_tail", "stderr_tail")}),
        flush=True,
    )
    if result.returncode:
        raise RuntimeError(json.dumps(entry))


try:
    run([sys.executable, "-m", "venv", str(folder / ".venv")])
    run([str(python), "-m", "pip", "install", "-r", "requirements.lock"])
    run([str(python), "-m", "pip", "install", "--no-deps", "-e", "."])
    run([str(python), "-m", "pip", "check"])
    run([str(python), "-m", "ruff", "check", "."])
    run([str(python), "-m", "ruff", "format", "--check", "."])
    run([str(python), "-m", "pytest", "-q"])
    npm = "npm.cmd" if os.name == "nt" else "npm"
    run([npm, "ci", "--prefix", "frontend"])
    run([npm, "run", "build", "--prefix", "frontend"])
    run([npm, "audit", "--prefix", "frontend", "--audit-level=high"])
    run([str(python), "scripts/import_demo.py", "--workflow", "v1"])
    if args.workflow == "v2":
        run([str(python), "scripts/import_demo.py", "--workflow", "v2"])
    result = "passed"
finally:
    evidence = {
        "status": locals().get("result", "failed"),
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "clean_directory": str(folder),
        "python": sys.version,
        "steps": steps,
        "scope": "Fresh Git archive, new Python venv and npm ci. No user-site packages or existing node_modules reused. Provider runtime is external and not reinstalled by this check.",
    }
    destination = ROOT / "docs/evidence"
    if args.workflow == "v2":
        destination = destination / "v2"
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "clean-install.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
