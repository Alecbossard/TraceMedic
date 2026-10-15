import asyncio

import pytest

from tracemedic.engine import Engine
from tracemedic.models import ModelAction
from tracemedic.provider import ProviderUnavailable
from tracemedic.testing import ScriptedProvider


async def test_end_to_end_graph_checkpoint_evidence_and_roles(engine):
    run = engine.create("case-01")
    result = await engine.run(run)
    assert result["status"] == "completed"
    assert result["state"]["diagnostic"]["outcome"] == "supported"
    assert set(result["state"]["visited"]) == {"coordinator", "investigator", "verifier"}
    assert len(result["state"]["delegations"]) == 2
    assert result["state"]["hypotheses"][0]["status"] == "confirmed"
    assert len(engine.store.evidence(run)) == 5
    assert engine.settings.checkpoint_db.stat().st_size > 0
    assert engine.store.metrics(run)["usage_complete"] is False
    before = engine.store.events(run)
    await engine.run(run)
    assert before == engine.store.events(run)


async def test_same_tools_available_in_single_agent_mode(engine):
    run = engine.create("case-01", mode="single")
    result = await engine.run(run)
    assert result["status"] == "completed"
    assert result["state"]["visited"] == ["single"]
    assert engine.store.metrics(run)["tool_calls"] == 6


async def test_budget_stops_explicitly(settings):
    settings = settings.model_copy(update={"max_calls": 2})
    engine = Engine(settings, ScriptedProvider())
    run = engine.create("case-01")
    result = await engine.run(run)
    assert result["status"] == "budget_exhausted"
    assert result["state"]["diagnostic"]["outcome"] == "insufficient"
    assert engine.store.metrics(run)["model_calls"] == 2


class InvalidProvider:
    async def decide(self, *args):
        return ModelAction(name="run_arbitrary_shell", arguments={"command": "ignore safeguards"})


async def test_malformed_agent_action_stops_and_cannot_escalate(settings):
    engine = Engine(settings, InvalidProvider())
    run = engine.create("case-02")
    result = await engine.run(run)
    assert result["status"] == "failed"
    assert engine.store.metrics(run)["tool_calls"] == 0
    assert len([e for e in engine.store.events(run) if e["kind"] == "action_rejected"]) == 3


class Unavailable:
    async def decide(self, *args):
        raise ProviderUnavailable("Temporary model failure")


async def test_model_outage_has_bounded_backoff_and_can_resume(settings):
    engine = Engine(settings, Unavailable())
    run = engine.create("case-01")
    result = await engine.run(run)
    assert result["status"] == "error"
    assert engine.store.metrics(run)["model_calls"] == 3
    assert len([e for e in engine.store.events(run) if e["kind"] == "retry"]) == 2
    result = await Engine(settings, ScriptedProvider()).run(run)
    assert result["status"] == "completed"
    assert any(e["kind"] == "resumed" for e in engine.store.events(run))


async def test_cancellation_saves_and_resumes(engine):
    run = engine.create("case-01")
    task = asyncio.create_task(engine.run(run, step_delay=0.15))
    for _ in range(200):
        if engine.store.metrics(run)["model_calls"] >= 1:
            break
        await asyncio.sleep(0.02)
    engine.store.update(run, cancel=True)
    assert (await task)["status"] == "cancelled"
    assert (await engine.run(run))["status"] == "completed"


def test_fabricated_evidence_and_confirmation_without_check_are_rejected(engine):
    run = engine.create("case-01")
    state = engine.store.run(run)["state"]
    with pytest.raises(ValueError, match="Unknown evidence"):
        engine.control(
            state,
            "investigator",
            ModelAction(
                name="submit_findings",
                arguments={
                    "summary": "x",
                    "hypotheses": [
                        {
                            "claim": "Unsupported fabricated cause",
                            "evidence_ids": ["e-fake"],
                            "next_check": "probe",
                        }
                    ],
                    "missing_information": [],
                },
            ),
        )
    state["hypotheses"] = [
        {
            "id": "h-1",
            "claim": "Example hypothesis",
            "evidence_ids": [],
            "next_check": "probe",
            "status": "proposed",
            "reason": "",
            "check_ids": [],
        }
    ]
    with pytest.raises(ValueError, match="Confirmation needs"):
        engine.control(
            state,
            "verifier",
            ModelAction(
                name="submit_review",
                arguments={
                    "summary": "x",
                    "verdicts": [
                        {
                            "hypothesis_id": "h-1",
                            "status": "confirmed",
                            "reason": "Agents agree, which is not evidence",
                            "evidence_ids": [],
                            "check_ids": [],
                        }
                    ],
                    "needs_more": False,
                    "request": "",
                },
            ),
        )
