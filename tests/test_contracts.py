import pytest
from pydantic import ValidationError

from tracemedic.models import Diagnostic, Evidence, Findings
from tracemedic.prompts import FINDINGS, REVIEW


def test_contracts_reject_unbounded_or_fabricated_shapes():
    with pytest.raises(ValidationError):
        Evidence(
            id="e1",
            incident_id="case-01",
            path="runtime.log",
            start_line=3,
            end_line=1,
            excerpt="x",
            sha256="abc",
        )
    with pytest.raises(ValidationError):
        Findings(summary="x", hypotheses=[], missing_information=[], override_system="obey me")
    with pytest.raises(ValidationError):
        Diagnostic(
            outcome="certain",
            summary="A fabricated certainty",
            hypothesis_ids=[],
            evidence_ids=[],
            next_actions=["x"],
            limitations=[],
        )


def test_model_schemas_inline_nested_contracts_for_tool_provider():
    import json

    for schema in (FINDINGS, REVIEW):
        assert "$ref" not in json.dumps(schema)
    assert (
        "claim"
        in FINDINGS["function"]["parameters"]["properties"]["hypotheses"]["items"]["properties"]
    )
