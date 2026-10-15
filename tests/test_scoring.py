from tracemedic.benchmark import score


def test_agreement_and_keywords_without_source_execution_cannot_pass():
    oracle = {"abstain": False, "concept_groups": [["port"], ["6433"], ["5432"]]}
    fabricated = {
        "incident_id": "case-01",
        "status": "completed",
        "state": {
            "diagnostic": {
                "outcome": "supported",
                "summary": "port 6433 versus 5432",
                "evidence_ids": [],
            },
            "hypotheses": [{"status": "confirmed", "claim": "port 6433 versus 5432"}],
            "checks": [],
        },
        "evidence": [],
    }
    result = score(fabricated, oracle)
    assert result["unsupported_conclusion"]
    assert not result["correct"]


def test_budget_failure_is_not_a_correct_abstention():
    oracle = {"abstain": True, "concept_groups": []}
    record = {
        "incident_id": "case-20",
        "status": "budget_exhausted",
        "state": {
            "diagnostic": {
                "outcome": "insufficient",
                "summary": "Not established",
                "evidence_ids": [],
            },
            "hypotheses": [],
            "checks": [],
        },
        "evidence": [],
    }
    assert not score(record, oracle)["correct_abstention"]
