"""Execute only shipped, hash-verified fixtures; this is never an arbitrary shell."""

import hashlib
import json
import os
import sys
from pathlib import Path


def main():
    root, incident = Path(sys.argv[1]).resolve(), sys.argv[2]
    manifest = json.loads((Path(__file__).with_name("fixture_hashes.json")).read_text())
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
    if os.name != "nt":
        import resource

        resource.setrlimit(resource.RLIMIT_AS, (256 * 1024**2, 256 * 1024**2))
        resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
    # Finite authored fixtures; inputs are immutable and <=64 KB. No network or subprocess code.
    if not (folder / "service.py").exists():
        print(
            json.dumps({"status": "unavailable", "detail": "No authorized executable reproduction"})
        )
        return
    namespace = {}
    exec(compile((folder / "service.py").read_text(), "service.py", "exec"), namespace)
    config = json.loads((folder / "settings.json").read_text())
    data = json.loads((folder / "input.json").read_text())
    report = json.loads((folder / "report.json").read_text())
    try:
        actual = namespace["run"](config, data)
        detail = f"expected={report['expected']!r}; actual={actual!r}"
        status = "reproduced" if actual != report["expected"] else "passed"
    except Exception as exc:
        detail, status = f"{type(exc).__name__}: {exc}", "reproduced"
    print(
        json.dumps(
            {
                "status": status,
                "detail": detail,
                "fixture": incident,
                "scope": "immutable synthetic fixture; no production resource contacted",
            }
        )
    )


if __name__ == "__main__":
    main()
