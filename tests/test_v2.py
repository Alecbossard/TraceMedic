import hashlib
import json
import os
import subprocess
import sys
import time

import pytest
from pydantic import ValidationError

from tracemedic.config import ROOT
from tracemedic.factory import build_engine
from tracemedic.mcp_client import connect_tools
from tracemedic.models import ModelAction
from tracemedic.store import Store, stable_id
from tracemedic.v2.benchmark import score
from tracemedic.v2.engine import Engine
from tracemedic.v2.testing import ScriptedProvider


async def prepared(settings):
    engine = Engine(settings, ScriptedProvider())
    run = engine.create("case-01")
    await engine.run(run, pause_after=3)
    return engine, run


def test_v2_reserved_suite_and_v1_code_are_frozen():
    for filename in (
        "benchmarks/v2/frozen_manifest.json",
        "benchmarks/implementation.json",
        "benchmarks/v2/implementation.json",
    ):
        frozen = json.loads((ROOT / filename).read_text())
        for relative, digest in frozen.get("files", frozen).items():
            assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest, relative


async def test_v2_causal_record_real_mcp_graph_context_and_idempotence(settings):
    engine = Engine(settings, ScriptedProvider())
    run = engine.create("case-01")
    result = await engine.run(run)
    state = result["state"]
    assert result["status"] == "completed"
    assert state["diagnostic"]["support_level"] == "controlled_intervention"
    assert state["diagnostic"]["summary"] == state["hypotheses"][0]["claim"]
    assert set(state["visited"]) == {"coordinator", "investigator", "verifier"}
    assert engine.store.metrics(run)["tool_calls"] == 3
    context = engine.context(state, "verifier")
    assert len(context["sources"]) == 5
    assert not any("excerpt" in json.dumps(o) for o in context["recent_actions"])
    assert all(len(e) < 5 for e in state["evidence_aliases"])
    before = engine.store.events(run)
    await Engine(settings, ScriptedProvider()).run(run)
    assert before == engine.store.events(run)


async def test_v2_single_uses_same_tools_and_causal_gate(settings):
    engine = Engine(settings, ScriptedProvider())
    run = engine.create("case-01", "single")
    result = await engine.run(run)
    assert result["status"] == "completed"
    assert result["state"]["visited"] == ["single"]
    assert engine.store.metrics(run)["tool_calls"] == 3


async def test_v2_common_scorer_requires_mechanism_sources_and_reproduced_baseline(settings):
    import copy

    engine = Engine(settings, ScriptedProvider())
    run = engine.create("case-01")
    record = await engine.run(run)
    record["evidence"] = engine.store.evidence(run)
    oracle = {"abstain": False, "concept_groups": [["6433"], ["5432"], ["port"]]}
    assert score(record, oracle)["correct_supported"]
    invalid = copy.deepcopy(record)
    invalid["state"]["diagnostic"]["summary"] = "The service experienced a connection error."
    assert score(invalid, oracle)["unsupported"]
    invalid = copy.deepcopy(record)
    invalid["state"]["checks"][0]["status"] = "passed"
    assert not score(invalid, oracle)["correct"]
    invalid = copy.deepcopy(record)
    invalid["evidence"][0]["sha256"] = "tampered"
    assert not score(invalid, oracle)["valid_citations"]


