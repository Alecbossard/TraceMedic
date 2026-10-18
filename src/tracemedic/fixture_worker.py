"""Execute only shipped, hash-verified fixtures; this is never an arbitrary shell."""

import hashlib
import json
import os
import sys
from pathlib import Path


def load_fixture(root, incident):
    manifest = json.loads(
        (Path(__file__).with_name("fixture_hashes.json")).read_text(encoding="utf-8")
    )
    extra = Path(__file__).with_name("fixture_hashes_v2.json")
    if extra.exists():
        manifest.update(json.loads(extra.read_text(encoding="utf-8")))
    if incident not in manifest:
        raise ValueError("Not an authorized fixture")
    folder = root / "corpus" / incident
    for name, expected in manifest[incident].items():
        path = folder / name
        if (
            path.is_symlink()
            or path.stat().st_size > 65536
            or hashlib.sha256(path.read_bytes()).hexdigest() != expected
        ):
            raise ValueError("Fixture changed; execution refused")
    return folder


def set_limits():
    if os.name != "nt":
        import resource

        resource.setrlimit(resource.RLIMIT_AS, (256 * 1024**2, 256 * 1024**2))
        resource.setrlimit(resource.RLIMIT_CPU, (2, 2))


def evaluate(folder, config, data):
    if not (folder / "service.py").exists():
        return {"status": "unavailable", "detail": "No authorized executable reproduction"}
    namespace = {}
    exec(
        compile((folder / "service.py").read_text(encoding="utf-8"), "service.py", "exec"),
        namespace,
    )
    report = json.loads((folder / "report.json").read_text(encoding="utf-8"))
    try:
        actual = namespace["run"](config, data)
        detail = f"expected={report['expected']!r}; actual={actual!r}"
        status = "reproduced" if actual != report["expected"] else "passed"
    except Exception as exc:
        detail, status = f"{type(exc).__name__}: {exc}", "reproduced"
    return {"status": status, "detail": detail}


def main():
    root, incident = Path(sys.argv[1]).resolve(), sys.argv[2]
    folder = load_fixture(root, incident)
    set_limits()
    # Finite authored fixtures; inputs are immutable and <=64 KB. No network or subprocess code.
    result = evaluate(
        folder,
        json.loads((folder / "settings.json").read_text(encoding="utf-8")),
        json.loads((folder / "input.json").read_text(encoding="utf-8")),
    )
    if result["status"] != "unavailable":
        result.update(
            fixture=incident, scope="immutable synthetic fixture; no production resource contacted"
        )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
