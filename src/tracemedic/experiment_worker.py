"""Isolated trusted-code experiment. Launched with python -I, JSON input on stdin."""

import json
import sys
from pathlib import Path

from tracemedic.fixture_worker import evaluate, load_fixture, set_limits
from tracemedic.interventions import apply_changes


def main():
    root, incident = Path(sys.argv[1]).resolve(), sys.argv[2]
    folder = load_fixture(root, incident)
    set_limits()
    changes = json.loads(sys.stdin.read(4097))
    config = json.loads((folder / "settings.json").read_text())
    data = json.loads((folder / "input.json").read_text())
    changed_config, changed_data = apply_changes(config, data, changes)
    baseline = evaluate(folder, config, data)
    trial = evaluate(folder, changed_config, changed_data)
    print(
        json.dumps(
            {
                "status": trial["status"],
                "detail": trial["detail"],
                "baseline": baseline,
                "trial": trial,
                "changes": changes,
                "scope": "Isolated trusted synthetic fixture, unchanged source and expected result. No repair applied. A changed result does not prove a production cause.",
            }
        )
    )


if __name__ == "__main__":
    main()