async def test_v2_missing_source_finishes_uncertain_with_empty_review(settings):
    class Abstaining:
        async def decide(self, role, system, context, tools):
            names = {s["function"]["name"] for s in tools}
            if "delegate" in names:
                target = next(s for s in tools if s["function"]["name"] == "delegate")["function"][
                    "parameters"
                ]["properties"]["target"]["enum"][0]
                return ModelAction(
                    name="delegate",
                    arguments={
                        "target": target,
                        "task": "Establish which missing evidence prevents a causal explanation.",
                        "hypothesis_ids": [],
                    },
                )
            if "read_bundle" in names and not context["sources"]:
                return ModelAction(
                    name="read_bundle",
                    arguments={
                        "paths": [
                            "runtime.log",
                            "service.py",
                            "settings.json",
                            "input.json",
                            "report.json",
                        ]
                    },
                )
            if "submit_findings" in names:
                schema = next(s for s in tools if s["function"]["name"] == "submit_findings")
                assert schema["function"]["parameters"]["properties"]["hypotheses"]["maxItems"] == 0
                return ModelAction(
                    name="submit_findings",
                    arguments={
                        "hypotheses": [],
                        "unknowns": [
                            "Relevant upstream source and captured failing request are missing."
                        ],
                    },
                )
            if "run_check" in names:
                return ModelAction(name="run_check", arguments={})
            if "submit_review" in names:
                assert names == {"submit_review"}
                assert tools[0]["function"]["parameters"]["properties"]["verdicts"]["maxItems"] == 0
                return ModelAction(
                    name="submit_review",
                    arguments={"verdicts": [], "needs_more": False, "request": ""},
                )
            return ModelAction(
                name="finish",
                arguments={
                    "outcome": "insufficient",
                    "hypothesis_ids": [],
                    "next_actions": ["Capture the upstream stack and request inputs."],
                },
            )

    engine = Engine(settings, Abstaining())
    run = engine.create("case-20")
    result = await engine.run(run)
    assert result["status"] == "completed"
    assert result["state"]["checks"][0]["status"] == "unavailable"
    assert result["state"]["diagnostic"]["outcome"] == "insufficient"
    assert not any(e["kind"] == "action_rejected" for e in engine.store.events(run))


async def test_v2_rejects_fabricated_quote_and_new_final_claim(settings):
    engine, run = await prepared(settings)
    state = engine.store.run(run)["state"]
    findings = dict(state["findings"])
    findings["hypotheses"][0]["citations"][0]["line_ref"] = "E2:L999"
    with pytest.raises(ValueError, match="outside captured source"):
        engine.control(
            state, "investigator", ModelAction(name="submit_findings", arguments=findings)
        )
    findings["hypotheses"][0]["citations"][0] = {
        "line_ref": "E2:L2",
        "quote": "Model-invented quote",
    }
    with pytest.raises(ValidationError, match="Extra inputs"):
        engine.control(
            state, "investigator", ModelAction(name="submit_findings", arguments=findings)
        )
    await engine.run(run)
    state = engine.store.run(run)["state"]
    with pytest.raises(ValidationError, match="Extra inputs"):
        engine.control(
            state,
            "coordinator",
            ModelAction(
                name="finish",
                arguments={
                    "outcome": "supported",
                    "hypothesis_ids": ["H1"],
                    "summary": "Unreviewed new explanation",
                    "next_actions": ["Inspect deployment"],
                },
            ),
        )


@pytest.mark.parametrize("check_status", ["unavailable", "passed", "indeterminate"])
async def test_v2_bad_confirmation_becomes_unresolved_not_failure(settings, check_status):
    engine, run = await prepared(settings)
    state = engine.store.run(run)["state"]
    state["checks"] = [{"check_id": "c-example", "status": check_status}]
    engine.control(
        state,
        "verifier",
        ModelAction(
            name="submit_review",
            arguments={
                "verdicts": [
                    {
                        "hypothesis_id": "H1",
                        "status": "confirmed",
                        "reason": "Agreement alone cannot establish a mechanism",
                        "check_ids": ["C1"],
                    }
                ],
                "needs_more": False,
                "request": "",
            },
        ),
    )
    assert state["hypotheses"][0]["status"] == "unresolved"
    assert state["review"]["verdicts"][0]["status"] == "unresolved"
    assert any(e["kind"] == "confirmation_blocked" for e in engine.store.events(run))
    state["visited"] = ["coordinator", "investigator", "verifier"]
    engine.control(
        state,
        "coordinator",
        ModelAction(
            name="finish",
            arguments={
                "outcome": "insufficient",
                "hypothesis_ids": [],
                "next_actions": ["Collect a matching reproduction"],
            },
        ),
    )
    assert state["status"] == "completed"
    assert state["diagnostic"]["outcome"] == "insufficient"


