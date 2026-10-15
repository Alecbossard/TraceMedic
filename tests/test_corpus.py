import hashlib
import json

from tracemedic.config import ROOT


def test_held_out_inputs_and_oracle_still_match_frozen_protocol():
    frozen = json.loads((ROOT / "benchmarks" / "frozen_manifest.json").read_text())
    for relative, expected in frozen.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected, relative
    oracle = json.loads((ROOT / "benchmarks" / "oracle.json").read_text())
    assert len(oracle) == 24
    assert sum(c["split"] == "test" for c in oracle.values()) == 12
    assert {c["family"] for c in oracle.values()} == {
        "configuration",
        "dependency",
        "data",
        "application",
        "timeout",
        "connection",
        "ambiguous",
    }
