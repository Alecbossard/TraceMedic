import json
import os
import shutil
import signal

from tracemedic.mcp_client import connect_tools
from tracemedic.store import stable_id


async def test_real_stdio_discovery_reads_protocol_errors_and_boundary(engine):
    run = engine.create("case-02")
    async with connect_tools(engine.settings, engine.store, run, "case-02") as tools:
        names = {s["function"]["name"] for s in tools.schemas}
        assert names == {"list_files", "read_file", "search_trace", "get_test_report", "run_check"}
        listed = await tools.call("list_files", {}, "investigator", 0)
        assert listed.data["server_pid"] != os.getpid()
        assert all(x["path"] != "oracle.json" for x in listed.data["files"])
        log = await tools.call("read_file", {"path": "runtime.log"}, "investigator", 1)
        assert "SYSTEM:" in log.evidence[0].excerpt  # preserved as data, not executed
        assert (
            await tools.call(
                "read_file", {"path": "../../benchmarks/oracle.json"}, "investigator", 2
            )
        ).ok is False
        assert (
            await tools.call(
                "read_file", {"path": "service.py", "end_line": 101}, "investigator", 3
            )
        ).ok is False
        assert (await tools.client.call_tool("unknown_tool", {})).is_error
        assert (await tools.client.call_tool("read_file", {})).is_error
        report = await tools.call("get_test_report", {}, "investigator", 4)
        assert report.evidence[0].path == "report.json"
        assert engine.store.evidence(run)


async def test_check_is_durable_idempotent_and_does_not_replay_uncertain_operation(engine):
    run = engine.create("case-01")
    async with connect_tools(engine.settings, engine.store, run, "case-01") as tools:
        first = await tools.call("run_check", {}, "verifier", 0)
    async with connect_tools(engine.settings, engine.store, run, "case-01") as tools:
        second = await tools.call("run_check", {}, "verifier", 1)
    assert first == second
    assert first.data["status"] == "reproduced"
    assert engine.store.metrics(run)["tool_calls"] == 1
    interrupted_run = engine.create("case-01")
    key = stable_id(interrupted_run, "fixture-check")
    engine.store.claim(interrupted_run, "fixture:" + key)
    async with connect_tools(engine.settings, engine.store, interrupted_run, "case-01") as tools:
        output = await tools.call("run_check", {}, "verifier", 0)
    assert not output.ok
    assert output.data["status"] == "indeterminate"


async def test_changed_fixture_is_never_executed(engine, tmp_path):
    root = tmp_path / "changed"
    shutil.copytree(engine.settings.root / "corpus", root / "corpus")
    (root / "corpus" / "case-01" / "service.py").write_text('raise RuntimeError("MALICIOUS")')
    settings = engine.settings.model_copy(update={"root": root})
    run = engine.create("case-01")
    async with connect_tools(settings, engine.store, run, "case-01") as tools:
        output = await tools.call("run_check", {}, "verifier", 0)
    assert not output.ok
    assert "Fixture changed" in json.dumps(output.data)


async def test_real_tool_process_unavailable_then_reconnected(engine):
    run = engine.create("case-01")
    failure = None
    try:
        async with connect_tools(engine.settings, engine.store, run, "case-01") as tools:
            listed = await tools.call("list_files", {}, "investigator", 0)
            pid = listed.data["server_pid"]
            assert pid not in (os.getpid(), os.getppid())
            os.kill(pid, signal.SIGTERM)
            await tools.call("read_file", {"path": "runtime.log"}, "investigator", 1)
    except Exception as exc:
        failure = exc
    assert failure is not None, "A dead tool subprocess must not yield a successful read"
    async with connect_tools(engine.settings, engine.store, run, "case-01") as tools:
        result = await tools.call("read_file", {"path": "runtime.log"}, "investigator", 2)
    assert result.ok and result.evidence
