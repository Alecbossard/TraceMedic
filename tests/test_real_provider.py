import os

import pytest

from tracemedic.config import Settings
from tracemedic.engine import Engine


@pytest.mark.real
@pytest.mark.skipif(
    os.environ.get("TRACEMEDIC_REAL_TESTS") != "1",
    reason="Real model tests are opt-in; deterministic CI is not model validation",
)
async def test_real_llm_end_to_end(tmp_path):
    engine = Engine(Settings(data_dir=tmp_path))
    run = engine.create("case-01")
    result = await engine.run(run)
    assert result["status"] == "completed"
    assert result["state"]["diagnostic"]["outcome"] == "supported"
    assert {"coordinator", "investigator", "verifier"} <= set(result["state"]["visited"])
    assert engine.store.metrics(run)["usage_complete"]