async def test_v2_mcp_bundle_experiment_boundary_idempotence_and_original_unchanged(settings):
    engine = Engine(settings, ScriptedProvider())
    run = engine.create("case-01")
    before = (ROOT / "corpus/case-01/settings.json").read_bytes()
    changes = [{"path": "/settings/port", "value": 5432}]
    async with connect_tools(settings, engine.store, run, "case-01", version=2) as tools:
        names = {s["function"]["name"] for s in tools.schemas}
        assert {"read_bundle", "run_experiment"} <= names
        discovery = await tools.call("list_files", {}, "system", 0)
        assert discovery.data["server_pid"] != os.getpid()
        partial = await tools.call(
            "read_bundle", {"paths": ["service.py", "../oracle.json"]}, "investigator", 1
        )
        assert partial.ok and "../oracle.json" in partial.data["file_errors"]
        first = await tools.call(
            "run_experiment",
            {"changes": changes, "operation_key": "model-must-not-own-this"},
            "verifier",
            2,
        )
        assert first.ok and first.data["baseline"]["status"] == "reproduced"
        assert first.data["trial"]["status"] == "passed"
        invalid = await tools.call(
            "run_experiment",
            {"changes": [{"path": "/source/service.py", "value": "print('bad')"}]},
            "verifier",
            3,
        )
        assert not invalid.ok
        unknown = await tools.call(
            "run_experiment",
            {"changes": [{"path": "/settings/nonexistent", "value": 1}]},
            "verifier",
            4,
        )
        assert not unknown.ok
    async with connect_tools(settings, engine.store, run, "case-01", version=2) as tools:
        second = await tools.call("run_experiment", {"changes": changes}, "verifier", 5)
    assert first == second
    assert (ROOT / "corpus/case-01/settings.json").read_bytes() == before
    key = "experiment:" + stable_id(run, "experiment", changes)
    assert engine.store.cached(run, key)["status"] == "completed"
    uncertain_run = engine.create("case-01")
    uncertain_key = "experiment:" + stable_id(uncertain_run, "experiment", changes)
    engine.store.claim(uncertain_run, uncertain_key)
    async with connect_tools(settings, engine.store, uncertain_run, "case-01", version=2) as tools:
        output = await tools.call("run_experiment", {"changes": changes}, "verifier", 0)
    assert not output.ok and output.data["status"] == "indeterminate"


def test_v2_hard_kill_resume_new_process_preserves_aliases_and_one_experiment(settings):
    run = "v2-hard-kill"
    command = [
        sys.executable,
        "-m",
        "tracemedic.cli",
        "--data-dir",
        str(settings.data_dir),
        "--provider",
        "scripted",
        "--workflow",
        "v2",
    ]
    process = subprocess.Popen(
        [*command, "run", "case-01", "--run-id", run, "--step-delay", "0.5"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    store = Store(settings.audit_db)
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            try:
                state = store.run(run)["state"]
                if len(state.get("checks", [])) == 2:
                    break
            except KeyError:
                pass
            time.sleep(0.03)
        else:
            raise AssertionError("Worker did not reach durable experiment")
        aliases = state["evidence_aliases"]
        process.kill()
        process.wait(timeout=5)
        result = subprocess.run(
            [*command, "resume", run], capture_output=True, text=True, timeout=30
        )
        assert result.returncode == 0, result.stderr
        state = store.run(run)["state"]
        assert state["diagnostic"]["outcome"] == "supported"
        assert state["evidence_aliases"] == aliases
        assert (
            len(
                [
                    e
                    for e in store.events(run)
                    if e["kind"] == "tool_result" and e["data"]["tool"] == "run_experiment"
                ]
            )
            == 1
        )
        assert type(build_engine(settings, run_id=run)) is Engine
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
