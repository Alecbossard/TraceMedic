"""Regression for the Windows isolated-process locale, independent of model decisions."""

import json
import subprocess
import sys

from tracemedic.config import ROOT


def test_isolated_fixture_reads_utf8_json_independent_of_windows_locale():
    worker = ROOT / "src/tracemedic/fixture_worker.py"
    result = subprocess.run(
        [sys.executable, "-I", str(worker), str(ROOT), "sample-10"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["status"] == "reproduced"
    assert "cafe\u0301" in output["detail"]
    assert "caf\u00c3" not in output["detail"]
